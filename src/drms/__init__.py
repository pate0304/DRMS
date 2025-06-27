"""
DRMS - Documentation RAG MCP Server
A powerful MCP server for real-time documentation retrieval and AI integration.
"""

__version__ = "1.0.0"
__author__ = "DRMS Team"
__description__ = "Documentation RAG MCP Server for AI Coding Tools"

from .cli import cli

def main():
    """Entry point for CLI"""
    cli()