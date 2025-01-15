from typing import AsyncGenerator
from shared.models import command, CommandResponse, ProgressUpdate

@command(
    name="echo",
    description="Echo a message back to the user",
    allowed_groups=["users"],  # Any user in the 'users' group can run this
)
class EchoCommand:
    message: str

    async def execute(self) -> AsyncGenerator[CommandResponse | ProgressUpdate, None]:
        """Echo the message back with a simple progress update"""
        try:
            # Simulate some processing with a progress update
            yield ProgressUpdate(
                status="running",
                message="Processing message...",
                progress=0.5,
                data={"step": "process"}
            )
            
            # Return the echoed message
            yield CommandResponse(
                status="success",
                message="Message processed successfully",
                progress=1.0,
                data={"echo": self.message}
            )
            
        except Exception as e:
            yield CommandResponse(
                status="error",
                message=str(e),
                progress=1.0,
                data={"error": str(e)}
            ) 