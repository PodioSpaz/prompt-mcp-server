# AI Generation Prompts

This directory contains prompts for recreating the MCP Prompt Server project using generative AI.

## Directory Structure

### v2.0.9/
Contains prompts for recreating version 2.0.9 of the MCP Prompt Server with security improvements:

- **CREATE_PROJECT_PROMPT.md** - Comprehensive project creation prompt
  - Complete feature specifications
  - Detailed project structure
  - Security requirements
  - Documentation and testing requirements
  - Best for: Complete project recreation

- **QUICK_GENERATION_PROMPT.md** - Concise generation prompt
  - Essential features and components
  - Simplified structure overview
  - Quick reference format
  - Best for: Rapid prototyping

- **TECHNICAL_SPEC_PROMPT.md** - Detailed technical specification
  - Architecture requirements
  - MCP protocol implementation details
  - Code examples and JSON schemas
  - Security implementation requirements
  - Best for: Developer implementation

## How to Use

1. **Choose the appropriate prompt** based on your needs:
   - Full recreation → `CREATE_PROJECT_PROMPT.md`
   - Quick start → `QUICK_GENERATION_PROMPT.md`
   - Technical details → `TECHNICAL_SPEC_PROMPT.md`

2. **Copy the entire prompt** from the chosen file

3. **Paste into your AI tool** (ChatGPT, Claude, etc.)

4. **The AI will generate** the complete project structure with all files

## What Gets Generated

- Complete MCP server implementation (version 2.0.9)
- Real-time file monitoring with MCP notifications
- Security-hardened code with input validation
- Production wrapper for Amazon Q CLI compatibility
- Comprehensive test suite
- Configuration examples for all deployment scenarios
- Complete documentation and setup instructions
- PyPI publishing configuration

## Version History

- **v2.0.9**: Security-enhanced version with comprehensive hardening
  - Path traversal protection
  - Input sanitization
  - File size validation
  - Secure logging practices
  - Resource usage limits

## Future Versions

New versions will be added to separate directories (e.g., v2.1.0/) to maintain version-specific generation capabilities.
