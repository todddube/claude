# Filesystem MCP Server - Test Suite

This directory contains comprehensive tests for the Filesystem MCP Server, organized for maintainability and ease of use.

## 📁 Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── requirements.txt            # Test dependencies
├── pytest.ini                 # Pytest configuration
├── test_runner.py             # Custom test runner (no dependencies)
├── test_pytest.py            # Pytest-compatible comprehensive tests
├── test_optimized_mcp.py      # Performance and optimization tests
├── test_mcp.py               # Basic MCP functionality tests
├── test_mcp_sequence.py      # MCP protocol sequence tests
└── test_simple.py            # Simple functionality tests
```

## 🧪 Running Tests

### Option 1: Using Custom Test Runner (No Dependencies)
```bash
# Run all tests with the built-in runner
cd claude
python tests/test_runner.py
```

### Option 2: Using pytest (Recommended for Development)
```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/ -m "unit" -v          # Unit tests only
python -m pytest tests/ -m "performance" -v   # Performance tests only
python -m pytest tests/ -m "not slow" -v      # Skip slow tests

# Run with coverage
python -m pytest tests/ --cov=filesystem_mcp --cov-report=html
```

### Option 3: Individual Test Files
```bash
# Run specific test files directly
cd claude
python tests/test_optimized_mcp.py
python tests/test_simple.py
python tests/test_mcp.py
```

## 🎯 Test Categories

### Unit Tests (`test_pytest.py`)
- **MCP Protocol Compliance**: Tests all MCP 2024-11-05 protocol methods
- **Performance Validation**: Cache performance, OS detection speed
- **Cross-Platform Compatibility**: OS detection, drive enumeration
- **Core Functionality**: Path validation, configuration loading

### Integration Tests (`test_optimized_mcp.py`)
- **End-to-End Protocol Testing**: Full MCP request/response cycles
- **Tool Execution**: All 6 filesystem tools with real data
- **Performance Benchmarks**: Real-world performance measurements
- **System Integration**: Actual filesystem operations

### Sequence Tests (`test_mcp_sequence.py`)
- **Protocol Flow**: Complete initialization and tool call sequences
- **Error Handling**: Protocol error scenarios and recovery
- **State Management**: Server state across multiple requests

### Basic Tests (`test_mcp.py`, `test_simple.py`)
- **Import Validation**: Module loading and basic instantiation
- **Configuration Testing**: Config file loading and validation
- **Quick Smoke Tests**: Fast validation of core functionality

## 📊 Performance Benchmarks

The test suite includes comprehensive performance benchmarks:

| Operation | Target Performance | Test Coverage |
|-----------|-------------------|---------------|
| Cache Write | < 0.01s per 1000 ops | ✅ |
| Cache Read | < 0.001s per 1000 ops | ✅ |
| OS Detection | < 0.01s complete | ✅ |
| Tool Execution | < 0.1s typical | ✅ |
| Protocol Handling | < 0.01s per request | ✅ |

## 🛡️ Test Coverage

The test suite covers:
- ✅ **MCP Protocol**: 100% of required methods
- ✅ **Error Handling**: All error scenarios and edge cases
- ✅ **Cross-Platform**: Windows, macOS, Linux compatibility
- ✅ **Performance**: All optimization claims validated
- ✅ **Security**: Path validation and access control
- ✅ **Configuration**: All config options and defaults

## 🔧 Test Configuration

### Environment Variables
```bash
# Optional: Override test behavior
export MCP_TEST_DRIVES="C:,D:"           # Windows: specify test drives
export MCP_TEST_TIMEOUT=30               # Test timeout in seconds
export MCP_TEST_VERBOSE=1                # Enable verbose output
```

### Pytest Markers
- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.slow` - Tests that take > 5 seconds
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.performance` - Performance benchmarks

## 🚀 Continuous Integration

For CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run Tests
  run: |
    pip install -r tests/requirements.txt
    python -m pytest tests/ --cov=filesystem_mcp --junitxml=test-results.xml

- name: Run Custom Test Suite
  run: python tests/test_runner.py
```

## 📈 Adding New Tests

### For New Features
1. Add unit tests to `test_pytest.py`
2. Add integration tests to `test_optimized_mcp.py`
3. Update performance benchmarks if applicable
4. Document any new test markers or requirements

### Test Naming Conventions
- `test_[feature]_[scenario]()` - Standard test functions
- `Test[Feature]` - Test classes for related functionality
- `test_[feature]_performance()` - Performance-specific tests
- `test_[feature]_error_[condition]()` - Error handling tests

## 🐛 Debugging Tests

### Running in Debug Mode
```bash
# Run with debug output
python tests/test_runner.py --debug

# Run single test with pytest debugger
python -m pytest tests/test_pytest.py::TestMCPProtocol::test_initialize_request -vv --pdb
```

### Common Issues
1. **Import Errors**: Ensure you're running from the project root
2. **Path Issues**: Tests expect to run from the `claude/` directory
3. **Permission Errors**: Some filesystem tests may need elevated permissions
4. **Timeout Issues**: Increase `MCP_TEST_TIMEOUT` for slow systems

## 📋 Test Results Interpretation

### Success Indicators
- ✅ **All tests pass**: Server is ready for production
- ✅ **Performance benchmarks met**: Optimizations are working
- ✅ **Cross-platform tests pass**: Compatible across OS platforms

### Warning Signs
- ⚠️ **Performance degradation**: Check for recent changes
- ⚠️ **Intermittent failures**: May indicate timing or resource issues
- ⚠️ **Platform-specific failures**: OS compatibility problems

### Failure Actions
1. **Review test output** for specific error messages
2. **Check recent changes** that might affect functionality
3. **Verify system requirements** (Python version, permissions)
4. **Run individual tests** to isolate issues
5. **Check configuration files** for corruption or missing files

---

**Note**: All tests are designed to run without external dependencies except for pytest-based tests. The custom test runner (`test_runner.py`) provides full functionality using only Python standard library.
