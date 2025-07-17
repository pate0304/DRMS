# 🚀 DRMS - Node.js/TypeScript Implementation

This is a complete Node.js/TypeScript port of the DRMS Documentation RAG MCP Server. It provides the same functionality as the Python version but with better performance and easier deployment.

## ✨ Features

- **Native TypeScript/Node.js implementation** - No Python dependencies
- **MCP (Model Context Protocol) integration** - Works with Windsurf, Cursor, Claude Code
- **Vector-based documentation search** - ChromaDB for semantic search
- **Automatic library discovery** - Scrapes and indexes documentation automatically
- **Real-time documentation access** - Up-to-date information from library docs
- **Code example extraction** - Finds relevant code snippets
- **CLI tools** - Command-line interface for management

## 🛠️ Quick Setup

### 1. Install Dependencies
```bash
npm install
```

### 2. Build the Project
```bash
npm run build
```

### 3. Test the Simple Server
```bash
node dist/server-simple.js
```

## 🔧 Configuration for IDEs

### Windsurf IDE

Add this to your Windsurf MCP configuration:

```json
{
  "mcpServers": {
    "drms-node-simple": {
      "command": "node",
      "args": ["dist/server-simple.js"],
      "cwd": "/Users/shiva-mac/Documents/CB/DRMS"
    }
  }
}
```

For the full version with ChromaDB:

```json
{
  "mcpServers": {
    "drms-node": {
      "command": "node", 
      "args": ["dist/server.js"],
      "cwd": "/Users/shiva-mac/Documents/CB/DRMS",
      "env": {
        "DRMS_VECTOR_DB_PATH": "/Users/shiva-mac/Documents/CB/DRMS/chroma_db_node"
      }
    }
  }
}
```

### Cursor IDE

```json
{
  "mcpServers": {
    "drms-node": {
      "command": "node",
      "args": ["dist/server-simple.js"],
      "cwd": "/Users/shiva-mac/Documents/CB/DRMS"
    }
  }
}
```

## 📋 Available Commands

### Development
```bash
npm run dev          # Run server in development mode
npm run build        # Build TypeScript to JavaScript
npm run start        # Run built server
npm run watch        # Watch for changes and rebuild
```

### CLI Tools
```bash
npm run cli search "react hooks"              # Search documentation
npm run cli discover "lodash"                 # Index a library
npm run cli info                               # Show statistics
npm run cli doctor                             # Health check
npm run cli generate-config --ide windsurf    # Generate IDE config
```

## 🔍 MCP Tools Available

Once connected to your IDE, you can use these tools:

1. **`search_documentation`** - Search across all indexed documentation
2. **`discover_library`** - Automatically find and index new libraries
3. **`get_library_info`** - Get information about indexed libraries
4. **`search_code_examples`** - Find specific code patterns and examples

## 🏗️ Architecture

```
src-node/
├── config/
│   └── settings.ts          # Configuration management
├── core/
│   └── vector-store.ts      # ChromaDB vector storage
├── scraper/
│   └── doc-scraper.ts       # Documentation scraping
├── cli.ts                   # Command-line interface
├── server.ts                # Full MCP server
└── server-simple.ts         # Simple demo server
```

## 🌟 Key Benefits of Node.js Version

- ✅ **Single Runtime** - No Python dependencies needed
- ✅ **Better Performance** - Faster I/O and async operations
- ✅ **Easy Deployment** - Standard npm package
- ✅ **Native TypeScript** - Better IDE integration and type safety
- ✅ **Smaller Footprint** - Reduced memory usage
- ✅ **Cross-platform** - Runs on macOS, Linux, Windows

## 🐛 Troubleshooting

### "ChromaDB connection failed"
The full server requires ChromaDB. For testing, use the simple server:
```bash
node dist/server-simple.js
```

### "Module not found"
Make sure to build the project first:
```bash
npm run build
```

### "Permission denied"
Ensure the file paths in your IDE configuration are correct and accessible.

## 🔄 Migration from Python Version

The Node.js version provides the same MCP tools and functionality as the Python version:

| Python Tool | Node.js Equivalent | Status |
|-------------|-------------------|---------|
| `search_documentation` | ✅ `search_documentation` | Complete |
| `discover_library` | ✅ `discover_library` | Complete |
| `get_library_info` | ✅ `get_library_info` | Complete |
| `search_code_examples` | ✅ `search_code_examples` | Complete |

## 🎯 Usage Example

After configuring in your IDE, you can ask:

- "How do I use React hooks?"
- "Show me FastAPI authentication examples"
- "What's new in TypeScript 5.0?"
- "Find lodash array methods"

The server will automatically search indexed documentation and provide relevant, up-to-date examples and explanations.

## 📦 Deployment

For production deployment:

1. **Build the project**: `npm run build`
2. **Copy dist/ folder** to your deployment environment
3. **Install production dependencies**: `npm ci --only=production`
4. **Configure environment variables** as needed
5. **Run**: `node dist/server.js`

## 🤝 Contributing

The Node.js implementation follows the same architecture as the Python version but leverages Node.js/TypeScript best practices:

- Use TypeScript for type safety
- Follow async/await patterns
- Implement proper error handling
- Use ESM modules
- Maintain compatibility with MCP specification

---

**🎉 The Node.js port is complete and ready for use! No more Python dependencies needed.**