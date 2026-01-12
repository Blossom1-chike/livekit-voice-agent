import logging
import smtplib
import os
import datetime
from enum import Enum
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    Agent,
    AgentSession,
)
from livekit.agents.llm import function_tool
from livekit.agents import RunContext
from livekit.plugins import openai, deepgram, silero

load_dotenv()
logger = logging.getLogger("state-machine-agent")

class AgentState(Enum):
    DISCOVERY = "DISCOVERY"
    COLLECT_INFO = "COLLECT_INFO"
    SCHEDULING = "SCHEDULING"
    CONFIRMATION = "CONFIRMATION"
    TERMINAL = "TERMINAL"

# Helper function to send confirmation email to user
def send_confirmation_email(to_email, name, time):
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")

    if not sender_email or not sender_password:
        logger.error("SMTP Credentials missing.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = "Appointment Confirmation"
        body = f"Hello {name},\n\nYour appointment is confirmed for: {time}.\n\nThank you!"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        logger.error(f"Email Failed: {e}")
        return False

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    now = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

    # Define State local to this session
    session_data = {
        "current_state": AgentState.DISCOVERY,
        "name": None,
        "email": None,
        "time": None
    }
    
    logger.info(f"Session started for Room: {ctx.room.name}")
    
    @function_tool
    async def start_booking(ctx: RunContext):  
        """User wants to book. Move to Data Collection."""
        session_data["current_state"] = AgentState.COLLECT_INFO
        logger.info(f"TRANSITION: DISCOVERY -> COLLECT_INFO")
        return "Intent received. Now ask for their Name and Email."

    @function_tool
    async def save_contact_details(ctx: RunContext, name: str, email: str): 
        """Save Name and Email. Move to Scheduling."""
        session_data["name"] = name
        session_data["email"] = email
        session_data["current_state"] = AgentState.SCHEDULING
        logger.info(f"TRANSITION: COLLECT_INFO -> SCHEDULING")
        return "Contact saved. Now ask for the preferred Date and Time."

    @function_tool
    async def save_time(ctx: RunContext, time: str): 
        """Save Time. Move to Confirmation."""
        session_data["time"] = time
        session_data["current_state"] = AgentState.CONFIRMATION
        logger.info(f"TRANSITION: SCHEDULING -> CONFIRMATION")
        return f"Time saved: {time}. Now read ALL details back and ask 'Is this correct?'"

    @function_tool
    async def finalize_booking(ctx: RunContext, confirmed: bool): 
        """
        Handle confirmation.
        If True: Sends email and ends.
        If False: Retries (Fallback).
        """
        if confirmed:
            send_confirmation_email(session_data["email"], session_data["name"], session_data["time"])
            session_data["current_state"] = AgentState.TERMINAL
            logger.info(f"TRANSITION: CONFIRMATION -> TERMINAL")
            return "Booking Confirmed. Email sent. Say goodbye."
        else:
            # Fallback Path
            session_data["current_state"] = AgentState.SCHEDULING
            logger.info(f"FALLBACK: CONFIRMATION -> SCHEDULING")
            return "User declined. Apologize and ask for the correct Date/Time again."

    # --- AGENT SETUP ---
    agent = Agent(
        instructions="""
            You are an Appointment Assistant following a strict state machine.
            1. Wait for intent -> Call start_booking.
            2. Ask Name/Email -> Call save_contact_details.
                - The email and name MUST be spelt out clearly FOR better accuracy.
                - Confirm the details back to the user before proceeding.
            3. Ask Time -> Call save_time.
                - If the user says tomorrow, next Monday, etc., convert to exact date/time.
                - CURRENT DATE/TIME: {now} (Use this to calculate relative dates like 'next Tuesday, tomorrow').
                - Confirm the time back to the user before proceeding.
            4. Confirm -> Call finalize_booking.
            If user says NO at step 4, go back to step 3.
        """,
        tools=[start_booking, save_contact_details, save_time, finalize_booking],
    )

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=openai.STT(),
        llm=openai.LLM(),
        tts=openai.TTS(),
    )

    participant = await ctx.wait_for_participant()
    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(instructions="Greet the user.")
