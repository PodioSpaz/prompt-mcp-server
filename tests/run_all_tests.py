#!/usr/bin/env python3
"""
Test Runner for Prompt MCP Server

Runs all tests (unit, functional, and uvx integration) and provides comprehensive reporting.

Usage:
    python3 tests/run_all_tests.py
    python3 tests/run_all_tests.py --unit-only
    python3 tests/run_all_tests.py --functional-only
    python3 tests/run_all_tests.py --uvx-only
    python3 tests/run_all_tests.py --no-uvx
    python3 tests/run_all_tests.py --verbose
"""

import sys
import argparse
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_unit_tests():
    """Run unit tests"""
    print("🧪 RUNNING UNIT TESTS")
    print("=" * 50)
    
    # Import and run unit tests
    from test_prompt_mcp_server import run_tests
    return run_tests()

def run_functional_tests():
    """Run functional tests"""
    print("\n🔧 RUNNING FUNCTIONAL TESTS")
    print("=" * 50)
    
    # Import and run functional tests
    from test_functional import run_functional_tests
    return run_functional_tests()

def run_uvx_tests():
    """Run UVX integration tests"""
    print("\n📦 RUNNING UVX INTEGRATION TESTS")
    print("=" * 50)
    
    try:
        # Import and run UVX tests
        from test_uvx_integration import run_uvx_tests
        return run_uvx_tests()
    except ImportError as e:
        print(f"❌ Could not import UVX tests: {e}")
        return False
    except Exception as e:
        print(f"❌ UVX tests failed with exception: {e}")
        return False

def run_mcp_integration_tests():
    """Run MCP integration tests"""
    print("🧪 RUNNING MCP INTEGRATION TESTS")
    print("=" * 50)
    
    try:
        # Import and run MCP integration tests
        from test_mcp_integration import MCPIntegrationTester
        tester = MCPIntegrationTester()
        return tester.run_all_tests() == 0
    except ImportError as e:
        print(f"❌ Could not import MCP integration tests: {e}")
        return False
    except Exception as e:
        print(f"❌ MCP integration tests failed with exception: {e}")
        return False

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run Prompt MCP Server tests")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--functional-only", action="store_true", help="Run only functional tests")
    parser.add_argument("--uvx-only", action="store_true", help="Run only UVX integration tests")
    parser.add_argument("--mcp-only", action="store_true", help="Run only MCP integration tests")
    parser.add_argument("--no-uvx", action="store_true", help="Skip UVX integration tests")
    parser.add_argument("--no-mcp", action="store_true", help="Skip MCP integration tests")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    start_time = time.time()
    
    print("🚀 PROMPT MCP SERVER - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # Determine which tests to run
    run_unit = not (args.functional_only or args.uvx_only or args.mcp_only)
    run_functional = not (args.unit_only or args.uvx_only or args.mcp_only)
    run_uvx = not (args.unit_only or args.functional_only or args.mcp_only or args.no_uvx)
    run_mcp = not (args.unit_only or args.functional_only or args.uvx_only or args.no_mcp)
    
    if args.uvx_only:
        run_uvx = True
    
    if args.mcp_only:
        run_mcp = True
    
    # Run unit tests
    if run_unit:
        try:
            results['unit'] = run_unit_tests()
        except Exception as e:
            print(f"❌ Unit tests failed with exception: {e}")
            results['unit'] = False
    
    # Run functional tests
    if run_functional:
        try:
            results['functional'] = run_functional_tests()
        except Exception as e:
            print(f"❌ Functional tests failed with exception: {e}")
            results['functional'] = False
    
    # Run UVX integration tests
    if run_uvx:
        try:
            results['uvx'] = run_uvx_tests()
        except Exception as e:
            print(f"❌ UVX integration tests failed with exception: {e}")
            results['uvx'] = False
    
    # Run MCP integration tests
    if run_mcp:
        try:
            results['mcp'] = run_mcp_integration_tests()
        except Exception as e:
            print(f"❌ MCP integration tests failed with exception: {e}")
            results['mcp'] = False
    
    # Calculate total time
    end_time = time.time()
    total_time = end_time - start_time
    
    # Print final summary
    print("\n" + "=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)
    
    if 'unit' in results:
        status = "✅ PASSED" if results['unit'] else "❌ FAILED"
        print(f"Unit Tests:           {status}")
    
    if 'functional' in results:
        status = "✅ PASSED" if results['functional'] else "❌ FAILED"
        print(f"Functional Tests:     {status}")
    
    if 'uvx' in results:
        status = "✅ PASSED" if results['uvx'] else "❌ FAILED"
        print(f"UVX Integration:      {status}")
    
    if 'mcp' in results:
        status = "✅ PASSED" if results['mcp'] else "❌ FAILED"
        print(f"MCP Integration:      {status}")
    
    print(f"Total Time:           {total_time:.2f} seconds")
    print(f"Completed at:         {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Determine overall success
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! PROJECT IS READY FOR PRODUCTION!")
        if 'uvx' in results and results['uvx']:
            print("📦 UVX integration verified - ready for publishing!")
    else:
        failed_tests = [name for name, passed in results.items() if not passed]
        print(f"\n❌ SOME TESTS FAILED: {', '.join(failed_tests)}")
    
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
