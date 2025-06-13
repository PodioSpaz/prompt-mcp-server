#!/usr/bin/env python3
"""
UVX Integration Tests for Prompt MCP Server

Tests the MCP server when run as a long-running process via uvx,
simulating real-world usage scenarios with Amazon Q CLI.

Test Categories:
- UVX package installation and execution
- Long-running process behavior
- Multiple request handling
- Process lifecycle management
- Real-world integration scenarios
"""

import unittest
import subprocess
import json
import time
import threading
import queue
import os
import sys
from pathlib import Path

class TestUVXIntegration(unittest.TestCase):
    """Test UVX integration scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        self.dist_dir = self.project_root / "dist"
        
        # Find the wheel file
        wheel_files = list(self.dist_dir.glob("*.whl"))
        if not wheel_files:
            self.skipTest("No wheel file found. Run 'pyproject-build' first.")
        
        self.wheel_path = wheel_files[0]
        self.timeout = 10  # seconds
    
    def run_uvx_server(self, input_data, timeout=None):
        """Run server via uvx and return output"""
        if timeout is None:
            timeout = self.timeout
        
        cmd = ["uvx", "--from", str(self.wheel_path), "prompt-mcp-server"]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=input_data, timeout=timeout)
            return stdout, stderr, process.returncode
            
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return stdout, stderr, -1

class TestUVXLongRunningProcess(TestUVXIntegration):
    """Test long-running process behavior"""
    
    def test_server_startup_via_uvx(self):
        """Test server starts up correctly via uvx"""
        input_data = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize"
        }) + "\n"
        
        stdout, stderr, returncode = self.run_uvx_server(input_data)
        
        # Should complete successfully
        self.assertEqual(returncode, 0, f"Server failed to start: {stderr}")
        
        # Should return valid JSON response
        self.assertTrue(stdout.strip(), "No output received")
        
        try:
            response = json.loads(stdout.strip())
            self.assertEqual(response["jsonrpc"], "2.0")
            self.assertEqual(response["id"], 1)
            self.assertIn("result", response)
            self.assertEqual(response["result"]["serverInfo"]["name"], "prompt-mcp-server")
        except json.JSONDecodeError as e:
            self.fail(f"Invalid JSON response: {e}\nOutput: {stdout}")
    
    def test_multiple_requests_sequence(self):
        """Test handling multiple requests in sequence"""
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize"},
            {"jsonrpc": "2.0", "id": 2, "method": "prompts/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "prompts/get", "params": {"name": "nonexistent"}}
        ]
        
        input_data = "\n".join(json.dumps(req) for req in requests) + "\n"
        
        stdout, stderr, returncode = self.run_uvx_server(input_data, timeout=15)
        
        self.assertEqual(returncode, 0, f"Server failed: {stderr}")
        
        # Parse responses
        responses = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                try:
                    responses.append(json.loads(line))
                except json.JSONDecodeError:
                    self.fail(f"Invalid JSON line: {line}")
        
        # Should get 3 responses
        self.assertEqual(len(responses), 3, f"Expected 3 responses, got {len(responses)}")
        
        # Verify response IDs match request IDs
        for i, response in enumerate(responses):
            self.assertEqual(response["id"], i + 1)
    
    def test_long_running_session_simulation(self):
        """Test simulated long-running session with multiple interactions"""
        # Simulate a realistic Amazon Q session
        session_requests = [
            # Initialize
            {"jsonrpc": "2.0", "id": 1, "method": "initialize"},
            
            # List prompts
            {"jsonrpc": "2.0", "id": 2, "method": "prompts/list"},
            
            # Get a prompt (assuming debug_code exists in default location)
            {"jsonrpc": "2.0", "id": 3, "method": "prompts/get", "params": {"name": "debug_code"}},
            
            # List again (test caching)
            {"jsonrpc": "2.0", "id": 4, "method": "prompts/list"},
            
            # Try to get a parameterized prompt
            {"jsonrpc": "2.0", "id": 5, "method": "prompts/get", "params": {
                "name": "create_function", 
                "arguments": {"language": "Python", "function_name": "test", "description": "test function"}
            }},
        ]
        
        input_data = "\n".join(json.dumps(req) for req in session_requests) + "\n"
        
        stdout, stderr, returncode = self.run_uvx_server(input_data, timeout=20)
        
        self.assertEqual(returncode, 0, f"Long session failed: {stderr}")
        
        # Parse and validate all responses
        responses = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                responses.append(json.loads(line))
        
        self.assertEqual(len(responses), 5, "Should handle all 5 requests")
        
        # Verify initialize response
        init_response = responses[0]
        self.assertEqual(init_response["id"], 1)
        self.assertIn("result", init_response)
        
        # Verify prompts/list responses
        list_response1 = responses[1]
        list_response2 = responses[3]  # Second list call
        self.assertEqual(list_response1["id"], 2)
        self.assertEqual(list_response2["id"], 4)
        self.assertIn("prompts", list_response1["result"])
        self.assertIn("prompts", list_response2["result"])

class TestUVXProcessLifecycle(TestUVXIntegration):
    """Test process lifecycle management"""
    
    def test_graceful_shutdown_on_stdin_close(self):
        """Test server shuts down gracefully when stdin is closed"""
        cmd = ["uvx", "--from", str(self.wheel_path), "prompt-mcp-server"]
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send initialize request
        init_request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize"
        }) + "\n"
        
        process.stdin.write(init_request)
        process.stdin.flush()
        
        # Give it time to process
        time.sleep(0.5)
        
        # Close stdin to signal shutdown
        process.stdin.close()
        
        # Wait for graceful shutdown
        try:
            stdout, stderr = process.communicate(timeout=5)
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            returncode = -1
        
        # Should exit cleanly
        self.assertEqual(returncode, 0, f"Server didn't shut down gracefully: {stderr}")
        
        # Should have processed the initialize request
        self.assertTrue(stdout.strip(), "No response to initialize request")
    
    def test_error_handling_in_long_running_mode(self):
        """Test error handling doesn't crash the long-running process"""
        # Send a mix of valid and invalid requests
        requests = [
            '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}',
            'invalid json',  # Should return parse error
            '{"jsonrpc": "2.0", "id": 2, "method": "unknown_method"}',  # Should return method not found
            '{"jsonrpc": "2.0", "id": 3, "method": "prompts/list"}',  # Should work normally
        ]
        
        input_data = "\n".join(requests) + "\n"
        
        stdout, stderr, returncode = self.run_uvx_server(input_data)
        
        # Process should complete successfully despite errors
        self.assertEqual(returncode, 0, f"Server crashed on errors: {stderr}")
        
        # Should get responses for all requests (including error responses)
        lines = [line for line in stdout.strip().split('\n') if line.strip()]
        self.assertGreaterEqual(len(lines), 3, "Should handle all valid requests plus error responses")

class TestUVXRealWorldScenarios(TestUVXIntegration):
    """Test real-world usage scenarios"""
    
    def test_amazon_q_cli_simulation(self):
        """Simulate typical Amazon Q CLI interaction pattern"""
        # This simulates what Amazon Q CLI would do:
        # 1. Initialize the server
        # 2. List available prompts
        # 3. Get a specific prompt with parameters
        
        amazon_q_session = [
            # Amazon Q initializes the MCP server
            {"jsonrpc": "2.0", "id": "init-1", "method": "initialize"},
            
            # User types "/prompts" - Amazon Q lists available prompts
            {"jsonrpc": "2.0", "id": "list-1", "method": "prompts/list"},
            
            # User selects a prompt - Amazon Q gets the prompt content
            {"jsonrpc": "2.0", "id": "get-1", "method": "prompts/get", "params": {"name": "debug_code"}},
        ]
        
        input_data = "\n".join(json.dumps(req) for req in amazon_q_session) + "\n"
        
        stdout, stderr, returncode = self.run_uvx_server(input_data)
        
        self.assertEqual(returncode, 0, f"Amazon Q simulation failed: {stderr}")
        
        # Verify the interaction worked as expected
        responses = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                responses.append(json.loads(line))
        
        self.assertEqual(len(responses), 3, "Should complete full Amazon Q interaction")
        
        # Check that we can handle string IDs (Amazon Q might use these)
        self.assertEqual(responses[0]["id"], "init-1")
        self.assertEqual(responses[1]["id"], "list-1")
        self.assertEqual(responses[2]["id"], "get-1")
    
    def test_concurrent_request_handling(self):
        """Test that server can handle rapid sequential requests"""
        # Generate many requests quickly
        requests = []
        for i in range(20):
            requests.append({
                "jsonrpc": "2.0",
                "id": f"req-{i}",
                "method": "prompts/list"
            })
        
        input_data = "\n".join(json.dumps(req) for req in requests) + "\n"
        
        start_time = time.time()
        stdout, stderr, returncode = self.run_uvx_server(input_data, timeout=30)
        end_time = time.time()
        
        self.assertEqual(returncode, 0, f"Concurrent requests failed: {stderr}")
        
        # Should handle all requests
        responses = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                responses.append(json.loads(line))
        
        self.assertEqual(len(responses), 20, "Should handle all 20 requests")
        
        # Should complete in reasonable time (caching should help)
        duration = end_time - start_time
        self.assertLess(duration, 10, f"Took too long: {duration:.2f}s")
        
        # Verify all responses are valid
        for i, response in enumerate(responses):
            self.assertEqual(response["id"], f"req-{i}")
            self.assertIn("result", response)
            self.assertIn("prompts", response["result"])

class TestUVXEnvironmentVariables(TestUVXIntegration):
    """Test environment variable handling in uvx context"""
    
    def test_custom_prompts_path_via_uvx(self):
        """Test PROMPTS_PATH environment variable works with uvx"""
        # Create a temporary prompt file
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_prompt = Path(temp_dir) / "test_prompt.md"
            temp_prompt.write_text("# Test Prompt\nThis is a test prompt from custom path.")
            
            # Set environment variable and run server
            env = os.environ.copy()
            env['PROMPTS_PATH'] = str(temp_dir)
            
            cmd = ["uvx", "--from", str(self.wheel_path), "prompt-mcp-server"]
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            # Request prompts list
            request = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "prompts/list"
            }) + "\n"
            
            try:
                stdout, stderr = process.communicate(input=request, timeout=10)
                
                # Should find our custom prompt
                response = json.loads(stdout.strip())
                prompt_names = [p["name"] for p in response["result"]["prompts"]]
                self.assertIn("test_prompt", prompt_names, "Should find custom prompt")
                
            except subprocess.TimeoutExpired:
                process.kill()
                self.fail("Server timed out with custom PROMPTS_PATH")

def run_uvx_tests():
    """Run UVX integration tests"""
    # Check if uvx is available
    try:
        subprocess.run(["uvx", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ uvx not available. Install with: brew install pipx && pipx install uv")
        return False
    
    # Check if package is built
    dist_dir = Path(__file__).parent.parent / "dist"
    if not dist_dir.exists() or not list(dist_dir.glob("*.whl")):
        print("❌ Package not built. Run: pyproject-build")
        return False
    
    # Create test suite
    test_classes = [
        TestUVXLongRunningProcess,
        TestUVXProcessLifecycle,
        TestUVXRealWorldScenarios,
        TestUVXEnvironmentVariables,
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("UVX INTEGRATION TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"- {test}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"- {test}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL UVX INTEGRATION TESTS PASSED!")
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)} UVX TESTS FAILED")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_uvx_tests()
    sys.exit(0 if success else 1)
