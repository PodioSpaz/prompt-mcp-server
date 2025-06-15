#!/usr/bin/env python3
"""
Production MCP Wrapper for Amazon Q CLI Compatibility

This wrapper solves the timing issue where Amazon Q CLI closes stdin after 
notifications/initialized, but background tasks need time to send their requests.

The wrapper keeps the server connection alive for background tasks by:
1. Monitoring Amazon Q CLI's stdin closure
2. Waiting for background tasks to execute (5 second window)
3. Properly forwarding all requests and responses
4. Ensuring clean shutdown after background tasks complete
"""
import sys
import subprocess
import json
import time
import threading
import logging
import os

# Configure minimal logging for production
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

def main():
    """Main wrapper function"""
    # Start the actual MCP server
    process = subprocess.Popen(
        [sys.executable, '-m', 'mcp_server.prompt_mcp_server'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    # Track initialization state for Amazon Q CLI compatibility
    initialized_received = False
    
    def stdin_reader():
        """Read from Amazon Q CLI and forward to server"""
        nonlocal initialized_received
        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    # Amazon Q CLI closed stdin
                    if initialized_received:
                        # Give background tasks time to execute
                        time.sleep(5)
                    process.stdin.close()
                    break
                    
                # Track initialized notification for timing
                try:
                    req = json.loads(line.strip())
                    if req.get('method') == 'notifications/initialized':
                        initialized_received = True
                except:
                    pass
                
                # Forward to server
                process.stdin.write(line)
                process.stdin.flush()
        except Exception as e:
            logger.error(f"stdin_reader error: {e}")
    
    def stdout_reader():
        """Read from server and forward to Amazon Q CLI"""
        try:
            while True:
                response = process.stdout.readline()
                if not response:
                    break
                    
                # Forward to Amazon Q CLI
                sys.stdout.write(response)
                sys.stdout.flush()
        except Exception as e:
            logger.error(f"stdout_reader error: {e}")
    
    def stderr_reader():
        """Read server stderr and forward to stderr + optional log file"""
        try:
            # Check if debug logging is enabled
            enable_debug_logging = os.environ.get('MCP_DEBUG_LOGGING', '').lower() in ('1', 'true', 'yes', 'on')
            log_file_path = os.environ.get('MCP_LOG_FILE', '/tmp/mcp_server_debug.log')
            
            if enable_debug_logging:
                # Create log file for easier monitoring when debug logging is enabled
                with open(log_file_path, "w") as log_file:
                    log_file.write(f"=== MCP Server Debug Log Started ===\n")
                    log_file.write(f"Log file: {log_file_path}\n")
                    log_file.flush()
                    
                    while True:
                        stderr_line = process.stderr.readline()
                        if not stderr_line:
                            break
                        
                        # Write to both stderr and log file
                        sys.stderr.write(stderr_line)
                        sys.stderr.flush()
                        
                        log_file.write(stderr_line)
                        log_file.flush()
            else:
                # Normal operation - only forward to stderr
                while True:
                    stderr_line = process.stderr.readline()
                    if not stderr_line:
                        break
                    # Forward server errors to stderr
                    sys.stderr.write(stderr_line)
                    sys.stderr.flush()
        except Exception as e:
            logger.error(f"stderr_reader error: {e}")
    
    # Start reader threads
    stdin_thread = threading.Thread(target=stdin_reader, daemon=True)
    stdout_thread = threading.Thread(target=stdout_reader, daemon=True)
    stderr_thread = threading.Thread(target=stderr_reader, daemon=True)
    
    stdin_thread.start()
    stdout_thread.start()
    stderr_thread.start()
    
    try:
        # Wait for the server process to complete
        exit_code = process.wait()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        process.terminate()
        process.wait()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Wrapper error: {e}")
        process.terminate()
        process.wait()
        sys.exit(1)

if __name__ == "__main__":
    main()
