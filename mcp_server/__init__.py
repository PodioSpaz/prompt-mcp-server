"""
MCP Server Package for Amazon Q Developer CLI

A Model Context Protocol (MCP) server that manages prompt files (*.md) from local directories.
"""

__version__ = "2.0.1"
__author__ = "Amazon Q Developer CLI Team"

from .prompt_mcp_server import main, main_sync, PromptMCPServer

__all__ = ["main", "main_sync", "PromptMCPServer"]
