"""
VS Code / Generic Integration Example
Using DRMS REST API for any development environment
"""

import requests
import json

class DRMSClient:
    """Simple DRMS client for VS Code and other tools."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def search_docs(self, query, library=None, max_results=5):
        """Search documentation using DRMS."""
        response = requests.post(f"{self.base_url}/search", json={
            "query": query,
            "library": library,
            "max_results": max_results
        })
        return response.json()
    
    def discover_library(self, library_name):
        """Discover and index a new library."""
        response = requests.post(f"{self.base_url}/discover", json={
            "library_name": library_name
        })
        return response.json()
    
    def health_check(self):
        """Check if DRMS is running."""
        try:
            response = requests.get(f"{self.base_url}/health")
            return response.json()
        except:
            return {"status": "offline"}

# Usage Example
if __name__ == "__main__":
    drms = DRMSClient()
    
    # Check if DRMS is running
    health = drms.health_check()
    print(f"DRMS Status: {health.get('status', 'unknown')}")
    
    if health.get('status') == 'healthy':
        # Search for React hooks documentation
        results = drms.search_docs("useState React hooks", library="react")
        print(f"Found {results['total_results']} results")
        
        for result in results['results'][:2]:
            print(f"\\n--- {result['metadata']['library']} ---")
            print(result['content'][:200] + "...")
    else:
        print("Start DRMS with: npx @drms/mcp-server api")