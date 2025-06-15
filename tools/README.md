# Development Tools

This directory contains development and maintenance tools for the Prompt MCP Server project (Version 2.0.9).

## Tools Overview

### 📦 `publish.py`
**Purpose**: Automated package publishing to PyPI

**Description**: A comprehensive publishing script that handles the complete release workflow including building, testing, and publishing the package to PyPI.

**Features**:
- 🔍 **Pre-publish validation**: Runs all tests before publishing
- 🏗️ **Automated building**: Creates both wheel and source distributions  
- 🧪 **Package testing**: Validates the built package works correctly
- 📤 **PyPI publishing**: Uploads to PyPI with proper authentication
- 🔒 **Safety checks**: Prevents accidental overwrites and validates versions
- 📊 **Detailed logging**: Comprehensive output for debugging
- ✅ **Version 2.0.9 ready**: Supports latest features including real-time file monitoring and configurable logging

**Usage**:
```bash
# Basic publish (interactive mode)
python3 tools/publish.py

# Publish with specific version
python3 tools/publish.py --version 2.1.0

# Dry run (build and test without publishing)
python3 tools/publish.py --dry-run

# Force publish (skip some safety checks)
python3 tools/publish.py --force

# Publish to test PyPI
python3 tools/publish.py --test-pypi
```

**Prerequisites**:
- PyPI account and API token configured
- `twine` installed (`pip install twine`)
- `build` package installed (`pip install build`)
- All tests passing

**Configuration**:
The script reads configuration from:
- `pyproject.toml` - Package metadata and version
- Environment variables for PyPI credentials
- Command line arguments for runtime options

## Development Workflow

### 🚀 Release Process
1. **Update Version**: Modify version in `pyproject.toml`
2. **Run Tests**: Ensure all tests pass
   ```bash
   python3 tests/run_all_tests.py
   ```
3. **Build Package**:
   ```bash
   pyproject-build
   ```
4. **Test Package**: Verify the built package works
   ```bash
   echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | uvx --from ./dist/prompt_mcp_server-X.X.X-py3-none-any.whl prompt-mcp-server
   ```
5. **Publish**: Use the publish tool
   ```bash
   python3 tools/publish.py
   ```

### 🧪 Testing Workflow
```bash
# Run all tests
python3 tests/run_all_tests.py

# Run specific test suites
python3 tests/test_prompt_mcp_server.py    # Unit tests
python3 tests/test_functional.py           # Functional tests
python3 tests/test_uvx_integration.py      # UVX integration tests
```

### 🔧 Development Setup
```bash
# Install development dependencies
pip install build twine pytest

# Set up pre-commit hooks (if available)
pre-commit install

# Run linting and formatting
black mcp_server/
flake8 mcp_server/
```

## Tool Configuration

### Environment Variables
- `TWINE_USERNAME`: PyPI username (usually `__token__`)
- `TWINE_PASSWORD`: PyPI API token
- `TWINE_REPOSITORY_URL`: Custom PyPI repository URL (optional)

### Command Line Options
- `--version`: Specify version to publish
- `--dry-run`: Build and test without publishing
- `--force`: Skip safety checks
- `--test-pypi`: Publish to test PyPI instead
- `--verbose`: Enable detailed logging
- `--help`: Show help message

## Adding New Tools

When adding new development tools to this directory:

1. **Create the tool**: Add your script to this directory
2. **Document it**: Update this README with tool description
3. **Add usage examples**: Include command examples
4. **Consider integration**: Think about how it fits with existing workflow
5. **Test thoroughly**: Ensure the tool works in different environments

### Tool Template
```python
#!/usr/bin/env python3
"""
Tool Name - Brief Description

Longer description of what the tool does and why it's useful.
"""

import argparse
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Tool description")
    parser.add_argument("--option", help="Option description")
    args = parser.parse_args()

    # Tool implementation
    print("Tool executed successfully!")

if __name__ == "__main__":
    main()
```

## Best Practices

### 🔒 Security
- Never commit API tokens or credentials
- Use environment variables for sensitive data
- Validate inputs and sanitize outputs
- Use secure communication protocols

### 📝 Documentation
- Document all command line options
- Provide usage examples
- Explain prerequisites and setup
- Include troubleshooting information

### 🧪 Testing
- Test tools in different environments
- Validate error handling
- Test edge cases and failure scenarios
- Include integration tests where appropriate

### 🔄 Maintenance
- Keep tools updated with project changes
- Review and update documentation regularly
- Monitor for deprecated dependencies
- Consider backward compatibility

## Troubleshooting

### Common Issues

**Publishing fails with authentication error**:
```bash
# Check PyPI credentials
echo $TWINE_USERNAME
echo $TWINE_PASSWORD

# Verify token format
# Should start with 'pypi-' for PyPI tokens
```

**Package build fails**:
```bash
# Clean previous builds
rm -rf dist/ build/

# Rebuild
pyproject-build
```

**Tests fail before publishing**:
```bash
# Run tests individually to identify issues
python3 tests/test_prompt_mcp_server.py
python3 tests/test_functional.py
```

**uvx installation fails**:
```bash
# Check if uvx is installed
uvx --version

# Install uvx if needed
brew install pipx
pipx install uvx
```

### Getting Help

1. **Check logs**: Tools provide detailed logging
2. **Review documentation**: Check this README and tool help
3. **Run tests**: Ensure basic functionality works
4. **Check dependencies**: Verify all required packages are installed
5. **Environment**: Ensure proper Python version and environment setup

## Contributing

When contributing to the tools:

1. **Follow conventions**: Use existing code style and patterns
2. **Add documentation**: Update this README for new tools
3. **Include tests**: Add tests for new functionality
4. **Consider compatibility**: Ensure tools work across environments
5. **Review security**: Check for security implications

---

For more information about the project, see the main [README.md](../README.md) in the project root.
