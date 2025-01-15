from fastapi import FastAPI, HTTPException
from typing import Dict, Type, Any, AsyncGenerator
from fastapi.responses import StreamingResponse
from shared.models import (
    CommandBase, CommandResponse, ProgressUpdate,
    CommandError, ValidationError, AuthorizationError,
    COMMAND_REGISTRY
)
from shared.auth import is_user_authorized, user_groups
import json

app = FastAPI(title="Command API")

# Command registry is now automatically populated from shared.models.COMMAND_REGISTRY
command_registry = COMMAND_REGISTRY

async def stream_command_updates(generator: AsyncGenerator[ProgressUpdate | CommandResponse, None]):
    """Convert command updates to SSE format"""
    try:
        async for update in generator:
            yield f"data: {json.dumps(update.model_dump())}\n\n"
    except Exception as e:
        error_update = CommandResponse(
            status="error",
            message=str(e)
        )
        yield f"data: {json.dumps(error_update.model_dump())}\n\n"

@app.get("/commands")
async def list_commands():
    """Get information about all available commands"""
    commands = {}
    for name, command_class in command_registry.items():
        command_info = command_class._command_info
        # Get model schema excluding base command fields
        schema = command_class.model_json_schema()
        # Remove base command properties from required list
        if "required" in schema:
            schema["required"] = [f for f in schema["required"] if f not in ["username", "command"]]
        # Remove base command properties from properties dict
        if "properties" in schema:
            schema["properties"] = {
                k: v for k, v in schema["properties"].items() 
                if k not in ["username", "command"]
            }
            
        commands[name] = {
            "name": name,
            "description": command_info["description"],
            "model_schema": schema,
            "required_users": command_info["allowed_users"],
            "required_groups": command_info["allowed_groups"]
        }
    
    return {"commands": commands}

@app.post("/execute")
async def execute_command(command: CommandBase):
    if command.command not in command_registry:
        raise HTTPException(status_code=404, detail="Command not found")
    
    command_class = command_registry[command.command]
    command_info = command_class._command_info
    
    # Authorization is now handled in the command's execute method
    try:
        # Convert base command to specific command instance
        command_instance = command_class(**command.model_dump())
        # Execute the command
        return StreamingResponse(
            stream_command_updates(command_instance.execute()),
            media_type="text/event-stream"
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except CommandError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add endpoints for user/group management
@app.post("/users/{username}/groups/{group_name}")
async def add_user_to_group(username: str, group_name: str):
    """Add a user to a group"""
    try:
        user_groups.add_user_to_group(username, group_name)
        return {"message": f"Added user '{username}' to group '{group_name}'"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{username}/groups/{group_name}")
async def remove_user_from_group(username: str, group_name: str):
    """Remove a user from a group"""
    try:
        user_groups.remove_user_from_group(username, group_name)
        return {"message": f"Removed user '{username}' from group '{group_name}'"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{username}/groups")
async def get_user_groups(username: str):
    """Get all groups a user belongs to"""
    groups = user_groups.get_user_groups(username)
    return {"username": username, "groups": list(groups)} 