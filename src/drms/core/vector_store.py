"""
Vector Store implementation using ChromaDB for document embeddings and search.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import openai
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, 
                 db_path: str = "./chroma_db",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 use_openai_embeddings: bool = False,
                 openai_api_key: Optional[str] = None):
        """
        Initialize vector store with ChromaDB backend.
        
        Args:
            db_path: Path to ChromaDB persistent storage
            embedding_model: Sentence transformer model name
            use_openai_embeddings: Whether to use OpenAI embeddings
            openai_api_key: OpenAI API key if using OpenAI embeddings
        """
        self.db_path = db_path
        self.use_openai_embeddings = use_openai_embeddings
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        if use_openai_embeddings and openai_api_key:
            openai.api_key = openai_api_key
            self.embedding_model = None
        else:
            # Force CPU usage to avoid MPS issues
            import torch
            device = "cpu"  # Force CPU to avoid MPS crashes
            self.embedding_model = SentenceTransformer(embedding_model, device=device)
        
        # Create collections for different types of documentation
        self.collections = {
            "docs": self._get_or_create_collection("documentation"),
            "api": self._get_or_create_collection("api_reference"),
            "examples": self._get_or_create_collection("code_examples"),
            "tutorials": self._get_or_create_collection("tutorials")
        }
        
        logger.info(f"VectorStore initialized with {len(self.collections)} collections")
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        try:
            return self.client.get_collection(name)
        except:
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
    
    async def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        if self.use_openai_embeddings:
            response = await openai.Embedding.acreate(
                model="text-embedding-ada-002",
                input=texts
            )
            return [item["embedding"] for item in response["data"]]
        else:
            # Use sentence transformers in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, self.embedding_model.encode, texts
            )
            return embeddings.tolist()
    
    async def add_documents(self, 
                          documents: List[Dict[str, Any]], 
                          collection_type: str = "docs") -> bool:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document dicts with 'content', 'metadata', 'id'
            collection_type: Type of collection ('docs', 'api', 'examples', 'tutorials')
        
        Returns:
            bool: Success status
        """
        try:
            if collection_type not in self.collections:
                logger.error(f"Unknown collection type: {collection_type}")
                return False
            
            collection = self.collections[collection_type]
            
            # Prepare data
            texts = [doc["content"] for doc in documents]
            ids = [doc["id"] for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]
            
            # Generate embeddings
            embeddings = await self._get_embeddings(texts)
            
            # Add to collection
            collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to {collection_type} collection")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False
    
    async def search_documents(self, 
                             query: str, 
                             collection_type: str = "docs",
                             n_results: int = 5,
                             filter_metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            collection_type: Collection to search
            n_results: Number of results to return
            filter_metadata: Metadata filters
        
        Returns:
            List of search results with scores
        """
        try:
            if collection_type not in self.collections:
                logger.error(f"Unknown collection type: {collection_type}")
                return []
            
            collection = self.collections[collection_type]
            
            # Generate query embedding
            query_embedding = await self._get_embeddings([query])
            
            # Search
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                where=filter_metadata,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity": 1 - results["distances"][0][i],  # Convert distance to similarity
                    "id": results["ids"][0][i] if "ids" in results else f"result_{i}"
                })
            
            logger.info(f"Found {len(formatted_results)} results for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def search_multi_collection(self, 
                                    query: str, 
                                    n_results: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """Search across all collections and return categorized results."""
        results = {}
        
        for collection_name in self.collections.keys():
            results[collection_name] = await self.search_documents(
                query=query,
                collection_type=collection_name,
                n_results=n_results
            )
        
        return results
    
    async def get_collection_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all collections."""
        stats = {}
        
        for name, collection in self.collections.items():
            try:
                count = collection.count()
                stats[name] = {
                    "document_count": count,
                    "collection_name": name
                }
            except Exception as e:
                stats[name] = {"error": str(e)}
        
        return stats
    
    async def delete_documents(self, 
                             doc_ids: List[str], 
                             collection_type: str = "docs") -> bool:
        """Delete documents by IDs."""
        try:
            if collection_type not in self.collections:
                return False
            
            collection = self.collections[collection_type]
            collection.delete(ids=doc_ids)
            
            logger.info(f"Deleted {len(doc_ids)} documents from {collection_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return False
    
    async def update_document(self, 
                            doc_id: str, 
                            content: str, 
                            metadata: Dict[str, Any],
                            collection_type: str = "docs") -> bool:
        """Update a single document."""
        try:
            # Delete old version
            await self.delete_documents([doc_id], collection_type)
            
            # Add new version
            return await self.add_documents([{
                "id": doc_id,
                "content": content,
                "metadata": metadata
            }], collection_type)
            
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            return False