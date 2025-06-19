# Filesystem MCP Server for Claude Desktop

A comprehensive Model Context Protocol (MCP) server that provides Claude Desktop with safe access to your local file system across all detected drives on Windows, macOS, and Linux.

## Features

- 🗂️ **Safe File System Access**: Browse all detected drives with intelligent exclusions
- 🔍 **Advanced Search**: Find files by name patterns, size, and type
- 📖 **File Reading**: Read text files with encoding support and size limits
- 📊 **Drive Information**: Get disk usage and drive statistics for all detected drives
- 🛡️ **Security Controls**: Built-in exclusions for system and sensitive directories
- ⚙️ **Self-Contained**: No external configuration files needed - everything embedded
- 🌍 **Cross-Platform**: Automatic OS detection and drive discovery (Windows, macOS, Linux)
- 🚀 **Easy Installation**: One-click installation with automatic Claude Desktop integration

## Tools Available

1. **list_directory** - List directory contents with detailed information
2. **read_file** - Read text files safely with encoding support
3. **search_files** - Search for files using wildcard patterns
4. **get_file_info** - Get detailed information about files/directories
5. **find_large_files** - Find files above a specified size threshold
6. **get_drive_info** - View drive usage and statistics for all detected drives

## Quick Installation

1. **Run the universal installer**:
   ```bash
   # Windows:
   python install.py
   
   # macOS/Linux:
   ./install.py
   ```

2. **The installer will**:
   - Detect your operating system
   - Find all available drives/volumes
   - Install the MCP server
   - Configure Claude Desktop automatically
   - Include drive information in the MCP environment

3. **Restart Claude Desktop**

4. **Start using filesystem tools**:
   - "List my Documents folder"
   - "Search for *.py files in my projects"
   - "Find large files over 100MB"
   - "Show me all my drives"

## What Gets Detected

- **Windows**: All drive letters (C:, D:, E:, etc.)
- **macOS**: Root, /Users, /Applications, /Volumes (external drives)
- **Linux**: Root, /home, /mnt, /media mount points

## Configuration

### Self-Contained Design
- **No config files needed** - all settings are embedded in the server
- **Automatic exclusions** - system directories are excluded by OS
- **Drive detection** - automatically finds all accessible drives/volumes
- **OS-optimized** - different exclusion patterns per operating system

### Built-in Exclusions
The server automatically excludes:
- System directories (Windows, System32, etc.)
- Hidden files and folders
- Package manager directories (node_modules, __pycache__)
- Version control directories (.git, .svn)
- Temporary directories

### Environment Variables
The installer configures Claude Desktop with:
- `FILESYSTEM_MCP_DRIVES` - Comma-separated list of detected drives
- `FILESYSTEM_MCP_OS` - Operating system (Windows, Darwin, Linux)

## Manual Installation

If you prefer manual installation:

1. **Copy the server file**:
   ```bash
   cp filesystem_mcp.py /path/to/your/mcp/servers/
   ```

2. **Add to Claude Desktop config**:
   
   Edit your Claude Desktop configuration file:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/claude/claude_desktop_config.json`

   Add this configuration:
   ```json
   {
     "mcpServers": {
       "filesystem": {
         "command": "python",
         "args": ["/path/to/filesystem_mcp.py"],
         "env": {
           "FILESYSTEM_MCP_DRIVES": "C:,D:",
           "FILESYSTEM_MCP_OS": "Windows"
         }
       }
     }
   }
   ```

## Usage Examples

Once installed, you can ask Claude:

- **"List the contents of my Documents folder"**
- **"Search for all Python files in my projects directory"**
- **"Find files larger than 100MB on my drives"**
- **"Show me information about my D: drive"**
- **"Read the contents of my README.md file"**
- **"Find all .log files in my system"**

## Security

The server includes comprehensive security measures:

### Windows Exclusions
- System directories (Windows, Program Files, etc.)
- Registry and system files
- User-specific sensitive directories

### macOS Exclusions
- System directories (/System, /private, etc.)
- Application internals
- System caches and logs

### Linux Exclusions
- System directories (/proc, /sys, /dev, etc.)
- System binaries and configuration
- Runtime and cache directories

### General Security
- File size limits to prevent memory issues
- Path validation to prevent directory traversal
- Encoding detection and safe file reading
- Error handling for permission issues

## Troubleshooting

### Common Issues

1. **"Server not found" error**:
   - Ensure Claude Desktop is restarted
   - Check that the server path is correct
   - Verify Python is accessible from the command line

2. **"Permission denied" errors**:
   - Normal for system directories (this is intended)
   - Ensure you have read access to the directories you're trying to access

3. **Large file warnings**:
   - Files over the size limit are automatically skipped
   - Adjust `max_file_size_mb` in the server code if needed

4. **Drive not showing**:
   - External drives may need to be mounted/connected
   - Network drives may not be detected automatically

### Debug Information

Check the server logs in the installation directory:
- Look for `filesystem_mcp.log`
- Check Claude Desktop logs for connection issues
- Verify file permissions on the server directory

## Development

### Project Structure
```
claude/
├── filesystem_mcp.py          # Main MCP server (self-contained)
├── install.py                 # Universal installer
├── install_for_claude.py      # Core installation logic
├── tests/                     # Test suite
│   ├── test_mcp.py
│   ├── test_mcp_sequence.py
│   └── ...
└── README.md                  # This file
```

### Running Tests
```bash
cd tests
python -m pytest
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is open source and available under the MIT License.
