#!/usr/bin/env python3
import sys
import subprocess
import json
import time

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

try:
    while True:
        # Read from stdin (Amazon Q CLI -> us)
        line = sys.stdin.readline()
        if not line:
            break
            
        log_message("IN ", line.strip())
        
        # Forward to actual server
        process.stdin.write(line)
        process.stdin.flush()
        
        # Read response from server
        response = process.stdout.readline()
        if response:
            log_message("OUT", response.strip())
            
            # Forward to Amazon Q CLI
            sys.stdout.write(response)
            sys.stdout.flush()
        
        # Check for any stderr output
        import select
        ready, _, _ = select.select([process.stderr], [], [], 0.1)
        if ready:
            stderr_line = process.stderr.readline()
            if stderr_line:
                log_message("ERR", stderr_line.strip())

except KeyboardInterrupt:
    pass
finally:
    process.terminate()
    process.wait()
