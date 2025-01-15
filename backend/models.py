from pydantic import BaseModel
from typing import Optional, Dict, Any, AsyncGenerator

class CommandBase(BaseModel):
    """Base model for all commands"""
    username: str
    command: str

class ProgressUpdate(BaseModel):
    """Model for progress updates during command execution"""
    status: str
    message: str
    progress: float  # 0.0 to 1.0
    data: Optional[Dict[str, Any]] = None

class CommandResponse(BaseModel):
    """Base response model for all commands"""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    progress: Optional[float] = None 