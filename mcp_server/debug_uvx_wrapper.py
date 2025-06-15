#!/usr/bin/env python3
"""
Debug wrapper to understand what happens when Amazon Q CLI calls the server through uvx
"""
import sys
import subprocess
import json
import time
import os

def log_message(msg):
    timestamp = time.strftime('%H:%M:%S.%f')[:-3]
    with open('/tmp/uvx_debug.log', 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")
        f.flush()

log_message("=== UVX DEBUG WRAPPER STARTED ===")
log_message(f"Python executable: {sys.executable}")
log_message(f"Working directory: {os.getcwd()}")
log_message(f"Command line args: {sys.argv}")
log_message(f"Environment PATH: {os.environ.get('PATH', 'NOT SET')}")

# Try to run the actual server
try:
    log_message("Starting uvx command...")
    
    # Run the actual uvx command
    process = subprocess.Popen(
        ['uvx', '--from', './dist/prompt_mcp_server-2.0.4-py3-none-any.whl', 'prompt-mcp-server'],
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    log_message(f"Process started with PID: {process.pid}")
    
    # Monitor stderr in a separate thread
    import threading
    
    def monitor_stderr():
        try:
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                log_message(f"STDERR: {line.strip()}")
        except Exception as e:
            log_message(f"Stderr monitoring error: {e}")
    
    stderr_thread = threading.Thread(target=monitor_stderr, daemon=True)
    stderr_thread.start()
    
    # Wait for the process to complete
    exit_code = process.wait()
    log_message(f"Process completed with exit code: {exit_code}")
    
    sys.exit(exit_code)
    
except Exception as e:
    log_message(f"Error running uvx command: {e}")
    sys.exit(1)
