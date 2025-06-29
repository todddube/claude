# Filesystem MCP Server (Standard)

A Model Context Protocol server that provides safe filesystem access tools for Claude Desktop, following standard MCP guidelines.

## Overview

This MCP server enables Claude to safely interact with your local filesystem by providing a set of secure tools for reading files, listing directories, and searching for files. It follows Claude MCP best practices for security and reliability.

## Features

- **Safe file access** - Restricted to current directory and subdirectories
- **Text file reading** - Supports common text file formats with encoding detection
- **Directory listing** - Browse folder contents with file metadata
- **File search** - Find files by name pattern
- **Security controls** - Automatic filtering of unsafe paths and file types
- **Standard compliance** - Follows official MCP protocol guidelines

## Installation

### Quick Install

1. Download or clone this repository
2. Run the installer:

```bash
python install_standard.py
```

3. Restart Claude Desktop

The installer will:
- Check system requirements
- Detect Claude Desktop configuration
- Configure the MCP server
- Test the installation

### Manual Installation

If you prefer manual setup:

1. Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "python",
      "args": ["/path/to/filesystem_mcp_standard.py"]
    }
  }
}
```

2. Restart Claude Desktop

## Available Tools

### `list_directory`
Lists the contents of a directory with file metadata.

**Parameters:**
- `path` (string): Directory path to list

**Example:**
```
List the files in the current directory
```

### `read_file`
Reads the contents of a text file.

**Parameters:**
- `path` (string): File path to read
- `encoding` (string, optional): Text encoding (default: utf-8)

**Example:**
```
Read the contents of README.md
```

### `search_files`
Searches for files matching a name pattern.

**Parameters:**
- `pattern` (string): Search pattern
- `path` (string, optional): Directory to search (default: current)

**Example:**
```
Search for all Python files in the project
```

### `get_file_info`
Gets detailed information about a file or directory.

**Parameters:**
- `path` (string): File or directory path

**Example:**
```
Get information about the package.json file
```

## Security Features

### Path Restrictions
- Access limited to current working directory and subdirectories
- No access to parent directories or absolute paths outside the project
- Automatic filtering of dangerous paths (`.git`, `.env`, etc.)

### File Type Restrictions
Allowed file extensions:
- Text: `.txt`, `.md`, `.json`, `.yaml`, `.yml`, `.xml`, `.csv`
- Code: `.py`, `.js`, `.ts`, `.html`, `.css`, `.sql`
- Scripts: `.sh`, `.bat`, `.ps1`
- Config: `.dockerfile`, `.gitignore`, `.env`

### Size Limits
- Maximum file size: 10MB
- Search results limited to 100 items
- Directory recursion limited to 5 levels

### Excluded Patterns
Automatically excludes:
- Hidden files and directories (starting with `.`)
- Version control (`.git`)
- Dependencies (`node_modules`, `__pycache__`)
- Sensitive files (`.env`, `.ssh`, `.aws`)

## Configuration

The server uses secure defaults and requires no additional configuration. All security settings are embedded in the code following MCP best practices.

### Working Directory
The server operates relative to the directory where it's started. This is automatically set to your project directory.

### Logging
Basic logging is enabled to help with troubleshooting. Logs include:
- Server startup and shutdown
- Tool execution
- Error messages

## Usage Examples

Once installed, you can ask Claude to help with filesystem tasks:

- *"What files are in my project directory?"*
- *"Show me the contents of the README file"*
- *"Find all Python files in this project"*
- *"What's the size of the main.py file?"*
- *"List all markdown files"*
- *"Read the package.json configuration"*

## Requirements

- Python 3.8 or higher
- Claude Desktop
- No external dependencies (uses only Python standard library)

## Troubleshooting

### Server Not Appearing
1. Check that Claude Desktop is properly installed
2. Verify the configuration in `claude_desktop_config.json`
3. Restart Claude Desktop completely
4. Check Claude Desktop logs for errors

### File Access Denied
- Ensure the file is within the current project directory
- Check that the file extension is supported
- Verify the file exists and is readable

### Large File Errors
- Files larger than 10MB cannot be read
- Consider breaking large files into smaller pieces
- Use directory listing to check file sizes first

## Development

### Project Structure
```
filesystem_mcp_standard.py  # Main MCP server
install_standard.py         # Installation script  
requirements_standard.txt   # Dependencies (none)
package_standard.json       # Project metadata
README_standard.md         # This file
```

### Testing
Test the server manually:

```bash
# Windows
run_filesystem_mcp.bat

# macOS/Linux  
./run_filesystem_mcp.sh
```

The server expects JSON-RPC messages on stdin and responds on stdout.

## Contributing

This implementation follows the official MCP specification. When contributing:

1. Maintain security restrictions
2. Follow the existing code style
3. Test with Claude Desktop
4. Update documentation as needed

## License

MIT License - see LICENSE file for details.

## Support

For issues related to:
- **MCP Protocol**: Check the official MCP documentation
- **Claude Desktop**: Contact Anthropic support
- **This Implementation**: Create an issue in the repository

## Changelog

### v1.0.0
- Initial standard implementation
- Safe filesystem access tools
- Standard MCP compliance
- Comprehensive security controls
