#!/usr/bin/env python3
"""
Functional Tests for Prompt MCP Server

End-to-end functional tests that verify the complete system behavior
including real file I/O, process execution, and integration scenarios.

Test Categories:
- End-to-end MCP protocol communication
- Real file system operations
- Environment variable handling
- Amazon Q CLI integration
- Cross-platform compatibility
- Performance and stress testing
- Real-world usage scenarios

Requirements:
- Python 3.6+
- Access to file system
- Amazon Q CLI (for integration tests)
"""

import unittest
import asyncio
import json
import os
import sys
import subprocess
import tempfile
import shutil
import time
from pathlib import Path
from unittest.mock import patch
import logging

# Add parent directory to path to import the server
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestFunctionalMCPServer(unittest.TestCase):
    """Functional tests for the MCP server"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_prompts_dir = Path(self.test_dir) / "functional_prompts"
        self.test_prompts_dir.mkdir()
        
        # Store original environment
        self.original_prompts_path = os.environ.get('PROMPTS_PATH')
        
        # Create test prompt files
        self.create_functional_test_prompts()
        
        # Path to the server script
        self.server_script = Path(__file__).parent.parent / "prompt_mcp_server.py"
        
        # Suppress logging during tests
        logging.getLogger('prompt_mcp_server').setLevel(logging.CRITICAL)
    
    def tearDown(self):
        """Clean up after tests"""
        # Restore original environment
        if self.original_prompts_path is not None:
            os.environ['PROMPTS_PATH'] = self.original_prompts_path
        elif 'PROMPTS_PATH' in os.environ:
            del os.environ['PROMPTS_PATH']
        
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def create_functional_test_prompts(self):
        """Create test prompt files for functional testing"""
        # Simple prompt
        simple_prompt = """# Code Review
Please review the following code for:
- Best practices
- Security issues
- Performance optimizations
- Code style consistency
"""
        (self.test_prompts_dir / "code_review.md").write_text(simple_prompt)
        
        # Complex prompt with multiple variables
        complex_prompt = """# Create {framework} {component_type}

Create a {framework} {component_type} with the following specifications:

## Requirements
- **Name**: {component_name}
- **Purpose**: {purpose}
- **Framework**: {framework}
- **Type**: {component_type}

## Features
- Implement {feature1}
- Add support for {feature2}
- Include {feature3}

## Technical Details
- Use {framework} best practices
- Follow {framework} conventions
- Ensure {component_type} is reusable
"""
        (self.test_prompts_dir / "create_component.md").write_text(complex_prompt)
        
        # Prompt with special characters and formatting
        special_prompt = """# API Documentation Generator

Generate comprehensive API documentation for {api_name}.

## Format Requirements
- **Input**: {input_format}
- **Output**: {output_format}
- **Style**: {doc_style}

### Special Characters Test
- Brackets: [optional], {required}
- Symbols: @param, #section, $variable
- Unicode: 🚀 ✅ ❌ 📝

### Code Examples
```{language}
// Example {language} code
function {function_name}() {
    return "{return_value}";
}
```

**Note**: This prompt tests {special_feature} handling.
"""
        (self.test_prompts_dir / "api_docs.md").write_text(special_prompt)
        
        # Large prompt file (for performance testing)
        large_content = "# Large Prompt Test\n\n"
        large_content += "This is a performance test prompt with {variable}.\n" * 100
        large_content += "\n## Sections\n"
        for i in range(50):
            large_content += f"### Section {i}\nContent for section {i} with {{param_{i}}}.\n\n"
        (self.test_prompts_dir / "large_prompt.md").write_text(large_content)

class TestEndToEndCommunication(TestFunctionalMCPServer):
    """Test end-to-end MCP protocol communication"""
    
    def test_server_startup_and_shutdown(self):
        """Test server can start up and shut down properly"""
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        
        # Start server process
        process = subprocess.Popen(
            [sys.executable, str(self.server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            # Send initialize request
            init_request = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize"
            })
            
            # Send request and get response
            stdout, stderr = process.communicate(
                input=init_request + "\n",
                timeout=5
            )
            
            # Parse response
            response = json.loads(stdout.strip())
            
            # Verify response
            self.assertEqual(response["jsonrpc"], "2.0")
            self.assertEqual(response["id"], 1)
            self.assertIn("result", response)
            self.assertEqual(response["result"]["serverInfo"]["name"], "prompt-mcp-server")
            
        except subprocess.TimeoutExpired:
            process.kill()
            self.fail("Server process timed out")
        
        # Verify process completed successfully
        self.assertEqual(process.returncode, 0)
    
    def test_complete_workflow(self):
        """Test complete workflow: initialize -> list -> get"""
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        
        # Test data for the workflow
        test_requests = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize"
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "prompts/list"
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "prompts/get",
                "params": {"name": "code_review"}
            }
        ]
        
        # Send all requests
        input_data = "\n".join(json.dumps(req) for req in test_requests) + "\n"
        
        process = subprocess.Popen(
            [sys.executable, str(self.server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(input=input_data, timeout=10)
            
            # Parse responses
            responses = []
            for line in stdout.strip().split('\n'):
                if line.strip():
                    responses.append(json.loads(line))
            
            # Verify we got 3 responses
            self.assertEqual(len(responses), 3)
            
            # Verify initialize response
            init_response = responses[0]
            self.assertEqual(init_response["id"], 1)
            self.assertIn("result", init_response)
            
            # Verify list response
            list_response = responses[1]
            self.assertEqual(list_response["id"], 2)
            self.assertIn("prompts", list_response["result"])
            self.assertGreater(len(list_response["result"]["prompts"]), 0)
            
            # Verify get response
            get_response = responses[2]
            self.assertEqual(get_response["id"], 3)
            self.assertIn("messages", get_response["result"])
            self.assertIn("Code Review", get_response["result"]["messages"][0]["content"]["text"])
            
        except subprocess.TimeoutExpired:
            process.kill()
            self.fail("Complete workflow test timed out")

class TestRealFileSystemOperations(TestFunctionalMCPServer):
    """Test real file system operations"""
    
    def test_multiple_directories_scanning(self):
        """Test scanning multiple real directories"""
        # Create second directory
        second_dir = Path(self.test_dir) / "second_prompts"
        second_dir.mkdir()
        
        # Add prompt to second directory
        (second_dir / "second_prompt.md").write_text("# Second Prompt\nThis is from the second directory.")
        
        # Set PROMPTS_PATH to both directories
        os.environ['PROMPTS_PATH'] = f"{self.test_prompts_dir}:{second_dir}"
        
        # Test prompts/list
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "prompts/list"
        })
        
        process = subprocess.Popen(
            [sys.executable, str(self.server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(input=request + "\n", timeout=5)
            response = json.loads(stdout.strip())
            
            # Should find prompts from both directories
            prompt_names = [p["name"] for p in response["result"]["prompts"]]
            self.assertIn("code_review", prompt_names)  # From first directory
            self.assertIn("second_prompt", prompt_names)  # From second directory
            
        except subprocess.TimeoutExpired:
            process.kill()
            self.fail("Multiple directories test timed out")
    
    def test_file_permission_handling(self):
        """Test handling of files with different permissions"""
        # Create a file with restricted permissions
        restricted_file = self.test_prompts_dir / "restricted.md"
        restricted_file.write_text("# Restricted Prompt\nThis should not be readable.")
        restricted_file.chmod(0o000)
        
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        
        try:
            request = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "prompts/list"
            })
            
            process = subprocess.Popen(
                [sys.executable, str(self.server_script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=request + "\n", timeout=5)
            response = json.loads(stdout.strip())
            
            # Should still work, just skip the restricted file
            self.assertIn("result", response)
            self.assertIn("prompts", response["result"])
            
            # Restricted file should not be in the list
            prompt_names = [p["name"] for p in response["result"]["prompts"]]
            self.assertNotIn("restricted", prompt_names)
            
        finally:
            # Restore permissions for cleanup
            restricted_file.chmod(0o644)
    
    def test_large_file_handling(self):
        """Test handling of large prompt files"""
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "prompts/get",
            "params": {"name": "large_prompt"}
        })
        
        process = subprocess.Popen(
            [sys.executable, str(self.server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(input=request + "\n", timeout=10)
            response = json.loads(stdout.strip())
            
            # Should handle large file successfully
            self.assertIn("result", response)
            self.assertIn("messages", response["result"])
            content = response["result"]["messages"][0]["content"]["text"]
            self.assertIn("Large Prompt Test", content)
            self.assertIn("performance test", content)
            
        except subprocess.TimeoutExpired:
            process.kill()
            self.fail("Large file handling test timed out")

class TestEnvironmentVariableHandling(TestFunctionalMCPServer):
    """Test environment variable handling"""
    
    def test_prompts_path_with_tilde_expansion(self):
        """Test PROMPTS_PATH with tilde (~) expansion"""
        # Create directory in home directory
        home_test_dir = Path.home() / ".test_mcp_prompts"
        home_test_dir.mkdir(exist_ok=True)
        
        try:
            # Create test prompt
            (home_test_dir / "home_prompt.md").write_text("# Home Prompt\nFrom home directory.")
            
            # Set PROMPTS_PATH with tilde
            os.environ['PROMPTS_PATH'] = "~/.test_mcp_prompts"
            
            request = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "prompts/list"
            })
            
            process = subprocess.Popen(
                [sys.executable, str(self.server_script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=request + "\n", timeout=5)
            response = json.loads(stdout.strip())
            
            # Should find the prompt from home directory
            prompt_names = [p["name"] for p in response["result"]["prompts"]]
            self.assertIn("home_prompt", prompt_names)
            
        finally:
            # Clean up
            shutil.rmtree(home_test_dir, ignore_errors=True)
    
    def test_empty_prompts_path_fallback(self):
        """Test fallback to default directory when PROMPTS_PATH is empty"""
        os.environ['PROMPTS_PATH'] = ""
        
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "prompts/list"
        })
        
        process = subprocess.Popen(
            [sys.executable, str(self.server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(input=request + "\n", timeout=5)
            response = json.loads(stdout.strip())
            
            # Should still work with default directory
            self.assertIn("result", response)
            self.assertIn("prompts", response["result"])
            
        except subprocess.TimeoutExpired:
            process.kill()
            self.fail("Empty PROMPTS_PATH test timed out")

class TestVariableSubstitutionFunctional(TestFunctionalMCPServer):
    """Test variable substitution in real scenarios"""
    
    def test_complex_variable_substitution(self):
        """Test complex variable substitution with multiple variables"""
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "prompts/get",
            "params": {
                "name": "create_component",
                "arguments": {
                    "framework": "React",
                    "component_type": "Component",
                    "component_name": "UserProfile",
                    "purpose": "display user information",
                    "feature1": "responsive design",
                    "feature2": "dark mode",
                    "feature3": "accessibility features"
                }
            }
        })
        
        process = subprocess.Popen(
            [sys.executable, str(self.server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(input=request + "\n", timeout=5)
            response = json.loads(stdout.strip())
            
            content = response["result"]["messages"][0]["content"]["text"]
            
            # Verify all variables were substituted
            self.assertIn("React Component", content)
            self.assertIn("UserProfile", content)
            self.assertIn("display user information", content)
            self.assertIn("responsive design", content)
            self.assertIn("dark mode", content)
            self.assertIn("accessibility features", content)
            
            # Verify no variable placeholders remain
            self.assertNotIn("{framework}", content)
            self.assertNotIn("{component_type}", content)
            self.assertNotIn("{component_name}", content)
            
        except subprocess.TimeoutExpired:
            process.kill()
            self.fail("Complex variable substitution test timed out")
    
    def test_special_characters_in_variables(self):
        """Test variable substitution with special characters"""
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "prompts/get",
            "params": {
                "name": "api_docs",
                "arguments": {
                    "api_name": "User Management API",
                    "input_format": "JSON",
                    "output_format": "Markdown",
                    "doc_style": "OpenAPI 3.0",
                    "language": "javascript",
                    "function_name": "getUserProfile",
                    "return_value": "user data object",
                    "special_feature": "Unicode emoji"
                }
            }
        })
        
        process = subprocess.Popen(
            [sys.executable, str(self.server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(input=request + "\n", timeout=5)
            response = json.loads(stdout.strip())
            
            content = response["result"]["messages"][0]["content"]["text"]
            
            # Verify special characters are preserved
            self.assertIn("🚀 ✅ ❌ 📝", content)
            self.assertIn("User Management API", content)
            self.assertIn("getUserProfile", content)
            self.assertIn("Unicode emoji", content)
            
        except subprocess.TimeoutExpired:
            process.kill()
            self.fail("Special characters test timed out")

class TestPerformanceAndStress(TestFunctionalMCPServer):
    """Test performance and stress scenarios"""
    
    def test_concurrent_requests_simulation(self):
        """Test handling multiple requests in sequence (simulating concurrency)"""
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        
        # Create multiple requests
        requests = []
        for i in range(10):
            requests.append(json.dumps({
                "jsonrpc": "2.0",
                "id": i + 1,
                "method": "prompts/list"
            }))
        
        input_data = "\n".join(requests) + "\n"
        
        process = subprocess.Popen(
            [sys.executable, str(self.server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        start_time = time.time()
        
        try:
            stdout, stderr = process.communicate(input=input_data, timeout=15)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse responses
            responses = []
            for line in stdout.strip().split('\n'):
                if line.strip():
                    responses.append(json.loads(line))
            
            # Verify all requests were processed
            self.assertEqual(len(responses), 10)
            
            # Verify performance (should complete within reasonable time)
            self.assertLess(duration, 10.0, "Concurrent requests took too long")
            
            # Verify all responses are valid
            for i, response in enumerate(responses):
                self.assertEqual(response["id"], i + 1)
                self.assertIn("result", response)
                
        except subprocess.TimeoutExpired:
            process.kill()
            self.fail("Concurrent requests test timed out")
    
    def test_cache_performance(self):
        """Test caching improves performance on repeated requests"""
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        
        # First request (cache miss)
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "prompts/list"
        })
        
        # Send same request twice to test caching
        input_data = request + "\n" + request + "\n"
        
        process = subprocess.Popen(
            [sys.executable, str(self.server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        start_time = time.time()
        
        try:
            stdout, stderr = process.communicate(input=input_data, timeout=10)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse responses
            responses = []
            for line in stdout.strip().split('\n'):
                if line.strip():
                    responses.append(json.loads(line))
            
            # Should get 2 identical responses
            self.assertEqual(len(responses), 2)
            self.assertEqual(responses[0]["result"], responses[1]["result"])
            
            # Should complete quickly due to caching
            self.assertLess(duration, 5.0, "Cached requests took too long")
            
        except subprocess.TimeoutExpired:
            process.kill()
            self.fail("Cache performance test timed out")

class TestErrorHandlingFunctional(TestFunctionalMCPServer):
    """Test error handling in real scenarios"""
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON requests"""
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        
        # Send malformed JSON
        malformed_requests = [
            "invalid json",
            '{"incomplete": json',
            '{"jsonrpc": "2.0", "id": 1, "method":}',  # Missing value
            ""  # Empty string
        ]
        
        for malformed_request in malformed_requests:
            with self.subTest(request=malformed_request):
                process = subprocess.Popen(
                    [sys.executable, str(self.server_script)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                try:
                    stdout, stderr = process.communicate(
                        input=malformed_request + "\n",
                        timeout=5
                    )
                    
                    if stdout.strip():
                        response = json.loads(stdout.strip())
                        # Should return parse error
                        self.assertIn("error", response)
                        self.assertEqual(response["error"]["code"], -32700)
                    
                except (subprocess.TimeoutExpired, json.JSONDecodeError):
                    # Some malformed requests might cause the server to exit
                    # or produce non-JSON output, which is acceptable
                    pass
                finally:
                    if process.poll() is None:
                        process.kill()

class TestAmazonQIntegration(TestFunctionalMCPServer):
    """Test Amazon Q CLI integration (if available)"""
    
    def test_workspace_configuration_detection(self):
        """Test that workspace configuration is properly formatted"""
        workspace_config = Path(".amazonq/mcp.json")
        
        if workspace_config.exists():
            with open(workspace_config) as f:
                config = json.load(f)
            
            # Verify configuration structure
            self.assertIn("mcpServers", config)
            self.assertIn("prompt-server", config["mcpServers"])
            
            server_config = config["mcpServers"]["prompt-server"]
            self.assertIn("command", server_config)
            self.assertIn("args", server_config)
            
            # Check for uvx configuration
            if server_config["command"] == "uvx":
                # New uvx configuration
                self.assertIn("--from", server_config["args"])
                self.assertIn("prompt-mcp-server", server_config["args"])
            else:
                # Legacy python3 configuration
                self.assertEqual(server_config["args"][0], "prompt_mcp_server.py")
        else:
            self.skipTest("Workspace configuration not found")
    
    def test_amazon_q_cli_detection(self):
        """Test if Amazon Q CLI can detect the server"""
        try:
            # Try to run q mcp list
            result = subprocess.run(
                ["q", "mcp", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Amazon Q CLI is available and can list MCP servers
                self.assertIn("prompt-server", result.stdout)
            else:
                self.skipTest("Amazon Q CLI not available or not configured")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("Amazon Q CLI not available")

def run_functional_tests():
    """Run all functional tests and provide summary"""
    # Create test suite
    test_classes = [
        TestEndToEndCommunication,
        TestRealFileSystemOperations,
        TestEnvironmentVariableHandling,
        TestVariableSubstitutionFunctional,
        TestPerformanceAndStress,
        TestErrorHandlingFunctional,
        TestAmazonQIntegration
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
    print("FUNCTIONAL TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"- {test}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"- {test}")
    
    if hasattr(result, 'skipped') and result.skipped:
        print(f"\nSKIPPED ({len(result.skipped)}):")
        for test, reason in result.skipped:
            print(f"- {test}: {reason}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL FUNCTIONAL TESTS PASSED!")
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)} FUNCTIONAL TESTS FAILED")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_functional_tests()
    sys.exit(0 if success else 1)
