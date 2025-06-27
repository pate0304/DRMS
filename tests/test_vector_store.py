"""
Test suite for VectorStore functionality.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drms.core.vector_store import VectorStore

class TestVectorStore:
    """Test VectorStore functionality."""
    
    @pytest.fixture
    async def vector_store(self):
        """Create a temporary vector store for testing."""
        temp_dir = tempfile.mkdtemp()
        store = VectorStore(
            db_path=temp_dir,
            use_openai_embeddings=False  # Use local embeddings for testing
        )
        yield store
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_add_documents(self, vector_store):
        """Test adding documents to vector store."""
        documents = [
            {
                "id": "doc1",
                "content": "React is a JavaScript library for building user interfaces",
                "metadata": {"library": "react", "type": "documentation"}
            },
            {
                "id": "doc2", 
                "content": "useState is a React Hook that lets you add state to functional components",
                "metadata": {"library": "react", "type": "api"}
            }
        ]
        
        result = await vector_store.add_documents(documents, "docs")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_search_documents(self, vector_store):
        """Test searching documents."""
        # Add test documents first
        documents = [
            {
                "id": "react_doc",
                "content": "React hooks like useState and useEffect are powerful features",
                "metadata": {"library": "react"}
            }
        ]
        
        await vector_store.add_documents(documents, "docs")
        
        # Search for documents
        results = await vector_store.search_documents("React hooks useState", "docs", n_results=1)
        
        assert len(results) > 0
        assert "react" in results[0]["content"].lower()
        assert "similarity" in results[0]
    
    @pytest.mark.asyncio
    async def test_collection_stats(self, vector_store):
        """Test getting collection statistics."""
        # Add some documents
        documents = [
            {
                "id": "test_doc",
                "content": "Test document content",
                "metadata": {"library": "test"}
            }
        ]
        
        await vector_store.add_documents(documents, "docs")
        
        stats = await vector_store.get_collection_stats()
        
        assert "docs" in stats
        assert stats["docs"]["document_count"] >= 1
    
    @pytest.mark.asyncio
    async def test_multi_collection_search(self, vector_store):
        """Test searching across multiple collections."""
        # Add documents to different collections
        doc_documents = [
            {
                "id": "doc1",
                "content": "Documentation about React components",
                "metadata": {"library": "react"}
            }
        ]
        
        example_documents = [
            {
                "id": "example1",
                "content": "function Component() { return <div>Hello</div>; }",
                "metadata": {"library": "react", "language": "javascript"}
            }
        ]
        
        await vector_store.add_documents(doc_documents, "docs")
        await vector_store.add_documents(example_documents, "examples")
        
        results = await vector_store.search_multi_collection("React components")
        
        assert "docs" in results
        assert "examples" in results
        assert len(results["docs"]) > 0 or len(results["examples"]) > 0

if __name__ == "__main__":
    pytest.main([__file__])