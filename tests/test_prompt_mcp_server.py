#!/usr/bin/env python3
"""
Unit Tests for Prompt MCP Server

Comprehensive test suite covering all functionality of the single-file MCP server.

Test Categories:
- Server initialization and configuration
- Directory management and PROMPTS_PATH
- Prompt file scanning and parsing
- Variable extraction and substitution
- MCP protocol methods (initialize, prompts/list, prompts/get)
- Error handling and edge cases
- Cross-platform compatibility
- Caching functionality

Requirements:
- Python 3.6+
- No external dependencies (uses built-in unittest)
"""

import unittest
import asyncio
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging

# Import the server class
sys.path.insert(0, str(Path(__file__).parent.parent))
from mcp_server.prompt_mcp_server import PromptMCPServer

class TestPromptMCPServer(unittest.TestCase):
    """Test suite for PromptMCPServer"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create temporary directory for test prompts
        self.test_dir = tempfile.mkdtemp()
        self.test_prompts_dir = Path(self.test_dir) / "test_prompts"
        self.test_prompts_dir.mkdir()
        
        # Create test prompt files
        self.create_test_prompts()
        
        # Store original environment
        self.original_prompts_path = os.environ.get('PROMPTS_PATH')
        
        # Suppress logging during tests
        logging.getLogger('__main__').setLevel(logging.CRITICAL)
    
    def tearDown(self):
        """Clean up after each test"""
        # Restore original environment
        if self.original_prompts_path is not None:
            os.environ['PROMPTS_PATH'] = self.original_prompts_path
        elif 'PROMPTS_PATH' in os.environ:
            del os.environ['PROMPTS_PATH']
        
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def create_test_prompts(self):
        """Create test prompt files"""
        # Simple prompt without variables
        simple_prompt = """# Debug Code Issues
Help me debug code by identifying issues and suggesting fixes.

## What I'll do:
- Analyze the code for common issues
- Suggest specific fixes
- Explain the root cause
"""
        (self.test_prompts_dir / "debug_code.md").write_text(simple_prompt)
        
        # Prompt with variables
        parameterized_prompt = """# Create {language} Function

Create a {language} function named {function_name} that {description}.

## Requirements:
- Follow {language} best practices
- Include error handling
- Add comprehensive tests
"""
        (self.test_prompts_dir / "create_function.md").write_text(parameterized_prompt)
        
        # Prompt with special characters and edge cases
        edge_case_prompt = """# Test {special_var} Prompt

This prompt tests {var1} and {var2} with {special_var}.
Also tests {duplicate_var} and {duplicate_var} again.
"""
        (self.test_prompts_dir / "edge_case.md").write_text(edge_case_prompt)
        
        # Empty prompt file
        (self.test_prompts_dir / "empty.md").write_text("")
        
        # Large prompt file (for size testing)
        large_content = "# Large Prompt\n" + "This is a test line.\n" * 1000
        (self.test_prompts_dir / "large.md").write_text(large_content)

class TestServerInitialization(TestPromptMCPServer):
    """Test server initialization and configuration"""
    
    def test_server_initialization_default(self):
        """Test server initialization with default settings"""
        server = PromptMCPServer()
        
        self.assertEqual(server.version, "2.0.2")
        self.assertEqual(server.name, "prompt-mcp-server")
        self.assertIsInstance(server.prompt_directories, list)
        self.assertGreaterEqual(len(server.prompt_directories), 1)
        self.assertEqual(server.cache_ttl, 300)
    
    def test_server_initialization_with_prompts_path(self):
        """Test server initialization with PROMPTS_PATH environment variable"""
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        
        server = PromptMCPServer()
        
        # Check if any directory in the list resolves to our test directory
        resolved_dirs = [d.resolve() for d in server.prompt_directories]
        self.assertIn(self.test_prompts_dir.resolve(), resolved_dirs)
    
    def test_server_initialization_multiple_paths(self):
        """Test server initialization with multiple paths in PROMPTS_PATH"""
        second_dir = Path(self.test_dir) / "second_prompts"
        second_dir.mkdir()
        
        os.environ['PROMPTS_PATH'] = f"{self.test_prompts_dir}:{second_dir}"
        
        server = PromptMCPServer()
        
        # Check if directories are resolved correctly
        resolved_dirs = [d.resolve() for d in server.prompt_directories]
        self.assertIn(self.test_prompts_dir.resolve(), resolved_dirs)
        self.assertIn(second_dir.resolve(), resolved_dirs)
    
    def test_server_initialization_invalid_paths(self):
        """Test server initialization with invalid paths in PROMPTS_PATH"""
        os.environ['PROMPTS_PATH'] = "/nonexistent/path:/another/invalid/path"
        
        server = PromptMCPServer()
        
        # Should fallback to default directory
        self.assertGreaterEqual(len(server.prompt_directories), 1)
        # Should not contain the invalid paths
        invalid_paths = [Path("/nonexistent/path"), Path("/another/invalid/path")]
        for invalid_path in invalid_paths:
            self.assertNotIn(invalid_path, server.prompt_directories)

class TestDirectoryManagement(TestPromptMCPServer):
    """Test directory management functionality"""
    
    def test_get_prompt_directories_default(self):
        """Test getting default prompt directories"""
        if 'PROMPTS_PATH' in os.environ:
            del os.environ['PROMPTS_PATH']
        
        server = PromptMCPServer()
        directories = server._get_prompt_directories()
        
        self.assertIsInstance(directories, list)
        self.assertGreaterEqual(len(directories), 1)
        # Should contain default directory
        default_dir = Path.home() / '.aws' / 'amazonq' / 'prompts'
        self.assertIn(default_dir, directories)
    
    def test_get_prompt_directories_custom(self):
        """Test getting custom prompt directories"""
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        
        server = PromptMCPServer()
        directories = server._get_prompt_directories()
        
        # Check if any directory resolves to our test directory
        resolved_dirs = [d.resolve() for d in directories]
        self.assertIn(self.test_prompts_dir.resolve(), resolved_dirs)
    
    def test_get_default_directory_creation(self):
        """Test default directory creation"""
        server = PromptMCPServer()
        directories = server._get_default_directory()
        
        self.assertIsInstance(directories, list)
        self.assertGreaterEqual(len(directories), 1)
        # Directory should exist after creation
        for directory in directories:
            self.assertTrue(directory.exists())

class TestPromptScanning(TestPromptMCPServer):
    """Test prompt file scanning and parsing"""
    
    def test_scan_prompts_basic(self):
        """Test basic prompt scanning"""
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        
        server = PromptMCPServer()
        prompts = server._scan_prompts()
        
        self.assertIsInstance(prompts, dict)
        self.assertIn("debug_code", prompts)
        self.assertIn("create_function", prompts)
        
        # Check prompt structure
        debug_prompt = prompts["debug_code"]
        self.assertEqual(debug_prompt["name"], "debug_code")
        self.assertEqual(debug_prompt["description"], "Debug Code Issues")
        self.assertIn("Help me debug code", debug_prompt["content"])
        self.assertEqual(len(debug_prompt["variables"]), 0)
        self.assertEqual(len(debug_prompt["arguments"]), 0)
    
    def test_scan_prompts_with_variables(self):
        """Test scanning prompts with variables"""
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        
        server = PromptMCPServer()
        prompts = server._scan_prompts()
        
        create_prompt = prompts["create_function"]
        self.assertIn("language", create_prompt["variables"])
        self.assertIn("function_name", create_prompt["variables"])
        self.assertIn("description", create_prompt["variables"])
        
        # Check arguments structure
        self.assertEqual(len(create_prompt["arguments"]), 3)
        arg_names = [arg["name"] for arg in create_prompt["arguments"]]
        self.assertIn("language", arg_names)
        self.assertIn("function_name", arg_names)
        self.assertIn("description", arg_names)
    
    def test_scan_prompts_edge_cases(self):
        """Test scanning prompts with edge cases"""
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        
        server = PromptMCPServer()
        prompts = server._scan_prompts()
        
        # Edge case prompt should be processed
        if "edge_case" in prompts:
            edge_prompt = prompts["edge_case"]
            # Should handle duplicate variables
            self.assertIn("duplicate_var", edge_prompt["variables"])
            # Should not have duplicates in variables list
            var_count = edge_prompt["variables"].count("duplicate_var")
            self.assertEqual(var_count, 1)
    
    def test_scan_prompts_empty_file(self):
        """Test scanning empty prompt files"""
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        
        server = PromptMCPServer()
        prompts = server._scan_prompts()
        
        # Empty file should be skipped
        self.assertNotIn("empty", prompts)
    
    def test_scan_prompts_nonexistent_directory(self):
        """Test scanning non-existent directory"""
        os.environ['PROMPTS_PATH'] = "/nonexistent/directory"
        
        server = PromptMCPServer()
        prompts = server._scan_prompts()
        
        # Should return empty dict or fallback to default
        self.assertIsInstance(prompts, dict)

class TestVariableSubstitution(TestPromptMCPServer):
    """Test variable substitution functionality"""
    
    def test_substitute_variables_basic(self):
        """Test basic variable substitution"""
        server = PromptMCPServer()
        
        content = "Create a {language} function named {function_name}"
        arguments = {"language": "Python", "function_name": "test_func"}
        
        result = server._substitute_variables(content, arguments)
        
        self.assertEqual(result, "Create a Python function named test_func")
    
    def test_substitute_variables_multiple_occurrences(self):
        """Test substitution with multiple occurrences of same variable"""
        server = PromptMCPServer()
        
        content = "Use {language} for {language} development with {language} best practices"
        arguments = {"language": "JavaScript"}
        
        result = server._substitute_variables(content, arguments)
        
        self.assertEqual(result, "Use JavaScript for JavaScript development with JavaScript best practices")
    
    def test_substitute_variables_missing_arguments(self):
        """Test substitution with missing arguments"""
        server = PromptMCPServer()
        
        content = "Create a {language} function named {function_name}"
        arguments = {"language": "Python"}  # Missing function_name
        
        result = server._substitute_variables(content, arguments)
        
        # Should leave unmatched variables as-is
        self.assertEqual(result, "Create a Python function named {function_name}")
    
    def test_substitute_variables_no_variables(self):
        """Test substitution with content that has no variables"""
        server = PromptMCPServer()
        
        content = "This is a simple prompt without variables"
        arguments = {"unused": "value"}
        
        result = server._substitute_variables(content, arguments)
        
        self.assertEqual(result, content)

class TestMCPProtocol(TestPromptMCPServer):
    """Test MCP protocol methods"""
    
    def setUp(self):
        super().setUp()
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        self.server = PromptMCPServer()
    
    def test_handle_initialize(self):
        """Test MCP initialize method"""
        async def run_test():
            request = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
            
            response = await self.server.handle_initialize(request)
            
            self.assertEqual(response["jsonrpc"], "2.0")
            self.assertEqual(response["id"], 1)
            self.assertIn("result", response)
            self.assertEqual(response["result"]["protocolVersion"], "2024-11-05")
            self.assertIn("capabilities", response["result"])
            self.assertIn("serverInfo", response["result"])
            self.assertEqual(response["result"]["serverInfo"]["name"], "prompt-mcp-server")
            self.assertEqual(response["result"]["serverInfo"]["version"], "2.0.2")
        
        asyncio.run(run_test())
    
    def test_handle_prompts_list(self):
        """Test MCP prompts/list method"""
        async def run_test():
            request = {"jsonrpc": "2.0", "id": 2, "method": "prompts/list"}
            
            response = await self.server.handle_prompts_list(request)
            
            self.assertEqual(response["jsonrpc"], "2.0")
            self.assertEqual(response["id"], 2)
            self.assertIn("result", response)
            self.assertIn("prompts", response["result"])
            
            prompts = response["result"]["prompts"]
            self.assertIsInstance(prompts, list)
            self.assertGreater(len(prompts), 0)
            
            # Check prompt structure
            for prompt in prompts:
                self.assertIn("name", prompt)
                self.assertIn("description", prompt)
                self.assertIn("arguments", prompt)
        
        asyncio.run(run_test())
    
    def test_handle_prompts_get_simple(self):
        """Test MCP prompts/get method with simple prompt"""
        async def run_test():
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "prompts/get",
                "params": {"name": "debug_code"}
            }
            
            response = await self.server.handle_prompts_get(request)
            
            self.assertEqual(response["jsonrpc"], "2.0")
            self.assertEqual(response["id"], 3)
            self.assertIn("result", response)
            self.assertIn("messages", response["result"])
            
            messages = response["result"]["messages"]
            self.assertEqual(len(messages), 1)
            self.assertEqual(messages[0]["role"], "user")
            self.assertIn("content", messages[0])
            self.assertIn("Help me debug code", messages[0]["content"]["text"])
        
        asyncio.run(run_test())
    
    def test_handle_prompts_get_with_variables(self):
        """Test MCP prompts/get method with variable substitution"""
        async def run_test():
            request = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "prompts/get",
                "params": {
                    "name": "create_function",
                    "arguments": {
                        "language": "Python",
                        "function_name": "calculate_sum",
                        "description": "adds two numbers"
                    }
                }
            }
            
            response = await self.server.handle_prompts_get(request)
            
            self.assertEqual(response["jsonrpc"], "2.0")
            self.assertEqual(response["id"], 4)
            self.assertIn("result", response)
            
            content = response["result"]["messages"][0]["content"]["text"]
            self.assertIn("Python", content)
            self.assertIn("calculate_sum", content)
            self.assertIn("adds two numbers", content)
            # Should not contain variable placeholders
            self.assertNotIn("{language}", content)
            self.assertNotIn("{function_name}", content)
            self.assertNotIn("{description}", content)
        
        asyncio.run(run_test())
    
    def test_handle_prompts_get_missing_prompt(self):
        """Test MCP prompts/get method with non-existent prompt"""
        async def run_test():
            request = {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "prompts/get",
                "params": {"name": "nonexistent_prompt"}
            }
            
            response = await self.server.handle_prompts_get(request)
            
            self.assertEqual(response["jsonrpc"], "2.0")
            self.assertEqual(response["id"], 5)
            self.assertIn("error", response)
            self.assertEqual(response["error"]["code"], -32602)
            self.assertIn("not found", response["error"]["message"])
        
        asyncio.run(run_test())
    
    def test_handle_prompts_get_missing_name(self):
        """Test MCP prompts/get method without name parameter"""
        async def run_test():
            request = {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "prompts/get",
                "params": {}
            }
            
            response = await self.server.handle_prompts_get(request)
            
            self.assertEqual(response["jsonrpc"], "2.0")
            self.assertEqual(response["id"], 6)
            self.assertIn("error", response)
            self.assertEqual(response["error"]["code"], -32602)
            self.assertIn("Missing required parameter", response["error"]["message"])
        
        asyncio.run(run_test())
    
    def test_handle_request_unknown_method(self):
        """Test MCP request handler with unknown method"""
        async def run_test():
            request = {"jsonrpc": "2.0", "id": 7, "method": "unknown_method"}
            
            response = await self.server.handle_request(request)
            
            self.assertEqual(response["jsonrpc"], "2.0")
            self.assertEqual(response["id"], 7)
            self.assertIn("error", response)
            self.assertEqual(response["error"]["code"], -32601)
            self.assertIn("Method not found", response["error"]["message"])
        
        asyncio.run(run_test())

class TestCaching(TestPromptMCPServer):
    """Test caching functionality"""
    
    def setUp(self):
        super().setUp()
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        self.server = PromptMCPServer()
    
    def test_cache_functionality(self):
        """Test that caching works correctly"""
        # First call should populate cache
        prompts1 = self.server._get_prompts()
        cache_time1 = self.server.cache_timestamp
        
        # Second call should use cache
        prompts2 = self.server._get_prompts()
        cache_time2 = self.server.cache_timestamp
        
        self.assertEqual(prompts1, prompts2)
        self.assertEqual(cache_time1, cache_time2)
    
    def test_cache_expiration(self):
        """Test that cache expires correctly"""
        # Set very short cache TTL
        self.server.cache_ttl = 0.1
        
        # First call
        prompts1 = self.server._get_prompts()
        cache_time1 = self.server.cache_timestamp
        
        # Wait for cache to expire
        import time
        time.sleep(0.2)
        
        # Second call should refresh cache
        prompts2 = self.server._get_prompts()
        cache_time2 = self.server.cache_timestamp
        
        self.assertGreater(cache_time2, cache_time1)

class TestErrorHandling(TestPromptMCPServer):
    """Test error handling and edge cases"""
    
    def setUp(self):
        super().setUp()
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        self.server = PromptMCPServer()
    
    def test_file_permission_error(self):
        """Test handling of file permission errors"""
        # Create a file with no read permissions
        restricted_file = self.test_prompts_dir / "restricted.md"
        restricted_file.write_text("# Restricted Prompt\nThis should not be readable.")
        restricted_file.chmod(0o000)
        
        try:
            prompts = self.server._scan_prompts()
            # Should not crash, may or may not include the restricted file
            self.assertIsInstance(prompts, dict)
        finally:
            # Restore permissions for cleanup
            restricted_file.chmod(0o644)
    
    def test_large_file_handling(self):
        """Test handling of large files"""
        prompts = self.server._scan_prompts()
        
        # Large file should be handled (may be skipped or included based on size limit)
        self.assertIsInstance(prompts, dict)
    
    def test_invalid_regex_in_content(self):
        """Test handling of content that might break regex"""
        # Create file with potentially problematic content
        problematic_content = """# Test Prompt
This has {unclosed_brace and [brackets] and (parentheses) and *asterisks*
"""
        problematic_file = self.test_prompts_dir / "problematic.md"
        problematic_file.write_text(problematic_content)
        
        prompts = self.server._scan_prompts()
        
        # Should not crash
        self.assertIsInstance(prompts, dict)

class TestAsyncMethods(TestPromptMCPServer):
    """Test async method execution"""
    
    def setUp(self):
        super().setUp()
        os.environ['PROMPTS_PATH'] = str(self.test_prompts_dir)
        self.server = PromptMCPServer()
    
    def test_async_initialize(self):
        """Test async initialize method"""
        async def run_test():
            request = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
            response = await self.server.handle_initialize(request)
            self.assertIn("result", response)
        
        asyncio.run(run_test())
    
    def test_async_prompts_list(self):
        """Test async prompts/list method"""
        async def run_test():
            request = {"jsonrpc": "2.0", "id": 2, "method": "prompts/list"}
            response = await self.server.handle_prompts_list(request)
            self.assertIn("result", response)
            self.assertIn("prompts", response["result"])
        
        asyncio.run(run_test())
    
    def test_async_prompts_get(self):
        """Test async prompts/get method"""
        async def run_test():
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "prompts/get",
                "params": {"name": "debug_code"}
            }
            response = await self.server.handle_prompts_get(request)
            self.assertIn("result", response)
        
        asyncio.run(run_test())

def run_tests():
    """Run all tests and provide summary"""
    # Create test suite
    test_classes = [
        TestServerInitialization,
        TestDirectoryManagement,
        TestPromptScanning,
        TestVariableSubstitution,
        TestMCPProtocol,
        TestCaching,
        TestErrorHandling,
        TestAsyncMethods
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
    print("TEST SUMMARY")
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
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)} TESTS FAILED")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
