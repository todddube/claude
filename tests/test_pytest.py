#!/usr/bin/env python3
"""
Pytest-compatible test suite for the Filesystem MCP Server.

Run with: python -m pytest tests/ -v
"""

import pytest
import asyncio
import json
import sys
import time
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from filesystem_mcp import FilesystemMCPServer, OSDetector, PerformanceCache, FilesystemMCP

class TestMCPProtocol:
    """Test MCP protocol compliance."""
    
    @pytest.fixture
    def server(self):
        """Create a server instance for testing."""
        return FilesystemMCPServer()
    
    @pytest.mark.asyncio
    async def test_initialize_request(self, server):
        """Test initialize request handling."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        response = await server.handle_request(request)
        
        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["protocolVersion"] == "2024-11-05"
        assert "capabilities" in response["result"]
        assert "serverInfo" in response["result"]
    
    @pytest.mark.asyncio
    async def test_initialized_notification(self, server):
        """Test initialized notification handling."""
        request = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        
        response = await server.handle_request(request)
        assert response is None  # Notifications don't return responses
    
    @pytest.mark.asyncio
    async def test_tools_list(self, server):
        """Test tools/list request."""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        response = await server.handle_request(request)
        
        assert response is not None
        assert "result" in response
        assert "tools" in response["result"]
        assert len(response["result"]["tools"]) > 0
    
    @pytest.mark.asyncio
    async def test_resources_list(self, server):
        """Test resources/list request."""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list",
            "params": {}
        }
        
        response = await server.handle_request(request)
        
        assert response is not None
        assert "result" in response
        assert "resources" in response["result"]
    
    @pytest.mark.asyncio
    async def test_unknown_method(self, server):
        """Test unknown method error handling."""
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "unknown_method",
            "params": {}
        }
        
        response = await server.handle_request(request)
        
        assert response is not None
        assert "error" in response
        assert response["error"]["code"] == -32601


class TestPerformance:
    """Test performance optimizations."""
    
    def test_cache_performance(self):
        """Test cache read/write performance."""
        cache = PerformanceCache(max_size=1000, ttl_seconds=60)
        
        # Test write performance
        start_time = time.time()
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")
        write_time = time.time() - start_time
        
        # Test read performance
        start_time = time.time()
        for i in range(100):
            value = cache.get(f"key_{i}")
            assert value == f"value_{i}"
        read_time = time.time() - start_time
        
        # Performance assertions (should be very fast)
        assert write_time < 1.0  # Should write 100 items in less than 1 second
        assert read_time < 0.1   # Should read 100 items in less than 0.1 seconds
    
    def test_os_detection_performance(self):
        """Test OS detection performance."""
        detector = OSDetector()
        
        start_time = time.time()
        os_info = detector.get_os_info()
        drives = detector.get_default_drives()
        exclusions = detector.get_default_exclusions()
        detection_time = time.time() - start_time
        
        # Should detect OS info quickly
        assert detection_time < 1.0
        
        # Should return valid data
        assert isinstance(os_info, dict)
        assert "system" in os_info
        assert isinstance(drives, list)
        assert len(drives) > 0
        assert isinstance(exclusions, list)
        assert len(exclusions) > 0


class TestCrossPlatform:
    """Test cross-platform compatibility."""
    
    def test_os_detection(self):
        """Test OS detection works."""
        detector = OSDetector()
        os_info = detector.get_os_info()
        
        assert "system" in os_info
        assert "release" in os_info
        assert "python_version" in os_info
        
        # Should detect a known OS
        assert os_info["system"] in ["Windows", "Darwin", "Linux"]
    
    def test_drive_detection(self):
        """Test drive/volume detection."""
        detector = OSDetector()
        drives = detector.get_default_drives()
        
        assert isinstance(drives, list)
        assert len(drives) > 0
        
        # At least one drive should be accessible
        accessible_count = 0
        for drive in drives[:3]:  # Test first 3 drives only
            try:
                path = Path(drive)
                if path.exists():
                    accessible_count += 1
            except (PermissionError, OSError):
                pass  # Some drives may not be accessible
        
        assert accessible_count > 0
    
    def test_os_exclusions(self):
        """Test OS-specific exclusions."""
        detector = OSDetector()
        exclusions = detector.get_default_exclusions()
        
        assert isinstance(exclusions, list)
        assert len(exclusions) > 5  # Should have basic exclusions
        
        # Should contain common exclusions
        exclusion_str = " ".join(exclusions)
        assert "*/__pycache__/*" in exclusions
        assert "*/.*" in exclusions


class TestFilesystemMCP:
    """Test FilesystemMCP class functionality."""
    
    @pytest.fixture
    def fs_mcp(self):
        """Create FilesystemMCP instance for testing."""
        return FilesystemMCP()
    
    def test_initialization(self, fs_mcp):
        """Test FilesystemMCP initialization."""
        assert fs_mcp is not None
        assert hasattr(fs_mcp, 'allowed_drives')
        assert hasattr(fs_mcp, 'exclusions')
        assert len(fs_mcp.allowed_drives) > 0
        assert len(fs_mcp.exclusions) > 0
    
    def test_path_validation(self, fs_mcp):
        """Test path validation functionality."""
        # Test valid paths
        if fs_mcp.allowed_drives:
            valid_path = fs_mcp.allowed_drives[0]
            assert fs_mcp.is_path_allowed(valid_path)
        
        # Test invalid paths (should be excluded)
        invalid_paths = [
            "__pycache__/test.py",
            ".git/config",
            "temp/file.txt"
        ]
        
        for invalid_path in invalid_paths:
            assert not fs_mcp.is_path_allowed(invalid_path)


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
