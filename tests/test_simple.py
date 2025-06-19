#!/usr/bin/env python3
"""
Simple test script for the Filesystem MCP Server
"""

import sys
import json
import asyncio
from pathlib import Path

# Add parent directory to path to import our module
sys.path.insert(0, str(Path(__file__).parent.parent))

from filesystem_mcp import FilesystemMCPServer

async def test_basic_functionality():
    """Test basic MCP server functionality."""
    print("🧪 Testing Filesystem MCP Server")
    print("=" * 40)
    
    # Create server instance
    server = FilesystemMCPServer()
    print("✅ Server created successfully")
    
    # Test tools list
    print(f"✅ Found {len(server.tools)} tools:")
    for tool in server.tools:
        print(f"   - {tool['name']}: {tool['description']}")
    
    # Test list_directory tool
    print("\n🔍 Testing list_directory tool...")
    try:
        result = await server.call_tool("list_directory", {"path": "C:\\"})
        if result and result[0].get("type") == "text":
            text = result[0]["text"]
            if "Directory listing for: C:" in text:
                print("✅ list_directory works correctly")
            else:
                print("⚠️ list_directory output unexpected")
        else:
            print("❌ list_directory failed")
    except Exception as e:
        print(f"❌ list_directory error: {e}")
    
    # Test get_drive_info tool
    print("\n💾 Testing get_drive_info tool...")
    try:
        result = await server.call_tool("get_drive_info", {})
        if result and result[0].get("type") == "text":
            text = result[0]["text"]
            if "Drive Information" in text:
                print("✅ get_drive_info works correctly")
            else:
                print("⚠️ get_drive_info output unexpected")
        else:
            print("❌ get_drive_info failed")
    except Exception as e:
        print(f"❌ get_drive_info error: {e}")
    
    # Test file search
    print("\n🔍 Testing search_files tool...")
    try:
        result = await server.call_tool("search_files", {
            "pattern": "*.txt",
            "root_path": "C:\\",
            "max_results": 10
        })
        if result and result[0].get("type") == "text":
            text = result[0]["text"]
            if "Search results for pattern:" in text:
                print("✅ search_files works correctly")
            else:
                print("⚠️ search_files output unexpected")
        else:
            print("❌ search_files failed")
    except Exception as e:
        print(f"❌ search_files error: {e}")
    
    print("\n🎉 Basic functionality test completed!")

def test_configuration():
    """Test configuration loading."""
    print("\n⚙️ Testing Configuration")
    print("=" * 30)
    
    config_dir = Path("config")
    if config_dir.exists():
        print("✅ Config directory exists")
        
        exclusions_file = config_dir / "exclusions.json"
        settings_file = config_dir / "settings.json"
        
        if exclusions_file.exists():
            try:
                with open(exclusions_file, 'r') as f:
                    exclusions = json.load(f)
                print(f"✅ Exclusions loaded: {len(exclusions.get('patterns', []))} patterns")
            except Exception as e:
                print(f"❌ Error loading exclusions: {e}")
        else:
            print("⚠️ Exclusions file not found")
        
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                print(f"✅ Settings loaded: {settings.get('allowed_drives', [])}")
            except Exception as e:
                print(f"❌ Error loading settings: {e}")
        else:
            print("⚠️ Settings file not found")
    else:
        print("⚠️ Config directory not found")

async def main():
    """Main test function."""
    print("🚀 Filesystem MCP Server Test Suite")
    print("=" * 50)
    
    # Test configuration
    test_configuration()
    
    # Test basic functionality
    await test_basic_functionality()
    
    print("\n📊 Test Summary:")
    print("- Configuration files should be in 'config/' directory")
    print("- Basic MCP server functionality tested")
    print("- Tools should respond with proper JSON-RPC format")
    print("\n💡 Next steps:")
    print("1. Run 'python install_for_claude.py' to install for Claude Desktop")
    print("2. Restart Claude Desktop")
    print("3. Ask Claude to 'list my C: drive' or 'search for *.py files'")

if __name__ == "__main__":
    asyncio.run(main())
