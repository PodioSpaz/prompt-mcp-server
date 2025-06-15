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
    
    MCP_LOG_LEVEL - Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                    Default: WARNING
    
    MCP_DEBUG_LOGGING - Enable comprehensive debug logging (1, true, yes, on)
                        Default: disabled
                        When enabled:
                        - Forces INFO level logging
                        - Creates debug log file for monitoring
                        - Logs all MCP requests/responses
                        - Logs file monitoring activity
    
    MCP_LOG_FILE - Set custom log file path when debug logging is enabled
                   Default: /tmp/mcp_server_debug.log
                   Example: /path/to/custom/mcp_debug.log

Version: 2.0.9
Author: Amazon Q Developer CLI Team
"""

import asyncio
import json
import os
import sys
import re
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
import logging

# Configure logging based on environment variables
log_level = os.environ.get('MCP_LOG_LEVEL', 'WARNING').upper()
enable_debug_logging = os.environ.get('MCP_DEBUG_LOGGING', '').lower() in ('1', 'true', 'yes', 'on')

# Set log level - default to WARNING (production), can be overridden
if enable_debug_logging:
    log_level = 'INFO'  # Force INFO level when debug logging is enabled

# Map string levels to logging constants
level_map = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

actual_level = level_map.get(log_level, logging.WARNING)

logging.basicConfig(
    level=actual_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

class PromptMCPServer:
    """Single-file MCP server for prompt management"""
    
    def __init__(self):
        self.version = "2.0.9"
        self.name = "prompt-mcp-server"
        self.prompt_directories = self._get_prompt_directories()
        self.prompts_cache = {}
        self.cache_timestamp = 0
        self.cache_ttl = 300  # 5 minutes
        
        # File monitoring
        self.file_monitor_thread = None
        self.file_monitor_stop_event = threading.Event()
        self.directory_snapshots = {}  # Track file modification times
        
        logger.info(f"Initialized {self.name} v{self.version}")
        logger.info(f"Monitoring {len(self.prompt_directories)} directories for prompts:")
        for directory in self.prompt_directories:
            logger.info(f"  - {directory}")
        
        # Start file monitoring
        self._start_file_monitoring()
    
    def _start_file_monitoring(self):
        """Start background thread to monitor file changes"""
        if self.file_monitor_thread is None or not self.file_monitor_thread.is_alive():
            self.file_monitor_thread = threading.Thread(
                target=self._file_monitor_worker,
                daemon=True,
                name="FileMonitor"
            )
            self.file_monitor_thread.start()
            logger.info("Started file monitoring thread")
    
    def _stop_file_monitoring(self):
        """Stop the file monitoring thread"""
        if self.file_monitor_thread and self.file_monitor_thread.is_alive():
            self.file_monitor_stop_event.set()
            self.file_monitor_thread.join(timeout=2.0)
            logger.info("Stopped file monitoring thread")
    
    def _get_directory_snapshot(self, directory: Path) -> Dict[str, float]:
        """Get snapshot of all .md files in directory with their modification times"""
        snapshot = {}
        try:
            if directory.exists() and directory.is_dir():
                for file_path in directory.glob("*.md"):
                    try:
                        snapshot[str(file_path)] = file_path.stat().st_mtime
                    except (OSError, IOError):
                        # File might have been deleted between glob and stat
                        pass
        except (OSError, IOError):
            # Directory might not be accessible
            pass
        return snapshot
    
    def _file_monitor_worker(self):
        """Background worker that monitors file changes"""
        # Initial snapshot
        for directory in self.prompt_directories:
            self.directory_snapshots[str(directory)] = self._get_directory_snapshot(directory)
        
        logger.info("File monitoring started - checking every 2 seconds")
        
        while not self.file_monitor_stop_event.is_set():
            try:
                # Check each directory for changes
                changes_detected = False
                
                for directory in self.prompt_directories:
                    dir_str = str(directory)
                    current_snapshot = self._get_directory_snapshot(directory)
                    previous_snapshot = self.directory_snapshots.get(dir_str, {})
                    
                    # Check for changes
                    if current_snapshot != previous_snapshot:
                        changes_detected = True
                        
                        # Log specific changes
                        added_files = set(current_snapshot.keys()) - set(previous_snapshot.keys())
                        removed_files = set(previous_snapshot.keys()) - set(current_snapshot.keys())
                        modified_files = set()
                        
                        for file_path in set(current_snapshot.keys()) & set(previous_snapshot.keys()):
                            if current_snapshot[file_path] != previous_snapshot[file_path]:
                                modified_files.add(file_path)
                        
                        if added_files:
                            logger.info(f"Detected new prompt files: {[Path(f).name for f in added_files]}")
                        if removed_files:
                            logger.info(f"Detected removed prompt files: {[Path(f).name for f in removed_files]}")
                        if modified_files:
                            logger.info(f"Detected modified prompt files: {[Path(f).name for f in modified_files]}")
                        
                        # Update snapshot
                        self.directory_snapshots[dir_str] = current_snapshot
                
                # Clear cache if changes detected
                if changes_detected:
                    logger.info("File changes detected - clearing prompts cache")
                    self.prompts_cache.clear()
                    self.cache_timestamp = 0
                    
                    # SEND NOTIFICATION TO AMAZON Q CLI
                    self._send_prompts_list_changed_notification()
                
                # Wait before next check
                self.file_monitor_stop_event.wait(2.0)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in file monitoring: {e}")
                self.file_monitor_stop_event.wait(5.0)  # Wait longer on error
    
    def _send_prompts_list_changed_notification(self):
        """Send notification to Amazon Q CLI that prompts have changed"""
        try:
            notification = {
                "jsonrpc": "2.0",
                "method": "notifications/prompts/list_changed",
                "params": {}
            }
            
            notification_json = json.dumps(notification, separators=(',', ':'))
            sys.stdout.write(notification_json + '\n')
            sys.stdout.flush()
            
            logger.info(f"📢 SENT NOTIFICATION: prompts/list_changed")
            logger.info(f"📢 NOTIFICATION DETAILS: {notification_json}")
            
        except Exception as e:
            logger.error(f"Error sending prompts list changed notification: {e}")
    
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
        cache_age = current_time - self.cache_timestamp
        
        logger.info(f"=== _GET_PROMPTS CALLED ===")
        logger.info(f"Current time: {current_time}")
        logger.info(f"Cache timestamp: {self.cache_timestamp}")
        logger.info(f"Cache age: {cache_age:.1f}s")
        logger.info(f"Cache TTL: {self.cache_ttl}s")
        logger.info(f"Cache has data: {bool(self.prompts_cache)}")
        logger.info(f"Cache valid: {cache_age < self.cache_ttl and bool(self.prompts_cache)}")
        
        # Check if cache is still valid
        if cache_age < self.cache_ttl and self.prompts_cache:
            logger.info(f"USING CACHED DATA - {len(self.prompts_cache)} prompts")
            logger.info(f"Cached prompt names: {list(self.prompts_cache.keys())}")
            return self.prompts_cache
        
        # Refresh cache
        logger.info("CACHE EXPIRED OR EMPTY - RESCANNING FILES")
        self.prompts_cache = self._scan_prompts()
        self.cache_timestamp = current_time
        logger.info(f"CACHE REFRESHED - {len(self.prompts_cache)} prompts")
        logger.info(f"New prompt names: {list(self.prompts_cache.keys())}")
        
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
                    },
                    "tools": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": self.name,
                    "version": self.version
                }
            }
        }
    
    async def handle_prompts_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list request"""
        logger.info("=== HANDLING PROMPTS/LIST REQUEST ===")
        logger.info(f"Request ID: {request.get('id', 'no-id')}")
        logger.info(f"Cache timestamp: {self.cache_timestamp}")
        logger.info(f"Current time: {time.time()}")
        logger.info(f"Cache age: {time.time() - self.cache_timestamp:.1f}s")
        logger.info(f"Cache TTL: {self.cache_ttl}s")
        logger.info(f"Cache valid: {time.time() - self.cache_timestamp < self.cache_ttl}")
        
        try:
            prompts = self._get_prompts()
            logger.info(f"Retrieved {len(prompts)} prompts from _get_prompts()")
            
            prompt_list = []
            for prompt_name, prompt_info in prompts.items():
                prompt_list.append({
                    "name": prompt_name,
                    "description": prompt_info["description"],
                    "arguments": prompt_info["arguments"]
                })
            
            logger.info(f"Built prompt list with {len(prompt_list)} items")
            logger.info(f"Prompt names: {[p['name'] for p in prompt_list]}")
            logger.info(f"Returning {len(prompt_list)} prompts")
            
            response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "prompts": prompt_list
                }
            }
            
            logger.info(f"=== PROMPTS/LIST RESPONSE READY ===")
            return response
            
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
        """Handle MCP tools/list request - return empty result quickly"""
        logger.info("Handling tools/list request - returning empty result")
        
        # Return empty tools quickly to complete initialization
        # but don't advertise tools capability to avoid confusion
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": []
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
        request_id = request.get("id", "no-id")
        
        # LOG ALL INCOMING REQUESTS
        logger.info(f"🔵 INCOMING REQUEST: method='{method}', id={request_id}")
        logger.info(f"🔵 REQUEST DETAILS: {json.dumps(request, separators=(',', ':'))}")
        
        response = None
        
        if method == "initialize":
            response = await self.handle_initialize(request)
        elif method == "initialized" or method == "notifications/initialized":
            # Notification that initialization is complete - no response needed
            logger.info("Received initialized notification")
            response = None
        elif method == "prompts/list":
            response = await self.handle_prompts_list(request)
        elif method == "prompts/get":
            response = await self.handle_prompts_get(request)
        elif method == "tools/list":
            response = await self.handle_tools_list(request)
        elif method == "resources/list":
            response = await self.handle_resources_list(request)
        else:
            logger.warning(f"Unknown method: {method}")
            response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        # LOG ALL OUTGOING RESPONSES
        if response is not None:
            logger.info(f"🟢 OUTGOING RESPONSE: method='{method}', id={request_id}")
            logger.info(f"🟢 RESPONSE DETAILS: {json.dumps(response, separators=(',', ':'))}")
        else:
            logger.info(f"🟡 NO RESPONSE: method='{method}' (notification)")
        
        return response
    
    def run_sync(self):
        """Run the MCP server synchronously - simplified for wrapper compatibility"""
        logger.info(f"Starting {self.name} v{self.version}")
        
        try:
            while True:
                try:
                    # Simple blocking read - wrapper handles timing
                    line = sys.stdin.readline()
                    
                    if not line:
                        # EOF - normal shutdown
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        request = json.loads(line)
                        
                        # LOG RAW REQUEST RECEIVED
                        logger.info(f"📥 RAW REQUEST RECEIVED: {line}")
                        
                        # Handle request
                        response = asyncio.run(self.handle_request(request))
                        
                        # Send response
                        if response is not None:
                            response_json = json.dumps(response, separators=(',', ':'))
                            sys.stdout.write(response_json + '\n')
                            sys.stdout.flush()
                            logger.info(f"📤 RAW RESPONSE SENT: {response_json}")
                        else:
                            logger.info(f"📤 NO RESPONSE SENT (notification)")
                        
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
                    break
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    continue
                
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            # Stop file monitoring
            self._stop_file_monitoring()
            logger.info(f"{self.name} stopped")

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
                    
                    # Write response to stdout (only if response is not None)
                    if response is not None:
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
            # Stop file monitoring
            self._stop_file_monitoring()
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
