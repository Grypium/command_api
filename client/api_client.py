import httpx
import json
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator, Callable
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

class CommandAPIClient:
    def __init__(self, base_url: str, username: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.client = httpx.AsyncClient()
        
    async def execute_command_with_progress(
        self,
        command: str,
        progress_callback: Callable[[Dict[str, Any]], None],
        **params
    ) -> Dict[str, Any]:
        """Execute a command on the API with progress tracking"""
        data = {
            "username": self.username,
            "command": command,
            **params
        }
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/execute",
                json=data,
                headers={"Accept": "text/event-stream"}
            ) as response:
                response.raise_for_status()
                last_update = None
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        update_data = json.loads(line[6:])
                        progress_callback(update_data)
                        last_update = update_data
                
                if last_update and last_update["status"] == "error":
                    raise Exception(last_update["message"])
                    
                return last_update or {}
                
        except httpx.HTTPError as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('detail', str(e))
                except json.JSONDecodeError:
                    pass
            raise Exception(f"API Error: {error_msg}")
    
    async def close(self):
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close() 