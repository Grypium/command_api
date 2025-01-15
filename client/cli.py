import typer
import asyncio
import os
from typing import Optional
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TaskID,
    TimeRemainingColumn,
)
from rich.style import Style
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.align import Align
from rich.box import DOUBLE
from .api_client import CommandAPIClient
from shared.models import EchoCommand, NvidiaInstallCommand
import httpx

# Default API URL - change this to your production API URL
DEFAULT_API_URL = "http://localhost:8000"

app = typer.Typer(
    help="Command API Client",
    no_args_is_help=True,  # Show help when no arguments are provided
    rich_markup_mode="rich",  # Enable rich markup in help text
)
console = Console()

def print_banner():
    """Print a nice banner with basic usage info"""
    title = Table(show_header=False, box=DOUBLE, show_edge=False)
    title.add_column(justify="center", style="cyan")
    title.add_row("[bold cyan]Command API Client[/bold cyan]")
    title.add_row("[dim]A powerful command execution system[/dim]")
    
    usage = Table(show_header=False, box=None, show_edge=False, padding=(0, 2))
    usage.add_column(style="green")
    usage.add_column(style="white")
    
    usage.add_row(
        "Usage:",
        "[bold]command-cli[/bold] [cyan]<command>[/cyan] [green]<arguments>[/green]"
    )
    usage.add_row(
        "Help:",
        "[bold]command-cli[/bold] [cyan]help[/cyan] [green]<command>[/green]"
    )
    
    examples = Table(show_header=False, box=None, show_edge=False, padding=(0, 2))
    examples.add_column(style="yellow")
    examples.add_column(style="white")
    
    examples.add_row(
        "Examples:",
        "[bold]command-cli[/bold] [cyan]list-commands[/cyan]"
    )
    examples.add_row(
        "",
        "[bold]command-cli[/bold] [cyan]help[/cyan] [green]install-nvidia[/green]"
    )
    examples.add_row(
        "",
        "[bold]command-cli[/bold] [cyan]echo[/cyan] [green]\"Hello World\"[/green]"
    )
    
    env_vars = Table(show_header=False, box=None, show_edge=False, padding=(0, 2))
    env_vars.add_column(style="magenta")
    env_vars.add_column(style="white")
    
    env_vars.add_row(
        "Environment:",
        f"API URL: [cyan]{get_api_url()}[/cyan]"
    )
    env_vars.add_row(
        "",
        "Set [magenta]COMMAND_API_URL[/magenta] to override"
    )
    
    # Combine all sections
    console.print("\n")
    console.print(Align.center(title))
    console.print("\n")
    console.print(usage)
    console.print("\n")
    console.print(examples)
    console.print("\n")
    console.print(env_vars)
    console.print("\n")
    console.print(Align.center("[dim]Run 'command-cli list-commands' to see all available commands[/dim]"))
    console.print("\n")

# Get username from environment or system
def get_username() -> str:
    return os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"

def get_api_url() -> str:
    """Get API URL from environment variable or use default"""
    return os.environ.get("COMMAND_API_URL", DEFAULT_API_URL)

class StatusProgress:
    def __init__(self, description: str):
        self.status_message = description
        self.progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            expand=True
        )
        self.task_id = self.progress.add_task("", total=100)
    
    def update(self, completed: int, status: str, message: str, is_error: bool = False):
        self.status_message = message
        style = "red" if is_error else "green"
        self.progress.update(
            self.task_id,
            completed=completed,
            description="",  # Keep the progress bar clean
            refresh=True
        )
        if is_error:
            self.progress.columns[1].complete_style = "red"
            self.progress.columns[1].finished_style = "red"
        
    def get_renderable(self):
        return Panel.fit(
            self.progress,
            title=f"[bold]{self.status_message}[/bold]",
            border_style="red" if "Error" in self.status_message else "green",
        )

async def run_command(command: str, **params):
    base_url = get_api_url()
    username = get_username()
    
    status_progress = StatusProgress(f"Starting {command}...")
    
    with Live(status_progress.get_renderable(), console=console, refresh_per_second=10) as live:
        def update_progress(data: dict):
            if data.get("progress") is not None:
                completed = int(data["progress"] * 100)
                status = data.get("status", "running")
                message = data.get("message", f"Executing {command}...")
                is_error = status == "error"
                
                status_progress.update(completed, status, message, is_error)
                live.update(status_progress.get_renderable())
        
        async with CommandAPIClient(base_url, username) as client:
            try:
                result = await client.execute_command_with_progress(
                    command,
                    progress_callback=update_progress,
                    **params
                )
                
                if result["status"] == "success":
                    if result.get("data"):
                        console.print("\n[bold]Command Output:[/bold]")
                        console.print(result["data"])
                elif result["status"] == "error":
                    raise Exception(result["message"])
            except Exception as e:
                status_progress.update(
                    100,
                    "error",
                    f"Error: {str(e)}",
                    is_error=True
                )
                live.update(status_progress.get_renderable())
                raise typer.Exit(1)

async def get_available_commands():
    """Get list of available commands from the API"""
    base_url = get_api_url()
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/commands")
        response.raise_for_status()
        return response.json()

def format_parameter_info(param_info: dict) -> str:
    """Format parameter information for display"""
    param_type = param_info.get("type", "any")
    description = param_info.get("description", "")
    return f"{param_type}" + (f" - {description}" if description else "")

@app.command()
def list_commands():
    """List all available commands and their parameters"""
    try:
        commands = asyncio.run(get_available_commands())
        username = get_username()
        
        # Get user's groups
        base_url = get_api_url()
        user_groups = asyncio.run(async_get_user_groups(username))
        user_groups = set(user_groups.get("groups", []))
        
        table = Table(title="Available Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Parameters", style="yellow")
        table.add_column("Access", style="magenta")
        
        for name, info in commands["commands"].items():
            # Check if user has access to this command
            required_users = info["required_users"] or []
            required_groups = info["required_groups"] or []
            
            # Skip command if user doesn't have access
            if required_users or required_groups:
                if not (username in (required_users or []) or user_groups.intersection(required_groups)):
                    continue
            
            params = []
            schema = info["model_schema"]
            required = set(schema.get("required", []))
            
            for param_name, param_info in schema.get("properties", {}).items():
                param_str = f"[bold]{param_name}[/bold]"
                if param_name in required:
                    param_str += "*"
                param_str += f": {format_parameter_info(param_info)}"
                params.append(param_str)
            
            # Format access requirements
            access_reqs = []
            if required_users:
                access_reqs.append(f"Users: {', '.join(required_users)}")
            if required_groups:
                access_reqs.append(f"Groups: {', '.join(required_groups)}")
            access_str = "\n".join(access_reqs) if access_reqs else "Any"
            
            table.add_row(
                name,
                info["description"],
                "\n".join(params) or "None",
                access_str
            )
        
        if table.row_count == 0:
            console.print("\n[yellow]No commands available for your access level.[/yellow]")
            console.print(f"Your groups: {', '.join(user_groups) if user_groups else 'None'}")
            return
        
        console.print("\n")
        console.print(table)
        console.print("\n[dim]* Required parameter[/dim]")
        console.print("\nUse [cyan]command-cli help <command>[/cyan] for detailed help on a specific command")
        
    except Exception as e:
        console.print(f"[red]Error listing commands: {str(e)}[/red]")
        raise typer.Exit(1)

async def async_get_user_groups(username: str) -> dict:
    """Get user's groups from the API"""
    base_url = get_api_url()
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/users/{username}/groups")
        response.raise_for_status()
        return response.json()

@app.command()
def help(command: str = typer.Argument(None, help="Command name to get help for")):
    """Get detailed help for a specific command or list all commands"""
    try:
        commands = asyncio.run(get_available_commands())
        
        if command is None:
            # Show command list with brief descriptions
            list_commands()
            return
            
        if command not in commands["commands"]:
            console.print(f"[red]Command '{command}' not found[/red]")
            return
            
        info = commands["commands"][command]
        
        # Show detailed help
        console.print(f"\n[bold cyan]{command}[/bold cyan]")
        console.print(f"\n{info['description']}\n")
        
        # Show parameters
        console.print("[bold]Parameters:[/bold]")
        schema = info["model_schema"]
        required = set(schema.get("required", []))
        for param_name, param_info in schema.get("properties", {}).items():
            req = "*" if param_name in required else " "
            desc = param_info.get("description", "")
            type_info = param_info.get("type", "any")
            console.print(f"{req} {param_name}: [yellow]{type_info}[/yellow]")
            if desc:
                console.print(f"  {desc}")
        
        # Show example usage
        console.print("\n[bold]Example:[/bold]")
        example_args = []
        for param in schema.get("properties", {}):
            example_args.append(f"<{param}>")
        
        example = f"command-cli {command} {' '.join(example_args)}"
        console.print(Syntax(example, "bash", theme="monokai"))
        
        if info["required_users"]:
            console.print(f"\n[bold]Required Users:[/bold] {', '.join(info['required_users'])}")
        
        console.print("\n[dim]* Required parameter[/dim]")
            
    except Exception as e:
        console.print(f"[red]Error getting help: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def echo(message: str = typer.Argument(..., help="Message to echo back")):
    """Echo a message back through the API"""
    command = EchoCommand(
        username=get_username(),
        command="echo",
        message=message
    )
    asyncio.run(run_command("echo", **command.model_dump()))

@app.command()
def install_nvidia(
    hostname: str = typer.Argument(..., help="The hostname or IP of the remote machine"),
    driver_version: str = typer.Argument(..., help="The NVIDIA driver version to install (e.g., '535')")
):
    """Install NVIDIA driver on a remote host"""
    command = NvidiaInstallCommand(
        username=get_username(),
        command="install_nvidia",
        hostname=hostname,
        driver_version=driver_version
    )
    asyncio.run(run_command("install_nvidia", **command.model_dump()))

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Command API Client"""
    # Show banner if no command was invoked
    if ctx.invoked_subcommand is None:
        print_banner()

if __name__ == "__main__":
    app() 