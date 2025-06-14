#!/usr/bin/env python3
"""
Debug version of the MCP server that logs all I/O for troubleshooting.
"""

import sys
import json
import logging
import asyncio
from mcp_server.prompt_mcp_server import PromptMCPServer

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mcp_debug.log'),
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)

class DebugPromptMCPServer(PromptMCPServer):
    """Debug version with extensive logging"""
    
    def run_sync(self):
        """Run the MCP server synchronously with debug logging"""
        logger.info(f"🚀 DEBUG: Starting {self.name} v{self.version}")
        logger.info(f"🚀 DEBUG: Python version: {sys.version}")
        logger.info(f"🚀 DEBUG: Working directory: {sys.path[0]}")
        logger.info(f"🚀 DEBUG: Stdin isatty: {sys.stdin.isatty()}")
        logger.info(f"🚀 DEBUG: Stdout isatty: {sys.stdout.isatty()}")
        
        request_count = 0
        
        try:
            logger.info("🚀 DEBUG: Entering main loop, waiting for requests...")
            
            while True:
                try:
                    logger.debug("🔍 DEBUG: Waiting for input on stdin...")
                    
                    # Read JSON-RPC request from stdin
                    line = sys.stdin.readline()
                    
                    logger.debug(f"📥 DEBUG: Received line: {repr(line)}")
                    
                    # Check for EOF
                    if not line:
                        logger.info("🔚 DEBUG: Received EOF, shutting down")
                        break
                    
                    line = line.strip()
                    if not line:
                        logger.debug("🔍 DEBUG: Empty line, continuing...")
                        continue
                    
                    request_count += 1
                    logger.info(f"📨 DEBUG: Processing request #{request_count}: {line}")
                    
                    try:
                        request = json.loads(line)
                        logger.info(f"✅ DEBUG: Parsed JSON request: {request}")
                        
                        # Handle request synchronously by running async handler
                        logger.debug("🔄 DEBUG: Calling handle_request...")
                        response = asyncio.run(self.handle_request(request))
                        logger.info(f"📤 DEBUG: Generated response: {response}")
                        
                        # Write response to stdout
                        response_json = json.dumps(response)
                        logger.info(f"📤 DEBUG: Sending response: {response_json}")
                        print(response_json, flush=True)
                        logger.debug("✅ DEBUG: Response sent and flushed")
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ DEBUG: Invalid JSON received: {e}")
                        logger.error(f"❌ DEBUG: Raw input was: {repr(line)}")
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {
                                "code": -32700,
                                "message": "Parse error"
                            }
                        }
                        error_json = json.dumps(error_response)
                        logger.info(f"📤 DEBUG: Sending error response: {error_json}")
                        print(error_json, flush=True)
                        
                except EOFError:
                    logger.info("🔚 DEBUG: Received EOFError, shutting down")
                    break
                except Exception as e:
                    logger.error(f"❌ DEBUG: Error in main loop: {e}")
                    logger.exception("❌ DEBUG: Full exception details:")
                    # Continue running despite errors
                    continue
                
        except KeyboardInterrupt:
            logger.info("⏹️ DEBUG: Server interrupted by user")
        except Exception as e:
            logger.error(f"❌ DEBUG: Server error: {e}")
            logger.exception("❌ DEBUG: Full exception details:")
        finally:
            logger.info(f"🔚 DEBUG: Enhanced Prompt MCP Server stopped after {request_count} requests")

def main():
    """Main entry point for debug server"""
    logger.info("🚀 DEBUG: Starting debug MCP server")
    server = DebugPromptMCPServer()
    server.run_sync()

if __name__ == "__main__":
    main()
