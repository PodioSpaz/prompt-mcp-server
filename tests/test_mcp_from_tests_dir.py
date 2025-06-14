#!/usr/bin/env python3
"""
Test script to verify MCP server works correctly from the tests directory.
This simulates how Amazon Q CLI would interact with the server when configured
to run from the tests/.amazonq/mcp.json configuration.
"""

import subprocess
import json
import sys
import os

def test_mcp_server_from_tests_dir():
    """Test the MCP server as configured in tests/.amazonq/mcp.json"""
    print("🧪 Testing MCP Server from tests/ directory")
    print("=" * 60)
    print("Configuration: tests/.amazonq/mcp.json")
    print("Command: python3 ../mcp_server/prompt_mcp_server.py")
    print("=" * 60)
    
    # Change to tests directory
    os.chdir(os.path.dirname(__file__))
    
    # Start the server process as configured
    cmd = ["python3", "../mcp_server/prompt_mcp_server.py"]
    print(f"Starting server: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    try:
        # Test sequence that Amazon Q CLI would perform
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "resources/list"},
            {"jsonrpc": "2.0", "id": 4, "method": "prompts/list"},
            {"jsonrpc": "2.0", "id": 5, "method": "prompts/get", "params": {
                "name": "debug_code", 
                "arguments": {"language": "Python", "code": "print('test')"}
            }}
        ]
        
        print(f"\n📨 Sending {len(requests)} requests...")
        
        # Send all requests
        for i, request in enumerate(requests, 1):
            request_json = json.dumps(request) + "\n"
            process.stdin.write(request_json)
            process.stdin.flush()
            
            # Read response
            response_line = process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                method = request["method"]
                
                print(f"\n{i}️⃣ {method}:")
                
                if "error" in response:
                    print(f"   ❌ ERROR: {response['error']['message']}")
                    return False
                else:
                    result = response.get("result", {})
                    
                    if method == "initialize":
                        server_info = result.get("serverInfo", {})
                        capabilities = result.get("capabilities", {})
                        print(f"   ✅ Server: {server_info.get('name')} v{server_info.get('version')}")
                        print(f"   ✅ Capabilities: {list(capabilities.keys())}")
                        
                    elif method == "tools/list":
                        tools = result.get("tools", [])
                        print(f"   ✅ Tools: {len(tools)} available")
                        
                    elif method == "resources/list":
                        resources = result.get("resources", [])
                        print(f"   ✅ Resources: {len(resources)} available")
                        
                    elif method == "prompts/list":
                        prompts = result.get("prompts", [])
                        print(f"   ✅ Prompts: {len(prompts)} available")
                        if prompts:
                            print(f"   📝 Sample prompts: {', '.join([p['name'] for p in prompts[:3]])}")
                            
                    elif method == "prompts/get":
                        messages = result.get("messages", [])
                        print(f"   ✅ Retrieved prompt with {len(messages)} message(s)")
                        if messages:
                            content_length = len(messages[0].get("content", {}).get("text", ""))
                            print(f"   📄 Content length: {content_length} characters")
            else:
                print(f"   ❌ No response to {request['method']}")
                return False
        
        print(f"\n🎉 All {len(requests)} requests completed successfully!")
        print("✅ MCP server is working correctly from tests/ directory")
        print("✅ Configuration in tests/.amazonq/mcp.json is valid")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        # Clean up
        try:
            process.stdin.close()
            process.terminate()
            process.wait(timeout=2)
        except:
            process.kill()
            process.wait()

if __name__ == "__main__":
    success = test_mcp_server_from_tests_dir()
    sys.exit(0 if success else 1)
