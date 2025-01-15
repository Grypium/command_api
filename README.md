# Command API System

A powerful and extensible command execution system with a FastAPI backend and a rich CLI client. The system allows you to create and execute remote commands with real-time progress updates, user authorization, and a beautiful command-line interface.

## Features

- 🚀 **Async Command Execution**: Handle multiple concurrent commands
- 📊 **Real-time Progress Updates**: Live progress bars and status messages
- 🔒 **Advanced Authorization**: User and group-based access control
- 🎨 **Beautiful CLI**: Rich formatting, progress bars, and help system
- 🔌 **Extensible**: Easy to add new commands
- 📝 **Self-documenting**: Automatic help and documentation generation
- 🛠️ **Type-safe**: Full Pydantic model validation

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd command-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

1. Start the backend server:
```bash
python run_backend.py
```

2. Add a user to a group (required for command access):
```bash
# Using curl or any HTTP client
curl -X POST http://localhost:8000/users/john/groups/users

# Add to admin group for privileged commands
curl -X POST http://localhost:8000/users/john/groups/admin
```

3. Use the CLI:
```bash
# Show available commands (filtered by user's access)
python -m client.cli list-commands

# Get help for a specific command
python -m client.cli help install-nvidia

# Run a command
python -m client.cli echo "Hello, World!"
```

## Project Structure

```
command-api/
├── backend/
│   ├── __init__.py
│   └── main.py          # FastAPI backend server
├── client/
│   ├── __init__.py
│   ├── cli.py           # CLI interface
│   └── api_client.py    # API client
├── shared/
│   ├── __init__.py
│   ├── models.py        # Shared models and command definitions
│   └── auth.py         # User/group management system
├── examples/
│   └── nvidia_install.py # Example command implementation
├── requirements.txt
├── run_backend.py       # Backend server runner
└── README.md
```

## Configuration

### Environment Variables

- `COMMAND_API_URL`: API server URL (default: `http://localhost:8000`)
- `USERNAME` or `USER`: Username for command execution

### Building the Client

To create a portable executable:
```bash
python build_cli.py
```

The executable will be created in the `dist` directory.

## User and Group Management

The system uses a YAML-based configuration for user groups and permissions. Groups and their members are defined in `config/groups.yaml`:

```yaml
# Default groups and their members
groups:
  admin:
    - admin
    - root
    - system
  
  system:
    - system
    - admin
  
  users:
    - john
    - jane
    - admin
    - system

# Users who can manage groups (used internally)
group_admins:
  - admin
  - root
  - system
```

To modify group membership:
1. Edit the `config/groups.yaml` file
2. Restart the backend server to apply changes

## Adding New Commands

Adding a new command is a single step - just define the command class with the `@command` decorator:

```python
from shared.models import command, ProgressUpdate, CommandResponse

@command(
    name="my_command",
    description="What my command does",
    allowed_users=["specific-user"],  # Optional: specific users
    allowed_groups=["admin", "power-users"]  # Optional: user groups
)
class MyCommand:
    # Command parameters (will be validated by Pydantic)
    param1: str
    param2: int
    
    async def execute(self):
        # Send progress updates
        yield ProgressUpdate(
            status="running",
            message="Step 1/2...",
            progress=0.5,
            data={"step": 1}
        )
        
        # Do work here...
        
        # Send final response
        yield CommandResponse(
            status="success",
            message="Command completed",
            progress=1.0,
            data={"result": "done"}
        )
```

The command will be automatically:
- Registered with the backend
- Available in the CLI (for authorized users)
- Validated using Pydantic
- Documented in help system
- Progress-tracked
- Error-handled

### Command Organization

For better organization, you can group related commands in modules:

1. **Create Command Modules**: Create a new module in `shared/commands/`:
```
shared/
├── commands/
│   ├── __init__.py
│   ├── system_commands.py
│   └── user_commands.py
└── models.py
```

2. **Import Command Modules**: In `shared/models.py`:
```python
# Import all command modules to register them
from .commands import system_commands, user_commands

# The commands will be automatically registered when imported
```

## API Documentation

### Backend Endpoints

#### Command Management
- `GET /commands`: List available commands and their parameters
- `POST /execute`: Execute a command
  - Body: Command parameters as JSON
  - Returns: Server-sent events with progress updates

#### User/Group Management
- `POST /users/{username}/groups/{group_name}`: Add user to group
- `DELETE /users/{username}/groups/{group_name}`: Remove user from group
- `GET /users/{username}/groups`: Get user's groups

### Command Response Format

Progress updates:
```json
{
    "status": "running",
    "message": "Processing...",
    "progress": 0.5,
    "data": {
        "step": 1,
        "additional_info": "any data"
    }
}
```

Final response:
```json
{
    "status": "success",
    "message": "Command completed",
    "progress": 1.0,
    "data": {
        "result": "command output"
    }
}
```

## CLI Usage

### Basic Commands

```bash
# Show help
command-cli --help

# List available commands (filtered by user's access)
command-cli list-commands

# Get detailed help for a command
command-cli help <command>

# Execute a command
command-cli <command> [arguments]
```

### Example Commands

```bash
# Echo command (requires 'users' group)
command-cli echo "Hello, World!"

# Install NVIDIA drivers (requires 'admin' or 'system' group)
command-cli install-nvidia example.com 535
```

## Error Handling

The system provides detailed error messages for:
- Invalid parameters
- Authorization failures (user/group access denied)
- Command execution errors
- Connection issues

Errors are displayed in the CLI with:
- Red progress bars for failures
- Clear error messages
- Appropriate exit codes

## Development

### Best Practices

1. **Command Design**:
   - Clear, descriptive names
   - Comprehensive parameter validation
   - Meaningful progress updates
   - Proper error handling

2. **Security**:
   - Use group-based access control
   - Validate all inputs
   - Handle sensitive data appropriately
   - Prefer group permissions over individual user permissions

3. **User Experience**:
   - Provide clear progress information
   - Meaningful error messages
   - Comprehensive help text
   - Show only commands the user can access

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
