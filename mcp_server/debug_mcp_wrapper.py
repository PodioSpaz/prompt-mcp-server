#!/usr/bin/env python3
import sys
import subprocess
import json
import time
import select
import threading

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

# Track if we've seen the initialized notification
initialized_received = False

def stdin_reader():
    """Read from Amazon Q CLI and forward to server"""
    global initialized_received
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                log_message("EOF", "Amazon Q CLI closed stdin")
                if initialized_received:
                    log_message("INFO", "Keeping connection alive for background tasks...")
                    # Don't close server stdin yet, wait for potential background requests
                    time.sleep(5)  # Give background tasks time to start
                    log_message("INFO", "Closing server stdin after delay")
                process.stdin.close()
                break
                
            log_message("IN ", line.strip())
            
            # Track initialized notification
            try:
                req = json.loads(line.strip())
                if req.get('method') == 'notifications/initialized':
                    initialized_received = True
                    log_message("INFO", "Initialized notification received - watching for background tasks")
            except:
                pass
            
            # Forward to actual server
            process.stdin.write(line)
            process.stdin.flush()
    except Exception as e:
        log_message("ERR", f"stdin_reader error: {e}")

def stdout_reader():
    """Read from server and forward to Amazon Q CLI"""
    try:
        while True:
            response = process.stdout.readline()
            if not response:
                log_message("EOF", "Server closed stdout")
                break
                
            log_message("OUT", response.strip())
            
            # Forward to Amazon Q CLI
            sys.stdout.write(response)
            sys.stdout.flush()
    except Exception as e:
        log_message("ERR", f"stdout_reader error: {e}")

def stderr_reader():
    """Read server stderr and log it"""
    try:
        while True:
            stderr_line = process.stderr.readline()
            if not stderr_line:
                break
            log_message("ERR", stderr_line.strip())
    except Exception as e:
        log_message("ERR", f"stderr_reader error: {e}")

# Start reader threads
stdin_thread = threading.Thread(target=stdin_reader, daemon=True)
stdout_thread = threading.Thread(target=stdout_reader, daemon=True)
stderr_thread = threading.Thread(target=stderr_reader, daemon=True)

stdin_thread.start()
stdout_thread.start()
stderr_thread.start()

try:
    # Wait for the process to complete
    process.wait()
    log_message("END", f"Server process ended with code {process.returncode}")
except KeyboardInterrupt:
    log_message("INT", "Interrupted by user")
    process.terminate()
    process.wait()
except Exception as e:
    log_message("EXC", f"Exception: {e}")
finally:
    log_message("END", "Debug wrapper ended")
