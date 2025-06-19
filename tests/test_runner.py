#!/usr/bin/env python3
"""
Test runner for the Filesystem MCP Server test suite.

This script runs all tests in the tests directory and provides
a comprehensive report of the test results.
"""

import sys
import os
import asyncio
import importlib.util
from pathlib import Path
from typing import List, Dict, Any
import time

class TestRunner:
    """Test runner for MCP server tests."""
    
    def __init__(self):
        self.tests_dir = Path(__file__).parent
        self.project_root = self.tests_dir.parent
        self.results = []
        
    def discover_tests(self) -> List[Path]:
        """Discover all test files in the tests directory."""
        test_files = []
        for file_path in self.tests_dir.glob("test_*.py"):
            if file_path.name != "test_runner.py":  # Exclude self
                test_files.append(file_path)
        return sorted(test_files)
    
    async def run_test_file(self, test_file: Path) -> Dict[str, Any]:
        """Run a single test file and return results."""
        test_name = test_file.stem
        result = {
            "name": test_name,
            "file": str(test_file),
            "status": "unknown",
            "duration": 0,
            "output": "",
            "error": None
        }
        
        print(f"\n🧪 Running {test_name}...")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Import and run the test
            spec = importlib.util.spec_from_file_location(test_name, test_file)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load {test_file}")
            
            test_module = importlib.util.module_from_spec(spec)
            
            # Capture output
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            
            from io import StringIO
            captured_output = StringIO()
            sys.stdout = captured_output
            sys.stderr = captured_output
            
            try:
                # Execute the test module
                spec.loader.exec_module(test_module)
                
                # If there's a main function, run it
                if hasattr(test_module, 'main'):
                    if asyncio.iscoroutinefunction(test_module.main):
                        await test_module.main()
                    else:
                        test_module.main()
                elif hasattr(test_module, 'test_mcp_server'):
                    test_module.test_mcp_server()
                elif hasattr(test_module, 'test_basic_functionality'):
                    if asyncio.iscoroutinefunction(test_module.test_basic_functionality):
                        await test_module.test_basic_functionality()
                    else:
                        test_module.test_basic_functionality()
                
                result["status"] = "passed"
                
            finally:
                # Restore output
                sys.stdout = original_stdout
                sys.stderr = original_stderr
                result["output"] = captured_output.getvalue()
                
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"❌ Test failed: {e}")
        
        result["duration"] = time.time() - start_time
        
        if result["status"] == "passed":
            print(f"✅ {test_name} passed ({result['duration']:.3f}s)")
        else:
            print(f"❌ {test_name} failed ({result['duration']:.3f}s)")
        
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all discovered tests."""
        print("🚀 Filesystem MCP Server Test Suite")
        print("=" * 60)
        
        test_files = self.discover_tests()
        
        if not test_files:
            print("❌ No test files found!")
            return {"status": "error", "message": "No tests found"}
        
        print(f"📋 Found {len(test_files)} test files")
        
        # Change to project root for tests
        original_cwd = os.getcwd()
        os.chdir(self.project_root)
        
        try:
            # Run each test
            for test_file in test_files:
                result = await self.run_test_file(test_file)
                self.results.append(result)
        
        finally:
            # Restore working directory
            os.chdir(original_cwd)
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive test report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["status"] == "passed")
        failed_tests = sum(1 for r in self.results if r["status"] == "failed")
        total_duration = sum(r["duration"] for r in self.results)
        
        report = {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "duration": total_duration,
            "results": self.results
        }
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏱️  Total Duration: {total_duration:.3f}s")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if result["status"] == "failed":
                    print(f"  • {result['name']}: {result['error']}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! 🎉")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed")
        
        return report

async def main():
    """Main entry point for the test runner."""
    runner = TestRunner()
    report = await runner.run_all_tests()
    
    # Exit with non-zero code if any tests failed
    return 0 if report.get("failed", 0) == 0 else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
        sys.exit(1)
