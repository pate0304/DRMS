#!/usr/bin/env python3
"""
DRMS Demo Script
Demonstrates the core functionality of DRMS documentation search.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from drms.core.vector_store import VectorStore
from drms.scraper.doc_scraper import DocumentationScraper
from drms.config.settings import Settings

async def demo_drms():
    """Demonstrate DRMS functionality."""
    print("🚀 DRMS Documentation RAG Demo")
    print("=" * 50)
    
    # Initialize components
    print("Initializing DRMS components...")
    settings = Settings()
    
    vector_store = VectorStore(
        db_path="./demo_chroma_db",
        use_openai_embeddings=False  # Use local embeddings for demo
    )
    
    scraper = DocumentationScraper(
        cache_dir="./demo_cache",
        vector_store=vector_store
    )
    
    # Demo 1: Scrape a small documentation site
    print("\n📚 Demo 1: Scraping React documentation...")
    try:
        result = await scraper.scrape_library("react", "https://react.dev/")
        if result:
            print(f"✅ Successfully scraped React documentation")
            print(f"   - Pages indexed: {result['pages_count']}")
            print(f"   - Text chunks: {result['chunks_count']}")
        else:
            print("❌ Failed to scrape React documentation")
    except Exception as e:
        print(f"❌ Error scraping React: {e}")
    
    # Demo 2: Search functionality
    print("\n🔍 Demo 2: Searching documentation...")
    
    search_queries = [
        "How to use useState hook?",
        "React component lifecycle",
        "JSX syntax rules",
        "React hooks best practices"
    ]
    
    for query in search_queries:
        print(f"\nSearching: '{query}'")
        try:
            results = await vector_store.search_documents(
                query=query,
                collection_type="docs",
                n_results=2
            )
            
            if results:
                print(f"  ✅ Found {len(results)} results")
                for i, result in enumerate(results):
                    similarity = result.get('similarity', 0)
                    url = result['metadata'].get('url', 'N/A')
                    content_preview = result['content'][:100].replace('\n', ' ')
                    print(f"    {i+1}. Similarity: {similarity:.2f}")
                    print(f"       URL: {url}")
                    print(f"       Preview: {content_preview}...")
            else:
                print("  ❌ No results found")
                
        except Exception as e:
            print(f"  ❌ Search error: {e}")
    
    # Demo 3: Code examples search
    print("\n💻 Demo 3: Searching code examples...")
    
    code_queries = [
        "useState example",
        "useEffect cleanup",
        "React functional component"
    ]
    
    for query in code_queries:
        print(f"\nSearching code: '{query}'")
        try:
            results = await vector_store.search_documents(
                query=query,
                collection_type="examples",
                n_results=1
            )
            
            if results:
                print(f"  ✅ Found {len(results)} code examples")
                for result in results:
                    print(f"     Code snippet:")
                    print(f"     {result['content'][:150]}...")
            else:
                print("  ❌ No code examples found")
                
        except Exception as e:
            print(f"  ❌ Code search error: {e}")
    
    # Demo 4: Vector store statistics
    print("\n📊 Demo 4: Vector store statistics...")
    try:
        stats = await vector_store.get_collection_stats()
        print("Collection statistics:")
        for collection_name, collection_stats in stats.items():
            if "error" not in collection_stats:
                count = collection_stats.get("document_count", 0)
                print(f"  - {collection_name}: {count} documents")
    except Exception as e:
        print(f"❌ Stats error: {e}")
    
    # Demo 5: Multi-collection search
    print("\n🔄 Demo 5: Multi-collection search...")
    try:
        multi_results = await vector_store.search_multi_collection(
            query="React component props",
            n_results=1
        )
        
        print("Results across all collections:")
        for collection_name, results in multi_results.items():
            if results:
                print(f"  - {collection_name}: {len(results)} results")
                for result in results:
                    similarity = result.get('similarity', 0)
                    print(f"    Similarity: {similarity:.2f}")
            else:
                print(f"  - {collection_name}: No results")
                
    except Exception as e:
        print(f"❌ Multi-search error: {e}")
    
    print("\n🎉 DRMS Demo completed!")
    print("\nTo use DRMS in production:")
    print("1. Run: python mcp_server.py (for MCP protocol)")
    print("2. Run: python drms_api.py (for REST API)")
    print("3. Configure your AI coding tool to use DRMS")

if __name__ == "__main__":
    try:
        asyncio.run(demo_drms())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)