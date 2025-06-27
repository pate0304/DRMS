"""
Documentation scraper for automatically discovering and indexing library documentation.
"""

import asyncio
import logging
import re
import hashlib
from typing import Dict, List, Optional, Any, Set
from urllib.parse import urljoin, urlparse
import aiohttp
from bs4 import BeautifulSoup
import requests
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class DocumentationScraper:
    """Scraper for library documentation with intelligent discovery."""
    
    def __init__(self, cache_dir: str = "./data/cache", vector_store=None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store = vector_store
        
        # Common documentation URL patterns
        self.doc_patterns = [
            "https://{}.readthedocs.io/",
            "https://docs.{}.com/",
            "https://{}.org/docs/",
            "https://{}.org/documentation/",
            "https://github.com/{}/wiki",
            "https://{}.dev/",
            "https://{}.js.org/",
        ]
        
        # Known documentation sites for popular libraries
        self.known_docs = {
            "react": "https://react.dev/",
            "vue": "https://vuejs.org/guide/",
            "angular": "https://angular.io/docs",
            "svelte": "https://svelte.dev/docs",
            "nextjs": "https://nextjs.org/docs",
            "nuxt": "https://nuxt.com/docs",
            "fastapi": "https://fastapi.tiangolo.com/",
            "django": "https://docs.djangoproject.com/",
            "flask": "https://flask.palletsprojects.com/",
            "express": "https://expressjs.com/",
            "nodejs": "https://nodejs.org/docs/",
            "requests": "https://requests.readthedocs.io/",
            "pandas": "https://pandas.pydata.org/docs/",
            "numpy": "https://numpy.org/doc/",
            "scipy": "https://docs.scipy.org/",
            "matplotlib": "https://matplotlib.org/stable/",
            "sklearn": "https://scikit-learn.org/stable/documentation.html",
            "tensorflow": "https://www.tensorflow.org/api_docs",
            "pytorch": "https://pytorch.org/docs/",
            "opencv": "https://docs.opencv.org/",
            "aws": "https://docs.aws.amazon.com/",
            "gcp": "https://cloud.google.com/docs",
            "azure": "https://docs.microsoft.com/azure/",
            "kubernetes": "https://kubernetes.io/docs/",
            "docker": "https://docs.docker.com/",
            "redis": "https://redis.io/documentation",
            "mongodb": "https://docs.mongodb.com/",
            "postgresql": "https://www.postgresql.org/docs/",
            "mysql": "https://dev.mysql.com/doc/",
            "tailwind": "https://tailwindcss.com/docs",
            "bootstrap": "https://getbootstrap.com/docs/",
            "material-ui": "https://mui.com/",
            "ant-design": "https://ant.design/docs/",
            "lodash": "https://lodash.com/docs/",
            "axios": "https://axios-http.com/docs/",
            "jest": "https://jestjs.io/docs/",
            "cypress": "https://docs.cypress.io/",
            "webpack": "https://webpack.js.org/concepts/",
            "vite": "https://vitejs.dev/guide/",
            "typescript": "https://www.typescriptlang.org/docs/",
        }
        
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "DRMS Documentation Scraper 1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _get_cache_path(self, library_name: str) -> Path:
        """Get cache file path for a library."""
        safe_name = re.sub(r'[^\w\-_.]', '_', library_name)
        return self.cache_dir / f"{safe_name}_docs.json"
    
    async def _discover_documentation_url(self, library_name: str) -> Optional[str]:
        """Automatically discover documentation URL for a library."""
        # Check known documentation sites first
        if library_name.lower() in self.known_docs:
            return self.known_docs[library_name.lower()]
        
        # Try common patterns
        for pattern in self.doc_patterns:
            try:
                url = pattern.format(library_name.lower())
                if await self._check_url_exists(url):
                    logger.info(f"Found documentation at: {url}")
                    return url
            except Exception:
                continue
        
        # Try searching GitHub for the library
        github_url = await self._search_github_docs(library_name)
        if github_url:
            return github_url
        
        logger.warning(f"Could not discover documentation URL for {library_name}")
        return None
    
    async def _check_url_exists(self, url: str) -> bool:
        """Check if a URL exists and returns valid content."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.head(url) as response:
                return response.status == 200
        except Exception:
            return False
    
    async def _search_github_docs(self, library_name: str) -> Optional[str]:
        """Search GitHub for library documentation."""
        try:
            # This is a simplified version - in production, you'd use GitHub API
            github_patterns = [
                f"https://github.com/{library_name}/{library_name}",
                f"https://github.com/{library_name}",
                f"https://{library_name}.github.io/",
            ]
            
            for pattern in github_patterns:
                if await self._check_url_exists(pattern):
                    return pattern
        except Exception as e:
            logger.debug(f"GitHub search failed for {library_name}: {e}")
        
        return None
    
    async def scrape_library(self, 
                           library_name: str, 
                           documentation_url: Optional[str] = None,
                           force_reindex: bool = False) -> Optional[Dict[str, Any]]:
        """
        Scrape and index a library's documentation.
        
        Args:
            library_name: Name of the library
            documentation_url: Optional direct URL to documentation
            force_reindex: Force reindexing even if cached
        
        Returns:
            Dictionary with scraping results
        """
        try:
            logger.info(f"Starting to scrape {library_name}")
            
            # Check cache first
            cache_path = self._get_cache_path(library_name)
            if cache_path.exists() and not force_reindex:
                logger.info(f"Using cached documentation for {library_name}")
                with open(cache_path, 'r') as f:
                    cached_data = json.load(f)
                
                # Add to vector store if not already there
                if self.vector_store:
                    await self._add_to_vector_store(cached_data, library_name)
                
                return cached_data
            
            # Discover documentation URL if not provided
            if not documentation_url:
                documentation_url = await self._discover_documentation_url(library_name)
                if not documentation_url:
                    raise ValueError(f"Could not find documentation for {library_name}")
            
            # Scrape the documentation
            async with self:
                scraped_data = await self._scrape_site(documentation_url, library_name)
            
            if not scraped_data:
                raise ValueError(f"Failed to scrape documentation from {documentation_url}")
            
            # Cache the results
            with open(cache_path, 'w') as f:
                json.dump(scraped_data, f, indent=2)
            
            # Add to vector store
            if self.vector_store:
                await self._add_to_vector_store(scraped_data, library_name)
            
            logger.info(f"Successfully scraped {library_name}: {len(scraped_data.get('pages', []))} pages")
            
            return {
                "library": library_name,
                "url": documentation_url,
                "pages_count": len(scraped_data.get('pages', [])),
                "chunks_count": sum(len(page.get('chunks', [])) for page in scraped_data.get('pages', [])),
                "last_updated": scraped_data.get('scraped_at')
            }
            
        except Exception as e:
            logger.error(f"Error scraping {library_name}: {e}")
            return None
    
    async def _scrape_site(self, base_url: str, library_name: str) -> Dict[str, Any]:
        """Scrape documentation site starting from base URL."""
        visited_urls: Set[str] = set()
        pages_data = []
        max_pages = 50  # Limit to prevent infinite scraping
        
        urls_to_visit = [base_url]
        
        while urls_to_visit and len(pages_data) < max_pages:
            current_url = urls_to_visit.pop(0)
            
            if current_url in visited_urls:
                continue
            
            try:
                page_data = await self._scrape_page(current_url, library_name)
                if page_data:
                    pages_data.append(page_data)
                    visited_urls.add(current_url)
                    
                    # Find additional URLs to scrape
                    if len(pages_data) < max_pages:
                        new_urls = await self._find_related_urls(current_url, base_url)
                        for url in new_urls:
                            if url not in visited_urls and url not in urls_to_visit:
                                urls_to_visit.append(url)
                
            except Exception as e:
                logger.warning(f"Failed to scrape {current_url}: {e}")
                continue
        
        return {
            "library": library_name,
            "base_url": base_url,
            "pages": pages_data,
            "scraped_at": asyncio.get_event_loop().time()
        }
    
    async def _scrape_page(self, url: str, library_name: str) -> Optional[Dict[str, Any]]:
        """Scrape a single page and extract content."""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract title
                title = soup.find('title')
                title_text = title.get_text().strip() if title else url
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extract main content (try common content selectors)
                content_selectors = [
                    'main', '.content', '.documentation', '.docs', 
                    '.main-content', '#content', 'article', '.page-content'
                ]
                
                content_element = None
                for selector in content_selectors:
                    content_element = soup.select_one(selector)
                    if content_element:
                        break
                
                if not content_element:
                    content_element = soup.find('body')
                
                if not content_element:
                    return None
                
                # Extract text content
                text_content = content_element.get_text()
                clean_content = self._clean_text(text_content)
                
                if len(clean_content.strip()) < 100:  # Skip pages with minimal content
                    return None
                
                # Extract code blocks
                code_blocks = []
                for code in content_element.find_all(['code', 'pre']):
                    code_text = code.get_text().strip()
                    if len(code_text) > 10:  # Only meaningful code blocks
                        code_blocks.append(code_text)
                
                # Chunk the content for better searchability
                chunks = self._chunk_content(clean_content, url, library_name)
                
                return {
                    "url": url,
                    "title": title_text,
                    "content": clean_content,
                    "code_blocks": code_blocks,
                    "chunks": chunks,
                    "library": library_name
                }
                
        except Exception as e:
            logger.warning(f"Error scraping page {url}: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text content."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere
        text = re.sub(r'[^\w\s\.\,\!\?\:\;\(\)\-\=\+\*\/\\\[\]\{\}\"\'`]', '', text)
        return text.strip()
    
    def _chunk_content(self, content: str, url: str, library_name: str) -> List[Dict[str, Any]]:
        """Chunk content into smaller pieces for better retrieval."""
        # Simple sentence-based chunking
        sentences = re.split(r'[.!?]+', content)
        chunks = []
        current_chunk = ""
        max_chunk_size = 500  # characters
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_chunk) + len(sentence) > max_chunk_size:
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "url": url,
                        "library": library_name,
                        "chunk_id": f"{library_name}_{len(chunks)}"
                    })
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk:
            chunks.append({
                "content": current_chunk.strip(),
                "url": url,
                "library": library_name,
                "chunk_id": f"{library_name}_{len(chunks)}"
            })
        
        return chunks
    
    async def _find_related_urls(self, current_url: str, base_url: str) -> List[str]:
        """Find related URLs to scrape from the current page."""
        try:
            async with self.session.get(current_url) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                urls = []
                base_domain = urlparse(base_url).netloc
                
                # Find all links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        full_url = urljoin(base_url, href)
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(current_url, href)
                    
                    # Only include URLs from the same domain and documentation-related paths
                    if (urlparse(full_url).netloc == base_domain and 
                        self._is_documentation_url(full_url)):
                        urls.append(full_url)
                
                return urls[:10]  # Limit number of URLs per page
                
        except Exception as e:
            logger.debug(f"Error finding related URLs for {current_url}: {e}")
            return []
    
    def _is_documentation_url(self, url: str) -> bool:
        """Check if URL appears to be documentation-related."""
        doc_indicators = [
            'doc', 'guide', 'tutorial', 'api', 'reference', 
            'manual', 'help', 'wiki', 'learn', 'getting-started'
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in doc_indicators)
    
    async def _add_to_vector_store(self, scraped_data: Dict[str, Any], library_name: str):
        """Add scraped data to vector store."""
        if not self.vector_store:
            return
        
        documents = []
        
        for page in scraped_data.get('pages', []):
            for chunk in page.get('chunks', []):
                doc_id = hashlib.md5(
                    f"{library_name}_{chunk['url']}_{chunk['chunk_id']}".encode()
                ).hexdigest()
                
                documents.append({
                    "id": doc_id,
                    "content": chunk['content'],
                    "metadata": {
                        "library": library_name,
                        "url": chunk['url'],
                        "title": page.get('title', ''),
                        "type": "documentation"
                    }
                })
            
            # Also add code blocks as examples
            for i, code_block in enumerate(page.get('code_blocks', [])):
                doc_id = hashlib.md5(
                    f"{library_name}_code_{page['url']}_{i}".encode()
                ).hexdigest()
                
                documents.append({
                    "id": doc_id,
                    "content": code_block,
                    "metadata": {
                        "library": library_name,
                        "url": page['url'],
                        "title": page.get('title', ''),
                        "type": "code_example"
                    }
                })
        
        # Add documents to appropriate collections
        if documents:
            docs = [doc for doc in documents if doc['metadata']['type'] == 'documentation']
            examples = [doc for doc in documents if doc['metadata']['type'] == 'code_example']
            
            if docs:
                await self.vector_store.add_documents(docs, "docs")
            if examples:
                await self.vector_store.add_documents(examples, "examples")
            
            logger.info(f"Added {len(docs)} docs and {len(examples)} examples to vector store")