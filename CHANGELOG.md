# Changelog

All notable changes to the Prompt MCP Server project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.7] - 2025-06-15

### Added
- **Real-time File Monitoring with MCP Notifications**: Complete solution for dynamic prompt updates
  - Monitors all prompt directories every 2 seconds for changes
  - Detects added, removed, and modified .md files automatically
  - Sends MCP `notifications/prompts/list_changed` to Amazon Q CLI
  - Amazon Q CLI automatically refreshes prompt list when notified
  - Background thread-based monitoring with proper cleanup
  - Logs specific file changes (added/removed/modified) for debugging

- **Configurable Logging System**: Production-ready logging with debug capabilities
  - **MCP_LOG_LEVEL**: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - **MCP_DEBUG_LOGGING**: Enable comprehensive debug logging (1, true, yes, on)
  - **MCP_LOG_FILE**: Set custom debug log file path (default: /tmp/mcp_server_debug.log)
  - Default: WARNING level (production-safe, minimal output)
  - Debug mode: Creates log file with detailed request/response tracing
  - Color-coded log messages with emojis for easy identification

- **Enhanced Debug Features**: When MCP_DEBUG_LOGGING is enabled
  - 📥 Raw requests received from Amazon Q CLI
  - 🔵 Parsed incoming requests with full JSON details
  - 🟢 Outgoing responses with complete content
  - 📤 Raw responses sent to Amazon Q CLI
  - 📢 MCP notifications sent (prompts list changed)
  - File monitoring activity and cache operations
  - Request/response timing and performance metrics

### Fixed
- **Dynamic Prompt Updates**: Resolved issue where Amazon Q CLI didn't refresh after file changes
  - Root cause: Missing MCP notification protocol implementation
  - Solution: Added `notifications/prompts/list_changed` when files change
  - Amazon Q CLI now automatically calls `prompts/list` when notified
  - No manual refresh needed - changes appear immediately

### Changed
- **Production-Ready Defaults**: Optimized for production use
  - Default logging level: WARNING (minimal, performance-focused)
  - Debug features disabled by default
  - Log file only created when debug logging is enabled
  - Maintains backward compatibility with existing configurations
  - Now: Continuously monitors directories and updates prompt list in real-time
  - Example: Deleting `home_test.md` while server is running now removes it from `/prompts list`

### Technical Details
- File monitoring runs in background daemon thread
- Uses polling approach (2-second intervals) for cross-platform compatibility
- Tracks file modification times to detect changes efficiently
- Graceful thread shutdown when server stops
- No external dependencies required (uses built-in threading)

## [2.0.6] - 2025-06-15

### Changed
- **Code Organization**: Moved all Python files to `mcp_server/` directory for better project structure
  - Moved `mcp_wrapper.py` to `mcp_server/mcp_wrapper.py`
  - Moved `debug_mcp_wrapper.py` to `mcp_server/debug_mcp_wrapper.py`
  - Moved `debug_uvx_wrapper.py` to `mcp_server/debug_uvx_wrapper.py`
  - All Python code now consolidated in single directory

### Updated
- **Package Configuration**: Updated entry point to `mcp_server.mcp_wrapper:main`
- **Build Configuration**: Updated pyproject.toml to include all files from mcp_server/ directory
- **Configuration Files**: Added multiple configuration options for different deployment scenarios
  - `mcp.json` - Main configuration (packaged version)
  - `mcp-packaged.json` - Explicit packaged version configuration
  - `mcp-source.json` - Source-based execution configuration
  - `mcp-direct.json` - Direct server execution (for testing)

### Benefits
- **Better Organization**: Cleaner project structure following Python package conventions
- **Easier Maintenance**: Logical grouping of related files in single directory
- **Professional Layout**: Standard Python project structure for better development experience
- **Preserved Functionality**: All v2.0.5 production wrapper features maintained

## [2.0.5] - 2025-06-15

### Added
- **SOLUTION**: Production MCP wrapper for Amazon Q CLI compatibility
  - New `mcp_wrapper.py` - Production-ready wrapper with clean architecture
  - Threaded I/O handling for reliable communication with Amazon Q CLI
  - 5-second background task window to handle Amazon Q CLI timing requirements
  - Proper error handling and graceful shutdown mechanisms
  - Minimal production logging (WARNING level)

### Fixed
- **CRITICAL**: Complete resolution of Amazon Q CLI infinite loading and timeout issues
  - Root cause: Amazon Q CLI closes stdin after `notifications/initialized` but background tasks need time to execute
  - Solution: Wrapper maintains server connection during background task execution window
  - Fixed "Operation timed out: recv for tools/list" errors permanently
  - Fixed "Prompt list query failed for prompt_server" errors permanently
  - All prompts now load consistently without timeout issues

### Changed
- **Architecture**: Wrapper-based solution for better separation of concerns
  - Wrapper handles Amazon Q CLI timing and communication patterns
  - Server simplified to focus purely on MCP protocol implementation
  - Entry point updated to use wrapper for both source and packaged execution
  - Clean separation between timing logic (wrapper) and business logic (server)

### Technical Details
- Amazon Q CLI communication pattern: `initialize` → `notifications/initialized` → closes stdin → background tasks execute
- Background tasks (`tools/list`, `prompts/list`) need 5-second window to start and send requests
- Wrapper uses threading to monitor stdin closure and maintain server connection
- Server uses simplified blocking I/O since wrapper handles timing complexity
- Both source execution and packaged distribution (uvx) now work reliably

## [2.0.4] - 2025-06-15

### Added
- **SOLUTION**: Production MCP wrapper for Amazon Q CLI compatibility
  - New `mcp_wrapper.py` - Production-ready wrapper with clean architecture
  - Threaded I/O handling for reliable communication with Amazon Q CLI
  - 5-second background task window to handle Amazon Q CLI timing requirements
  - Proper error handling and graceful shutdown mechanisms
  - Minimal production logging (WARNING level)

### Fixed
- **CRITICAL**: Complete resolution of Amazon Q CLI infinite loading and timeout issues
  - Root cause: Amazon Q CLI closes stdin after `notifications/initialized` but background tasks need time to execute
  - Solution: Wrapper maintains server connection during background task execution window
  - Fixed "Operation timed out: recv for tools/list" errors permanently
  - Fixed "Prompt list query failed for prompt_server" errors permanently
  - All prompts now load consistently without timeout issues

### Changed
- **Architecture**: Wrapper-based solution for better separation of concerns
  - Wrapper handles Amazon Q CLI timing and communication patterns
  - Server simplified to focus purely on MCP protocol implementation
  - Entry point updated to use wrapper for both source and packaged execution
  - Clean separation between timing logic (wrapper) and business logic (server)

### Technical Details
- Amazon Q CLI communication pattern: `initialize` → `notifications/initialized` → closes stdin → background tasks execute
- Background tasks (`tools/list`, `prompts/list`) need 5-second window to start and send requests
- Wrapper uses threading to monitor stdin closure and maintain server connection
- Server uses simplified blocking I/O since wrapper handles timing complexity
- Both source execution and packaged distribution (uvx) now work reliably

## [2.0.4] - 2025-06-15

### Fixed
- **CRITICAL**: Resolved Amazon Q CLI infinite loading and timeout issues
  - Fixed "Operation timed out: recv for tools/list" error
  - Fixed "Prompt list query failed for prompt_server" error
  - Server now stays alive after `notifications/initialized` for background tasks
  - Proper handling of Amazon Q CLI's asynchronous background task execution
  - Enhanced server lifecycle management for MCP protocol compliance

### Changed
- Server persistence: Continues running after initialization to handle background requests
- Improved Amazon Q CLI compatibility with proper background task timing
- Enhanced error handling for stdin connection lifecycle
- Better logging and debugging capabilities for MCP communication

### Technical Details
- Amazon Q CLI spawns background tasks after `notifications/initialized` 
- Background tasks call `tools/list` and `prompts/list` asynchronously
- Server must remain alive to handle these delayed requests
- Fixed race condition between server shutdown and background task execution

## [2.0.3] - 2025-06-15

### Security
- **CRITICAL**: Fixed HIGH severity shell injection vulnerability (CWE-78) in `tools/publish.py`
  - Removed dangerous `shell=True` from subprocess calls
  - Replaced shell commands with secure argument lists
  - Added proper input validation and sanitization
- Fixed LOW severity security issues:
  - Enhanced exception handling (replaced bare `except:` with specific exceptions)
  - Added full executable path resolution for tools (uvx, etc.)
  - Improved tool availability checking with graceful fallbacks

### Removed
- Removed obsolete `debug_mcp_server.py` (no longer needed due to project maturity)
- Cleaned up documentation references to removed debug server

### Improved
- Enhanced `.gitignore` with comprehensive Python project exclusions
- Updated security best practices throughout codebase
- Added comprehensive security audit documentation
- Improved error handling and logging in build tools

### Security Audit Results
- HIGH severity vulnerabilities: 1 → 0 (FIXED)
- MEDIUM severity vulnerabilities: 0 → 0 (NONE)
- LOW severity vulnerabilities: 35 → 32 (3 FIXED, 29 acceptable test-code only)
- Production server code: ZERO vulnerabilities

## [2.0.2] - 2025-06-15

### Added
- Complete MCP protocol compliance with all required methods
- `tools/list` method returning empty tools array (we provide prompts, not tools)
- `resources/list` method returning empty resources array
- Enhanced capabilities declaration in initialize method
- Comprehensive MCP testing guide (`tests/MCP_TESTING.md`)
- MCP protocol compliance test (`test_mcp_protocol.py`)
- Connection test script (`test_mcp_connection.py`)

### Fixed
- **MAJOR**: Fixed "Servers still loading" issue with Amazon Q CLI
- UVX caching compatibility by bumping version number
- MCP protocol initialization sequence now completes successfully
- Server properly declares tools and resources capabilities even when empty
- Enhanced error handling and request routing

### Changed
- Updated initialize method to include tools and resources in capabilities
- Improved server startup and shutdown handling with signal management
- Enhanced logging for better debugging of MCP client interactions
- Updated test configuration to use wheel package distribution

### Technical Details
- Added synchronous and asynchronous run methods for better client compatibility
- Implemented proper MCP JSON-RPC request/response handling
- Enhanced stdin/stdout communication for MCP protocol
- Added comprehensive test suite covering all MCP methods

## [2.0.1] - 2025-06-14

### Added
- Enhanced prompt scanning with better error handling
- Comprehensive test suite with 31 unit tests
- Support for multiple prompt directories via PROMPTS_PATH environment variable
- Caching mechanism for improved performance
- Variable substitution in prompt content
- Detailed logging and debugging capabilities

### Fixed
- File permission error handling
- Empty file detection and warnings
- Large file handling improvements
- Regex compatibility in prompt content

### Changed
- Improved prompt file parsing and validation
- Enhanced directory management and creation
- Better error messages and user feedback

## [2.0.0] - 2025-06-13

### Added
- Initial MCP (Model Context Protocol) server implementation
- Prompt file management and scanning
- Support for markdown prompt files with frontmatter
- Variable substitution in prompts using `{variable}` syntax
- Default prompt directory at `~/.aws/amazonq/prompts`
- Basic MCP protocol methods: `initialize`, `prompts/list`, `prompts/get`
- UVX package distribution support
- Comprehensive documentation and README

### Features
- **Prompt Discovery**: Automatically scans directories for `.md` files
- **Variable Support**: Dynamic variable substitution in prompt content
- **Caching**: Intelligent caching with TTL for performance
- **Error Handling**: Robust error handling for file operations
- **Logging**: Detailed logging for debugging and monitoring
- **Testing**: Comprehensive test suite with multiple test categories

### Technical Implementation
- Single-file MCP server for easy distribution
- Asynchronous request handling
- JSON-RPC 2.0 protocol compliance
- Cross-platform compatibility (Windows, macOS, Linux)
- Python 3.8+ support

## [Unreleased]

### Planned
- Support for HTTP transport (currently stdio only)
- Plugin system for custom prompt processors
- Web interface for prompt management
- Integration with additional AI development tools
- Performance optimizations for large prompt collections

---

## Version History Summary

| Version | Date | Key Changes |
|---------|------|-------------|
| 2.0.2 | 2025-06-15 | **Complete MCP protocol compliance**, fixes Amazon Q CLI loading issue |
| 2.0.1 | 2025-06-14 | Enhanced testing, error handling, and performance improvements |
| 2.0.0 | 2025-06-13 | Initial MCP server implementation with prompt management |

## Breaking Changes

### 2.0.0
- Initial release, no breaking changes from previous versions

## Migration Guide

### Upgrading to 2.0.2
- No breaking changes from 2.0.1
- Existing configurations will continue to work
- New MCP methods are automatically available
- UVX cache may need clearing for immediate upgrade: use new version number

### Upgrading to 2.0.1
- No breaking changes from 2.0.0
- Enhanced error handling may show different warning messages
- Improved caching may affect performance characteristics

## Development Notes

### Testing
- All versions include comprehensive test suites
- MCP protocol compliance verified for each release
- Cross-platform testing on Windows, macOS, and Linux
- Integration testing with Amazon Q CLI

### Distribution
- Available as wheel package and source distribution
- UVX compatible for easy installation and execution
- Direct Python execution supported for development

### Documentation
- Complete API documentation in README.md
- Testing guides in tests/MCP_TESTING.md
- Inline code documentation and examples

---

**Note**: This project follows semantic versioning. Major version changes indicate breaking changes, minor versions add functionality, and patch versions include bug fixes and improvements.

For detailed technical information, see the [README.md](README.md) file.
For testing instructions, see [tests/MCP_TESTING.md](tests/MCP_TESTING.md).
