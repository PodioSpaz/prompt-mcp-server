# Technical Specification for MCP Prompt Server

## Project Overview
Create a Model Context Protocol (MCP) server that manages markdown prompt files for Amazon Q Developer CLI with real-time monitoring and security hardening.

## Architecture Requirements

### Core Server (`mcp_server/prompt_mcp_server.py`)
```python
class PromptMCPServer:
    def __init__(self):
        self.version = "2.0.9"
        self.name = "prompt-mcp-server"
        # File monitoring setup
        # Cache management
        # Directory configuration
```

**Key Methods:**
- `handle_initialize()` - MCP protocol initialization
- `handle_prompts_list()` - Return available prompts
- `handle_prompts_get()` - Serve prompt with variable substitution
- `_file_monitor_worker()` - Background file monitoring
- `_send_prompts_list_changed_notification()` - MCP notifications

### Production Wrapper (`mcp_server/mcp_wrapper.py`)
- Subprocess management for server process
- Stdin/stdout/stderr forwarding
- Amazon Q CLI timing compatibility
- Debug logging to file when enabled

### Environment Variables
- `PROMPTS_PATH`: Colon-separated directories (default: ~/.aws/amazonq/prompts)
- `MCP_LOG_LEVEL`: DEBUG|INFO|WARNING|ERROR|CRITICAL (default: WARNING)
- `MCP_DEBUG_LOGGING`: 1|true|yes|on (enables comprehensive logging)
- `MCP_LOG_FILE`: Custom log file path (default: /tmp/mcp_server_debug.log)

## MCP Protocol Implementation

### Initialize Request/Response
```json
Request: {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
Response: {
  "jsonrpc": "2.0", "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {"prompts": {"listChanged": true}},
    "serverInfo": {"name": "prompt-mcp-server", "version": "2.0.9"}
  }
}
```

### Prompts List Request/Response
```json
Request: {"jsonrpc": "2.0", "id": 2, "method": "prompts/list"}
Response: {
  "jsonrpc": "2.0", "id": 2,
  "result": {
    "prompts": [
      {
        "name": "debug_code",
        "description": "Debug code issues",
        "arguments": [{"name": "code", "description": "Code to debug", "required": true}]
      }
    ]
  }
}
```

### Prompts Get Request/Response
```json
Request: {
  "jsonrpc": "2.0", "id": 3, "method": "prompts/get",
  "params": {"name": "debug_code", "arguments": {"code": "print('hello')"}}
}
Response: {
  "jsonrpc": "2.0", "id": 3,
  "result": {
    "description": "Prompt: debug_code",
    "messages": [{"role": "user", "content": {"type": "text", "text": "Debug this code: print('hello')"}}]
  }
}
```

### Notification (Server to Client)
```json
{"jsonrpc": "2.0", "method": "notifications/prompts/list_changed", "params": {}}
```

## File Monitoring Implementation
- Background thread checking every 2 seconds
- Track file modification times per directory
- Detect added, removed, and modified files
- Clear cache and send MCP notification on changes
- Proper thread cleanup on shutdown

## Security Requirements

### Path Validation
```python
def _validate_path(self, path_str: str) -> Path:
    # Resolve and validate path
    # Prevent traversal attacks
    # Ensure within allowed directories
```

### File Processing Security
- Maximum file size: 1MB
- Only process .md files
- Validate file permissions
- Handle encoding errors gracefully
- Sanitize file content for logging

### Input Sanitization
- Sanitize all user input before logging
- Validate prompt names and arguments
- Escape special characters in error messages
- Prevent log injection attacks

## Configuration Files

### Local Development (`.amazonq/mcp.json`)
```json
{
  "mcpServers": {
    "prompt-server": {
      "command": "python3",
      "args": ["mcp_server/prompt_mcp_server.py"],
      "timeout": 30000
    }
  }
}
```

### TestPyPI Configuration (`.amazonq/mcp-testpypi.json`)
```json
{
  "mcpServers": {
    "prompt-server": {
      "command": "uvx",
      "args": ["--index-url", "https://test.pypi.org/simple/", "prompt-mcp-server@latest"],
      "env": {
        "PROMPTS_PATH": "~/.aws/amazonq/prompts",
        "MCP_DEBUG_LOGGING": "true",
        "MCP_LOG_LEVEL": "DEBUG",
        "MCP_LOG_FILE": "/tmp/mcp_server_debug.log"
      },
      "timeout": 30000
    }
  }
}
```

### Production Configuration (`.amazonq/mcp-pypi.json`)
```json
{
  "mcpServers": {
    "prompt-server": {
      "command": "uvx",
      "args": ["prompt-mcp-server@latest"],
      "timeout": 30000
    }
  }
}
```

## Package Configuration (`pyproject.toml`)
```toml
[project]
name = "prompt-mcp-server"
version = "2.0.9"
description = "MCP server for Amazon Q Developer CLI that manages prompt files"
requires-python = ">=3.8"
dependencies = []

[project.scripts]
prompt-mcp-server = "mcp_server.mcp_wrapper:main"
```

## Testing Requirements
- Unit tests for all MCP protocol methods
- File monitoring functionality tests
- Security validation tests
- Cross-platform compatibility tests
- Integration tests with uvx
- Error handling and edge case tests

## Documentation Requirements
- Comprehensive README with setup instructions
- Configuration examples for all deployment scenarios
- Environment variable documentation
- Troubleshooting guide
- Security considerations
- API documentation for MCP protocol implementation

**Generate complete implementation following this specification with proper error handling, logging, security measures, and comprehensive testing.**
