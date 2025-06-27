# DRMS + Cursor Integration

## Setup Instructions

1. **Install DRMS dependencies:**
   ```bash
   cd /path/to/DRMS
   pip install -r requirements.txt
   ```

2. **Configure MCP in Cursor:**
   - Open Cursor settings
   - Navigate to MCP Servers section
   - Add the configuration from `mcp_config.json`
   - Update the `cwd` path to your DRMS installation directory
   - Add your OpenAI API key (optional but recommended)

3. **Test the integration:**
   - Open a new file in Cursor
   - Use the chat or ask questions like:
     - "How do I use useState in React?"
     - "Show me FastAPI routing examples"
     - "What's the syntax for pandas DataFrame?"

## Example Usage

### Search Documentation
```
@drms search "React hooks useState"
```

### Discover New Library
```
@drms discover "tailwindcss"
```

### Get Code Examples
```
@drms examples "FastAPI authentication"
```

## Features Available

- ✅ Real-time documentation search
- ✅ Automatic library discovery
- ✅ Code example retrieval  
- ✅ Multi-library search
- ✅ Semantic similarity matching
- ✅ Up-to-date documentation access

## Troubleshooting

**MCP Server not starting:**
- Check Python path and DRMS installation
- Verify all dependencies are installed
- Check logs for specific error messages

**No search results:**
- Library might not be indexed yet
- Try using the discover function first
- Check if OpenAI API key is configured

**Slow responses:**
- Consider using OpenAI embeddings for better performance
- Reduce max_results if getting too many results
- Check network connection for web scraping