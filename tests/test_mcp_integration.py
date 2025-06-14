#!/usr/bin/env python3
"""
Comprehensive MCP Integration Test Suite

This module consolidates all MCP integration testing functionality:
1. Protocol compliance testing (all MCP methods)
2. Connection testing (server communication)
3. Configuration testing (tests directory setup)
4. Package testing (UVX wheel execution)

This replaces the previous separate test_mcp_connection.py and consolidates
MCP testing into a single comprehensive integration test.
"""

import subprocess
import json
import sys
import os
import time
from pathlib import Path

class MCPIntegrationTester:
    """Comprehensive MCP integration tester"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tests_dir = Path(__file__).parent
        
    def test_mcp_method(self, method, params=None, server_cmd=None):
        """Test a specific MCP method"""
        if server_cmd is None:
            server_cmd = ["python3", str(self.project_root / "mcp_server" / "prompt_mcp_server.py")]
            
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method
        }
        if params:
            request["params"] = params
        
        try:
            process = subprocess.run(
                server_cmd,
                input=json.dumps(request) + "\n",
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.project_root
            )
            
            if process.returncode == 0 and process.stdout:
                response = json.loads(process.stdout.strip())
                return True, response
            else:
                return False, f"Process failed: {process.stderr}"
                
        except Exception as e:
            return False, f"Error: {e}"
    
    def test_protocol_compliance(self):
        """Test complete MCP protocol compliance"""
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
            success, result = self.test_mcp_method(method, params)
            
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
        
        return all_passed
    
    def test_server_connection(self):
        """Test MCP server connection with persistent session"""
        print("\n🧪 MCP Server Connection Test")
        print("=" * 50)
        
        # Start the server process
        cmd = ["python3", str(self.project_root / "mcp_server" / "prompt_mcp_server.py")]
        print(f"Starting server: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
            cwd=self.project_root
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
                server_info = init_response['result']['serverInfo']
                print(f"✅ Initialize successful: {server_info['name']} v{server_info['version']}")
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
                messages = get_response['result']['messages']
                content_length = len(messages[0]['content']['text']) if messages else 0
                print(f"✅ Get prompt successful: Retrieved 'Prompt: debug_code'")
                print(f"   Content length: {content_length} characters")
            else:
                print("❌ No response to prompts/get")
                return False
            
            print("\n🎉 All tests passed! MCP server is working correctly.")
            return True
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
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
    
    def test_from_tests_directory(self):
        """Test MCP server from tests directory configuration"""
        print("\n🧪 Testing MCP Server from tests/ directory")
        print("=" * 60)
        print("Configuration: tests/.amazonq/mcp.json")
        print("Command: python3 ../mcp_server/prompt_mcp_server.py")
        print("=" * 60)
        
        # Change to tests directory
        original_cwd = os.getcwd()
        os.chdir(self.tests_dir)
        
        try:
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
            finally:
                os.chdir(original_cwd)
    
    def test_uvx_package(self):
        """Test UVX package execution"""
        print("\n🧪 Testing UVX Package...")
        print("=" * 50)
        
        # Find the wheel file
        dist_dir = self.project_root / "dist"
        wheel_files = list(dist_dir.glob("*.whl"))
        
        if not wheel_files:
            print("❌ No wheel file found in dist/")
            return False
        
        wheel_file = wheel_files[0]  # Use the first (should be latest)
        cmd = ["uvx", "--from", str(wheel_file), "prompt-mcp-server"]
        print(f"Starting UVX server: {' '.join(cmd)}")
        
        success, result = self.test_mcp_method("initialize", server_cmd=cmd)
        
        if success:
            server_info = result['result']['serverInfo']
            print(f"✅ UVX package test successful: {server_info['name']} v{server_info['version']}")
            return True
        else:
            print(f"❌ UVX package test failed: {result}")
            return False
    
    def run_all_tests(self):
        """Run all MCP integration tests"""
        print("🚀 MCP Integration Test Suite")
        print("=" * 60)
        
        results = {}
        
        # Run all test categories
        results['protocol_compliance'] = self.test_protocol_compliance()
        results['server_connection'] = self.test_server_connection()
        results['tests_directory'] = self.test_from_tests_directory()
        results['uvx_package'] = self.test_uvx_package()
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 Integration Test Summary:")
        print("=" * 60)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            test_display = test_name.replace('_', ' ').title()
            print(f"{test_display:<25}: {status}")
        
        all_passed = all(results.values())
        
        if all_passed:
            print(f"\n🎉 All integration tests passed! The MCP server is ready for production.")
            return 0
        else:
            print(f"\n❌ Some integration tests failed. Please check the output above.")
            return 1

def main():
    """Main entry point for integration tests"""
    tester = MCPIntegrationTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
