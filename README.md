# 🚀 DRMS - Documentation RAG MCP Server

**Real-time documentation access for AI coding tools with automatic library discovery**

DRMS provides your AI coding assistants with instant access to up-to-date documentation from any library or framework. No more outdated examples or deprecated APIs!

## ✨ What It Does

- 🔥 **Instant Documentation**: Pre-loaded with 40+ popular libraries (React, Next.js, Vue, Python, FastAPI, etc.)
- 🧠 **Smart Search**: Vector-based semantic search finds exactly what you need
- 🚀 **Auto Discovery**: Mention any library → DRMS finds and indexes it automatically
- ⚡ **Universal**: Works with Cursor, Windsurf, Claude Code, and any MCP-compatible tool

## 🛠️ Quick Install

### Step 1: Install DRMS
```bash
# Install globally via npm
npm install -g drms-mcp-server

# Install Python dependencies
pip install mcp chromadb sentence-transformers requests beautifulsoup4 pydantic-settings
```

### Step 2: Configure Your IDE

#### **Cursor**
Add to your Cursor settings (`Cmd/Ctrl + ,` → MCP):
```json
{
  "mcpServers": {
    "drms": {
      "command": "drms",
      "args": ["start"]
    }
  }
}
```

#### **Windsurf**
Add to your Windsurf MCP config:
```json
{
  "mcpServers": {
    "drms": {
      "command": "drms", 
      "args": ["start"]
    }
  }
}
```

#### **Claude Code (Desktop)**
Add to your Claude Code MCP settings:
```json
{
  "mcpServers": {
    "drms": {
      "command": "drms",
      "args": ["start"]
    }
  }
}
```

### Step 3: Start Using
Restart your IDE and start asking for documentation:
- "How do I use React hooks?"
- "Show me FastAPI authentication examples"
- "What's new in Vue 3?"

## 📋 Available Commands

| Command | What it does |
|---------|-------------|
| `drms start` | Start MCP server for IDE integration |
| `drms api` | Start REST API server |
| `drms search "query"` | Search documentation from terminal |
| `drms setup` | Interactive setup wizard |

## 🔧 Alternative Installation (Source)

If npm doesn't work for you:

```bash
# Clone and install
git clone https://github.com/pate0304/DRMS.git
cd DRMS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-minimal.txt

# Configure your IDE to use:
# Command: python
# Args: ["mcp_server.py"] 
# Working Directory: /path/to/DRMS
```

## 💡 How It Works

1. **Ask your AI**: "How do I use useState in React?"
2. **DRMS searches**: Latest React documentation in real-time
3. **AI responds**: With current, accurate examples and explanations
4. **You code**: With confidence using up-to-date information

## 🔍 MCP Tools Available in Your IDE

Once configured, your AI assistant can use these tools:

- `search_documentation` - Find docs across all libraries
- `discover_library` - Auto-index new libraries  
- `get_library_info` - Show what's available
- `search_code_examples` - Find specific code patterns

## 🌟 Pre-loaded Libraries

**Frontend**: React, Next.js, Vue, Angular, Svelte, Tailwind CSS  
**Backend**: FastAPI, Django, Flask, Express, Node.js  
**Python**: Pandas, NumPy, Requests, Scikit-learn  
**Tools**: TypeScript, Jest, Docker, AWS, GCP  

Plus automatic discovery for any library you mention!

## 🆘 Troubleshooting

**Installation Issues:**
```bash
# If pip install fails, try:
pip install --user mcp chromadb sentence-transformers requests beautifulsoup4 pydantic-settings

# Check Python version (need 3.8+)
python3 --version
```

**IDE Not Finding DRMS:**
```bash
# Test if drms command works
drms --help

# If not found, check npm global path
npm list -g drms-mcp-server
```

**Python Dependencies Missing:**
```bash
# Install in virtual environment
python3 -m venv drms-env
source drms-env/bin/activate
pip install mcp chromadb sentence-transformers requests beautifulsoup4 pydantic-settings
```

## 📞 Support

- 🐛 Issues: [GitHub Issues](https://github.com/pate0304/DRMS/issues)
- 📦 NPM: [drms-mcp-server](https://www.npmjs.com/package/drms-mcp-server)
- 📖 Docs: This README + inline help (`drms --help`)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Ready to revolutionize your AI coding experience? Get started with DRMS today!** 🎯

```bash
npm install -g drms-mcp-server
pip install mcp chromadb sentence-transformers requests beautifulsoup4 pydantic-settings
# Add to your IDE config and start coding with confidence!
```