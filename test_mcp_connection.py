#!/usr/bin/env python3
"""
Test script to verify MCP server connection and functionality.
This simulates how the Amazon Q CLI would interact with the MCP server.
"""

import subprocess
import json
import time
import sys

def test_mcp_server():
    """Test the MCP server with a sequence of requests"""
    print("🧪 Testing MCP Server Connection...")
    print("=" * 50)
    
    # Start the server process
    cmd = ["python3", "mcp_server/prompt_mcp_server.py"]
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
        # Test 1: Initialize
        print("\n1️⃣ Testing initialize...")
        init_request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize"
        }) + "\n"
        
        process.stdin.write(init_request)
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        if response:
            init_response = json.loads(response.strip())
            print(f"✅ Initialize successful: {init_response['result']['serverInfo']['name']} v{init_response['result']['serverInfo']['version']}")
        else:
            print("❌ No response to initialize")
            return False
        
        # Test 2: List prompts
        print("\n2️⃣ Testing prompts/list...")
        list_request = json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "prompts/list"
        }) + "\n"
        
        process.stdin.write(list_request)
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        if response:
            list_response = json.loads(response.strip())
            prompt_count = len(list_response['result']['prompts'])
            print(f"✅ List prompts successful: Found {prompt_count} prompts")
            
            # Show first few prompts
            for i, prompt in enumerate(list_response['result']['prompts'][:3]):
                print(f"   - {prompt['name']}: {prompt['description']}")
        else:
            print("❌ No response to prompts/list")
            return False
        
        # Test 3: Get a specific prompt
        print("\n3️⃣ Testing prompts/get...")
        get_request = json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "prompts/get",
            "params": {
                "name": "debug_code",
                "arguments": {
                    "language": "Python",
                    "code": "print('Hello, World!')"
                }
            }
        }) + "\n"
        
        process.stdin.write(get_request)
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        if response:
            get_response = json.loads(response.strip())
            print(f"✅ Get prompt successful: Retrieved '{get_response['result']['description']}'")
            content_length = len(get_response['result']['messages'][0]['content']['text'])
            print(f"   Content length: {content_length} characters")
        else:
            print("❌ No response to prompts/get")
            return False
        
        print("\n🎉 All tests passed! MCP server is working correctly.")
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

def test_uvx_package():
    """Test the UVX package version"""
    print("\n🧪 Testing UVX Package...")
    print("=" * 50)
    
    cmd = ["uvx", "--from", "./dist/prompt_mcp_server-2.0.1-py3-none-any.whl", "prompt-mcp-server"]
    print(f"Starting UVX server: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    try:
        # Test initialize
        init_request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize"
        }) + "\n"
        
        process.stdin.write(init_request)
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        if response:
            init_response = json.loads(response.strip())
            print(f"✅ UVX package test successful: {init_response['result']['serverInfo']['name']} v{init_response['result']['serverInfo']['version']}")
            return True
        else:
            print("❌ No response from UVX package")
            return False
            
    except Exception as e:
        print(f"❌ UVX test failed with error: {e}")
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
    print("🚀 MCP Server Connection Test")
    print("=" * 50)
    
    # Test direct Python execution
    success1 = test_mcp_server()
    
    # Test UVX package
    success2 = test_uvx_package()
    
    print("\n📋 Test Summary:")
    print("=" * 50)
    print(f"Direct Python execution: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"UVX package execution:   {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! The MCP server should work with Amazon Q CLI.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the server implementation.")
        sys.exit(1)
