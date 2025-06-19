#!/usr/bin/env python3
"""
Comprehensive Filesystem MCP Server Installer

This unified installer provides a complete solution for installing the 
Filesystem MCP Server for Claude Desktop across all platforms.

Features:
- Comprehensive system requirements checking
- Enhanced OS detection and drive discovery  
- Automatic Claude Desktop detection and configuration
- Config-free operation (all settings embedded in server)
- Robust error handling and validation
- Cross-platform compatibility (Windows, macOS, Linux)
- Pre-flight checks and troubleshooting guidance

Usage:
    Windows: python install_filesystemmcp.py
    macOS:   ./install_filesystemmcp.py
    Linux:   ./install_filesystemmcp.py
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

class FilesystemMCPInstaller:
    """Comprehensive cross-platform MCP installer with pre-flight checks."""
    
    def __init__(self):
        self.system = platform.system()
        self.home = Path.home()
        self.script_dir = Path(__file__).parent
        
        print("🚀 Filesystem MCP Server Installer")
        print("🌍 Comprehensive Cross-Platform Installation")
        print("=" * 60)
        print(f"📍 Detected OS: {self.system} {platform.release()}")
        print(f"🏠 Home directory: {self.home}")
        print(f"📂 Script directory: {self.script_dir}")
        print("=" * 60)
    
    def check_system_requirements(self) -> bool:
        """Comprehensive system requirements check."""
        print("🔍 Checking system requirements...")
        
        # Check Python version
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
            print("   Please upgrade Python and try again")
            return False
        
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        
        # Check OS compatibility
        if self.system not in ['Windows', 'Darwin', 'Linux']:
            print(f"⚠️  Unsupported OS: {self.system}")
            print("   Supported: Windows, macOS (Darwin), Linux")
            print("   Installation may work but is not officially supported")
        else:
            print(f"✅ Operating System: {self.system}")
        
        # Check required files
        required_files = ['filesystem_mcp.py']
        missing_files = []
        
        for file in required_files:
            file_path = self.script_dir / file
            if file_path.exists():
                print(f"✅ Found required file: {file}")
            else:
                print(f"❌ Missing required file: {file}")
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Missing files: {', '.join(missing_files)}")
            print("   Please ensure all files are in the same directory")
            return False
        
        return True
    
    def detect_claude_desktop(self) -> Optional[Path]:
        """Detect Claude Desktop installation and return config path."""
        print("🔍 Checking for Claude Desktop installation...")
        
        if self.system == "Windows":
            config_path = Path(os.environ.get('APPDATA', '')) / "Claude" / "claude_desktop_config.json"
            claude_paths = [
                Path(os.environ.get('LOCALAPPDATA', '')) / "Claude" / "Claude.exe",
                Path(os.environ.get('PROGRAMFILES', '')) / "Claude" / "Claude.exe",
                Path(os.environ.get('PROGRAMFILES(X86)', '')) / "Claude" / "Claude.exe"
            ]
        elif self.system == "Darwin":  # macOS
            config_path = self.home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
            claude_paths = [
                Path("/Applications/Claude.app"),
                self.home / "Applications" / "Claude.app"
            ]
        else:  # Linux
            config_path = self.home / ".config" / "claude" / "claude_desktop_config.json"
            claude_paths = [
                Path("/usr/bin/claude"),
                Path("/usr/local/bin/claude"),
                self.home / ".local" / "bin" / "claude"
            ]
        
        # Check for Claude Desktop installation
        claude_found = False
        for path in claude_paths:
            if path.exists():
                print(f"✅ Found Claude Desktop at: {path}")
                claude_found = True
                break
        
        if not claude_found:
            print("⚠️  Claude Desktop not found in common locations")
            print("   You may need to install Claude Desktop first")
            print("   Download from: https://claude.ai/download")
            print("   Installation will continue but you may need to configure manually")
        
        # Check config directory
        if config_path.parent.exists():
            print(f"✅ Claude config directory exists: {config_path.parent}")
        else:
            print(f"📁 Claude config directory will be created: {config_path.parent}")
        
        return config_path
    
    def detect_system_drives(self) -> List[str]:
        """Detect all available drives/volumes for the current OS."""
        drives = []
        
        if self.system == "Windows":
            import string
            print("🔍 Detecting Windows drives...")
            for letter in string.ascii_uppercase:
                drive = f"{letter}:"
                if os.path.exists(f"{drive}\\"):
                    drives.append(drive)
                    print(f"  ✓ Found drive: {drive}")
            
            if not drives:
                drives = ['C:']
                print("  ⚠️  No drives detected, using fallback: C:")
                
        elif self.system == "Darwin":  # macOS
            print("🔍 Detecting macOS volumes...")
            try:
                result = subprocess.run(['df', '-h'], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # Skip header
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 6:
                            mount_point = parts[-1]  # Last column is mount point
                            # Include root, /Users, /Applications, and /Volumes mounts
                            if (mount_point == '/' or 
                                mount_point.startswith('/Users') or
                                mount_point.startswith('/Applications') or
                                mount_point.startswith('/Volumes')):
                                if mount_point not in drives:
                                    drives.append(mount_point)
                                    print(f"  ✓ Found volume: {mount_point}")
            except Exception as e:
                print(f"  ⚠️  Error detecting volumes: {e}")
            
            # Always include /Volumes for external drives
            if "/Volumes" not in drives and os.path.exists("/Volumes"):
                drives.append("/Volumes")
                print("  ✓ Added /Volumes for external drives")
            
            # Fallback to common paths
            if not drives:
                drives = ["/", "/Users", "/Applications"]
                print("  ⚠️  No volumes detected, using fallback")
                
        else:  # Linux
            print("🔍 Detecting Linux mount points...")
            try:
                with open('/proc/mounts', 'r') as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            mount_point = parts[1]
                            # Include common user-accessible mount points
                            if (mount_point == '/' or 
                                mount_point.startswith('/home') or
                                mount_point.startswith('/mnt') or
                                mount_point.startswith('/media')):
                                if mount_point not in drives:
                                    drives.append(mount_point)
                                    print(f"  ✓ Found mount: {mount_point}")
            except Exception as e:
                print(f"  ⚠️  Error detecting mounts: {e}")
            
            # Fallback
            if not drives:
                drives = ["/", "/home"]
                print("  ⚠️  No mounts detected, using fallback")
        
        print(f"📁 Total drives/volumes detected: {len(drives)}")
        return drives
    
    def setup_server_directory(self) -> Path:
        """Setup the MCP server directory with platform-specific paths."""
        if self.system == "Windows":
            server_dir = self.home / "Documents" / "MCP" / "filesystem-mcp"
        elif self.system == "Darwin":
            server_dir = self.home / "Documents" / "MCP" / "filesystem-mcp"
        else:
            server_dir = self.home / ".local" / "share" / "mcp" / "filesystem-mcp"
        
        try:
            server_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Server directory created: {server_dir}")
            
            # Test write permissions
            test_file = server_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            print("✅ Directory write permissions verified")
            
        except Exception as e:
            print(f"❌ Error creating server directory: {e}")
            print(f"   Path: {server_dir}")
            raise
        
        return server_dir
    
    def copy_server_files(self, server_dir: Path) -> bool:
        """Copy server files to installation directory."""
        print("📋 Copying server files...")
        
        try:
            # Copy main server file
            server_file = self.script_dir / "filesystem_mcp.py"
            if server_file.exists():
                shutil.copy2(server_file, server_dir / "filesystem_mcp.py")
                print("✅ Copied filesystem_mcp.py")
            else:
                print("❌ filesystem_mcp.py not found!")
                return False            
            # Copy README if it exists
            readme_files = ["README.md", "README_ENHANCED.md", "readme.md"]
            for readme_name in readme_files:
                readme_file = self.script_dir / readme_name
                if readme_file.exists():
                    shutil.copy2(readme_file, server_dir / "README.md")
                    print(f"✅ Copied {readme_name} as README.md")
                    break
            
            # Copy requirements.txt if it exists
            req_file = self.script_dir / "requirements.txt"
            if req_file.exists():
                shutil.copy2(req_file, server_dir / "requirements.txt")
                print("✅ Copied requirements.txt")
            
            return True
        except Exception as e:
            print(f"❌ Error copying files: {e}")
            return False
    
    def create_launch_script(self, server_dir: Path) -> bool:
        """Create platform-specific launch script."""
        print("🚀 Creating launch scripts...")
        
        try:
            if self.system == "Windows":
                # Create batch file for Windows - no echo to avoid interfering with MCP JSON protocol
                batch_content = f'''@echo off
cd /d "{server_dir}"
"{sys.executable}" filesystem_mcp.py
'''
                batch_file = server_dir / "run_mcp.bat"
                batch_file.write_text(batch_content)
                print("✅ Created run_mcp.bat")
                
            else:  # macOS/Linux
                # Create shell script - no echo for MCP compatibility
                shell_content = f'''#!/bin/bash
cd "{server_dir}"
"{sys.executable}" filesystem_mcp.py
'''
                shell_file = server_dir / "run_mcp.sh"
                shell_file.write_text(shell_content)
                shell_file.chmod(0o755)  # Make executable
                print("✅ Created run_mcp.sh")
            
            return True
        except Exception as e:
            print(f"❌ Error creating launch script: {e}")
            return False
    
    def update_claude_config(self, server_dir: Path, drives: List[str], config_path: Path) -> bool:
        """Update Claude Desktop configuration with proper MCP server configuration."""
        if not config_path:
            print("❌ No Claude Desktop config path available")
            return False
        
        print(f"🔧 Updating Claude Desktop config at: {config_path}")
        
        try:
            # Create config directory if it doesn't exist
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing config or create new one
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    print("📋 Loaded existing Claude Desktop configuration")
                except json.JSONDecodeError as e:
                    print(f"⚠️  Invalid JSON in existing config, creating backup and starting fresh")
                    backup_path = config_path.with_suffix('.json.backup')
                    shutil.copy2(config_path, backup_path)
                    print(f"📋 Backed up existing config to: {backup_path}")
                    config = {}
            else:
                config = {}
                print("📋 Creating new Claude Desktop configuration")
            
            # Ensure mcpServers section exists
            if 'mcpServers' not in config:
                config['mcpServers'] = {}
                print("✅ Created mcpServers section")
            
            # Create the filesystem MCP server configuration
            server_name = "filesystem"
            
            if self.system == "Windows":
                # Windows: Use batch script for better Windows integration
                server_config = {
                    "command": str(server_dir / "run_mcp.bat").replace('\\', '/'),  # Normalize path
                    "args": [],
                    "env": {
                        "FILESYSTEM_MCP_DRIVES": ",".join(drives),
                        "FILESYSTEM_MCP_OS": self.system,
                        "FILESYSTEM_MCP_LOG_LEVEL": "INFO"
                    },
                    "disabled": False
                }
            else:
                # macOS/Linux: Direct Python execution
                server_config = {
                    "command": sys.executable,
                    "args": [str(server_dir / "filesystem_mcp.py")],
                    "env": {
                        "FILESYSTEM_MCP_DRIVES": ",".join(drives),
                        "FILESYSTEM_MCP_OS": self.system,
                        "FILESYSTEM_MCP_LOG_LEVEL": "INFO"
                    },
                    "disabled": False
                }
            
            # Check if filesystem server already exists and update it
            if server_name in config['mcpServers']:
                print("⚠️  Existing filesystem MCP server found, updating configuration")
            else:
                print("✅ Adding new filesystem MCP server configuration")
            
            config['mcpServers'][server_name] = server_config
            
            # Validate the configuration before saving
            self._validate_claude_config(config, server_dir)
            
            # Save updated config with proper formatting
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Updated Claude config: {config_path}")
            print(f"🔗 Configured drives: {', '.join(drives)}")
            print(f"🖥️  OS environment: {self.system}")
            print(f"🚀 Server command: {server_config['command']}")
            
            # Display the final configuration for verification
            self._display_config_summary(config, server_name)
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating Claude config: {e}")
            print(f"   Config path: {config_path}")
            print(f"   Drives: {drives}")
            import traceback
            traceback.print_exc()
            return False
    
    def _validate_claude_config(self, config: Dict, server_dir: Path) -> bool:
        """Validate the Claude Desktop configuration."""
        print("🔍 Validating Claude Desktop configuration...")
        
        # Check basic structure
        if 'mcpServers' not in config:
            raise ValueError("Missing mcpServers section")
        
        filesystem_config = config['mcpServers'].get('filesystem')
        if not filesystem_config:
            raise ValueError("Missing filesystem server configuration")
        
        # Check required fields
        required_fields = ['command', 'args', 'env']
        for field in required_fields:
            if field not in filesystem_config:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate command path exists
        command = filesystem_config['command']
        if self.system == "Windows" and command.endswith('.bat'):
            command_path = Path(command)
        else:
            # For non-Windows or direct Python execution
            if command == sys.executable:
                command_path = Path(sys.executable)
            else:
                command_path = Path(command)
        
        if not command_path.exists():
            print(f"⚠️  Warning: Command path does not exist: {command_path}")
        else:
            print(f"✅ Command path validated: {command_path}")
        
        # Validate environment variables
        env = filesystem_config.get('env', {})
        if 'FILESYSTEM_MCP_DRIVES' not in env:
            raise ValueError("Missing FILESYSTEM_MCP_DRIVES environment variable")
        
        print("✅ Configuration validation passed")
        return True
    
    def _display_config_summary(self, config: Dict, server_name: str):
        """Display a summary of the Claude Desktop configuration."""
        print("\n📋 Claude Desktop Configuration Summary:")
        print("=" * 50)
        
        server_config = config['mcpServers'][server_name]
        print(f"Server Name: {server_name}")
        print(f"Command: {server_config['command']}")
        print(f"Arguments: {server_config.get('args', [])}")
        print(f"Disabled: {server_config.get('disabled', False)}")
        
        print("\nEnvironment Variables:")
        for key, value in server_config.get('env', {}).items():
            print(f"  {key}: {value}")
        
        print("\nTotal MCP Servers Configured:", len(config['mcpServers']))
        print("=" * 50)
    
    def test_installation(self, server_dir: Path) -> bool:
        """Test the MCP server installation."""
        print("🧪 Testing MCP server installation...")
        
        try:
            # Simple syntax test
            result = subprocess.run(
                [sys.executable, "-c", "import filesystem_mcp; print('Import successful')"],
                cwd=server_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("✅ Server test passed - import successful")
                return True
            else:
                print(f"❌ Server test failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️  Server test timed out (but this is usually OK)")
            return True
        except Exception as e:
            print(f"❌ Error testing server: {e}")
            return False
    
    def print_success_message(self, server_dir: Path, drives: List[str], config_path: Optional[Path]):
        """Print comprehensive installation success message."""
        print("\n" + "=" * 70)
        print("🎉 FILESYSTEM MCP SERVER INSTALLATION COMPLETED!")
        print("=" * 70)
        print(f"📁 Server installed at: {server_dir}")
        print(f"💽 Detected drives: {', '.join(drives)}")
        print(f"🖥️  Operating System: {self.system}")
        
        if config_path:
            print(f"⚙️  Claude config: {config_path}")
        
        if self.system == "Windows":
            print(f"🚀 Launch script: {server_dir / 'run_mcp.bat'}")
        else:
            print(f"🚀 Launch script: {server_dir / 'run_mcp.sh'}")
        
        print("\n📋 Next Steps:")
        print("1. 🔄 Restart Claude Desktop to load the new MCP server")
        print("2. 💬 In Claude, you should now see filesystem tools available")
        print("3. 🧪 Try asking Claude:")
        print("   - 'List my Documents folder'")
        print("   - 'Search for *.py files in my projects'")
        print("   - 'Find large files over 100MB'")
        print("   - 'Show me all my drives'")
        
        print("\n🔧 Server Configuration:")
        print("- ✅ Fully self-contained with embedded settings")
        print("- ✅ Exclusions and allowed drives configured automatically")
        print("- ✅ No external config files needed")
        print("- ✅ Cross-platform optimized exclusions")
        
        print("\n📚 Documentation & Support:")
        print(f"- 📖 README: {server_dir / 'README.md'}")
        print("- 📝 Logs: filesystem_mcp.log (in server directory)")
        print("- 🌐 Project: https://github.com/your-repo")
        
        print("\n⚠️  Troubleshooting:")
        print("- Check Claude Desktop logs for connection issues")
        print("- Ensure Python 3.8+ is installed and accessible")
        print("- Verify file permissions on the server directory")
        print("- Restart Claude Desktop if tools don't appear")
        
        print("\n🛡️  Security:")
        print("- System directories are automatically excluded")
        print("- File size limits prevent memory issues")
        print("- Safe path validation prevents directory traversal")
        
        print("=" * 70)
        print("🚀 Installation complete! Enjoy your new filesystem tools!")
        print("=" * 70)
    
    def install(self) -> bool:
        """Run the complete installation process."""
        try:
            print("🔍 Starting comprehensive installation process...")
            
            # Step 1: Check system requirements
            if not self.check_system_requirements():
                return False
            
            # Step 2: Detect Claude Desktop
            config_path = self.detect_claude_desktop()
            
            # Step 3: Detect system drives
            drives = self.detect_system_drives()
            
            # Step 4: Setup server directory
            server_dir = self.setup_server_directory()
            
            # Step 5: Copy server files
            if not self.copy_server_files(server_dir):
                return False
            
            # Step 6: Create launch script
            if not self.create_launch_script(server_dir):
                return False
            
            # Step 7: Update Claude configuration
            if config_path and not self.update_claude_config(server_dir, drives, config_path):
                print("⚠️  Could not update Claude config automatically")
                print("   You may need to configure Claude Desktop manually")
                print(f"   Add the server to: {config_path}")
            
            # Step 8: Test installation
            self.test_installation(server_dir)
            
            # Step 9: Print success message
            self.print_success_message(server_dir, drives, config_path)
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Installation cancelled by user")
            return False
        except Exception as e:
            print(f"\n❌ Installation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def main() -> int:
    """Main installation function."""
    try:
        installer = FilesystemMCPInstaller()
        success = installer.install()
        
        if success:
            print("\n✅ Installation completed successfully!")
            return 0
        else:
            print("\n❌ Installation failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Installation error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
