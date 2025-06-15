# Prompt MCP Server for Amazon Q

A single-file Model Context Protocol (MCP) server for Amazon Q Developer CLI that manages prompt files (*.md) from local directories.

## Features

- **🔄 Real-time File Monitoring**: Automatically detects file changes and updates prompt list
- **📢 MCP Notifications**: Sends notifications to Amazon Q CLI for automatic refresh
- **📁 Prompt Discovery**: Lists all `*.md` files from configured directories
- **🏠 Default Directory**: `~/.aws/amazonq/prompts` (created automatically)
- **🎯 Custom Directories**: Override with `PROMPTS_PATH` environment variable (PATH-like format)
- **🔧 Variable Substitution**: Supports `{variable}` placeholders in prompts
- **🔍 Configurable Logging**: Production-safe defaults with comprehensive debug mode
- **🌐 Cross-Platform**: Works on Unix/Linux/macOS (Windows compatible)
- **⚡ Error Handling**: Comprehensive error handling and logging
- **📦 No Dependencies**: Pure Python 3.8+ implementation

## Installation & Usage

### Quick Start with uvx (Recommended)

```bash
# Install and run directly (after publishing to PyPI)
uvx prompt-mcp-server

# Or install from local build
pyproject-build
uvx --from ./dist/prompt_mcp_server-2.0.3-py3-none-any.whl prompt-mcp-server
```

### Direct Usage

```bash
# Run the server directly
python3 mcp_server/prompt_mcp_server.py

# With custom prompt directories
PROMPTS_PATH="./my-prompts:~/.aws/amazonq/prompts" python3 mcp_server/prompt_mcp_server.py
```

### Amazon Q Integration

```bash
# The workspace is configured to use uvx with the built package
q mcp list                    # Verify configuration (should show: prompt-server uvx)
q chat                        # Start Amazon Q CLI
/prompts                      # List available prompts
@debug_code                   # Use a prompt
```

**Configuration files:**

- `.amazonq/mcp.json` - Uses local development path
- `tests/.amazonq/mcp.json` - Uses local built package
- `tests/.amazonq/mcp-published.json` - For published package (copy to `mcp.json` after publishing)

### Building and Testing

```bash
# Build package
pyproject-build

# Test with uvx
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | uvx --from ./dist/prompt_mcp_server-2.0.0-py3-none-any.whl prompt-mcp-server
```

## Configuration

### Environment Variables
- `PROMPTS_PATH`: Colon-separated list of directories (Unix) or semicolon-separated (Windows)
- Default: `~/.aws/amazonq/prompts`

### Workspace Configuration
The `.amazonq/mcp.json` file configures Amazon Q to use this server:

#### Development Configuration (Local)
```json
{
  "mcpServers": {
    "prompt-server": {
      "command": "python3",
      "args": ["mcp_server/prompt_mcp_server.py"],
      "timeout": 10000
    }
  }
}
```

#### Production Configuration (PyPI)
```json
{
  "mcpServers": {
    "prompt-server": {
      "command": "uvx",
      "args": ["prompt-mcp-server@latest"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Environment Variables

### PROMPTS_PATH
- **Purpose**: Specify custom directories to search for prompt files
- **Format**: Colon-separated list of directories (Unix/Linux/macOS) or semicolon-separated (Windows)
- **Default**: `~/.aws/amazonq/prompts`
- **Example**: 
  ```bash
  export PROMPTS_PATH="/path/to/prompts1:/path/to/prompts2"
  ```

### MCP_LOG_LEVEL
- **Purpose**: Set the logging level for the MCP server
- **Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Default**: `WARNING` (production level - only warnings and errors)
- **Example**:
  ```bash
  export MCP_LOG_LEVEL=INFO
  ```

### MCP_DEBUG_LOGGING
- **Purpose**: Enable comprehensive debug logging with detailed request/response tracing
- **Values**: `1`, `true`, `yes`, `on` (case-insensitive)
- **Default**: Disabled
- **When enabled**:
  - Forces `INFO` level logging regardless of `MCP_LOG_LEVEL`
  - Creates debug log file for easy monitoring
  - Logs all MCP requests and responses with full JSON details
  - Logs file monitoring activity and cache operations
  - Color-coded log messages with emojis for easy identification
- **Example**:
  ```bash
  export MCP_DEBUG_LOGGING=1
  # Then monitor logs with:
  tail -f /tmp/mcp_server_debug.log
  ```

### MCP_LOG_FILE
- **Purpose**: Set custom path for the debug log file
- **Default**: `/tmp/mcp_server_debug.log`
- **Only used when**: `MCP_DEBUG_LOGGING` is enabled
- **Example**:
  ```bash
  export MCP_DEBUG_LOGGING=1
  export MCP_LOG_FILE=/path/to/custom/mcp_debug.log
  # Then monitor logs with:
  tail -f /path/to/custom/mcp_debug.log
  ```

### Debug Logging Usage

To enable debug logging for troubleshooting:

```bash
# Enable debug logging with default log file
export MCP_DEBUG_LOGGING=1

# Or enable with custom log file location
export MCP_DEBUG_LOGGING=1
export MCP_LOG_FILE=/path/to/custom/debug.log

# Start Amazon Q CLI
q chat

# In another terminal, monitor detailed logs
tail -f /tmp/mcp_server_debug.log
# Or if using custom log file:
tail -f /path/to/custom/debug.log

# Test file changes
echo "# Test" > ~/.aws/amazonq/prompts/test.md
rm ~/.aws/amazonq/prompts/test.md
```

The debug logs will show:
- 📥 Raw requests received from Amazon Q CLI
- 🔵 Parsed incoming requests with details
- 🟢 Outgoing responses with full content
- 📤 Raw responses sent to Amazon Q CLI
- 📢 MCP notifications sent (e.g., prompts list changed)
- File monitoring activity and cache operations

## Testing

The project includes comprehensive unit and functional tests:

### Run All Tests
```bash
# Run both unit and functional tests
python3 tests/run_all_tests.py

# Run only unit tests
python3 tests/run_all_tests.py --unit-only

# Run only functional tests
python3 tests/run_all_tests.py --functional-only
```

### Individual Test Suites
```bash
# Unit tests (31 tests)
python3 tests/test_prompt_mcp_server.py

# Functional tests (14 tests)
python3 tests/test_functional.py

# UVX integration tests (8 tests)
python3 tests/test_uvx_integration.py
```

### Test Results
- **Current Status**: ✅ All 53 tests passing (100% success rate)
- **Detailed Results**: See `tests/results/` directory for comprehensive reports
- **Performance**: Complete test suite runs in ~10.5 seconds

### Test Coverage
- **Unit Tests**: 31 tests covering all server components
- **Functional Tests**: 14 end-to-end integration tests
- **UVX Integration**: 8 tests for package execution scenarios
- **Total Coverage**: 53 comprehensive tests

## Creating Prompts

### Simple Prompt
Create `~/.aws/amazonq/prompts/debug_code.md`:
```markdown
# Debug Code Issues
Help me debug code by identifying issues and suggesting fixes.
```

### Parameterized Prompt
Create `~/.aws/amazonq/prompts/create_function.md`:
```markdown
# Create {language} Function
Create a {language} function named {function_name} that {description}.

Requirements:
- Follow {language} best practices
- Include error handling
- Add comprehensive tests
```

## Usage Examples

### List Available Prompts
```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "prompts/list"}' | python3 mcp_server/prompt_mcp_server.py
```

### Get a Prompt with Variables
```bash
echo '{"jsonrpc": "2.0", "id": 2, "method": "prompts/get", "params": {"name": "create_function", "arguments": {"language": "Python", "function_name": "calculate", "description": "adds two numbers"}}}' | python3 mcp_server/prompt_mcp_server.py
```

## Requirements

- Python 3.6+
- No external dependencies
- Cross-platform support

## Error Handling

The server includes comprehensive error handling:
- File permission validation
- File size limits (1MB max)
- Unicode encoding support (UTF-8 with latin-1 fallback)
- Directory access validation
- Graceful fallback to default directories
- Detailed logging to stderr

## Testing

All core features have been tested:
- ✅ MCP protocol compliance (initialize, prompts/list, prompts/get)
- ✅ Prompt discovery and variable extraction
- ✅ PROMPTS_PATH environment variable support
- ✅ Cross-platform path handling
- ✅ Error handling and edge cases
- ✅ Amazon Q CLI integration

## Project Structure

```
mcp-prompts-local/
├── mcp_server/                    # Main package
│   ├── __init__.py               # Package initialization
│   └── prompt_mcp_server.py      # MCP server implementation
├── tools/                        # Development tools
│   ├── publish.py                # Automated publishing script
│   └── README.md                 # Tools documentation
├── tests/                        # Test suite
│   ├── test_prompt_mcp_server.py # Unit tests (31 tests)
│   ├── test_functional.py        # Functional tests (14 tests)
│   ├── test_uvx_integration.py   # UVX integration tests (8 tests)
│   ├── results/                  # Test execution results
│   │   ├── FULL_TEST_RESULTS.md  # Initial test results
│   │   ├── FINAL_TEST_RESULTS.md # Final test results (100% success)
│   │   └── README.md             # Test results documentation
│   └── .amazonq/                 # Test configurations
├── .amazonq/                     # Workspace configuration
│   └── mcp.json                  # Development MCP config
├── dist/                         # Built packages
├── pyproject.toml                # Package configuration
├── README.md                     # This file
└── LICENSE                       # MIT license
```

## Architecture

This is a single-file implementation that:
1. Reads JSON-RPC requests from stdin
2. Scans configured directories for `*.md` files
3. Extracts variables using regex (`{variable}` pattern)
4. Substitutes variables in prompt content
5. Returns responses via stdout
6. Logs to stderr

## Version History

For detailed version information, release notes, and changelog, see [CHANGELOG.md](CHANGELOG.md).

---

For more information about the Model Context Protocol, see the [MCP specification](https://spec.modelcontextprotocol.io/).
