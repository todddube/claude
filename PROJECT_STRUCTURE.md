# Filesystem MCP Server - Project Structure

```
claude/
├── filesystem_mcp.py          # Main MCP server implementation
├── install_for_claude.py      # Cross-platform installer script
├── install.bat                # Windows batch installer
├── install_macos.sh           # macOS installer script
├── requirements.txt           # Python dependencies (none needed)
├── package.json              # Node.js package metadata
├── README.md                 # Main documentation
├── ERROR_FIXES_SUMMARY.md    # Error fixes documentation
├── OPTIMIZATION_SUMMARY.md   # Performance optimizations
├── PROJECT_STRUCTURE.md      # This file
├── config/                   # Configuration directory
│   ├── exclusions.json       # Directory exclusion patterns
│   └── settings.json         # Server settings
└── tests/                    # Test suite
    ├── __init__.py           # Test package initialization
    ├── README.md             # Test documentation
    ├── requirements.txt      # Test dependencies
    ├── pytest.ini           # Pytest configuration
    ├── test_runner.py        # Custom test runner (no deps)
    ├── test_pytest.py        # Pytest-compatible tests
    ├── test_optimized_mcp.py # Performance tests
    ├── test_mcp.py           # Basic MCP tests
    ├── test_mcp_sequence.py  # Protocol sequence tests
    └── test_simple.py        # Simple functionality tests

Generated files:
├── filesystem_mcp.log         # Server log file (created at runtime)
└── __pycache__/              # Python cache directories (auto-generated)
```

## File Descriptions

### Core Files

**filesystem_mcp.py**
- Main MCP server implementation
- Handles all filesystem operations
- Implements MCP protocol for Claude Desktop
- Security controls and path validation
- No external dependencies (uses only Python standard library)

**install_for_claude.py**
- Automated installation script
- Updates Claude Desktop configuration
- Creates/updates claude_desktop_config.json
- Cross-platform support (Windows/macOS/Linux)

**install.bat**
- Windows batch file for easy installation
- Checks Python availability
- Runs the Python installer
- User-friendly error handling

### Configuration Files

**config/exclusions.json**
- Controls which directories/files are blocked
- Uses wildcard patterns (e.g., "C:\\Windows\\*")
- Protects system directories and sensitive areas
- User-customizable

**config/settings.json**
- Server behavior configuration
- Allowed drives (C:, D: by default)
- File size limits
- Search result limits

### Test Files

**test_simple.py**
- Basic functionality testing
- Tests major tools (list_directory, search_files, etc.)
- Configuration validation
- Quick verification script

**test_mcp.py**
- Comprehensive test suite
- Import validation
- Path security testing
- Claude Desktop config verification

### Documentation

**README.md**
- Complete usage guide
- Installation instructions
- Configuration details
- Security features
- Troubleshooting

## Installation Methods

### Method 1: Automatic (Recommended)
```bash
# Double-click install.bat or run:
.\install.bat
```

### Method 2: Manual Python
```bash
python install_for_claude.py
```

### Method 3: Manual Configuration
1. Add to Claude Desktop config manually
2. Point to filesystem_mcp.py location
3. Restart Claude Desktop

## Tool Capabilities

1. **list_directory** - Browse directories safely
2. **read_file** - Read text files with size limits
3. **search_files** - Find files by name patterns
4. **get_file_info** - Detailed file/directory information
5. **find_large_files** - Locate files above size threshold
6. **get_drive_info** - Drive usage statistics

## Security Features

- **Path Validation**: All paths checked and resolved
- **Drive Restrictions**: Only C: and D: by default
- **Exclusion Patterns**: System directories blocked
- **File Size Limits**: Prevents memory issues
- **Permission Handling**: Graceful error handling
- **No External Dependencies**: Uses only Python stdlib

## Configuration Examples

### Custom Exclusions
```json
{
  "patterns": [
    "C:\\Windows\\*",
    "C:\\Program Files\\*", 
    "*\\AppData\\*",
    "*\\.git\\*",
    "*.tmp"
  ]
}
```

### Custom Settings
```json
{
  "allowed_drives": ["C:", "D:", "E:"],
  "max_file_size_mb": 20,
  "max_search_results": 500
}
```

## Claude Desktop Integration

The MCP server integrates with Claude Desktop through:
- JSON-RPC protocol over stdin/stdout
- Tool definitions with input schemas
- Structured responses with proper typing
- Error handling and logging

## Usage Examples

Once installed, ask Claude:
- "List my Documents folder contents"
- "Search for Python files in my projects"
- "Find files larger than 100MB"
- "Show me drive usage information"
- "Read my README.md file"

## Troubleshooting

### Common Issues
1. **"Tool not found"** - Restart Claude Desktop
2. **"Permission denied"** - Path may be in exclusions
3. **"Path not allowed"** - Check allowed_drives setting
4. **"File too large"** - Adjust max_file_size_mb

### Log Files
- `filesystem_mcp.log` - Server operation logs
- Check Claude Desktop logs for connection issues

## Development

### Adding New Tools
1. Add tool definition to `setup_tools()`
2. Create handler method `handle_[tool_name]()`
3. Add handler to `call_tool()` dispatcher

### Testing Changes
```bash
python test_simple.py
```

### Manual Testing
```bash
python filesystem_mcp.py
# Then send JSON-RPC requests via stdin
```

## License
MIT License - Free to use and modify
