# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server for Amazon Q Developer CLI that manages prompt files (*.md) from local directories. It's a pure Python implementation with zero dependencies, designed for cross-platform compatibility.

**Key Architecture:**
- Single-file MCP server implementation (`mcp_server/prompt_mcp_server.py`)
- Production wrapper (`mcp_server/mcp_wrapper.py`) that handles Amazon Q CLI timing issues by keeping connections alive for background tasks
- Real-time file monitoring with notifications to Amazon Q CLI
- Variable substitution in prompts using `{variable}` placeholders
- Optional YAML frontmatter for explicit metadata and argument control
- PATH-like directory configuration via `PROMPTS_PATH` environment variable

## Common Commands

### Testing
```bash
# Run all tests (53 tests total)
python3 tests/run_all_tests.py

# Run only unit tests (31 tests)
python3 tests/run_all_tests.py --unit-only

# Run only functional tests (14 tests)
python3 tests/run_all_tests.py --functional-only

# Run specific test suites
python3 tests/test_prompt_mcp_server.py    # Unit tests
python3 tests/test_functional.py           # Functional tests
python3 tests/test_uvx_integration.py      # UVX integration tests (8 tests)
```

### Building & Publishing
```bash
# Build package
pyproject-build

# Test with uvx (use actual version from pyproject.toml)
uvx --from ./dist/prompt_mcp_server-2.0.9-py3-none-any.whl prompt-mcp-server

# Publishing workflow
python3 tools/publish.py --build-only    # Build only
python3 tools/publish.py --test          # Build and test with uvx
python3 tools/publish.py --testpypi      # Publish to TestPyPI
python3 tools/publish.py --pypi          # Publish to PyPI
```

### Running the Server
```bash
# Direct execution
python3 mcp_server/prompt_mcp_server.py

# With custom directories
PROMPTS_PATH="./prompts:~/.aws/amazonq/prompts" python3 mcp_server/prompt_mcp_server.py

# With debug logging
MCP_DEBUG_LOGGING=1 python3 mcp_server/prompt_mcp_server.py
# Monitor debug logs in another terminal:
tail -f /tmp/mcp_server_debug.log
```

### Amazon Q Integration
```bash
# Verify MCP configuration
q mcp list

# Start Amazon Q CLI
q chat

# In Amazon Q CLI:
/prompts                  # List available prompts
@prompt_name              # Use a prompt
```

## Code Architecture

### Core Components

**prompt_mcp_server.py** (single-file server):
- `PromptMCPServer` class: Main server implementation
- JSON-RPC over stdin/stdout communication
- File monitoring with threading
- Prompt discovery and variable extraction using regex
- YAML frontmatter parsing (zero-dependency implementation)
- Cache management with 5-minute TTL
- MCP protocol methods: `initialize`, `prompts/list`, `prompts/get`

**mcp_wrapper.py** (production wrapper):
- Solves Amazon Q CLI timing issues where stdin closes after `notifications/initialized`
- Keeps server alive for 5 seconds after stdin closure to allow background tasks
- Three-thread architecture: stdin reader, stdout reader, stderr reader
- Optional debug logging to file when `MCP_DEBUG_LOGGING=1`

**File Monitoring Architecture:**
- Background thread monitors prompt directories for changes
- Uses file modification timestamps to detect changes
- Sends `notifications/prompts/list_changed` to Amazon Q CLI on changes
- 1-second polling interval with graceful shutdown

### Key Design Patterns

1. **Zero Dependencies**: Pure Python 3.6+ with no external packages (includes custom YAML parser)
2. **Cross-Platform Paths**: Uses `pathlib.Path` for Unix/Linux/macOS compatibility
3. **Error Handling**: Comprehensive validation with detailed logging to stderr
4. **Caching**: 5-minute TTL cache for prompt discovery with invalidation on file changes
5. **Variable Substitution**: Regex-based `{variable}` placeholder replacement in prompts
6. **Frontmatter Parsing**: Zero-dependency YAML parser supporting key-value pairs, arrays, and nested objects

## Environment Variables

- `PROMPTS_PATH`: Colon-separated directories (default: `~/.aws/amazonq/prompts`)
- `MCP_LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: WARNING)
- `MCP_DEBUG_LOGGING`: Enable debug mode (1, true, yes, on)
- `MCP_LOG_FILE`: Debug log path (default: `/tmp/mcp_server_debug.log`)

## Configuration Files

The `.amazonq/` directory contains multiple MCP configurations for different use cases:
- `mcp.json`: Local development using source files
- `mcp-packaged.json`: Local development using built wheel
- `mcp-pypi.json`: Production using PyPI package
- `mcp-testpypi.json`: Testing with TestPyPI
- `mcp-with-env-var.json`: Example with custom `PROMPTS_PATH`

Switch configurations by copying the desired file to `mcp.json` or use workspace-specific configs in `tests/.amazonq/`.

## Important Implementation Details

**Version Management:**
- Version is defined in `pyproject.toml` and hardcoded in `prompt_mcp_server.py`
- Always update both locations when changing version

**Entry Point:**
- Package entry point is `mcp_wrapper.py` via `pyproject.toml` scripts section
- Wrapper launches the actual server using `python3 -m mcp_server.prompt_mcp_server`

**File Size Limits:**
- Prompt files are limited to 1MB for safety
- Files use UTF-8 encoding with latin-1 fallback

**Testing Philosophy:**
- Current status: 100% test success rate (53 tests)
- Tests cover MCP protocol compliance, file monitoring, error handling, and Amazon Q integration
- Test results are documented in `tests/results/`

## Prompt File Format

Prompts are markdown files (*.md) in configured directories.

### Basic Format (Legacy - Still Supported)
```markdown
# Prompt Title
Description of what this prompt does.

Use {variable} placeholders for substitution.
```

Variables are automatically extracted and prompted to the user in Amazon Q CLI.

### YAML Frontmatter Format (New in 2.1.0)

Add optional YAML frontmatter for explicit control:

```markdown
---
name: "code-reviewer"
title: "Code Review Assistant"
description: "Performs comprehensive code review"
arguments:
  - name: "code"
    description: "Source code to review"
    required: true
  - name: "language"
    description: "Programming language"
    default: "Python"
  - name: "focus"
    description: "Review focus area"
    default: "security"
---

Analyze the following {language} code with focus on {focus}:

{code}
```

**Frontmatter Fields:**
- `name`: Custom prompt identifier (default: filename stem)
- `title`: Display title (default: `description` or first heading)
- `description`: Detailed description (default: `title` or first heading)
- `arguments`: Explicit argument definitions (default: auto-discovered from content)

**Argument Fields:**
- `name` (required): Parameter identifier
- `description` (required): Parameter explanation
- `default` (optional): Default value (makes argument optional)
- `required` (optional): Explicit required flag (default: `true` if no `default`)

**Backward Compatibility:**
- Files without frontmatter work exactly as before
- No breaking changes to existing prompts
