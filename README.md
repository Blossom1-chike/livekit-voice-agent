Conversation Flow Agent (State / DAG)

Goal
To extend the voice agent to support a structured conversation flow, moving away from a generic chatbot to a deterministic Finite State Machine (FSM). This ensures the agent collects specific data and follows a strict business process.

Use Case: Appointment Scheduling
I implemented an intelligent Receptionist Agent designed to book appointments. The agent refuses to proceed until valid information is collected for each step, ensuring high data integrity.

Design Explanation
The agent is architected as a State Machine with 5 distinct states. Transitions are triggered exclusively by Function Calling (Tools). This approach prevents the LLM from hallucinating or skipping steps, as the current_state variable strictly controls the agent's behavior.

The 5 Conversation States:
Discovery (Start): The agent waits for the user to express intent (e.g., "I want to book an appointment").

Data Collection (Slot Filling): The agent actively requests the user's Name and Email. It stays in this state until both slots are filled.

Scheduling: The agent requests a preferred Date and Time. It uses dynamic date injection to understand relative terms like "next Tuesday."

Confirmation (Verification): The agent explicitly reads back all collected data and asks for a "Yes/No" confirmation.

Fallback / Retry Logic: If the user rejects the details (e.g., "No, the time is wrong"), the agent triggers a fallback transition back to the Scheduling state to correct the error, rather than ending the call.

Terminal (End): Once confirmed, the agent executes a real-world action (sending an SMTP email via Gmail) and terminates the session.

Technical Implementation
Framework: LiveKit Agents (v1.3+) using the modern @function_tool decorator syntax.

State Management: maintained a local session_data dictionary within the entrypoint closure to track current_state and user slots (Name, Email, Time) safely across async turns.

Tooling:

start_booking: Transitions Discovery → Collect Info.

save_contact_details: Transitions Collect Info → Scheduling.

save_time: Transitions Scheduling → Confirmation.

finalize_booking: Handles the branching logic for Success (Terminal) vs. Retry (Scheduling).

Real-World Integration: Uses Python's smtplib to send actual confirmation emails upon successful booking.
