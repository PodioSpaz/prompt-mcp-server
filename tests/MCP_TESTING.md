# MCP Server Testing Guide (Version 2.0.7)

This directory contains the test configuration and tools for testing the MCP server with Amazon Q CLI.

## Version 2.0.7 Features

✅ **Real-time File Monitoring**: Test dynamic prompt updates
✅ **MCP Notifications**: Verify automatic Amazon Q CLI refresh
✅ **Configurable Logging**: Test debug logging capabilities
✅ **Production Ready**: Validate minimal logging defaults

## Configuration

### `tests/.amazonq/mcp.json`
This is the MCP configuration file that Amazon Q CLI will use when running from the `tests/` directory.

**Current Configuration:**

```json
{
  "mcpServers": {
    "prompt-server": {
      "command": "uvx",
      "args": ["--from", "../dist/prompt_mcp_server-2.0.7-py3-none-any.whl", "prompt-mcp-server"],
      "timeout": 30000
    }
  }
}
```

This configuration:

- Uses UVX with the built wheel package for testing (Version 2.0.7)
- Points to the server wheel file relative to the tests directory
- Sets a 30-second timeout for server responses (increased for file monitoring)
- Supports all Version 2.0.7 features including real-time updates

## Testing the MCP Server

### Basic Functionality Testing

### 1. Quick Manual Test
From the tests directory, you can manually test the server:

```bash
cd tests/
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}' | python3 ../mcp_server/prompt_mcp_server.py
```

### 2. Comprehensive Test
Run the comprehensive test script:

```bash
python3 tests/test_mcp_from_tests_dir.py
```

This test verifies:
- ✅ Server initialization
- ✅ Tools/list (returns empty array)
- ✅ Resources/list (returns empty array)
- ✅ Prompts/list (returns available prompts)
- ✅ Prompts/get (retrieves specific prompts)

### 3. Protocol Compliance Test
Run the MCP protocol compliance test:

```bash
python3 test_mcp_protocol.py
```

## Testing with Amazon Q CLI

### Setup
1. Navigate to the `tests/` directory
2. Ensure the `.amazonq/mcp.json` file exists
3. Run Amazon Q CLI from this directory

### Expected Behavior
When you run `/tools` in Amazon Q CLI from the tests directory:
- The `prompt-server` should load successfully
- No "Servers still loading" message should appear
- The server should be available for use

### Troubleshooting

#### Server Shows "Still Loading"
If the server still shows as loading:
1. Check the server logs for errors
2. Verify the Python path is correct
3. Test manually with the commands above
4. Ensure all MCP protocol methods are working

#### Server Not Found
If the server is not found:
1. Verify you're in the `tests/` directory
2. Check that `.amazonq/mcp.json` exists
3. Verify the relative path `../mcp_server/prompt_mcp_server.py` is correct

#### Permission Errors
If you get permission errors:
1. Ensure the server file is executable
2. Check Python is available in PATH
3. Verify file permissions on the server script

## Configuration Variants

### For Development (Current)
```json
{
  "command": "python3",
  "args": ["../mcp_server/prompt_mcp_server.py"]
}
```
- Uses direct Python execution
- Good for testing changes without rebuilding

### For Production Testing
```json
{
  "command": "uvx",
  "args": ["--from", "../dist/prompt_mcp_server-2.0.1-py3-none-any.whl", "prompt-mcp-server"]
}
```
- Uses built wheel package
- Good for testing final package

### For Published Package
```json
{
  "command": "uvx",
  "args": ["prompt-mcp-server"]
}
```
- Uses published package from PyPI
- Good for end-user testing

## Test Results

### Expected MCP Protocol Responses

**Initialize:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "prompts": {"listChanged": true},
      "tools": {},
      "resources": {}
    },
    "serverInfo": {
      "name": "prompt-mcp-server",
      "version": "2.0.1"
    }
  }
}
```

**Tools/List:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": []
  }
}
```

**Resources/List:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "resources": []
  }
}
```

**Prompts/List:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "prompts": [
      {
        "name": "debug_code",
        "description": "Debug {language} Code",
        "arguments": [...]
      }
      // ... more prompts
    ]
  }
}
```

## Success Criteria

The MCP server is working correctly when:
- ✅ All protocol methods return valid responses
- ✅ No "Method not found" errors occur
- ✅ Server initializes with proper capabilities
- ✅ Amazon Q CLI shows server as loaded (not "still loading")
- ✅ Prompts can be retrieved and used

---

**Last Updated:** 2025-06-15
**Configuration Version:** Direct Python execution
**Server Version:** 2.0.1
