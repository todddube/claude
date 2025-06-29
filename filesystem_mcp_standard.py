#!/usr/bin/env python3
"""
Filesystem MCP Server

A Model Context Protocol server that provides filesystem access tools for Claude Desktop.
Follows standard MCP guidelines for safe filesystem operations.

Author: Claude MCP Team
Version: 1.0.0
Protocol: MCP 2024-11-05
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("filesystem-mcp")

class FilesystemMCPServer:
    """MCP Server providing filesystem access tools."""
    
    def __init__(self):
        self.name = "filesystem"
        self.version = "1.0.0"
        
        # Security settings
        self.max_file_size = 10 * 1024 * 1024  # 10MB limit
        self.allowed_extensions = {
            '.txt', '.md', '.json', '.yaml', '.yml', '.xml', '.csv',
            '.py', '.js', '.ts', '.html', '.css', '.sql', '.sh',
            '.bat', '.ps1', '.dockerfile', '.gitignore', '.env'
        }
        
        # Get current working directory as root
        self.root_path = Path.cwd()
        logger.info(f"Filesystem MCP Server initialized with root: {self.root_path}")
    
    def is_safe_path(self, path: Path) -> bool:
        """Check if path is safe to access."""
        try:
            resolved_path = path.resolve()
            
            # Must be under root directory
            if not str(resolved_path).startswith(str(self.root_path)):
                return False
            
            # Check for unsafe patterns
            unsafe_patterns = [
                '..', '__pycache__', '.git', '.env', 'node_modules',
                '.ssh', '.aws', '.docker', 'passwords', 'secrets'
            ]
            
            path_str = str(resolved_path).lower()
            for pattern in unsafe_patterns:
                if pattern in path_str:
                    return False
            
            return True
        except Exception:
            return False
    
    def get_safe_path(self, path_str: str) -> Optional[Path]:
        """Convert string to safe Path object."""
        try:
            # Handle relative paths
            if not os.path.isabs(path_str):
                path = self.root_path / path_str
            else:
                path = Path(path_str)
            
            if self.is_safe_path(path):
                return path
            return None
        except Exception:
            return None
    
    async def list_directory(self, path: str) -> Dict[str, Any]:
        """List directory contents safely."""
        try:
            safe_path = self.get_safe_path(path)
            if not safe_path:
                return {"error": "Invalid or unsafe path"}
            
            if not safe_path.exists():
                return {"error": "Path does not exist"}
            
            if not safe_path.is_dir():
                return {"error": "Path is not a directory"}
            
            items = []
            for item in safe_path.iterdir():
                if not self.is_safe_path(item):
                    continue
                
                item_info = {
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "path": str(item.relative_to(self.root_path))
                }
                
                if item.is_file():
                    try:
                        stat = item.stat()
                        item_info["size"] = stat.st_size
                        item_info["modified"] = stat.st_mtime
                    except Exception:
                        pass
                
                items.append(item_info)
            
            return {
                "path": path,
                "items": sorted(items, key=lambda x: (x["type"] == "file", x["name"]))
            }
        
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            return {"error": str(e)}
    
    async def read_file(self, path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Read file contents safely."""
        try:
            safe_path = self.get_safe_path(path)
            if not safe_path:
                return {"error": "Invalid or unsafe path"}
            
            if not safe_path.exists():
                return {"error": "File does not exist"}
            
            if not safe_path.is_file():
                return {"error": "Path is not a file"}
            
            # Check file size
            if safe_path.stat().st_size > self.max_file_size:
                return {"error": f"File too large (max {self.max_file_size // 1024 // 1024}MB)"}
            
            # Check file extension
            if safe_path.suffix.lower() not in self.allowed_extensions:
                return {"error": f"File type {safe_path.suffix} not allowed"}
            
            # Read file
            content = safe_path.read_text(encoding=encoding)
            
            return {
                "path": path,
                "content": content,
                "size": len(content),
                "encoding": encoding
            }
        
        except UnicodeDecodeError:
            return {"error": f"Cannot decode file with {encoding} encoding"}
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            return {"error": str(e)}
    
    async def search_files(self, pattern: str, path: str = ".") -> Dict[str, Any]:
        """Search for files matching pattern."""
        try:
            safe_path = self.get_safe_path(path)
            if not safe_path:
                return {"error": "Invalid or unsafe path"}
            
            if not safe_path.exists():
                return {"error": "Path does not exist"}
            
            matches = []
            
            def search_recursive(current_path: Path, depth: int = 0):
                if depth > 5:  # Limit recursion depth
                    return
                
                try:
                    for item in current_path.iterdir():
                        if not self.is_safe_path(item):
                            continue
                        
                        if pattern.lower() in item.name.lower():
                            matches.append({
                                "name": item.name,
                                "path": str(item.relative_to(self.root_path)),
                                "type": "directory" if item.is_dir() else "file"
                            })
                        
                        if item.is_dir() and len(matches) < 100:  # Limit results
                            search_recursive(item, depth + 1)
                            
                except PermissionError:
                    pass
            
            search_recursive(safe_path)
            
            return {
                "pattern": pattern,
                "search_path": path,
                "matches": matches[:100]  # Limit to 100 results
            }
        
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return {"error": str(e)}
    
    async def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get file/directory information."""
        try:
            safe_path = self.get_safe_path(path)
            if not safe_path:
                return {"error": "Invalid or unsafe path"}
            
            if not safe_path.exists():
                return {"error": "Path does not exist"}
            
            stat = safe_path.stat()
            
            info = {
                "path": path,
                "name": safe_path.name,
                "type": "directory" if safe_path.is_dir() else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "permissions": oct(stat.st_mode)[-3:]
            }
            
            if safe_path.is_file():
                info["extension"] = safe_path.suffix
                info["readable"] = safe_path.suffix.lower() in self.allowed_extensions
            
            return info
        
        except Exception as e:
            logger.error(f"Error getting file info for {path}: {e}")
            return {"error": str(e)}
    
    async def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle MCP requests."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": self.name,
                            "version": self.version
                        }
                    }
                }
            
            elif method == "initialized":
                logger.info("MCP server initialized")
                return None
            
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [
                            {
                                "name": "list_directory",
                                "description": "List contents of a directory",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "path": {
                                            "type": "string",
                                            "description": "Directory path to list"
                                        }
                                    },
                                    "required": ["path"]
                                }
                            },
                            {
                                "name": "read_file",
                                "description": "Read contents of a text file",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "path": {
                                            "type": "string",
                                            "description": "File path to read"
                                        },
                                        "encoding": {
                                            "type": "string",
                                            "description": "Text encoding (default: utf-8)",
                                            "default": "utf-8"
                                        }
                                    },
                                    "required": ["path"]
                                }
                            },
                            {
                                "name": "search_files",
                                "description": "Search for files by name pattern",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "pattern": {
                                            "type": "string",
                                            "description": "Search pattern"
                                        },
                                        "path": {
                                            "type": "string",
                                            "description": "Directory to search in (default: current)",
                                            "default": "."
                                        }
                                    },
                                    "required": ["pattern"]
                                }
                            },
                            {
                                "name": "get_file_info",
                                "description": "Get information about a file or directory",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "path": {
                                            "type": "string",
                                            "description": "File or directory path"
                                        }
                                    },
                                    "required": ["path"]
                                }
                            }
                        ]
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name == "list_directory":
                    result = await self.list_directory(arguments.get("path", "."))
                elif tool_name == "read_file":
                    result = await self.read_file(
                        arguments.get("path"),
                        arguments.get("encoding", "utf-8")
                    )
                elif tool_name == "search_files":
                    result = await self.search_files(
                        arguments.get("pattern"),
                        arguments.get("path", ".")
                    )
                elif tool_name == "get_file_info":
                    result = await self.get_file_info(arguments.get("path"))
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                    }
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Unknown method: {method}"}
                }
        
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": str(e)}
            }
    
    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Filesystem MCP Server")
        
        try:
            while True:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    response = await self.handle_request(request)
                    
                    if response:
                        print(json.dumps(response), flush=True)
                
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
        
        except KeyboardInterrupt:
            logger.info("Server stopped")
        except Exception as e:
            logger.error(f"Server error: {e}")

async def main():
    """Main entry point."""
    server = FilesystemMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
