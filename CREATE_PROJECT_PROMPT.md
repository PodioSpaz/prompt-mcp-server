# Create MCP Prompt Server Project - AI Generation Prompt

Use this prompt with any generative AI to recreate the complete MCP Prompt Server project:

---

## Project Creation Prompt

**Create a complete Model Context Protocol (MCP) server project for Amazon Q Developer CLI with the following specifications:**

### Core Requirements
- **Language**: Python 3.8+ (no external dependencies)
- **Protocol**: JSON-RPC 2.0 compliant MCP server
- **Purpose**: Manage and serve prompt files (*.md) from local directories
- **Architecture**: Single-file server with wrapper for production compatibility

### Key Features to Implement

#### 1. Real-time File Monitoring
- Monitor prompt directories for file changes (add/remove/modify)
- Background thread checking every 2 seconds
- Send MCP notifications to Amazon Q CLI when changes detected
- Cache invalidation on file changes

#### 2. MCP Protocol Compliance
- Handle `initialize` request with proper capabilities
- Implement `prompts/list` to return available prompts
- Implement `prompts/get` with variable substitution
- Support `notifications/prompts/list_changed` for real-time updates
- Handle `tools/list` and `resources/list` (return empty)

#### 3. Configurable Logging System
- **MCP_LOG_LEVEL**: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: WARNING)
- **MCP_DEBUG_LOGGING**: Enable comprehensive debug logging (1, true, yes, on)
- **MCP_LOG_FILE**: Custom debug log file path (default: /tmp/mcp_server_debug.log)
- Color-coded log messages with emojis for easy identification
- Production-safe defaults with minimal output

#### 4. Prompt Management
- **Default directory**: `~/.aws/amazonq/prompts` (auto-created)
- **Custom directories**: Support `PROMPTS_PATH` environment variable (PATH-like format)
- **File processing**: Only *.md files, with size limits (1MB max)
- **Variable extraction**: Find `{variable}` placeholders in content
- **Variable substitution**: Replace placeholders in prompts/get requests

#### 5. Security Features
- Path validation and sanitization to prevent traversal attacks
- File size limits with proper validation
- Input sanitization for logging
- Error message sanitization
- Secure file permissions for log files
- Resource usage limits

#### 6. Cross-platform Support
- Unix/Linux/macOS primary support
- Windows compatibility
- Proper path handling with Path objects
- Environment variable parsing (colon vs semicolon separated)

### Project Structure
```
mcp-prompts-local/
├── mcp_server/
│   ├── __init__.py
│   ├── prompt_mcp_server.py    # Main server implementation
│   └── mcp_wrapper.py          # Production wrapper for Amazon Q CLI
├── .amazonq/
│   ├── mcp.json                # Local development config
│   ├── mcp-testpypi.json       # TestPyPI configuration
│   └── mcp-pypi.json           # Production PyPI configuration
├── tests/
│   ├── test_prompt_mcp_server.py
│   ├── test_functional.py
│   ├── test_mcp_integration.py
│   └── run_all_tests.py
├── tools/
│   └── publish.py              # Publishing automation
├── pyproject.toml              # Package configuration
├── README.md                   # Comprehensive documentation
├── CHANGELOG.md                # Version history
└── LICENSE                     # MIT License
```

### Technical Implementation Details

#### Main Server Class (PromptMCPServer)
- Version: 2.0.9
- Async and sync execution modes
- File monitoring thread management
- Cache management with TTL
- Comprehensive error handling

#### MCP Wrapper (Production)
- Subprocess management for server
- Stdin/stdout/stderr forwarding
- Amazon Q CLI compatibility timing
- Debug log file creation when enabled
- Clean shutdown handling

#### Configuration Examples
Provide multiple MCP configuration examples:
- Development (local Python execution)
- TestPyPI (testing with uvx)
- Production (PyPI with uvx)
- Debug mode (with all environment variables)

### Package Configuration
- **Name**: prompt-mcp-server
- **Version**: 2.0.9
- **Entry point**: mcp_server.mcp_wrapper:main
- **Python**: >=3.6
- **License**: MIT
- **No dependencies**: Pure Python implementation

### Testing Requirements
- Unit tests for all core functionality
- Functional tests for MCP protocol
- Integration tests with uvx
- File monitoring tests
- Error handling tests
- Cross-platform compatibility tests

### Documentation Requirements
- Comprehensive README with installation instructions
- Configuration examples for all scenarios
- Environment variable documentation
- Troubleshooting guide
- Security considerations
- Version history in CHANGELOG

### Security Considerations
- Implement path traversal protection
- File size validation with streaming
- Input sanitization for all user data
- Secure logging practices
- Resource usage limits
- Error message sanitization

### Publishing Setup
- PyPI-ready package configuration
- Automated build and test scripts
- TestPyPI testing workflow
- Version management automation
- Git tag integration

**Generate the complete project with all files, proper error handling, comprehensive tests, and production-ready code. Include detailed comments explaining the MCP protocol implementation and security measures.**

---

## Additional Context

This project should be a complete, production-ready MCP server that:
1. Integrates seamlessly with Amazon Q Developer CLI
2. Provides real-time prompt management
3. Follows security best practices
4. Includes comprehensive testing
5. Has proper documentation and examples
6. Can be published to PyPI

The generated code should be immediately usable and require no additional dependencies beyond Python 3.8+.
