#!/usr/bin/env python3
"""
Single-File Prompt MCP Server for Amazon Q Developer CLI

A Model Context Protocol (MCP) server that manages prompt files (*.md) from local directories.

Features:
- List all prompt files (*.md) from local directory
- Default directory: ~/.aws/amazonq/prompts
- Override with PROMPTS_PATH environment variable (PATH-like format)
- Cross-platform support (Unix/Linux/macOS)
- Error handling and user feedback
- MCP protocol compliance

Requirements:
- Python 3.6+
- No external dependencies

Usage:
    python3 prompt_mcp_server.py

Environment Variables:
    PROMPTS_PATH - Colon-separated list of directories to search for prompts
                   Default: ~/.aws/amazonq/prompts

Version: 2.0.2
Author: Amazon Q Developer CLI Team
"""

import asyncio
import json
import os
import sys
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
import logging

# Configure logging - INFO level for debugging Amazon Q CLI issues
logging.basicConfig(
    level=logging.INFO,  # Temporarily increase for debugging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

class PromptMCPServer:
    """Single-file MCP server for prompt management"""
    
    def __init__(self):
        self.version = "2.0.3"
        self.name = "prompt-mcp-server"
        self.prompt_directories = self._get_prompt_directories()
        self.prompts_cache = {}
        self.cache_timestamp = 0
        self.cache_ttl = 300  # 5 minutes
        
        logger.info(f"Initialized {self.name} v{self.version}")
        logger.info(f"Monitoring {len(self.prompt_directories)} directories for prompts:")
        for directory in self.prompt_directories:
            logger.info(f"  - {directory}")
    
    def _get_prompt_directories(self) -> List[Path]:
        """Get list of directories to search for prompts"""
        prompts_path = os.environ.get('PROMPTS_PATH')
        
        if prompts_path:
            # Parse PATH-like environment variable (cross-platform)
            separator = ';' if os.name == 'nt' else ':'
            directories = []
            for path_str in prompts_path.split(separator):
                if path_str.strip():
                    try:
                        path = Path(path_str.strip()).expanduser().resolve()
                        if path.exists() and path.is_dir():
                            directories.append(path)
                        else:
                            logger.warning(f"Directory not found: {path}")
                    except Exception as e:
                        logger.error(f"Invalid path '{path_str}': {e}")
            
            if not directories:
                logger.warning("No valid directories found in PROMPTS_PATH, using default")
                return self._get_default_directory()
            
            return directories
        else:
            return self._get_default_directory()
    
    def _get_default_directory(self) -> List[Path]:
        """Get default prompt directory with cross-platform support"""
        try:
            default_dir = Path.home() / '.aws' / 'amazonq' / 'prompts'
            default_dir.mkdir(parents=True, exist_ok=True)
            return [default_dir]
        except Exception as e:
            logger.error(f"Failed to create default directory: {e}")
            # Fallback to current directory
            fallback_dir = Path.cwd() / 'prompts'
            fallback_dir.mkdir(exist_ok=True)
            logger.info(f"Using fallback directory: {fallback_dir}")
            return [fallback_dir]
    
    def _scan_prompts(self) -> Dict[str, Dict[str, Any]]:
        """Scan directories for prompt files with comprehensive error handling"""
        prompts = {}
        total_files = 0
        
        for directory in self.prompt_directories:
            if not directory.exists():
                logger.warning(f"Directory does not exist: {directory}")
                continue
                
            try:
                # Check directory permissions
                if not os.access(directory, os.R_OK):
                    logger.error(f"No read permission for directory: {directory}")
                    continue
                
                for md_file in directory.glob('*.md'):
                    total_files += 1
                    try:
                        # Check file permissions and size
                        if not os.access(md_file, os.R_OK):
                            logger.warning(f"No read permission for file: {md_file}")
                            continue
                        
                        file_size = md_file.stat().st_size
                        if file_size > 1024 * 1024:  # 1MB limit
                            logger.warning(f"File too large (>{file_size} bytes): {md_file}")
                            continue
                        
                        if file_size == 0:
                            logger.warning(f"Empty file: {md_file}")
                            continue
                        
                        # Read file with proper encoding handling
                        try:
                            with open(md_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                        except UnicodeDecodeError:
                            # Try with different encoding
                            with open(md_file, 'r', encoding='latin-1') as f:
                                content = f.read()
                            logger.warning(f"File read with latin-1 encoding: {md_file}")
                        
                        if not content.strip():
                            logger.warning(f"File has no content: {md_file}")
                            continue
                        
                        # Extract title from first line or filename
                        lines = content.strip().split('\n')
                        title = lines[0].lstrip('#').strip() if lines and lines[0].startswith('#') else md_file.stem
                        
                        # Find variables in content (e.g., {variable})
                        try:
                            variables = list(set(re.findall(r'\{([^}]+)\}', content)))
                        except re.error as e:
                            logger.error(f"Regex error in file {md_file}: {e}")
                            variables = []
                        
                        # Create prompt info
                        prompt_name = md_file.stem
                        
                        # Handle duplicate prompt names
                        if prompt_name in prompts:
                            logger.warning(f"Duplicate prompt name '{prompt_name}' found in {md_file}, skipping")
                            continue
                        
                        prompts[prompt_name] = {
                            'name': prompt_name,
                            'description': title[:200],  # Limit description length
                            'content': content,
                            'file_path': str(md_file),
                            'variables': variables,
                            'arguments': [
                                {
                                    'name': var,
                                    'description': f'Value for {var}',
                                    'required': True
                                }
                                for var in variables if var.isalnum() or '_' in var  # Basic validation
                            ]
                        }
                        
                    except PermissionError:
                        logger.error(f"Permission denied reading file: {md_file}")
                    except OSError as e:
                        logger.error(f"OS error reading file {md_file}: {e}")
                    except Exception as e:
                        logger.error(f"Unexpected error reading {md_file}: {e}")
                        
            except PermissionError:
                logger.error(f"Permission denied accessing directory: {directory}")
            except OSError as e:
                logger.error(f"OS error scanning directory {directory}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error scanning directory {directory}: {e}")
        
        logger.info(f"Successfully processed {len(prompts)} prompts from {total_files} files")
        return prompts
    
    def _get_prompts(self) -> Dict[str, Dict[str, Any]]:
        """Get prompts with caching"""
        current_time = time.time()
        
        # Check if cache is still valid
        if (current_time - self.cache_timestamp) < self.cache_ttl and self.prompts_cache:
            return self.prompts_cache
        
        # Refresh cache
        self.prompts_cache = self._scan_prompts()
        self.cache_timestamp = current_time
        
        logger.info(f"Scanned {len(self.prompts_cache)} prompt files from {len(self.prompt_directories)} directories")
        
        return self.prompts_cache
    
    def _substitute_variables(self, content: str, arguments: Dict[str, Any]) -> str:
        """Substitute variables in prompt content"""
        result = content
        
        for key, value in arguments.items():
            placeholder = f'{{{key}}}'
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        
        return result
    
    async def handle_initialize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "prompts": {
                        "listChanged": True
                    }
                },
                "serverInfo": {
                    "name": self.name,
                    "version": self.version
                }
            }
        }
    
    async def handle_prompts_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list request"""
        logger.info("Handling prompts/list request")
        
        try:
            prompts = self._get_prompts()
            
            prompt_list = []
            for prompt_name, prompt_info in prompts.items():
                prompt_list.append({
                    "name": prompt_name,
                    "description": prompt_info["description"],
                    "arguments": prompt_info["arguments"]
                })
            
            logger.info(f"Returning {len(prompt_list)} prompts")
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "prompts": prompt_list
                }
            }
            
        except Exception as e:
            logger.error(f"Error in prompts/list: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def handle_prompts_get(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get request"""
        logger.info("Handling prompts/get request")
        
        try:
            params = request.get("params", {})
            prompt_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not prompt_name:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32602,
                        "message": "Missing required parameter: name"
                    }
                }
            
            prompts = self._get_prompts()
            
            if prompt_name not in prompts:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32602,
                        "message": f"Prompt not found: {prompt_name}"
                    }
                }
            
            prompt_info = prompts[prompt_name]
            content = self._substitute_variables(prompt_info["content"], arguments)
            
            logger.info(f"Retrieved and processed prompt '{prompt_name}'")
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "description": f"Prompt: {prompt_name}",
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": content
                            }
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in prompts/get: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def handle_tools_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tools/list request - return error to trigger Amazon Q CLI fallback mode"""
        logger.info("Handling tools/list request - returning error to trigger fallback")
        
        # Amazon Q CLI works better when server is marked as "failed"
        # Return an error for tools/list to trigger the working fallback mode
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32601,
                "message": "Method not implemented"
            }
        }
    
    async def handle_resources_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP resources/list request"""
        logger.info("Handling resources/list request")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "resources": []  # We don't provide any resources
            }
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method")
        
        if method == "initialize":
            return await self.handle_initialize(request)
        elif method == "prompts/list":
            return await self.handle_prompts_list(request)
        elif method == "prompts/get":
            return await self.handle_prompts_get(request)
        elif method == "tools/list":
            return await self.handle_tools_list(request)
        elif method == "resources/list":
            return await self.handle_resources_list(request)
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    def run_sync(self):
        """Run the MCP server synchronously"""
        logger.info(f"Starting {self.name} v{self.version}")
        
        # Set up signal handlers for graceful shutdown
        import signal
        shutdown_requested = False
        
        def signal_handler(signum, frame):
            nonlocal shutdown_requested
            logger.info(f"Received signal {signum}, initiating graceful shutdown")
            shutdown_requested = True
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            # Make stdin non-blocking to handle client connection timing
            import select
            
            while not shutdown_requested:
                try:
                    # Check if data is available on stdin with a timeout
                    ready, _, _ = select.select([sys.stdin], [], [], 1.0)
                    
                    if not ready:
                        # No data available, continue waiting
                        continue
                    
                    # Read JSON-RPC request from stdin
                    line = sys.stdin.readline()
                    
                    # Check for EOF or empty line
                    if not line:
                        logger.info("Received EOF, shutting down")
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        request = json.loads(line)
                        
                        # Handle request synchronously by running async handler
                        response = asyncio.run(self.handle_request(request))
                        
                        # Write response to stdout with explicit newline and flush
                        response_json = json.dumps(response, separators=(',', ':'))
                        sys.stdout.write(response_json + '\n')
                        sys.stdout.flush()
                        
                        # For debugging: log the request/response
                        logger.info(f"Sent response for {request.get('method', 'unknown')} (id: {request.get('id')})")
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON received: {e}")
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {
                                "code": -32700,
                                "message": "Parse error"
                            }
                        }
                        error_json = json.dumps(error_response, separators=(',', ':'))
                        sys.stdout.write(error_json + '\n')
                        sys.stdout.flush()
                        
                except EOFError:
                    logger.info("Received EOFError, shutting down")
                    break
                except KeyboardInterrupt:
                    logger.info("Received KeyboardInterrupt, shutting down")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    # Don't break on individual errors, keep server running
                    continue
                
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            logger.info("Enhanced Prompt MCP Server stopped")

    async def run(self):
        """Run the MCP server"""
        logger.info(f"Starting {self.name} v{self.version}")
        
        try:
            while True:
                # Read JSON-RPC request from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    response = await self.handle_request(request)
                    
                    # Write response to stdout with explicit formatting
                    response_json = json.dumps(response, separators=(',', ':'))
                    sys.stdout.write(response_json + '\n')
                    sys.stdout.flush()
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    error_json = json.dumps(error_response, separators=(',', ':'))
                    sys.stdout.write(error_json + '\n')
                    sys.stdout.flush()
                
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            logger.info("Enhanced Prompt MCP Server stopped")

async def main():
    """Main entry point for uvx and direct execution"""
    server = PromptMCPServer()
    await server.run()

def main_sync():
    """Synchronous entry point for uvx and MCP clients"""
    server = PromptMCPServer()
    server.run_sync()

if __name__ == "__main__":
    # Use synchronous version for better MCP client compatibility
    main_sync()
