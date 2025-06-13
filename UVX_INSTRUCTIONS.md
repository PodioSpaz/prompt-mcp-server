# UVX Usage Instructions

This document provides step-by-step instructions for building, testing, and using the Prompt MCP Server with uvx.

## Prerequisites

1. **Install uvx** (if not already installed):
   ```bash
   brew install pipx
   pipx install uv
   ```

2. **Verify uvx installation**:
   ```bash
   uvx --version
   ```

## Building the Package

1. **Install build tools**:
   ```bash
   pipx install build
   ```

2. **Build the package**:
   ```bash
   pyproject-build
   ```

3. **Verify build artifacts**:
   ```bash
   ls -la dist/
   # Should show:
   # prompt_mcp_server-2.0.0-py3-none-any.whl
   # prompt_mcp_server-2.0.0.tar.gz
   ```

## Testing with UVX

### Important Notes

- **Long-running process**: The MCP server is designed to run continuously and read from stdin
- **No --help flag**: The server doesn't support command-line help flags
- **JSON-RPC protocol**: All communication is via JSON-RPC 2.0 over stdin/stdout
- **Testing on macOS**: Use Ctrl+C to interrupt tests since `timeout` command is not available

### Basic Functionality Test

1. **Test server initialization**:
   ```bash
   echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | uvx --from ./dist/prompt_mcp_server-2.0.0-py3-none-any.whl prompt-mcp-server
   ```
   
   **Expected**: JSON response with server info, then press Ctrl+C to stop
   ```json
   {"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05", "capabilities": {"prompts": {"listChanged": true}}, "serverInfo": {"name": "prompt-mcp-server", "version": "2.0.0"}}}
   ```

2. **Test prompts listing**:
   ```bash
   echo '{"jsonrpc": "2.0", "id": 2, "method": "prompts/list"}' | uvx --from ./dist/prompt_mcp_server-2.0.0-py3-none-any.whl prompt-mcp-server
   ```
   
   **Expected**: JSON response with available prompts, then press Ctrl+C to stop

3. **Test prompt retrieval**:
   ```bash
   echo '{"jsonrpc": "2.0", "id": 3, "method": "prompts/get", "params": {"name": "debug_code"}}' | uvx --from ./dist/prompt_mcp_server-2.0.0-py3-none-any.whl prompt-mcp-server
   ```
   
   **Expected**: JSON response with prompt content, then press Ctrl+C to stop

### Multiple Request Test

Create a test file with multiple requests:

```bash
cat > test_requests.jsonl << 'EOF'
{"jsonrpc": "2.0", "id": 1, "method": "initialize"}
{"jsonrpc": "2.0", "id": 2, "method": "prompts/list"}
{"jsonrpc": "2.0", "id": 3, "method": "prompts/get", "params": {"name": "debug_code"}}
EOF

# Test multiple requests (press Ctrl+C after responses)
uvx --from ./dist/prompt_mcp_server-2.0.0-py3-none-any.whl prompt-mcp-server < test_requests.jsonl
```

**Expected**: Three JSON responses, one for each request, then press Ctrl+C to stop

### Environment Variable Test

Test with custom prompt directory:

```bash
# Create test prompt
mkdir -p /tmp/test_prompts
echo "# Test Prompt
This is a test prompt." > /tmp/test_prompts/test.md

# Test with custom PROMPTS_PATH (press Ctrl+C after response)
PROMPTS_PATH="/tmp/test_prompts" echo '{"jsonrpc": "2.0", "id": 1, "method": "prompts/list"}' | uvx --from ./dist/prompt_mcp_server-2.0.0-py3-none-any.whl prompt-mcp-server
```

**Expected**: JSON response showing the test prompt, then press Ctrl+C to stop

## Amazon Q CLI Integration

### Workspace Configuration

The project includes two configuration files:

1. **`.amazonq/mcp.json`** - For local development (uses built wheel):
   ```json
   {
     "mcpServers": {
       "prompt-server": {
         "command": "uvx",
         "args": ["--from", "./dist/prompt_mcp_server-2.0.0-py3-none-any.whl", "prompt-mcp-server"],
         "timeout": 10000
       }
     }
   }
   ```

2. **`.amazonq/mcp-published.json`** - For published package (copy to `mcp.json` after publishing):
   ```json
   {
     "mcpServers": {
       "prompt-server": {
         "command": "uvx",
         "args": ["prompt-mcp-server"],
         "timeout": 10000
       }
     }
   }
   ```

### Testing Amazon Q Integration

1. **Verify configuration**:
   ```bash
   q mcp list
   # Should show: prompt-server uvx
   ```

2. **Test in Amazon Q**:
   ```bash
   q chat
   # Then in the chat:
   /prompts
   @debug_code
   ```

### Switching Configurations

**For local development** (current setup):
```bash
# Already configured - uses local wheel file
q mcp list
```

**After publishing to PyPI**:
```bash
# Copy the published configuration
cp .amazonq/mcp-published.json .amazonq/mcp.json

# Verify
q mcp list
# Should still show: prompt-server uvx
```

## Publishing Preparation

### Test Installation from Different Sources

1. **Test from local wheel**:
   ```bash
   echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | uvx --from ./dist/prompt_mcp_server-2.0.0-py3-none-any.whl prompt-mcp-server
   ```

2. **Test from local directory**:
   ```bash
   echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | uvx --from . prompt-mcp-server
   ```

3. **Test from tarball**:
   ```bash
   echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | uvx --from ./dist/prompt_mcp_server-2.0.0.tar.gz prompt-mcp-server
   ```

### Verify Package Contents

```bash
# Extract and inspect wheel
unzip -l ./dist/prompt_mcp_server-2.0.0-py3-none-any.whl

# Should contain:
# - prompt_mcp_server.py
# - README.md
# - LICENSE
# - METADATA files
```

## Performance Testing

### Response Time Test

```bash
# Test response time (press Ctrl+C after response)
time echo '{"jsonrpc": "2.0", "id": 1, "method": "prompts/list"}' | uvx --from ./dist/prompt_mcp_server-2.0.0-py3-none-any.whl prompt-mcp-server
```

**Note**: The timing will include server startup time plus response time

### Memory Usage Test

```bash
# Monitor memory usage during execution (press Ctrl+C after response)
echo '{"jsonrpc": "2.0", "id": 1, "method": "prompts/list"}' | /usr/bin/time -l uvx --from ./dist/prompt_mcp_server-2.0.0-py3-none-any.whl prompt-mcp-server
```

**Note**: Use Ctrl+C to stop the server after seeing the response

## Troubleshooting

### Common Issues

1. **"Command not found" error**:
   - Ensure uvx is installed: `uvx --version`
   - Check PATH includes uvx location

2. **"Package not found" error**:
   - Verify wheel file exists: `ls -la dist/`
   - Use absolute path to wheel file

3. **JSON parsing errors**:
   - Ensure proper JSON format
   - Check for trailing newlines
   - Validate JSON with: `echo '...' | jq .`

4. **Process behavior on macOS**:
   - **Expected behavior**: MCP server waits for stdin input
   - **No timeout command**: Use Ctrl+C to interrupt tests
   - **Server runs indefinitely**: Until stdin is closed or interrupted
   - Increase timeout in Amazon Q config for production use

5. **Process hangs**:
   - **Normal behavior**: Server waits for JSON-RPC requests
   - Send requests via stdin or close stdin to terminate
   - Use Ctrl+C to interrupt if needed
   - Server will continue running until explicitly stopped

### Debug Mode

Enable debug logging:

```bash
# Set log level and test
MCP_LOG_LEVEL=DEBUG echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | uvx --from ./dist/prompt_mcp_server-2.0.0-py3-none-any.whl prompt-mcp-server
```

## Publishing Checklist

Before publishing to PyPI:

- [ ] All uvx tests pass
- [ ] Package builds successfully
- [ ] Amazon Q integration works
- [ ] Documentation is complete
- [ ] Version number is correct
- [ ] License is included
- [ ] README is comprehensive

## Publishing Commands

When ready to publish:

```bash
# Install publishing tools
pipx install twine

# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test from TestPyPI
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | uvx --from https://test.pypi.org/simple/ prompt-mcp-server

# Upload to PyPI
twine upload dist/*

# Test from PyPI
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | uvx prompt-mcp-server
```

## Post-Publishing Usage

Once published to PyPI:

```bash
# Install and run directly
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | uvx prompt-mcp-server

# Update Amazon Q config to use published version
{
  "mcpServers": {
    "prompt-server": {
      "command": "uvx",
      "args": ["prompt-mcp-server"],
      "timeout": 10000
    }
  }
}
```

---

**Note**: Replace `prompt_mcp_server-2.0.0-py3-none-any.whl` with the actual filename from your `dist/` directory if different.
