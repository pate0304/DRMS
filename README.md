# 🚀 DRMS - Documentation RAG MCP Server

[![npm version](https://badge.fury.io/js/drms-mcp-server.svg)](https://www.npmjs.com/package/drms-mcp-server)
[![GitHub stars](https://img.shields.io/github/stars/pate0304/DRMS.svg?style=social&label=Star)](https://github.com/pate0304/DRMS)
[![GitHub issues](https://img.shields.io/github/issues/pate0304/DRMS.svg)](https://github.com/pate0304/DRMS/issues)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Real-time documentation access for AI coding tools with automatic library discovery**

DRMS provides your AI coding assistants with instant access to up-to-date documentation from any library or framework. No more outdated examples or deprecated APIs!

## ✨ What It Does

- 🔥 **Instant Documentation**: Pre-loaded with 40+ popular libraries (React, Next.js, Vue, Python, FastAPI, etc.)
- 🧠 **Smart Search**: Vector-based semantic search finds exactly what you need
- 🚀 **Auto Discovery**: Mention any library → DRMS finds and indexes it automatically
- ⚡ **Universal**: Works with Cursor, Windsurf, Claude Code, and any MCP-compatible tool

## 🛠️ Quick Install

### One-Command Setup (Recommended) ⚡
```bash
# Install globally
npm install -g drms-mcp-server

# Auto-setup everything (Python deps, virtual env, config)
npx drms install
```

That's it! The installer will:
- ✅ Detect your Python installation  
- ✅ Create a virtual environment
- ✅ Install all Python dependencies
- ✅ Generate configuration for your IDE
- ✅ Test the installation

### Manual Setup (Advanced)
If you prefer manual control:

#### **Step 1: Install DRMS**
```bash
npm install -g drms-mcp-server
```

#### **Step 2: Create Virtual Environment**
```bash
# Create a dedicated virtual environment for DRMS
python3 -m venv ~/.drms/venv
source ~/.drms/venv/bin/activate  # On Windows: ~/.drms/venv\Scripts\activate

# Install dependencies in the virtual environment
pip install mcp chromadb sentence-transformers requests beautifulsoup4 pydantic-settings
```

#### **Option B: System Python (if allowed)**
```bash
# Try system-wide install (may require --user flag)
pip install mcp chromadb sentence-transformers requests beautifulsoup4 pydantic-settings

# If that fails, try user install:
pip install --user mcp chromadb sentence-transformers requests beautifulsoup4 pydantic-settings
```

### Step 3: Get Your Configuration

**🎯 Easy Way - Use Configuration Generator:**
```bash
# Use the built-in configuration generator
drms config

# This will automatically detect your system and generate the correct configuration
```

**📝 Manual Configuration:**

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

**If you used Virtual Environment:**
```json
{
  "mcpServers": {
    "drms": {
      "command": "/Users/YOUR_USERNAME/.drms-env/bin/python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/node_modules/drms-mcp-server",
      "env": {
        "PYTHONPATH": "/path/to/node_modules/drms-mcp-server/src"
      }
    }
  }
}
```

**If System Python Works:**
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

### **"0 tools available" in IDE**
This means the MCP server is connecting but failing to start properly.

**Quick Fix:**
```bash
# Run automated diagnostics
drms doctor

# If issues found, run auto-installer
drms install

# Test if DRMS starts correctly
drms start
```

### **Installation Issues**
```bash
# Run full health check and diagnostics
drms doctor

# Re-run the auto-installer
drms install

# Generate fresh configuration
drms config

# This will detect your system and show the exact config to use
```

### **System-Specific Issues**

**macOS (Externally Managed Python):**
```bash
# If you get "externally-managed-environment" error:
python3 -m venv ~/.drms-env
source ~/.drms-env/bin/activate
pip install mcp chromadb sentence-transformers requests beautifulsoup4 pydantic-settings

# Then use virtual environment config in your IDE
```

**Windows:**
```bash
# Use Windows paths
python -m venv %USERPROFILE%\.drms-env
%USERPROFILE%\.drms-env\Scripts\activate
pip install mcp chromadb sentence-transformers requests beautifulsoup4 pydantic-settings
```

**Linux (Ubuntu/Debian):**
```bash
# Install python3-venv if needed
sudo apt update && sudo apt install python3-venv

# Then follow virtual environment setup
python3 -m venv ~/.drms-env
source ~/.drms-env/bin/activate
pip install mcp chromadb sentence-transformers requests beautifulsoup4 pydantic-settings
```

### **Quick Verification**
```bash
# 1. Check npm package is installed
npm list -g drms-mcp-server

# 2. Check Python dependencies
python -c "import mcp; print('✅ MCP available')"

# 3. Test DRMS command
drms --help

# 4. Generate configuration
drms config
```

## 📞 Support

- 🐛 Issues: [GitHub Issues](https://github.com/pate0304/DRMS/issues)
- 📦 NPM: [drms-mcp-server](https://www.npmjs.com/package/drms-mcp-server)
- 📖 Docs: This README + inline help (`drms --help`)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🚀 Get Started Now

**Ready to revolutionize your AI coding experience? Get started with DRMS today!** 🎯

```bash
# One-command installation
npm install -g drms-mcp-server
npx drms install
```

## 📦 NPM Package

[![npm version](https://badge.fury.io/js/drms-mcp-server.svg)](https://www.npmjs.com/package/drms-mcp-server)
[![npm downloads](https://img.shields.io/npm/dm/drms-mcp-server.svg)](https://www.npmjs.com/package/drms-mcp-server)

**Install:** `npm install -g drms-mcp-server`

## 🤝 Contributing & Support

- 🐛 **Report Issues**: [GitHub Issues](https://github.com/pate0304/DRMS/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/pate0304/DRMS/discussions)
- 📚 **Documentation**: [GitHub Wiki](https://github.com/pate0304/DRMS/wiki)
- ⭐ **Star us on GitHub**: [DRMS Repository](https://github.com/pate0304/DRMS)

## 👨‍💻 Author

**Created by DRMS Team**

Connect with us:
- 💼 **LinkedIn**: [https://www.linkedin.com/in/irenicj/](https://www.linkedin.com/in/irenicj/)
- 🐙 **GitHub**: [https://github.com/pate0304](https://github.com/pate0304)

---

**🎯 Transform your AI coding workflow with DRMS - Documentation at your fingertips!**