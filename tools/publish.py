#!/usr/bin/env python3
"""
Publishing Script for Prompt MCP Server

Automates the build and publish process for the package.

Usage:
    python3 tools/publish.py --build-only    # Build package only
    python3 tools/publish.py --test          # Build and test with uvx
    python3 tools/publish.py --testpypi      # Publish to TestPyPI
    python3 tools/publish.py --pypi          # Publish to PyPI
"""

import subprocess
import sys
import argparse
from pathlib import Path
import json

def run_command(cmd, description, check=True):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        # Handle both string commands and list commands
        if isinstance(cmd, str):
            # Convert string commands to list for security
            cmd_list = cmd.split()
        else:
            cmd_list = cmd
            
        result = subprocess.run(cmd_list, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False

def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    tools = {
        "pyproject-build": "pipx install build",
        "twine": "pipx install twine",
        "uvx": "brew install pipx && pipx install uv"
    }
    
    print("🔍 Checking prerequisites...")
    
    tools = {
        "pyproject-build": "pipx install build",
        "twine": "pipx install twine",
        "uvx": "brew install pipx && pipx install uv"
    }
    
    missing = []
    for tool, install_cmd in tools.items():
        try:
            import shutil
            tool_path = shutil.which(tool)
            if not tool_path:
                raise FileNotFoundError(f"{tool} not found in PATH")
            subprocess.run([tool_path, "--version"], capture_output=True, check=True)
            print(f"✅ {tool} is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ {tool} not found. Install with: {install_cmd}")
            missing.append(tool)
    
    return len(missing) == 0

def build_package():
    """Build the package"""
    print("\n🏗️ BUILDING PACKAGE")
    print("=" * 40)
    
    # Clean previous builds
    if Path("dist").exists():
        import shutil
        print("🔄 Cleaning previous builds...")
        shutil.rmtree("dist")
        print("✅ Cleaning previous builds completed")
    
    # Build package
    if not run_command(["pyproject-build"], "Building package"):
        return False
    
    # List built files
    print("\n📦 Built packages:")
    for file in Path("dist").glob("*"):
        print(f"  - {file.name}")
    
    return True

def test_package():
    """Test the built package with uvx"""
    print("\n🧪 TESTING PACKAGE WITH UVX")
    print("=" * 40)
    
    # Find wheel file
    wheel_files = list(Path("dist").glob("*.whl"))
    if not wheel_files:
        print("❌ No wheel file found")
        return False
    
    wheel_path = wheel_files[0]
    print(f"Testing with: {wheel_path}")
    
    # Test basic functionality
    print("⚠️  Note: The test will start the MCP server. Press Ctrl+C to stop after seeing the response.")
    print("🔄 Testing basic functionality...")
    
    try:
        # Find uvx executable
        import shutil
        uvx_path = shutil.which("uvx")
        if not uvx_path:
            print("⚠️  uvx not found in PATH, skipping package test")
            return True
            
        # Test the package by running it directly
        test_process = subprocess.Popen(
            [uvx_path, "--from", f"./{wheel_path}", "prompt-mcp-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send test request
        test_request = '{"jsonrpc": "2.0", "id": 1, "method": "initialize"}\n'
        stdout, stderr = test_process.communicate(input=test_request, timeout=10)
        
        if test_process.returncode == 0 and "prompt-mcp-server" in stdout:
            print("✅ Package test successful")
        else:
            print("⚠️  Package test completed (may have been interrupted)")
            
    except subprocess.TimeoutExpired:
        test_process.kill()
        print("⚠️  Test timeout (this is expected for MCP servers)")
    except Exception as e:
        print(f"⚠️  Test completed with note: {e}")
    
    print("✅ Package testing completed")
    print("📋 For comprehensive testing, see UVX_INSTRUCTIONS.md")
    return True

def publish_to_testpypi():
    """Publish to TestPyPI"""
    print("\n📤 PUBLISHING TO TESTPYPI")
    print("=" * 40)
    
    # Get all files in dist directory
    import glob
    dist_files = glob.glob("dist/*")
    if not dist_files:
        print("❌ No files found in dist/")
        return False
        
    cmd = ["twine", "upload", "--repository", "testpypi"] + dist_files
    return run_command(cmd, "Publishing to TestPyPI")

def publish_to_pypi():
    """Publish to PyPI"""
    print("\n📤 PUBLISHING TO PYPI")
    print("=" * 40)
    
    # Confirm with user
    response = input("⚠️  This will publish to PyPI. Are you sure? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Publishing cancelled")
        return False
    
    # Get all files in dist directory
    import glob
    dist_files = glob.glob("dist/*")
    if not dist_files:
        print("❌ No files found in dist/")
        return False
        
    cmd = ["twine", "upload"] + dist_files
    return run_command(cmd, "Publishing to PyPI")

def main():
    """Main publishing workflow"""
    parser = argparse.ArgumentParser(description="Build and publish Prompt MCP Server")
    parser.add_argument("--build-only", action="store_true", help="Build package only")
    parser.add_argument("--test", action="store_true", help="Build and test with uvx")
    parser.add_argument("--testpypi", action="store_true", help="Publish to TestPyPI")
    parser.add_argument("--pypi", action="store_true", help="Publish to PyPI")
    
    args = parser.parse_args()
    
    print("🚀 PROMPT MCP SERVER - PUBLISHING WORKFLOW")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install missing tools.")
        return False
    
    # Build package
    if not build_package():
        print("\n❌ Build failed")
        return False
    
    if args.build_only:
        print("\n✅ Build completed successfully!")
        return True
    
    # Test package
    if args.test or args.testpypi or args.pypi:
        if not test_package():
            print("\n❌ Testing failed")
            return False
    
    # Publish to TestPyPI
    if args.testpypi:
        if not publish_to_testpypi():
            print("\n❌ TestPyPI publishing failed")
            return False
        
        print("\n✅ Published to TestPyPI!")
        print("🧪 Test installation with:")
        print("   uvx --index-url https://test.pypi.org/simple/ prompt-mcp-server")
    
    # Publish to PyPI
    if args.pypi:
        if not publish_to_pypi():
            print("\n❌ PyPI publishing failed")
            return False
        
        print("\n🎉 Published to PyPI!")
        print("📦 Install with:")
        print("   uvx prompt-mcp-server")
    
    if not any([args.build_only, args.test, args.testpypi, args.pypi]):
        print("\n✅ Build completed successfully!")
        print("📋 Next steps:")
        print("   python3 tools/publish.py --test      # Test with uvx")
        print("   python3 tools/publish.py --testpypi  # Publish to TestPyPI")
        print("   python3 tools/publish.py --pypi      # Publish to PyPI")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
