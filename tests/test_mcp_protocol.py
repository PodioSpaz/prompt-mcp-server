#!/usr/bin/env python3
"""
Test script to verify MCP protocol compliance.
Tests all the methods that Amazon Q CLI expects during initialization.
"""

import subprocess
import json
import sys

def test_mcp_method(method, params=None):
    """Test a specific MCP method"""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method
    }
    if params:
        request["params"] = params
    
    cmd = ["python3", "mcp_server/prompt_mcp_server.py"]
    
    try:
        process = subprocess.run(
            cmd,
            input=json.dumps(request) + "\n",
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if process.returncode == 0 and process.stdout:
            response = json.loads(process.stdout.strip())
            return True, response
        else:
            return False, f"Process failed: {process.stderr}"
            
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Test all MCP protocol methods"""
    print("🧪 MCP Protocol Compliance Test")
    print("=" * 50)
    
    methods_to_test = [
        ("initialize", None),
        ("tools/list", None),
        ("resources/list", None),
        ("prompts/list", None),
        ("prompts/get", {"name": "debug_code", "arguments": {"language": "Python", "code": "test"}})
    ]
    
    all_passed = True
    
    for method, params in methods_to_test:
        print(f"\n🔍 Testing {method}...")
        success, result = test_mcp_method(method, params)
        
        if success:
            print(f"✅ {method}: SUCCESS")
            
            # Show specific results for key methods
            if method == "initialize":
                capabilities = result.get("result", {}).get("capabilities", {})
                print(f"   Capabilities: {list(capabilities.keys())}")
            elif method == "tools/list":
                tools = result.get("result", {}).get("tools", [])
                print(f"   Tools count: {len(tools)}")
            elif method == "resources/list":
                resources = result.get("result", {}).get("resources", [])
                print(f"   Resources count: {len(resources)}")
            elif method == "prompts/list":
                prompts = result.get("result", {}).get("prompts", [])
                print(f"   Prompts count: {len(prompts)}")
            elif method == "prompts/get":
                messages = result.get("result", {}).get("messages", [])
                print(f"   Messages count: {len(messages)}")
        else:
            print(f"❌ {method}: FAILED - {result}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All MCP protocol methods working correctly!")
        print("✅ Server should be compatible with Amazon Q CLI")
        return 0
    else:
        print("❌ Some MCP protocol methods failed")
        print("⚠️  Server may not work properly with Amazon Q CLI")
        return 1

if __name__ == "__main__":
    sys.exit(main())
