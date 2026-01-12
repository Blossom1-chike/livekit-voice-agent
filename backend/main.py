from livekit.agents import cli, WorkerOptions
from agent.advanced import entrypoint

if __name__ == "__main__":
    # This starts the worker process and listens for LiveKit jobs
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))