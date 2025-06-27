#!/usr/bin/env python3
"""
DRMS REST API
FastAPI-based REST API for universal integration with AI coding tools.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from drms.core.vector_store import VectorStore
from drms.scraper.doc_scraper import DocumentationScraper
from drms.config.settings import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("drms-api")

# Global instances
vector_store: Optional[VectorStore] = None
scraper: Optional[DocumentationScraper] = None
settings: Optional[Settings] = None

# Pydantic models for API
class SearchRequest(BaseModel):
    query: str
    library: Optional[str] = None
    doc_type: str = "docs"
    max_results: int = 5

class SearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    library_filter: Optional[str] = None

class DiscoverRequest(BaseModel):
    library_name: str
    documentation_url: Optional[str] = None
    force_reindex: bool = False

class DiscoverResponse(BaseModel):
    success: bool
    library: str
    message: str
    pages_count: Optional[int] = None
    chunks_count: Optional[int] = None

class LibraryInfoResponse(BaseModel):
    libraries: Dict[str, Dict[str, Any]]
    total_documents: int

class HealthResponse(BaseModel):
    status: str
    version: str
    vector_store_status: str
    collections: Dict[str, int]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global vector_store, scraper, settings
    
    # Startup
    logger.info("Starting DRMS API server...")
    
    settings = Settings()
    
    # Initialize vector store
    vector_store = VectorStore(
        db_path=settings.vector_db_path,
        use_openai_embeddings=settings.use_openai_embeddings,
        openai_api_key=settings.openai_api_key
    )
    
    # Initialize scraper
    scraper = DocumentationScraper(
        cache_dir=settings.cache_dir,
        vector_store=vector_store
    )
    
    logger.info("DRMS API server initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down DRMS API server...")

# Create FastAPI app
app = FastAPI(
    title="DRMS API",
    description="Documentation RAG MCP Server REST API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "DRMS API",
        "version": "1.0.0",
        "description": "Documentation RAG MCP Server REST API",
        "endpoints": {
            "search": "/search",
            "discover": "/discover",
            "libraries": "/libraries",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        stats = await vector_store.get_collection_stats()
        collections = {name: stats[name].get("document_count", 0) for name in stats}
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            vector_store_status="connected",
            collections=collections
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/search", response_model=SearchResponse)
async def search_documentation(request: SearchRequest):
    """Search documentation across indexed libraries."""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not available")
        
        # Build metadata filter
        filter_metadata = {}
        if request.library:
            filter_metadata["library"] = request.library
        
        # Search vector store
        results = await vector_store.search_documents(
            query=request.query,
            collection_type=request.doc_type,
            n_results=request.max_results,
            filter_metadata=filter_metadata if filter_metadata else None
        )
        
        # Try auto-discovery if no results and library specified
        if not results and request.library and scraper:
            logger.info(f"No results found, attempting auto-discovery for {request.library}")
            await scraper.scrape_library(request.library)
            
            # Retry search
            results = await vector_store.search_documents(
                query=request.query,
                collection_type=request.doc_type,
                n_results=request.max_results,
                filter_metadata=filter_metadata
            )
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            library_filter=request.library
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/discover", response_model=DiscoverResponse)
async def discover_library(request: DiscoverRequest):
    """Discover and index a new library's documentation."""
    try:
        if not scraper:
            raise HTTPException(status_code=503, detail="Scraper not available")
        
        result = await scraper.scrape_library(
            library_name=request.library_name,
            documentation_url=request.documentation_url,
            force_reindex=request.force_reindex
        )
        
        if result:
            return DiscoverResponse(
                success=True,
                library=request.library_name,
                message=f"Successfully indexed {request.library_name}",
                pages_count=result.get("pages_count"),
                chunks_count=result.get("chunks_count")
            )
        else:
            return DiscoverResponse(
                success=False,
                library=request.library_name,
                message=f"Failed to discover or index {request.library_name}"
            )
            
    except Exception as e:
        logger.error(f"Discovery error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/libraries", response_model=LibraryInfoResponse)
async def get_libraries_info():
    """Get information about all indexed libraries."""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not available")
        
        stats = await vector_store.get_collection_stats()
        
        # Get unique libraries from vector store
        # This is a simplified approach - in production, you'd maintain a libraries index
        libraries = {}
        total_docs = 0
        
        for collection_name, collection_stats in stats.items():
            if "error" not in collection_stats:
                doc_count = collection_stats.get("document_count", 0)
                total_docs += doc_count
                libraries[collection_name] = {
                    "document_count": doc_count,
                    "collection_type": collection_name
                }
        
        return LibraryInfoResponse(
            libraries=libraries,
            total_documents=total_docs
        )
        
    except Exception as e:
        logger.error(f"Libraries info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/{query}")
async def quick_search(query: str, library: Optional[str] = None, max_results: int = 5):
    """Quick search endpoint via GET request."""
    request = SearchRequest(
        query=query,
        library=library,
        max_results=max_results
    )
    return await search_documentation(request)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time search."""
    await websocket.accept()
    
    try:
        while True:
            # Receive search query
            data = await websocket.receive_json()
            
            if "query" not in data:
                await websocket.send_json({
                    "error": "Missing 'query' field",
                    "type": "error"
                })
                continue
            
            try:
                # Create search request
                request = SearchRequest(**data)
                
                # Send search start notification
                await websocket.send_json({
                    "type": "search_start",
                    "query": request.query
                })
                
                # Perform search
                if not vector_store:
                    raise ValueError("Vector store not available")
                
                filter_metadata = {}
                if request.library:
                    filter_metadata["library"] = request.library
                
                results = await vector_store.search_documents(
                    query=request.query,
                    collection_type=request.doc_type,
                    n_results=request.max_results,
                    filter_metadata=filter_metadata if filter_metadata else None
                )
                
                # Send results
                await websocket.send_json({
                    "type": "search_results",
                    "query": request.query,
                    "results": results,
                    "total_results": len(results)
                })
                
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "error": str(e)
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

@app.get("/examples/{library}")
async def get_code_examples(library: str, query: Optional[str] = None, max_results: int = 5):
    """Get code examples for a specific library."""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not available")
        
        search_query = f"{library} code example"
        if query:
            search_query += f" {query}"
        
        results = await vector_store.search_documents(
            query=search_query,
            collection_type="examples",
            n_results=max_results,
            filter_metadata={"library": library}
        )
        
        return {
            "library": library,
            "query": query,
            "examples": results,
            "total_examples": len(results)
        }
        
    except Exception as e:
        logger.error(f"Examples error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "detail": str(exc)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DRMS REST API Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    uvicorn.run(
        "drms_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )