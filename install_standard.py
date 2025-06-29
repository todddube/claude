#!/usr/bin/env python3
"""
Filesystem MCP Server Installer

Standard installer for the Filesystem MCP Server following Claude Desktop guidelines.
Creates proper configuration for safe filesystem access.

Author: Claude MCP Team
Version: 1.0.0
"""

import json
import os
import sys
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional

class FilesystemMCPInstaller:
    """Standard MCP installer for filesystem access."""
    
    def __init__(self):
        self.system = platform.system()
        self.home = Path.home()
        self.script_dir = Path(__file__).parent
        
        print("Filesystem MCP Server Installer")
        print("================================")
        print(f"Operating System: {self.system}")
        print(f"Python Version: {platform.python_version()}")
        print(f"Installation Directory: {self.script_dir}")
        print()
    
    def check_requirements(self) -> bool:
        """Check system requirements."""
        print("Checking requirements...")
        
        # Check Python version
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
            return False
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        
        # Check required files
        mcp_file = self.script_dir / "filesystem_mcp_standard.py"
        if not mcp_file.exists():
            print("❌ filesystem_mcp_standard.py not found")
            return False
        print("✅ MCP server file found")
        
        return True
    
    def detect_claude_config(self) -> Optional[Path]:
        """Detect Claude Desktop configuration path."""
        print("Looking for Claude Desktop...")
        
        if self.system == "Windows":
            config_path = Path(os.environ.get('APPDATA', '')) / "Claude" / "claude_desktop_config.json"
        elif self.system == "Darwin":  # macOS
            config_path = self.home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        else:  # Linux
            config_path = self.home / ".config" / "claude" / "claude_desktop_config.json"
        
        if config_path.parent.exists():
            print(f"✅ Claude config directory: {config_path.parent}")
            return config_path
        else:
            print("⚠️  Claude Desktop not found - you may need to install it first")
            print("   Configuration will be created for manual setup")
            return config_path
    
    def create_config(self, config_path: Path) -> bool:
        """Create or update Claude Desktop configuration."""
        print("Configuring Claude Desktop...")
        
        try:
            # Create config directory if needed
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing config or create new
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print("📝 Updating existing configuration")
            else:
                config = {}
                print("📝 Creating new configuration")
            
            # Ensure mcpServers section exists
            if 'mcpServers' not in config:
                config['mcpServers'] = {}
            
            # Configure the filesystem server
            server_config = {
                "command": sys.executable,
                "args": [str(self.script_dir / "filesystem_mcp_standard.py")],
                "env": {}
            }
            
            config['mcpServers']['filesystem'] = server_config
            
            # Save configuration
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Configuration saved to: {config_path}")
            return True
        
        except Exception as e:
            print(f"❌ Error creating configuration: {e}")
            return False
    
    def test_installation(self) -> bool:
        """Test the MCP server."""
        print("Testing installation...")
        
        try:
            mcp_file = self.script_dir / "filesystem_mcp_standard.py"
            result = subprocess.run([
                sys.executable, str(mcp_file), "--help"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 or "Filesystem MCP Server" in result.stderr:
                print("✅ MCP server test passed")
                return True
            else:
                print(f"❌ MCP server test failed: {result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            print("✅ MCP server started (timeout expected)")
            return True
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False
    
    def create_launch_script(self) -> bool:
        """Create a launch script for manual testing."""
        print("Creating launch script...")
        
        try:
            if self.system == "Windows":
                script_content = f'''@echo off
cd /d "{self.script_dir}"
"{sys.executable}" filesystem_mcp_standard.py
pause
'''
                script_file = self.script_dir / "run_filesystem_mcp.bat"
                script_file.write_text(script_content)
                print("✅ Created run_filesystem_mcp.bat")
            
            else:  # macOS/Linux
                script_content = f'''#!/bin/bash
cd "{self.script_dir}"
"{sys.executable}" filesystem_mcp_standard.py
'''
                script_file = self.script_dir / "run_filesystem_mcp.sh"
                script_file.write_text(script_content)
                script_file.chmod(0o755)
                print("✅ Created run_filesystem_mcp.sh")
            
            return True
        
        except Exception as e:
            print(f"❌ Error creating launch script: {e}")
            return False
    
    def print_success_message(self, config_path: Path):
        """Print installation success message."""
        print()
        print("🎉 Installation Complete!")
        print("=" * 40)
        print(f"📁 Server location: {self.script_dir / 'filesystem_mcp_standard.py'}")
        print(f"⚙️  Configuration: {config_path}")
        print()
        print("Next Steps:")
        print("1. Restart Claude Desktop")
        print("2. The filesystem tools should now be available")
        print("3. Try asking Claude: 'List the files in the current directory'")
        print()
        print("Available Tools:")
        print("• list_directory - List directory contents")
        print("• read_file - Read text file contents")
        print("• search_files - Search for files by name")
        print("• get_file_info - Get file/directory information")
        print()
        print("Security Notes:")
        print("• Only text files with safe extensions can be read")
        print("• Access is limited to the current directory and subdirectories")
        print("• Maximum file size: 10MB")
        print("• System directories are automatically excluded")
        print()
        print("For troubleshooting, check the Claude Desktop logs.")
    
    def install(self) -> bool:
        """Run the installation process."""
        try:
            # Check requirements
            if not self.check_requirements():
                return False
            
            # Detect Claude Desktop
            config_path = self.detect_claude_config()
            if not config_path:
                print("❌ Could not determine Claude config path")
                return False
            
            # Create configuration
            if not self.create_config(config_path):
                return False
            
            # Test installation
            if not self.test_installation():
                print("⚠️  Installation completed but test failed")
                print("   The server may still work - try restarting Claude Desktop")
            
            # Create launch script
            self.create_launch_script()
            
            # Print success message
            self.print_success_message(config_path)
            
            return True
        
        except KeyboardInterrupt:
            print("\n❌ Installation cancelled by user")
            return False
        except Exception as e:
            print(f"\n❌ Installation failed: {e}")
            return False

def main():
    """Main installation function."""
    installer = FilesystemMCPInstaller()
    success = installer.install()
    
    if success:
        print("\n✅ Installation successful!")
        return 0
    else:
        print("\n❌ Installation failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
