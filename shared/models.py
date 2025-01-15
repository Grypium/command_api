from pydantic import BaseModel
from typing import Optional, Dict, Any, List, AsyncGenerator, Type
from functools import wraps
from .auth import is_user_authorized

# Global registry of all command classes
COMMAND_REGISTRY: Dict[str, Type[CommandBase]] = {}

class CommandError(Exception):
    """Base exception for command errors"""
    pass

class ValidationError(CommandError):
    """Invalid command parameters"""
    pass

class AuthorizationError(CommandError):
    """User not authorized"""
    pass

class CommandBase(BaseModel):
    """Base model for all commands"""
    username: str
    command: str

class CommandResponse(BaseModel):
    """Base response model for all commands"""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    progress: Optional[float] = None

class ProgressUpdate(BaseModel):
    """Model for progress updates during command execution"""
    status: str
    message: str
    progress: float  # 0.0 to 1.0
    data: Optional[Dict[str, Any]] = None

def command(
    name: str,
    description: str,
    allowed_users: Optional[List[str]] = None,
    allowed_groups: Optional[List[str]] = None
):
    """Decorator to create command models and handlers in one place
    
    Args:
        name: Command name
        description: Command description
        allowed_users: List of usernames allowed to run this command
        allowed_groups: List of groups allowed to run this command
    """
    def decorator(cls):
        # Create the command model by inheriting from CommandBase
        model_fields = {
            k: v for k, v in cls.__dict__.items() 
            if not k.startswith('_') and not callable(v)
        }
        
        # Create new command model class
        command_model = type(
            cls.__name__,
            (CommandBase,),
            {
                **model_fields,
                '__doc__': description,
                '_command_info': {
                    'name': name,
                    'description': description,
                    'allowed_users': allowed_users,
                    'allowed_groups': allowed_groups
                }
            }
        )
        
        # Add the execute method from the original class
        if not hasattr(cls, 'execute'):
            raise ValueError(f"Command class {cls.__name__} must define an 'execute' method")
        
        # Add authorization check to execute method
        original_execute = cls.execute
        
        async def execute_with_auth(self):
            if not is_user_authorized(
                self.username,
                allowed_users=allowed_users,
                allowed_groups=allowed_groups
            ):
                raise AuthorizationError(
                    f"User '{self.username}' is not authorized to run this command. "
                    f"Required: users={allowed_users or 'any'}, groups={allowed_groups or 'any'}"
                )
            async for update in original_execute(self):
                yield update
        
        command_model.execute = execute_with_auth
        
        # Register the command
        COMMAND_REGISTRY[name] = command_model
        
        return command_model
    return decorator

# Example commands using the new decorator
@command(
    name="echo",
    description="Echo a message back to the user",
    allowed_groups=["users"]  # Any user in the 'users' group can run this
)
class EchoCommand:
    message: str
    
    async def execute(self) -> AsyncGenerator[ProgressUpdate | CommandResponse, None]:
        for i in range(5):
            yield ProgressUpdate(
                status="running",
                message=f"Processing echo {i+1}/5...",
                progress=(i + 1) / 5,
                data={"current_step": i + 1}
            )
        
        yield CommandResponse(
            status="success",
            message="Echo completed",
            data={"echo": self.message},
            progress=1.0
        )

@command(
    name="install_nvidia",
    description="Install NVIDIA drivers on a remote Ubuntu host",
    allowed_groups=["admin", "system"]  # Only admin or system users can run this
)
class NvidiaInstallCommand:
    hostname: str
    driver_version: str
    
    async def execute(self) -> AsyncGenerator[ProgressUpdate | CommandResponse, None]:
        # This is just a placeholder - the actual implementation is in examples/nvidia_install.py
        from examples.nvidia_install import install_nvidia_driver
        async for update in install_nvidia_driver(self.hostname, self.driver_version):
            if update["status"] == "running":
                yield ProgressUpdate(**update)
            else:
                yield CommandResponse(**update) 