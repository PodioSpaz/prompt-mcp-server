# Quick MCP Server Generation Prompt

**Create a Python MCP server for Amazon Q CLI that manages prompt files:**

## Core Features
- **Real-time file monitoring** with MCP notifications
- **JSON-RPC 2.0** compliant MCP protocol
- **Configurable logging** (MCP_LOG_LEVEL, MCP_DEBUG_LOGGING, MCP_LOG_FILE)
- **Security hardened** with path validation and input sanitization
- **Cross-platform** support (Unix/Linux/macOS/Windows)

## Key Components
1. **Main Server** (`prompt_mcp_server.py`):
   - PromptMCPServer class with version 2.0.9
   - File monitoring thread (2-second intervals)
   - MCP protocol handlers (initialize, prompts/list, prompts/get)
   - Variable substitution for `{variable}` placeholders
   - Cache management with TTL

2. **Production Wrapper** (`mcp_wrapper.py`):
   - Subprocess management for Amazon Q CLI compatibility
   - Stdin/stdout/stderr forwarding
   - Debug log file creation

3. **Configuration**:
   - Default: `~/.aws/amazonq/prompts`
   - Custom: `PROMPTS_PATH` environment variable
   - Multiple MCP config examples (.amazonq/*.json)

4. **Package Setup** (`pyproject.toml`):
   - Name: prompt-mcp-server
   - Entry: mcp_server.mcp_wrapper:main
   - No dependencies, Python 3.8+

## Security Features
- Path traversal protection
- File size limits (1MB)
- Input sanitization
- Secure logging
- Error message sanitization

## File Structure
```
mcp_server/
├── prompt_mcp_server.py  # Main server
└── mcp_wrapper.py        # Production wrapper
.amazonq/
├── mcp.json             # Local config
├── mcp-testpypi.json    # TestPyPI config
└── mcp-pypi.json        # Production config
tests/                   # Comprehensive tests
tools/publish.py         # Publishing automation
pyproject.toml          # Package config
README.md               # Documentation
CHANGELOG.md            # Version history
```

**Generate complete, production-ready code with proper MCP protocol implementation, security measures, and comprehensive documentation.**
