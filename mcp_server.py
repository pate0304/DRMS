#!/usr/bin/env python3
"""
DRMS - Documentation RAG MCP Server
Main MCP server implementation for real-time documentation search and retrieval.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from drms.core.vector_store import VectorStore
from drms.scraper.doc_scraper import DocumentationScraper
from drms.config.settings import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("drms-mcp-server")

class DRMSServer:
    """DRMS MCP Server for documentation search and retrieval."""
    
    def __init__(self):
        self.settings = Settings()
        self.vector_store: Optional[VectorStore] = None
        self.scraper: Optional[DocumentationScraper] = None
        self.server = Server("drms")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name="search_documentation",
                    description="Search documentation for libraries and frameworks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for documentation"
                            },
                            "library": {
                                "type": "string",
                                "description": "Specific library/framework to search (optional)"
                            },
                            "doc_type": {
                                "type": "string",
                                "enum": ["docs", "api", "examples", "tutorials"],
                                "description": "Type of documentation to search"
                            },
                            "max_results": {
                                "type": "integer",
                                "default": 5,
                                "description": "Maximum number of results to return"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="discover_library",
                    description="Automatically discover and index a new library's documentation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "library_name": {
                                "type": "string",
                                "description": "Name of the library to discover"
                            },
                            "documentation_url": {
                                "type": "string",
                                "description": "Optional: Direct URL to documentation"
                            },
                            "force_reindex": {
                                "type": "boolean",
                                "default": False,
                                "description": "Force reindexing even if library exists"
                            }
                        },
                        "required": ["library_name"]
                    }
                ),
                types.Tool(
                    name="get_library_info",
                    description="Get information about indexed libraries",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "library": {
                                "type": "string",
                                "description": "Specific library name (optional)"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="search_code_examples",
                    description="Search for specific code examples and patterns",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Description of the code example needed"
                            },
                            "language": {
                                "type": "string",
                                "description": "Programming language (optional)"
                            },
                            "library": {
                                "type": "string",
                                "description": "Specific library/framework (optional)"
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> List[types.TextContent]:
            """Handle tool calls."""
            try:
                if name == "search_documentation":
                    return await self._search_documentation(arguments)
                elif name == "discover_library":
                    return await self._discover_library(arguments)
                elif name == "get_library_info":
                    return await self._get_library_info(arguments)
                elif name == "search_code_examples":
                    return await self._search_code_examples(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            
            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
    
    async def initialize(self):
        """Initialize the DRMS server components."""
        try:
            logger.info("Initializing DRMS server...")
            
            # Initialize vector store
            self.vector_store = VectorStore(
                db_path=self.settings.vector_db_path,
                use_openai_embeddings=self.settings.use_openai_embeddings,
                openai_api_key=self.settings.openai_api_key
            )
            
            # Initialize scraper
            self.scraper = DocumentationScraper(
                cache_dir=self.settings.cache_dir,
                vector_store=self.vector_store
            )
            
            # Load pre-populated libraries
            await self._load_popular_libraries()
            
            logger.info("DRMS server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize DRMS server: {e}")
            raise
    
    async def _load_popular_libraries(self):
        """Load popular libraries that are pre-configured."""
        popular_libraries = [
            {"name": "react", "url": "https://react.dev/"},
            {"name": "vue", "url": "https://vuejs.org/guide/"},
            {"name": "nextjs", "url": "https://nextjs.org/docs"},
            {"name": "fastapi", "url": "https://fastapi.tiangolo.com/"},
            {"name": "express", "url": "https://expressjs.com/"},
            {"name": "django", "url": "https://docs.djangoproject.com/"},
            {"name": "flask", "url": "https://flask.palletsprojects.com/"},
            {"name": "requests", "url": "https://requests.readthedocs.io/"},
            {"name": "pandas", "url": "https://pandas.pydata.org/docs/"},
            {"name": "numpy", "url": "https://numpy.org/doc/"}
        ]
        
        logger.info("Loading popular libraries...")
        
        for library in popular_libraries:
            try:
                # Check if library already exists
                stats = await self.vector_store.get_collection_stats()
                library_exists = any(
                    library["name"] in str(collection_stats) 
                    for collection_stats in stats.values()
                )
                
                if not library_exists:
                    logger.info(f"Pre-loading {library['name']}...")
                    await self.scraper.scrape_library(
                        library["name"], 
                        library["url"]
                    )
                    
            except Exception as e:
                logger.warning(f"Failed to pre-load {library['name']}: {e}")
        
        logger.info("Popular libraries loading completed")
    
    async def _search_documentation(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Search documentation based on query."""
        query = args["query"]
        library = args.get("library")
        doc_type = args.get("doc_type", "docs")
        max_results = args.get("max_results", 5)
        
        # Add library filter if specified
        filter_metadata = {}
        if library:
            filter_metadata["library"] = library
        
        # Search vector store
        results = await self.vector_store.search_documents(
            query=query,
            collection_type=doc_type,
            n_results=max_results,
            filter_metadata=filter_metadata if filter_metadata else None
        )
        
        if not results:
            # Try to discover the library if not found
            if library:
                await self._auto_discover_library(library)
                # Retry search after discovery
                results = await self.vector_store.search_documents(
                    query=query,
                    collection_type=doc_type,
                    n_results=max_results,
                    filter_metadata=filter_metadata
                )
        
        # Format results
        if results:
            formatted_results = []
            for i, result in enumerate(results, 1):
                metadata = result.get("metadata", {})
                lib_name = metadata.get("library", "Unknown")
                url = metadata.get("url", "")
                similarity = result.get("similarity", 0)
                
                formatted_results.append(
                    f"**Result {i}** (Similarity: {similarity:.2f})\n"
                    f"**Library:** {lib_name}\n"
                    f"**URL:** {url}\n"
                    f"**Content:**\n{result['content']}\n"
                    f"{'=' * 50}\n"
                )
            
            response = f"Found {len(results)} documentation results for: '{query}'\n\n" + "\n".join(formatted_results)
        else:
            response = f"No documentation found for query: '{query}'"
            if library:
                response += f" in library: '{library}'"
        
        return [types.TextContent(type="text", text=response)]
    
    async def _discover_library(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Discover and index a new library."""
        library_name = args["library_name"]
        doc_url = args.get("documentation_url")
        force_reindex = args.get("force_reindex", False)
        
        try:
            result = await self.scraper.scrape_library(
                library_name=library_name,
                documentation_url=doc_url,
                force_reindex=force_reindex
            )
            
            if result:
                response = f"Successfully discovered and indexed '{library_name}' documentation!"
                response += f"\nIndexed {result.get('pages_count', 0)} pages"
                response += f"\nAdded {result.get('chunks_count', 0)} documentation chunks"
            else:
                response = f"Failed to discover library '{library_name}'. Please check the library name or provide a documentation URL."
        
        except Exception as e:
            response = f"Error discovering library '{library_name}': {str(e)}"
        
        return [types.TextContent(type="text", text=response)]
    
    async def _get_library_info(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Get information about indexed libraries."""
        library = args.get("library")
        
        stats = await self.vector_store.get_collection_stats()
        
        if library:
            # Search for specific library info
            results = await self.vector_store.search_documents(
                query=f"{library} documentation",
                collection_type="docs",
                n_results=1,
                filter_metadata={"library": library}
            )
            
            if results:
                metadata = results[0].get("metadata", {})
                response = f"**Library:** {library}\n"
                response += f"**Description:** {metadata.get('description', 'N/A')}\n"
                response += f"**Version:** {metadata.get('version', 'N/A')}\n"
                response += f"**URL:** {metadata.get('url', 'N/A')}\n"
                response += f"**Last Updated:** {metadata.get('last_updated', 'N/A')}\n"
            else:
                response = f"Library '{library}' not found in index."
        else:
            # Return general statistics
            response = "**DRMS Library Statistics:**\n\n"
            for collection_name, collection_stats in stats.items():
                if "error" not in collection_stats:
                    response += f"**{collection_name.title()}:** {collection_stats['document_count']} documents\n"
        
        return [types.TextContent(type="text", text=response)]
    
    async def _search_code_examples(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Search for code examples."""
        query = args["query"]
        language = args.get("language")
        library = args.get("library")
        
        # Build enhanced query for code examples
        enhanced_query = f"code example {query}"
        if language:
            enhanced_query += f" {language}"
        if library:
            enhanced_query += f" {library}"
        
        # Search in examples collection
        filter_metadata = {}
        if library:
            filter_metadata["library"] = library
        if language:
            filter_metadata["language"] = language
        
        results = await self.vector_store.search_documents(
            query=enhanced_query,
            collection_type="examples",
            n_results=3,
            filter_metadata=filter_metadata if filter_metadata else None
        )
        
        # Also search in general docs for code patterns
        if not results:
            results = await self.vector_store.search_documents(
                query=enhanced_query,
                collection_type="docs",
                n_results=3,
                filter_metadata=filter_metadata if filter_metadata else None
            )
        
        if results:
            formatted_results = []
            for i, result in enumerate(results, 1):
                metadata = result.get("metadata", {})
                lib_name = metadata.get("library", "Unknown")
                lang = metadata.get("language", "")
                
                formatted_results.append(
                    f"**Example {i}**\n"
                    f"**Library:** {lib_name}\n"
                    f"**Language:** {lang}\n"
                    f"**Code:**\n```{lang.lower() if lang else ''}\n{result['content']}\n```\n"
                    f"{'=' * 40}\n"
                )
            
            response = f"Found {len(results)} code examples for: '{query}'\n\n" + "\n".join(formatted_results)
        else:
            response = f"No code examples found for: '{query}'"
        
        return [types.TextContent(type="text", text=response)]
    
    async def _auto_discover_library(self, library_name: str):
        """Automatically discover a library if not found."""
        try:
            logger.info(f"Auto-discovering library: {library_name}")
            await self.scraper.scrape_library(library_name)
        except Exception as e:
            logger.warning(f"Auto-discovery failed for {library_name}: {e}")

async def main():
    """Main entry point for the DRMS MCP server."""
    drms_server = DRMSServer()
    
    # Initialize server
    await drms_server.initialize()
    
    # Run server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await drms_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="drms",
                server_version="1.0.0",
                capabilities=drms_server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("DRMS server stopped by user")
    except Exception as e:
        logger.error(f"DRMS server failed: {e}")
        sys.exit(1)