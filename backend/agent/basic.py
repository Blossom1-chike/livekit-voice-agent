import logging
from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    Agent,
    AgentSession,
)
from livekit.plugins import openai, deepgram, silero

load_dotenv()
logger = logging.getLogger("voice-agent")

async def entrypoint(ctx: JobContext):
    # Connect to the Room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info(f"Connected to room: {ctx.room.name}")

    # Define the Agent
    agent = Agent(
        instructions="You are a helpful voice assistant. Keep answers concise.",
    )

    # Define the Session
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=openai.STT(),
        llm=openai.LLM(),
        tts=openai.TTS(),
    )

    # Start the Agent
    participant = await ctx.wait_for_participant()
    logger.info(f"User joined: {participant.identity}")

    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(instructions="Say hello to the user")