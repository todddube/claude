# Installation Instructions - Filesystem MCP Server

Multiple installation options available for all platforms:

## 🚀 Quick Installation

### Option 1: Universal Installer (Recommended)
```bash
# Works on all platforms
python install.py
```

### Option 2: Platform-Specific

#### Windows
```cmd
# Double-click or run in Command Prompt/PowerShell
install.bat

# Or run Python script directly
python install_for_claude.py
```

#### macOS
```bash
# Make executable and run
chmod +x install_macos.sh
./install_macos.sh

# Or run directly
bash install_macos.sh

# Or use Python installer
python3 install_for_claude.py
```

#### Linux
```bash
# Use Python installer
python3 install_for_claude.py

# Or use the universal installer
chmod +x install.py
./install.py
```

## 📋 File Permissions

To make installers executable on Unix systems (macOS/Linux):

```bash
# Make all installers executable
chmod +x install.py
chmod +x install_for_claude.py
chmod +x install_macos.sh

# Or make all Python files executable
find . -name "*.py" -exec chmod +x {} \;
```

## 🔧 Manual Permission Setup

If you encounter permission issues:

### macOS/Linux
```bash
# Set execute permissions
chmod 755 install.py
chmod 755 install_for_claude.py
chmod 755 install_macos.sh

# Verify permissions
ls -la install*
```

### Windows
Windows doesn't use Unix-style permissions, but you can:
- Right-click → "Run as administrator" if needed
- Ensure Python is in your PATH
- Use PowerShell or Command Prompt

## 🎯 What Each Installer Does

- **`install.py`**: Universal executable installer (calls install_for_claude.py)
- **`install_for_claude.py`**: Main cross-platform installer with full functionality
- **`install.bat`**: Windows batch file wrapper
- **`install_macos.sh`**: macOS shell script wrapper

All installers provide the same functionality:
- ✅ OS detection and drive scanning
- ✅ Optimized configuration generation
- ✅ Claude Desktop integration
- ✅ Performance optimization
- ✅ Error handling and validation

## 🚨 Troubleshooting

### Permission Denied
```bash
# macOS/Linux - if you get "Permission denied"
chmod +x install.py
./install.py

# Or run with Python directly
python3 install.py
```

### Python Not Found
```bash
# Try different Python commands
python install.py      # Windows/some Linux
python3 install.py     # macOS/most Linux
py install.py         # Windows Python Launcher
```

### Execution Policy (Windows PowerShell)
```powershell
# If PowerShell blocks execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## ✅ Verification

After installation, verify it worked:

```bash
# Check if files were created
ls ~/Documents/MCP/filesystem-mcp/

# Test the server
cd ~/Documents/MCP/filesystem-mcp/
python filesystem_mcp.py --test
```

## 📞 Support

If installation fails:
1. Check Python version: `python --version` (need 3.8+)
2. Check permissions on install files
3. Try running with `sudo` (macOS/Linux) or "Run as administrator" (Windows)
4. Check the installer logs for specific error messages
