from typing import AsyncGenerator, Tuple
import asyncio
import asyncssh
from shared.models import command, CommandResponse, ProgressUpdate

@command(
    name="install_nvidia",
    description="Install NVIDIA driver on a remote host",
    allowed_groups=["admin", "system"],  # Only admin and system groups can run this
)
class NvidiaInstallCommand:
    hostname: str
    driver_version: str

    async def run_remote_command(self, connection: asyncssh.SSHClientConnection, command: str) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, and stderr"""
        result = await connection.run(command, check=False)
        return result.exit_status, result.stdout, result.stderr

    async def execute(self) -> AsyncGenerator[CommandResponse | ProgressUpdate, None]:
        """Install NVIDIA driver on remote host with progress updates"""
        try:
            # Connect to remote host
            yield ProgressUpdate(
                status="running",
                message=f"Connecting to {self.hostname}...",
                progress=0.1,
                data={"step": "connect"}
            )
            
            async with asyncssh.connect(self.hostname) as conn:
                # Check if NVIDIA driver is already installed
                status, stdout, stderr = await self.run_remote_command(
                    conn, "nvidia-smi --query-gpu=driver_version --format=csv,noheader"
                )
                
                if status == 0:
                    current_version = stdout.strip()
                    if current_version == self.driver_version:
                        yield CommandResponse(
                            status="success",
                            message=f"NVIDIA driver {self.driver_version} is already installed",
                            progress=1.0,
                            data={"current_version": current_version}
                        )
                        return
                
                # Update package list
                yield ProgressUpdate(
                    status="running",
                    message="Updating package list...",
                    progress=0.2,
                    data={"step": "update"}
                )
                status, stdout, stderr = await self.run_remote_command(
                    conn, "sudo apt-get update"
                )
                if status != 0:
                    raise Exception(f"Failed to update package list: {stderr}")
                
                # Install required packages
                yield ProgressUpdate(
                    status="running",
                    message="Installing required packages...",
                    progress=0.3,
                    data={"step": "dependencies"}
                )
                status, stdout, stderr = await self.run_remote_command(
                    conn,
                    "sudo apt-get install -y build-essential dkms"
                )
                if status != 0:
                    raise Exception(f"Failed to install required packages: {stderr}")
                
                # Remove existing NVIDIA drivers
                yield ProgressUpdate(
                    status="running",
                    message="Removing existing NVIDIA drivers...",
                    progress=0.4,
                    data={"step": "remove_old"}
                )
                status, stdout, stderr = await self.run_remote_command(
                    conn,
                    "sudo apt-get remove -y nvidia* && sudo apt-get autoremove -y"
                )
                
                # Add NVIDIA repository
                yield ProgressUpdate(
                    status="running",
                    message="Adding NVIDIA repository...",
                    progress=0.5,
                    data={"step": "add_repo"}
                )
                commands = [
                    "sudo add-apt-repository -y ppa:graphics-drivers/ppa",
                    "sudo apt-get update"
                ]
                for cmd in commands:
                    status, stdout, stderr = await self.run_remote_command(conn, cmd)
                    if status != 0:
                        raise Exception(f"Failed to add NVIDIA repository: {stderr}")
                
                # Install NVIDIA driver
                yield ProgressUpdate(
                    status="running",
                    message=f"Installing NVIDIA driver {self.driver_version}...",
                    progress=0.7,
                    data={"step": "install"}
                )
                status, stdout, stderr = await self.run_remote_command(
                    conn,
                    f"sudo apt-get install -y nvidia-driver-{self.driver_version}"
                )
                if status != 0:
                    raise Exception(f"Failed to install NVIDIA driver: {stderr}")
                
                # Verify installation
                yield ProgressUpdate(
                    status="running",
                    message="Verifying installation...",
                    progress=0.9,
                    data={"step": "verify"}
                )
                status, stdout, stderr = await self.run_remote_command(
                    conn,
                    "nvidia-smi --query-gpu=driver_version --format=csv,noheader"
                )
                if status != 0:
                    raise Exception("Failed to verify driver installation. A system reboot may be required.")
                
                installed_version = stdout.strip()
                if installed_version != self.driver_version:
                    raise Exception(f"Driver version mismatch. Expected {self.driver_version}, got {installed_version}")
                
                yield CommandResponse(
                    status="success",
                    message=f"Successfully installed NVIDIA driver {self.driver_version}",
                    progress=1.0,
                    data={
                        "installed_version": installed_version,
                        "reboot_required": True
                    }
                )
                
        except Exception as e:
            yield CommandResponse(
                status="error",
                message=str(e),
                progress=1.0,
                data={"error": str(e)}
            ) 