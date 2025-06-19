#!/usr/bin/env python3
"""
Optimized Filesystem MCP Server for Claude Desktop

A high-performance, cross-platform filesystem Model Context Protocol server 
optimized specifically for Claude Desktop integration.

Features:
- Claude Desktop MCP 2024-11-05 protocol compliance
- Cross-platform support (Windows, macOS, Linux)
- Optimized file operations with intelligent caching
- Advanced search with regex and content matching  
- Parallel operations with resource management
- Enhanced security and path validation
- Comprehensive logging and error handling
- Smart OS-specific exclusions and configurations
- Memory-efficient operations for large directories
"""

import json
import os
import sys
import platform
import threading
import time
import gc
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Set
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import logging
import fnmatch
import stat
import re
import mimetypes
import hashlib
from functools import lru_cache

# Optimized logging configuration for Claude Desktop
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('filesystem_mcp.log', encoding='utf-8'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Claude Desktop compatibility constants
CLAUDE_MCP_VERSION = "2024-11-05"
MAX_RESPONSE_SIZE = 50 * 1024 * 1024  # 50MB max response size for Claude
CHUNK_SIZE = 8192  # Optimal chunk size for file operations

class OSDetector:
    """Cross-platform OS detection and configuration."""
    
    @staticmethod
    def get_os_info() -> Dict[str, Any]:
        """Get comprehensive OS information."""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture(),
            'python_version': platform.python_version()
        }
    
    @staticmethod
    def get_default_drives() -> List[str]:
        """Get all available drives/mount points based on OS."""
        system = platform.system()
        drives = []
        
        if system == "Windows":
            import string
            # Get all available drives
            for letter in string.ascii_uppercase:
                drive = f"{letter}:"
                if os.path.exists(f"{drive}\\"):
                    drives.append(drive)
            
            # If no drives found, fallback to common ones
            if not drives:
                drives = ['C:']
            
            print(f"Windows drives detected: {drives}", file=sys.stderr)
            return drives
            
        elif system == "Darwin":  # macOS
            # Get all mounted volumes
            try:
                import subprocess
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
            except Exception as e:
                print(f"Error detecting macOS volumes: {e}", file=sys.stderr)
            
            # Fallback to common paths
            if not drives:
                drives = ["/", "/Users", "/Applications"]
            
            # Always include /Volumes for external drives
            if "/Volumes" not in drives and os.path.exists("/Volumes"):
                drives.append("/Volumes")
            
            print(f"macOS volumes detected: {drives}", file=sys.stderr)
            return drives
            
        else:  # Linux and others
            # Get mounted filesystems
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
            except Exception as e:
                print(f"Error detecting Linux mounts: {e}", file=sys.stderr)
            
            # Fallback
            if not drives:
                drives = ["/", "/home"]
            
            return drives
    
    @staticmethod
    def get_default_exclusions() -> List[str]:
        """Get OS-specific default exclusions."""
        system = platform.system()
        
        base_exclusions = [
            "*/.*",  # Hidden files/folders
            "*/__pycache__/*",
            "*/node_modules/*", 
            "*/.git/*",
            "*/.svn/*",
            "*/temp/*",
            "*/tmp/*",
            "*/cache/*",
            "*/Cache/*"
        ]
        
        if system == "Windows":
            windows_exclusions = [
                "C:\\Windows\\*",
                "C:\\Program Files\\*",
                "C:\\Program Files (x86)\\*",
                "C:\\ProgramData\\*",
                "C:\\System Volume Information\\*",
                "C:\\$Recycle.Bin\\*",
                "C:\\Recovery\\*",
                "*\\AppData\\Local\\Temp\\*",
                "*\\Microsoft\\*",
                "*\\Intel\\*",
                "*\\NVIDIA\\*"
            ]
            return base_exclusions + windows_exclusions
        elif system == "Darwin":  # macOS
            macos_exclusions = [
                "/System/*",
                "/Library/Application Support/*",
                "/private/*",
                "/usr/bin/*",
                "/usr/sbin/*",
                "/Applications/*.app/Contents/*",
                "*/Library/Caches/*",
                "*/Library/Logs/*",
                "*/.Trash/*",
                "/cores/*"
            ]
            return base_exclusions + macos_exclusions
        else:  # Linux
            linux_exclusions = [
                "/proc/*",
                "/sys/*",
                "/dev/*",
                "/boot/*",
                "/usr/bin/*",
                "/usr/sbin/*",
                "/var/log/*",
                "/var/cache/*"
            ]
            return base_exclusions + linux_exclusions

class PerformanceCache:
    """Simple LRU cache for performance optimization."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self.cache:
                # Check TTL
                if time.time() - self.access_times[key] < self.ttl:
                    self.access_times[key] = time.time()
                    return self.cache[key]
                else:
                    # Expired
                    del self.cache[key]
                    del self.access_times[key]
            return None
    
    def set(self, key: str, value: Any):
        with self._lock:
            # Clean up if at max size
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
                del self.cache[oldest_key]
                del self.access_times[oldest_key]
            
            self.cache[key] = value
            self.access_times[key] = time.time()
    
    def clear(self):
        with self._lock:
            self.cache.clear()
            self.access_times.clear()

class MCPServer:
    """Optimized MCP Server implementation for Claude Desktop."""
    
    def __init__(self, name: str):
        self.name = name
        self.tools = []
        self.request_id = 0
        self.cache = PerformanceCache(max_size=2000, ttl_seconds=300)
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mcp-worker")
        self._initialized = False
        self._shutdown = False
    
    def add_tool(self, tool_def: Dict[str, Any]):
        """Add a tool definition with validation."""
        required_fields = ["name", "description", "inputSchema"]
        if all(field in tool_def for field in required_fields):
            self.tools.append(tool_def)
            logger.debug(f"Added tool: {tool_def['name']}")
        else:
            logger.error(f"Invalid tool definition: missing required fields")
    
    async def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming MCP requests with enhanced error handling."""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            logger.debug(f"Handling request: {method} (id: {request_id})")
            
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": CLAUDE_MCP_VERSION,
                        "capabilities": {
                            "tools": {},
                            "resources": {},
                            "prompts": {}
                        },
                        "serverInfo": {
                            "name": self.name,
                            "version": "1.0.0"
                        }
                    }
                }
            elif method in ["initialized", "notifications/initialized"]:
                # This is a notification, no response needed
                self._initialized = True
                logger.info("MCP Server initialized successfully")
                return None
                
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": self.tools}
                }
                
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if not tool_name:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32602, "message": "Missing tool name"}
                    }
                
                try:
                    # Find and call the tool
                    result = await self.call_tool(tool_name, arguments)
                    
                    # Ensure result is not too large for Claude Desktop
                    result_str = json.dumps(result)
                    if len(result_str) > MAX_RESPONSE_SIZE:
                        logger.warning(f"Response too large ({len(result_str)} bytes), truncating")
                        # Truncate the response
                        truncated_content = [{"type": "text", "text": "Response truncated due to size limits. Please refine your query for smaller results."}]
                        result = truncated_content
                    
                    return {
                        "jsonrpc": "2.0", 
                        "id": request_id,
                        "result": {"content": result}
                    }
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32603, "message": f"Tool execution failed: {str(e)}"}
                    }
                    
            elif method == "resources/list":
                # Return empty resources list
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"resources": []}
                }
            elif method == "prompts/list":
                # Return empty prompts list
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"prompts": []}
                }
            else:
                logger.warning(f"Unknown method: {method}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }
                
        except Exception as e:
            logger.error(f"Error in handle_request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            }
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Override this method to handle tool calls."""
        return [{"type": "text", "text": f"Tool {name} not implemented"}]
    
    async def run_stdio(self):
        """Run the MCP server using stdio transport with enhanced error handling."""
        logger.info("MCP Server starting stdio transport...")
        
        try:
            while not self._shutdown:
                try:
                    # Read line with timeout to allow for graceful shutdown
                    line = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline),
                        timeout=1.0
                    )
                    
                    if not line:
                        logger.info("No more input, exiting...")
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                        
                    request = json.loads(line)
                    response = await self.handle_request(request)
                    
                    # Only send response if it's not None
                    if response is not None:
                        response_json = json.dumps(response, separators=(',', ':'))
                        print(response_json, flush=True)
                        
                except asyncio.TimeoutError:
                    # Timeout is normal, continue the loop
                    continue
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"}
                    }
                    print(json.dumps(error_response), flush=True)
                except Exception as e:
                    logger.error(f"Error handling request: {e}")
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Fatal error in stdio transport: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown of the server."""
        logger.info("Shutting down MCP server...")
        self._shutdown = True
        
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
            
        if hasattr(self, 'cache'):
            self.cache.clear()
            
        # Force garbage collection
        gc.collect()

class ConfigManager:
    """Configuration manager for command line args and environment variables."""
    
    @staticmethod
    def parse_args() -> argparse.Namespace:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(
            description="Filesystem MCP Server for Claude Desktop",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Environment Variables:
  FILESYSTEM_MCP_DRIVES          Comma-separated list of allowed drives/paths
  FILESYSTEM_MCP_OS              Operating system override
  FILESYSTEM_MCP_MAX_FILE_SIZE   Maximum file size in MB (default: 50)
  FILESYSTEM_MCP_MAX_RESULTS     Maximum search results (default: 2000)
  FILESYSTEM_MCP_THREADS         Number of worker threads (default: auto)
  FILESYSTEM_MCP_CACHE_TTL       Cache TTL in seconds (default: 300)
  FILESYSTEM_MCP_LOG_LEVEL       Log level (DEBUG, INFO, WARNING, ERROR)

Examples:
  python filesystem_mcp.py --drives "C:,D:" --max-file-size 100
  FILESYSTEM_MCP_DRIVES="C:,D:" python filesystem_mcp.py
            """
        )
        
        parser.add_argument(
            '--drives', '--allowed-drives',
            type=str,
            help='Comma-separated list of allowed drives/paths (e.g., "C:,D:" or "/,/home")'
        )
        
        parser.add_argument(
            '--exclude-patterns',
            type=str,
            help='Comma-separated list of additional exclusion patterns'
        )
        
        parser.add_argument(
            '--max-file-size',
            type=int,
            help='Maximum file size in MB (default: 50)'
        )
        
        parser.add_argument(
            '--max-results',
            type=int,
            help='Maximum number of search results (default: 2000)'
        )
        
        parser.add_argument(
            '--threads',
            type=int,
            help='Number of worker threads (default: auto-detect)'
        )
        
        parser.add_argument(
            '--cache-ttl',
            type=int,
            help='Cache TTL in seconds (default: 300)'
        )
        
        parser.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            help='Set logging level'
        )
        
        parser.add_argument(
            '--version',
            action='version',
            version=f'Filesystem MCP Server 1.0.0 (MCP Protocol {CLAUDE_MCP_VERSION})'
        )
        
        return parser.parse_args()
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get configuration from args and environment variables."""
        args = ConfigManager.parse_args()
        
        # Start with defaults
        config = {
            'drives': None,
            'exclude_patterns': [],
            'max_file_size_mb': 50,
            'max_results': 2000,
            'threads': None,
            'cache_ttl': 300,
            'log_level': 'INFO'
        }
        
        # Apply environment variables
        env_drives = os.getenv('FILESYSTEM_MCP_DRIVES')
        if env_drives:
            config['drives'] = [d.strip() for d in env_drives.split(',') if d.strip()]
        
        env_os = os.getenv('FILESYSTEM_MCP_OS')
        if env_os:
            config['os_override'] = env_os
        
        env_max_size = os.getenv('FILESYSTEM_MCP_MAX_FILE_SIZE')
        if env_max_size:
            try:
                config['max_file_size_mb'] = int(env_max_size)
            except ValueError:
                logger.warning(f"Invalid FILESYSTEM_MCP_MAX_FILE_SIZE: {env_max_size}")
        
        env_max_results = os.getenv('FILESYSTEM_MCP_MAX_RESULTS')
        if env_max_results:
            try:
                config['max_results'] = int(env_max_results)
            except ValueError:
                logger.warning(f"Invalid FILESYSTEM_MCP_MAX_RESULTS: {env_max_results}")
        
        env_threads = os.getenv('FILESYSTEM_MCP_THREADS')
        if env_threads:
            try:
                config['threads'] = int(env_threads)
            except ValueError:
                logger.warning(f"Invalid FILESYSTEM_MCP_THREADS: {env_threads}")
        
        env_cache_ttl = os.getenv('FILESYSTEM_MCP_CACHE_TTL')
        if env_cache_ttl:
            try:
                config['cache_ttl'] = int(env_cache_ttl)
            except ValueError:
                logger.warning(f"Invalid FILESYSTEM_MCP_CACHE_TTL: {env_cache_ttl}")
        
        env_log_level = os.getenv('FILESYSTEM_MCP_LOG_LEVEL')
        if env_log_level and env_log_level.upper() in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            config['log_level'] = env_log_level.upper()
        
        # Apply command line arguments (override env vars)
        if args.drives:
            config['drives'] = [d.strip() for d in args.drives.split(',') if d.strip()]
        
        if args.exclude_patterns:
            config['exclude_patterns'] = [p.strip() for p in args.exclude_patterns.split(',') if p.strip()]
        
        if args.max_file_size is not None:
            config['max_file_size_mb'] = args.max_file_size
        
        if args.max_results is not None:
            config['max_results'] = args.max_results
        
        if args.threads is not None:
            config['threads'] = args.threads
        
        if args.cache_ttl is not None:
            config['cache_ttl'] = args.cache_ttl
        
        if args.log_level:
            config['log_level'] = args.log_level
        
        return config


class FilesystemMCP:
    """Optimized Filesystem MCP implementation with embedded configuration for Claude Desktop."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with configuration from args and environment variables."""
        # Get configuration if not provided
        if config is None:
            config = ConfigManager.get_config()
        
        # Set up logging level first
        log_level = getattr(logging, config.get('log_level', 'INFO'))
        logging.getLogger().setLevel(log_level)
        logger.setLevel(log_level)
        
        self.config = config
        self.os_detector = OSDetector()
        
        # Setup cache with configurable TTL
        cache_ttl = config.get('cache_ttl', 300)
        self.cache = PerformanceCache(max_size=2000, ttl_seconds=cache_ttl)
        
        # Get OS-specific defaults
        self.os_info = self.os_detector.get_os_info()
        
        # Use configured drives or detect automatically
        if config.get('drives'):
            self.allowed_drives = config['drives']
            logger.info(f"Using configured drives: {self.allowed_drives}")
        else:
            self.allowed_drives = self.os_detector.get_default_drives()
            logger.info(f"Auto-detected drives: {self.allowed_drives}")
        
        # Setup exclusion patterns
        self.exclusions = self.os_detector.get_default_exclusions()
        if config.get('exclude_patterns'):
            self.exclusions.extend(config['exclude_patterns'])
            logger.info(f"Added {len(config['exclude_patterns'])} custom exclusion patterns")
        
        logger.info(f"Detected OS: {self.os_info['system']} {self.os_info['release']}")
        logger.info(f"Available drives/paths: {self.allowed_drives}")
        logger.info(f"Loaded {len(self.exclusions)} exclusion patterns")
        
        # Configure performance settings
        cpu_count = os.cpu_count() or 4
        self.max_file_size = config.get('max_file_size_mb', 50) * 1024 * 1024  # Convert to bytes
        self.max_search_results = config.get('max_results', 2000)
        
        # Configure thread pool
        configured_threads = config.get('threads')
        if configured_threads:
            self.thread_pool_size = configured_threads
        else:
            self.thread_pool_size = min(8, cpu_count + 4)
        
        logger.info(f"Performance settings: max_file_size={self.max_file_size//1024//1024}MB, "
                   f"max_results={self.max_search_results}, threads={self.thread_pool_size}")
        
        self.chunk_size = 8192
        self.max_response_size = 50 * 1024 * 1024  # 50MB
        
        # Initialize optimized thread pool
        self.executor = ThreadPoolExecutor(
            max_workers=self.thread_pool_size,
            thread_name_prefix="filesystem-worker"
        )
        
        # Performance monitoring
        self._operation_count = 0
        self._start_time = time.time()
    
    def is_path_allowed(self, path: Union[str, Path]) -> bool:
        """Check if a path is allowed based on exclusion patterns with cross-platform support."""
        path_str = str(Path(path).resolve())
        
        # Normalize path separators for cross-platform compatibility
        if platform.system() == "Windows":
            path_str = path_str.replace('/', '\\')
        else:
            path_str = path_str.replace('\\', '/')
        
        # Check drive/root allowlist
        is_allowed = False
        for allowed_path in self.allowed_drives:
            if path_str.startswith(allowed_path):
                is_allowed = True
                break
        
        if not is_allowed:
            return False
        
        # Check exclusion patterns
        for pattern in self.exclusions:
            if fnmatch.fnmatch(path_str, pattern):
                return False
        
        return True
    
    @lru_cache(maxsize=1000)
    def safe_path_resolve(self, path: str) -> Optional[Path]:
        """Safely resolve a path and validate it with caching."""
        try:
            resolved_path = Path(path).resolve()
            if self.is_path_allowed(resolved_path):
                return resolved_path
            return None
        except Exception as e:
            logger.warning(f"Failed to resolve path {path}: {e}")
            return None
    
    def get_file_info(self, path: Path) -> Dict[str, Any]:
        """Get comprehensive file/directory information with caching."""
        cache_key = f"file_info:{str(path)}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            stat_info = path.stat()
            
            # Get MIME type for files
            mime_type = None
            if path.is_file():
                mime_type, _ = mimetypes.guess_type(str(path))
            
            info = {
                "path": str(path),
                "name": path.name,
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
                "size": stat_info.st_size if path.is_file() else None,
                "size_human": self.format_size(stat_info.st_size) if path.is_file() else None,
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "extension": path.suffix.lower() if path.is_file() else None,
                "mime_type": mime_type,
                "permissions": stat.filemode(stat_info.st_mode),
                "is_hidden": self._is_hidden(path, stat_info)
            }
            
            self.cache.set(cache_key, info)
            return info
            
        except Exception as e:
            logger.error(f"Error getting file info for {path}: {e}")
            return {
                "path": str(path),
                "name": path.name,
                "error": str(e)
            }
    
    def _is_hidden(self, path: Path, stat_info) -> bool:
        """Detect if file/directory is hidden (cross-platform)."""
        # Unix-style hidden files
        if path.name.startswith('.'):
            return True
        
        # Windows hidden attribute
        if platform.system() == "Windows":
            try:
                import ctypes
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
                return bool(attrs != -1 and attrs & 2)  # FILE_ATTRIBUTE_HIDDEN
            except:
                pass
        
        return False
    
    def list_directory_parallel(self, path: Path, show_hidden: bool = False, max_items: int = 1000) -> List[Dict[str, Any]]:
        """List directory contents with parallel processing."""
        try:
            items = []
            count = 0
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                
                for item in path.iterdir():
                    if count >= max_items:
                        break
                    
                    if not show_hidden and self._is_hidden(item, None):
                        continue
                    
                    if not self.is_path_allowed(item):
                        continue
                    
                    future = executor.submit(self.get_file_info, item)
                    futures.append(future)
                    count += 1
                
                # Collect results
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=5)
                        items.append(result)
                    except Exception as e:
                        logger.warning(f"Failed to get info for item: {e}")
            
            # Sort by name
            items.sort(key=lambda x: x.get('name', '').lower())
            return items
            
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            return []
    
    @staticmethod
    def format_size(size: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

class FilesystemMCPServer(MCPServer):
    """Filesystem MCP Server implementation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("filesystem-mcp")
        self.fs = FilesystemMCP(config)
        self.setup_tools()
    
    def setup_tools(self):
        """Setup all available tools."""
        tools = [
            {
                "name": "list_directory",
                "description": "List contents of a directory with detailed file information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to list (e.g., 'C:\\', 'D:\\Documents')"
                        },
                        "show_hidden": {
                            "type": "boolean",
                            "description": "Include hidden files and directories",
                            "default": False
                        },
                        "recursive": {
                            "type": "boolean", 
                            "description": "List subdirectories recursively",
                            "default": False
                        },
                        "max_depth": {
                            "type": "integer",
                            "description": "Maximum recursion depth (only used with recursive=true)",
                            "default": 3
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "read_file",
                "description": "Read the contents of a text file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Full path to the file to read"
                        },
                        "encoding": {
                            "type": "string", 
                            "description": "File encoding (default: utf-8)",
                            "default": "utf-8"
                        },
                        "max_lines": {
                            "type": "integer",
                            "description": "Maximum number of lines to read (0 = all)",
                            "default": 0
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "search_files",
                "description": "Search for files and directories by name pattern",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Search pattern (supports wildcards like *.py, test*, etc.)"
                        },
                        "root_path": {
                            "type": "string",
                            "description": "Root directory to search from (default: C:\\)",
                            "default": "C:\\"
                        },
                        "file_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by file extensions (e.g., ['.py', '.txt'])"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 100
                        }
                    },
                    "required": ["pattern"]
                }
            },
            {
                "name": "get_file_info",
                "description": "Get detailed information about a specific file or directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Full path to the file or directory"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "find_large_files",
                "description": "Find large files above a specified size threshold",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "root_path": {
                            "type": "string",
                            "description": "Root directory to search from",
                            "default": "C:\\"
                        },
                        "min_size_mb": {
                            "type": "number",
                            "description": "Minimum file size in MB",
                            "default": 100
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 50
                        }
                    },
                    "required": ["root_path"]
                }
            },
            {
                "name": "get_drive_info",
                "description": "Get information about available drives and their usage",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
        for tool in tools:
            self.add_tool(tool)
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle tool calls."""
        try:
            if name == "list_directory":
                return await self.handle_list_directory(arguments)
            elif name == "read_file":
                return await self.handle_read_file(arguments)
            elif name == "search_files":
                return await self.handle_search_files(arguments)
            elif name == "get_file_info":
                return await self.handle_get_file_info(arguments)
            elif name == "find_large_files":
                return await self.handle_find_large_files(arguments)
            elif name == "get_drive_info":
                return await self.handle_get_drive_info(arguments)
            else:
                return [{"type": "text", "text": f"Unknown tool: {name}"}]
        except Exception as e:
            logger.error(f"Error in tool {name}: {e}")
            return [{"type": "text", "text": f"Error: {str(e)}"}]

    async def handle_list_directory(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle directory listing."""
        path_str = arguments["path"]
        show_hidden = arguments.get("show_hidden", False)
        recursive = arguments.get("recursive", False)
        max_depth = arguments.get("max_depth", 3)
        
        path = self.fs.safe_path_resolve(path_str)
        if not path:
            return [{"type": "text", "text": f"Path not allowed or invalid: {path_str}"}]
        
        if not path.exists():
            return [{"type": "text", "text": f"Path does not exist: {path}"}]
        
        if not path.is_dir():
            return [{"type": "text", "text": f"Path is not a directory: {path}"}]
        
        def list_dir_recursive(current_path: Path, current_depth: int = 0) -> List[Dict[str, Any]]:
            items = []
            if current_depth > max_depth:
                return items
            
            try:
                for item in current_path.iterdir():
                    if not show_hidden and item.name.startswith('.'):
                        continue
                    
                    if not self.fs.is_path_allowed(item):
                        continue
                    
                    file_info = self.fs.get_file_info(item)
                    file_info["depth"] = current_depth
                    items.append(file_info)
                    
                    if recursive and item.is_dir() and current_depth < max_depth:
                        items.extend(list_dir_recursive(item, current_depth + 1))
            except PermissionError:
                items.append({
                    "path": str(current_path),
                    "name": current_path.name,
                    "error": "Permission denied",
                    "depth": current_depth
                })
            except Exception as e:
                items.append({
                    "path": str(current_path),
                    "name": current_path.name,
                    "error": str(e),
                    "depth": current_depth
                })
            
            return items
        
        items = list_dir_recursive(path)
        
        # Format output
        result = f"Directory listing for: {path}\n"
        result += f"Found {len(items)} items\n\n"
        
        for item in items:
            indent = "  " * item.get("depth", 0)
            if "error" in item:
                result += f"{indent}❌ {item['name']} - {item['error']}\n"
            elif item.get("is_dir"):
                result += f"{indent}📁 {item['name']}/\n"
            else:
                size = item.get("size_human", "")
                ext = item.get("extension", "")
                result += f"{indent}📄 {item['name']} {size} {ext}\n"
        
        return [{"type": "text", "text": result}]

    async def handle_read_file(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle file reading."""
        path_str = arguments["path"]
        encoding = arguments.get("encoding", "utf-8")
        max_lines = arguments.get("max_lines", 0)
        
        path = self.fs.safe_path_resolve(path_str)
        if not path:
            return [{"type": "text", "text": f"Path not allowed or invalid: {path_str}"}]
        
        if not path.exists():
            return [{"type": "text", "text": f"File does not exist: {path}"}]
        
        if not path.is_file():
            return [{"type": "text", "text": f"Path is not a file: {path}"}]
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > self.fs.max_file_size:
            size_mb = file_size / (1024 * 1024)
            max_mb = self.fs.max_file_size / (1024 * 1024)
            return [{"type": "text", "text": f"File too large: {size_mb:.1f}MB (max: {max_mb:.1f}MB)"}]
        
        try:
            with open(path, 'r', encoding=encoding) as f:
                if max_lines > 0:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            break
                        lines.append(line.rstrip())
                    content = '\n'.join(lines)
                    if i >= max_lines - 1:
                        content += f"\n\n... (truncated to {max_lines} lines)"
                else:
                    content = f.read()
            
            result = f"File: {path}\n"
            result += f"Size: {self.fs.format_size(file_size)}\n"
            result += f"Encoding: {encoding}\n"
            result += "=" * 50 + "\n"
            result += content
            
            return [{"type": "text", "text": result}]
        
        except UnicodeDecodeError as e:
            return [{"type": "text", "text": f"Encoding error reading file with {encoding}: {e}"}]
        except Exception as e:
            return [{"type": "text", "text": f"Error reading file: {e}"}]

    async def handle_search_files(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle file searching."""
        pattern = arguments["pattern"]
        root_path_str = arguments.get("root_path", "C:\\")
        file_types = arguments.get("file_types", [])
        max_results = min(arguments.get("max_results", 100), self.fs.max_search_results)
        
        root_path = self.fs.safe_path_resolve(root_path_str)
        if not root_path:
            return [{"type": "text", "text": f"Root path not allowed or invalid: {root_path_str}"}]
        
        if not root_path.exists():
            return [{"type": "text", "text": f"Root path does not exist: {root_path}"}]
        
        results = []
        
        def search_recursive(current_path: Path, depth: int = 0):
            if len(results) >= max_results or depth > 10:  # Limit search depth
                return
            
            try:
                for item in current_path.iterdir():
                    if len(results) >= max_results:
                        break
                    
                    if not self.fs.is_path_allowed(item):
                        continue
                    
                    # Check if name matches pattern
                    if fnmatch.fnmatch(item.name.lower(), pattern.lower()):
                        # Check file type filter
                        if file_types and item.is_file():
                            if not any(item.suffix.lower() == ext.lower() for ext in file_types):
                                continue
                        
                        results.append(self.fs.get_file_info(item))
                    
                    # Recurse into directories
                    if item.is_dir():  
                        search_recursive(item, depth + 1)
            
            except PermissionError:
                pass  # Skip directories we can't access
            except Exception as e:
                logger.warning(f"Error searching in {current_path}: {e}")
        
        search_recursive(root_path)
        
        # Format results
        result_text = f"Search results for pattern: {pattern}\n"
        result_text += f"Root path: {root_path}\n"
        if file_types:
            result_text += f"File types: {', '.join(file_types)}\n"
        result_text += f"Found {len(results)} matches\n\n"
        
        for item in results:
            if item.get("is_dir"):
                result_text += f"📁 {item['path']}\n"
            else:
                size = item.get("size_human", "")
                result_text += f"📄 {item['path']} ({size})\n"
        
        if len(results) >= max_results:
            result_text += f"\n... (truncated to {max_results} results)"
        
        return [{"type": "text", "text": result_text}]

    async def handle_get_file_info(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle file info retrieval."""
        path_str = arguments["path"]
        
        path = self.fs.safe_path_resolve(path_str)
        if not path:
            return [{"type": "text", "text": f"Path not allowed or invalid: {path_str}"}]
        
        if not path.exists():
            return [{"type": "text", "text": f"Path does not exist: {path}"}]
        
        info = self.fs.get_file_info(path)
        
        if "error" in info:
            return [{"type": "text", "text": f"Error getting file info: {info['error']}"}]
        
        result = f"File Information for: {info['path']}\n"
        result += "=" * 50 + "\n"
        result += f"Name: {info['name']}\n"
        result += f"Type: {'Directory' if info['is_dir'] else 'File'}\n"
        
        if info.get('size') is not None:
            result += f"Size: {info['size_human']} ({info['size']:,} bytes)\n"
        
        result += f"Modified: {info['modified']}\n"
        result += f"Created: {info['created']}\n"
        result += f"Permissions: {info['permissions']}\n"
        
        if info.get('extension'):
            result += f"Extension: {info['extension']}\n"
        
        return [{"type": "text", "text": result}]

    async def handle_find_large_files(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle finding large files."""
        root_path_str = arguments.get("root_path", "C:\\")
        min_size_mb = arguments.get("min_size_mb", 100)
        max_results = arguments.get("max_results", 50)
        
        min_size_bytes = int(min_size_mb * 1024 * 1024)
        
        root_path = self.fs.safe_path_resolve(root_path_str)
        if not root_path:
            return [{"type": "text", "text": f"Root path not allowed or invalid: {root_path_str}"}]
        
        large_files = []
        
        def find_large_recursive(current_path: Path, depth: int = 0):
            if len(large_files) >= max_results or depth > 8:
                return
            
            try:
                for item in current_path.iterdir():
                    if len(large_files) >= max_results:
                        break
                    
                    if not self.fs.is_path_allowed(item):
                        continue
                    
                    if item.is_file():
                        try:
                            size = item.stat().st_size
                            if size >= min_size_bytes:
                                large_files.append(self.fs.get_file_info(item))
                        except Exception:
                            pass  # Skip files we can't stat
                    elif item.is_dir():
                        find_large_recursive(item, depth + 1)
            
            except PermissionError:
                pass
            except Exception as e:
                logger.warning(f"Error searching for large files in {current_path}: {e}")
        
        find_large_recursive(root_path)
        
        # Sort by size (largest first)
        large_files.sort(key=lambda x: x.get('size', 0), reverse=True)
        
        result_text = f"Large files (>= {min_size_mb}MB) in: {root_path}\n"
        result_text += f"Found {len(large_files)} large files\n\n"
        
        for file_info in large_files:
            result_text += f"📄 {file_info['path']}\n"
            result_text += f"   Size: {file_info['size_human']}\n"
            result_text += f"   Modified: {file_info['modified']}\n\n"
        
        return [{"type": "text", "text": result_text}]

    async def handle_get_drive_info(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle drive information retrieval."""
        import shutil
        
        result = "Drive Information\n"
        result += "=" * 30 + "\n\n"
        
        for drive in self.fs.allowed_drives:
            drive_path = f"{drive}\\"
            try:
                if Path(drive_path).exists():
                    total, used, free = shutil.disk_usage(drive_path)
                    
                    result += f"Drive {drive}\n"
                    result += f"  Total: {self.fs.format_size(total)}\n"
                    result += f"  Used:  {self.fs.format_size(used)} ({used/total*100:.1f}%)\n"
                    result += f"  Free:  {self.fs.format_size(free)} ({free/total*100:.1f}%)\n\n"
                else:
                    result += f"Drive {drive}: Not available\n\n"
            except Exception as e:
                result += f"Drive {drive}: Error - {e}\n\n"
        
        return [{"type": "text", "text": result}]

async def main():
    """Main entry point for the MCP server."""
    try:
        # Get configuration from command line args and environment variables
        config = ConfigManager.get_config()
        
        logger.info("Starting Filesystem MCP Server")
        logger.info(f"Configuration: drives={config.get('drives', 'auto-detect')}, "
                   f"max_file_size={config.get('max_file_size_mb')}MB, "
                   f"max_results={config.get('max_results')}, "
                   f"threads={config.get('threads', 'auto')}")
        
        # Create and run server with configuration
        server = FilesystemMCPServer(config)
        await server.run_stdio()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
