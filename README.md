# 🚀 DRMS - Documentation RAG MCP Server

**Real-time documentation access for AI coding tools with automatic library discovery**

DRMS (Documentation RAG MCP Server) provides your AI coding assistants with instant access to up-to-date documentation from any library or framework. No more outdated examples or deprecated APIs!

## ✨ Key Features

🔥 **Pre-populated Documentation**
- React, Next.js, Vue, Python, FastAPI, Express, and 40+ popular libraries
- Ready-to-use without any setup

🧠 **Intelligent Search**
- Vector-based semantic search using ChromaDB
- Context-aware documentation retrieval
- Code example extraction and categorization

🚀 **Dynamic Library Discovery** 
- Search for unknown library → system finds and indexes it automatically
- Permanent caching for future searches
- Smart URL discovery for documentation sites

⚡ **Universal Integration**
- **MCP Protocol**: Works with Cursor, Windsurf, Claude Dev
- **REST API**: Works with any tool via HTTP
- **WebSocket**: Real-time streaming search
- **Python SDK**: Direct integration

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- OpenAI API key (optional, for better embeddings)

### Quick Start

```bash
# Clone the repository
git clone <your-repo-url>
cd DRMS

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-minimal.txt  # Core dependencies
# OR pip install -r requirements.txt     # Full dependencies

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings (OpenAI key optional)

# Test installation
python examples/demo_search.py

# Start MCP server (for Cursor/Windsurf)
python mcp_server.py

# OR start REST API server (for universal access)
python drms_api.py --host localhost --port 8000
```

### ✅ Verified Installation

DRMS has been **tested and verified** on:
- **Python 3.13.3** on macOS ARM64
- **All core dependencies** installed successfully
- **MCP server** syntax validated
- **REST API** health endpoints functional
- **Basic functionality** tests passing

## 🎯 Integration Guides

### Cursor Integration

1. Install DRMS and start the MCP server
2. Configure Cursor MCP settings:
   ```json
   {
     "mcpServers": {
       "drms": {
         "command": "python",
         "args": ["mcp_server.py"],
         "cwd": "/path/to/DRMS"
       }
     }
   }
   ```
3. Start using documentation search in Cursor!

### Windsurf Integration

1. Configure Windsurf MCP settings (see `examples/windsurf/mcp_config.json`)
2. Restart Windsurf
3. Use DRMS tools in your development workflow

### VS Code / Generic Integration

Use the REST API for custom integrations:

```python
import requests

# Search documentation
response = requests.post("http://localhost:8000/search", json={
    "query": "How to use useState in React?",
    "library": "react",
    "max_results": 5
})

results = response.json()
print(f"Found {results['total_results']} results")
```

## 🔧 Usage Examples

### Search Documentation
```python
# Via MCP tools in your AI coding assistant:
search_documentation("React hooks useState", library="react")
search_documentation("FastAPI authentication", max_results=3)
search_documentation("pandas DataFrame operations")
```

### Discover New Libraries
```python
# Automatically find and index documentation
discover_library("tailwindcss")
discover_library("pytest", "https://docs.pytest.org/")
```

### Get Code Examples
```python
# Find specific code patterns
search_code_examples("async function example", language="javascript")
search_code_examples("database migration", library="django")
```

### REST API Usage
```bash
# Quick search via GET
curl "http://localhost:8000/search/React%20useState?library=react"

# Advanced search via POST
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "FastAPI dependency injection", "max_results": 3}'

# Discover new library
curl -X POST "http://localhost:8000/discover" \
  -H "Content-Type: application/json" \
  -d '{"library_name": "streamlit"}'
```

## 📊 API Reference

### MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_documentation` | Search docs across libraries | `query`, `library?`, `doc_type?`, `max_results?` |
| `discover_library` | Index new library docs | `library_name`, `documentation_url?`, `force_reindex?` |
| `get_library_info` | Get indexed library info | `library?` |
| `search_code_examples` | Find code examples | `query`, `language?`, `library?` |

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search` | POST | Search documentation |
| `/discover` | POST | Discover new library |
| `/libraries` | GET | Get library info |
| `/examples/{library}` | GET | Get code examples |
| `/health` | GET | Health check |
| `/ws` | WebSocket | Real-time search |

## ⚙️ Configuration

### Environment Variables

```bash
# OpenAI (optional - for better embeddings)
OPENAI_API_KEY=your_key_here

# Vector Database
DRMS_VECTOR_DB_PATH=./chroma_db
DRMS_USE_OPENAI_EMBEDDINGS=false

# Scraping Settings
DRMS_MAX_PAGES_PER_LIBRARY=50
DRMS_SCRAPING_DELAY=1.0

# API Settings
DRMS_API_HOST=localhost
DRMS_API_PORT=8000

# Performance
DRMS_CHUNK_SIZE=500
DRMS_MAX_RESULTS=20
```

### Pre-populated Libraries

DRMS comes with documentation for these popular libraries:

**Frontend Frameworks:**
- React, Next.js, Vue, Nuxt, Angular, Svelte
- Tailwind CSS, Bootstrap, Material-UI, Ant Design

**Backend Frameworks:**
- FastAPI, Django, Flask, Express, Node.js

**Python Libraries:**
- Requests, Pandas, NumPy, SciPy, Matplotlib
- Scikit-learn, TensorFlow, PyTorch, OpenCV

**Development Tools:**
- TypeScript, Jest, Cypress, Webpack, Vite
- Docker, Kubernetes, AWS, GCP, Azure

**Databases:**
- PostgreSQL, MySQL, MongoDB, Redis

## 🎛️ Advanced Features

### Custom Documentation Sources

Add your own documentation sources:

```python
# Add private/internal documentation
await scraper.scrape_library(
    "internal-api", 
    "https://internal-docs.company.com/api/"
)
```

### Performance Optimization

```python
# Use OpenAI embeddings for better performance
settings = Settings(
    use_openai_embeddings=True,
    openai_api_key="your-key"
)

# Adjust chunk size for better retrieval
settings.chunk_size = 300  # Smaller chunks for more precise results
```

### Filtering and Search Options

```python
# Search specific documentation types
search_documentation("authentication", doc_type="api")
search_documentation("tutorial", doc_type="tutorials")

# Filter by library version or language
search_documentation("hooks", library="react", filter={"version": "18.x"})
```

## 🧪 Testing

### ✅ Verified Test Results

**All core functionality has been tested and verified:**

```bash
# Activate virtual environment
source venv/bin/activate

# Test basic functionality (recommended first test)
python examples/demo_search.py
# ✅ All imports successful
# ✅ Settings configuration working
# ✅ Text processing functional
# ✅ Content chunking operational

# Test REST API server
python drms_api.py --host localhost --port 8001 &
curl http://localhost:8001/health
# ✅ {"status":"healthy","vector_store_status":"connected"}

# Test integration example
python examples/vscode/integration_example.py
# ✅ Search, discovery, and examples working

# Run unit tests (basic components)
PYTHONPATH=src python -m pytest tests/ -v
# ✅ Core vector store tests passing
```

### Installation Verification

If you encounter issues, run this quick verification:

```bash
# Test core imports
python -c "
import sys; sys.path.insert(0, 'src')
from drms.config.settings import Settings
from drms.core.vector_store import VectorStore
from drms.scraper.doc_scraper import DocumentationScraper
print('✅ All core modules imported successfully')
"
```

## 🐳 Docker Deployment

```bash
# Build Docker image
docker build -t drms .

# Run with Docker Compose
docker-compose up -d

# Access API
curl http://localhost:8000/health
```

## 🔧 Troubleshooting

### Common Issues

**Installation Issues:**
```bash
# Use minimal dependencies if full install fails
pip install -r requirements-minimal.txt

# Check Python version compatibility
python --version  # Should be 3.8+

# Verify virtual environment
which python  # Should point to venv/bin/python
```

**MCP Server not starting:**
```bash
# Check Python path and dependencies
python --version
pip list | grep mcp

# Test syntax first
python -m py_compile mcp_server.py

# Run with debug logging
DRMS_LOG_LEVEL=DEBUG python mcp_server.py
```

**REST API Issues:**
```bash
# Test API server startup
python drms_api.py --host localhost --port 8001

# Check health endpoint
curl http://localhost:8001/health
# Should return: {"status":"healthy"}

# Test basic search
curl "http://localhost:8001/search/test?max_results=1"
```

**Vector Store/ChromaDB Issues:**
```bash
# ChromaDB will auto-create on first use
# Check if directory is writable
ls -la chroma_db/  # Should exist after first run

# Clear and reset if needed
rm -rf chroma_db/ && python drms_api.py
```

**Import Errors:**
```bash
# Set Python path explicitly
export PYTHONPATH=src
python -c "from drms.core.vector_store import VectorStore; print('OK')"

# Or use absolute imports
python -c "import sys; sys.path.insert(0, 'src'); from drms.core.vector_store import VectorStore; print('OK')"
```

### Debug Mode

```bash
# Enable debug logging
export DRMS_LOG_LEVEL=DEBUG

# Run with verbose output
python mcp_server.py --verbose
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install black flake8 mypy pytest

# Run code formatting
black src/ *.py

# Run type checking
mypy src/

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [MCP (Model Context Protocol)](https://github.com/modelcontextprotocol)
- Powered by [ChromaDB](https://www.trychroma.com/) for vector storage
- Uses [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for web scraping
- Embeddings via [Sentence Transformers](https://www.sbert.net/) or [OpenAI](https://openai.com/)

## 🚀 What Makes DRMS Special?

### The Problem DRMS Solves

AI coding assistants often provide outdated documentation examples because they were trained on older data. DRMS solves this by:

1. **Real-time Access**: Fetches the latest documentation directly from official sources
2. **Automatic Discovery**: Finds documentation for libraries you mention, even if not pre-indexed
3. **Smart Search**: Uses semantic search to find exactly what you need
4. **Universal Integration**: Works with any AI coding tool via MCP or REST API

### Real-World Impact

**Before DRMS:**
```
Developer: "How do I use the new React 18 features?"
AI: *Provides React 16 examples from training data*
Developer: *Spends time finding current documentation*
```

**With DRMS:**
```
Developer: "How do I use the new React 18 features?"
AI: *Uses DRMS to fetch latest React 18 docs*
AI: *Provides current, accurate examples*
Developer: *Continues coding with confidence*
```

---

**Ready to revolutionize your AI coding experience? Get started with DRMS today!** 🎯