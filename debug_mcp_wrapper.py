#!/usr/bin/env python3
import sys
import subprocess
import json
import time
import select

# Start the actual MCP server
process = subprocess.Popen(
    [sys.executable, 'mcp_server/prompt_mcp_server.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=0
)

def log_message(direction, data):
    timestamp = time.strftime('%H:%M:%S.%f')[:-3]
    with open('/tmp/mcp_debug.log', 'a') as f:
        f.write(f"[{timestamp}] {direction}: {repr(data)}\n")
        f.flush()

try:
    while True:
        # Check for input from Amazon Q CLI with timeout
        ready, _, _ = select.select([sys.stdin], [], [], 0.1)
        if ready:
            line = sys.stdin.readline()
            if not line:
                log_message("EOF", "Amazon Q CLI disconnected")
                break
                
            log_message("IN ", line.strip())
            
            # Forward to actual server
            process.stdin.write(line)
            process.stdin.flush()
        
        # Check for response from server with timeout
        ready, _, _ = select.select([process.stdout], [], [], 0.1)
        if ready:
            response = process.stdout.readline()
            if response:
                log_message("OUT", response.strip())
                
                # Forward to Amazon Q CLI
                sys.stdout.write(response)
                sys.stdout.flush()
        
        # Check for any stderr output
        ready, _, _ = select.select([process.stderr], [], [], 0.1)
        if ready:
            stderr_line = process.stderr.readline()
            if stderr_line:
                log_message("ERR", stderr_line.strip())
        
        # Check if server process is still alive
        if process.poll() is not None:
            log_message("SRV", f"Server process ended with code {process.returncode}")
            break

except KeyboardInterrupt:
    log_message("INT", "Interrupted by user")
except Exception as e:
    log_message("EXC", f"Exception: {e}")
finally:
    process.terminate()
    process.wait()
    log_message("END", "Debug wrapper ended")
