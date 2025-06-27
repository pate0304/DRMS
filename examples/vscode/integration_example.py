"""
DRMS + VS Code Integration Example
Using the REST API for custom integrations
"""

import requests
import json
from typing import List, Dict, Any

class DRMSClient:
    """Client for interacting with DRMS REST API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def search_docs(self, query: str, library: str = None, max_results: int = 5) -> Dict[str, Any]:
        """Search documentation."""
        payload = {
            "query": query,
            "library": library,
            "max_results": max_results
        }
        
        response = self.session.post(f"{self.base_url}/search", json=payload)
        response.raise_for_status()
        return response.json()
    
    def discover_library(self, library_name: str, doc_url: str = None) -> Dict[str, Any]:
        """Discover and index a new library."""
        payload = {
            "library_name": library_name,
            "documentation_url": doc_url
        }
        
        response = self.session.post(f"{self.base_url}/discover", json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_libraries(self) -> Dict[str, Any]:
        """Get information about indexed libraries."""
        response = self.session.get(f"{self.base_url}/libraries")
        response.raise_for_status()
        return response.json()
    
    def get_code_examples(self, library: str, query: str = None) -> Dict[str, Any]:
        """Get code examples for a library."""
        params = {"query": query} if query else {}
        response = self.session.get(f"{self.base_url}/examples/{library}", params=params)
        response.raise_for_status()
        return response.json()

# Example usage
def main():
    # Initialize client
    client = DRMSClient()
    
    # Search for React hooks documentation
    print("Searching for React hooks...")
    results = client.search_docs("useState useEffect hooks", library="react")
    print(f"Found {results['total_results']} results")
    
    for i, result in enumerate(results['results'][:2]):
        print(f"\n--- Result {i+1} ---")
        print(f"Library: {result['metadata']['library']}")
        print(f"URL: {result['metadata']['url']}")
        print(f"Content: {result['content'][:200]}...")
    
    # Discover a new library
    print("\nDiscovering Tailwind CSS...")
    discovery = client.discover_library("tailwindcss", "https://tailwindcss.com/docs")
    print(f"Discovery result: {discovery['message']}")
    
    # Get code examples
    print("\nGetting FastAPI examples...")
    examples = client.get_code_examples("fastapi", "routing")
    print(f"Found {examples['total_examples']} examples")
    
    # Get library info
    print("\nGetting library information...")
    libraries = client.get_libraries()
    print(f"Total documents indexed: {libraries['total_documents']}")
    print("Libraries:", list(libraries['libraries'].keys()))

if __name__ == "__main__":
    main()