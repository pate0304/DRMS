#!/usr/bin/env python3

import os
import sys
import json
import click
import subprocess
import platform
from pathlib import Path
from typing import Dict, Any, Optional
import uvicorn
from .config.settings import get_settings
from .core.vector_store import VectorStore

@click.group()
@click.version_option(version="1.0.0", prog_name="DRMS")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """DRMS - Documentation RAG MCP Server"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    if verbose:
        click.echo("🔍 Verbose mode enabled")

@cli.command()
@click.option('--host', default='localhost', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--log-level', default='INFO', help='Logging level')
@click.pass_context
def start(ctx, host, port, log_level):
    """Start the MCP server"""
    click.echo(f"🚀 Starting DRMS MCP server on {host}:{port}")
    
    # Set environment variables
    os.environ['DRMS_HOST'] = host
    os.environ['DRMS_PORT'] = str(port)
    os.environ['DRMS_LOG_LEVEL'] = log_level
    
    # Import and run the MCP server
    try:
        from ..mcp_server import main as mcp_main
        mcp_main()
    except ImportError:
        # Fallback to subprocess if module import fails
        script_path = Path(__file__).parent.parent.parent / 'mcp_server.py'
        if script_path.exists():
            subprocess.run([sys.executable, str(script_path)], check=True)
        else:
            click.echo("❌ MCP server not found", err=True)
            sys.exit(1)

@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
@click.pass_context
def api(ctx, host, port, reload):
    """Start the REST API server"""
    click.echo(f"🌐 Starting DRMS API server on {host}:{port}")
    
    try:
        from ..drms_api import app
        uvicorn.run(app, host=host, port=port, reload=reload)
    except ImportError:
        # Fallback to subprocess
        script_path = Path(__file__).parent.parent.parent / 'drms_api.py'
        if script_path.exists():
            cmd = [sys.executable, str(script_path), '--host', host, '--port', str(port)]
            subprocess.run(cmd, check=True)
        else:
            click.echo("❌ API server not found", err=True)
            sys.exit(1)

@cli.command()
@click.argument('url')
@click.option('--name', help='Name for the documentation source')
@click.option('--type', 'doc_type', default='web', help='Documentation type (web, git, local)')
@click.pass_context
def add_source(ctx, url, name, doc_type):
    """Add a documentation source"""
    click.echo(f"📚 Adding documentation source: {url}")
    
    settings = get_settings()
    vector_store = VectorStore(settings.CHROMA_DB_PATH)
    
    try:
        # Add the source to configuration
        config_path = Path.home() / '.drms' / 'sources.json'
        config_path.parent.mkdir(exist_ok=True)
        
        sources = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                sources = json.load(f)
        
        source_name = name or url.split('/')[-1] or 'unnamed'
        sources[source_name] = {
            'url': url,
            'type': doc_type,
            'added_at': click.DateTime().today().isoformat()
        }
        
        with open(config_path, 'w') as f:
            json.dump(sources, f, indent=2)
        
        click.echo(f"✅ Added source '{source_name}' to configuration")
        click.echo("💡 Run 'drms index' to start indexing the documentation")
        
    except Exception as e:
        click.echo(f"❌ Error adding source: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.pass_context
def list_sources(ctx):
    """List configured documentation sources"""
    config_path = Path.home() / '.drms' / 'sources.json'
    
    if not config_path.exists():
        click.echo("📚 No documentation sources configured")
        click.echo("💡 Add sources with: drms add-source <url>")
        return
    
    with open(config_path, 'r') as f:
        sources = json.load(f)
    
    if not sources:
        click.echo("📚 No documentation sources configured")
        return
    
    click.echo("📚 Configured documentation sources:")
    click.echo("=" * 50)
    
    for name, info in sources.items():
        click.echo(f"📖 {name}")
        click.echo(f"   URL: {info['url']}")
        click.echo(f"   Type: {info['type']}")
        click.echo(f"   Added: {info['added_at']}")
        click.echo()

@cli.command()
@click.argument('query')
@click.option('--limit', default=5, help='Number of results to return')
@click.pass_context
def search(ctx, query, limit):
    """Search documentation"""
    click.echo(f"🔍 Searching for: {query}")
    
    settings = get_settings()
    vector_store = VectorStore(settings.CHROMA_DB_PATH)
    
    try:
        results = vector_store.search(query, limit=limit)
        
        if not results:
            click.echo("❌ No results found")
            return
        
        click.echo(f"📄 Found {len(results)} results:")
        click.echo("=" * 50)
        
        for i, result in enumerate(results, 1):
            click.echo(f"{i}. {result.get('title', 'Untitled')}")
            click.echo(f"   Score: {result.get('score', 0):.3f}")
            click.echo(f"   Source: {result.get('source', 'Unknown')}")
            if result.get('content'):
                content = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                click.echo(f"   Content: {content}")
            click.echo()
            
    except Exception as e:
        click.echo(f"❌ Search error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.pass_context
def index(ctx):
    """Index documentation sources"""
    click.echo("📚 Indexing documentation sources...")
    
    config_path = Path.home() / '.drms' / 'sources.json'
    if not config_path.exists():
        click.echo("❌ No sources configured. Add sources first with: drms add-source <url>")
        return
    
    with open(config_path, 'r') as f:
        sources = json.load(f)
    
    if not sources:
        click.echo("❌ No sources configured")
        return
    
    settings = get_settings()
    vector_store = VectorStore(settings.CHROMA_DB_PATH)
    
    for name, info in sources.items():
        click.echo(f"📖 Indexing {name}...")
        try:
            # Import scraper and index the source
            from ..scraper.doc_scraper import DocScraper
            scraper = DocScraper()
            documents = scraper.scrape_documentation(info['url'], info['type'])
            
            for doc in documents:
                vector_store.add_document(doc)
            
            click.echo(f"✅ Indexed {len(documents)} documents from {name}")
            
        except Exception as e:
            click.echo(f"❌ Error indexing {name}: {e}")
    
    click.echo("🎉 Indexing complete!")

@cli.command()
@click.pass_context
def test(ctx):
    """Run tests"""
    click.echo("🧪 Running DRMS tests...")
    
    test_dir = Path(__file__).parent.parent.parent / 'tests'
    if not test_dir.exists():
        click.echo("❌ Tests directory not found")
        sys.exit(1)
    
    result = subprocess.run([sys.executable, '-m', 'pytest', str(test_dir), '-v'], 
                          capture_output=False)
    sys.exit(result.returncode)

@cli.command()
@click.pass_context
def setup(ctx):
    """Run interactive setup"""
    click.echo("🚀 DRMS Interactive Setup")
    click.echo("=" * 30)
    
    # Run the setup script
    setup_script = Path(__file__).parent.parent.parent / 'bin' / 'setup.py'
    if setup_script.exists():
        subprocess.run([sys.executable, str(setup_script)], check=True)
    else:
        click.echo("❌ Setup script not found")
        sys.exit(1)

@cli.command()
@click.pass_context
def config(ctx):
    """Show configuration"""
    settings = get_settings()
    
    click.echo("⚙️  DRMS Configuration")
    click.echo("=" * 30)
    click.echo(f"DRMS Home: {settings.DRMS_HOME}")
    click.echo(f"Data Directory: {settings.DRMS_DATA_DIR}")
    click.echo(f"Log Level: {settings.DRMS_LOG_LEVEL}")
    click.echo(f"Host: {settings.DRMS_HOST}")
    click.echo(f"Port: {settings.DRMS_PORT}")
    click.echo(f"ChromaDB Path: {settings.CHROMA_DB_PATH}")
    click.echo(f"Cache Directory: {settings.CACHE_DIR}")
    click.echo(f"OpenAI API Key: {'Set' if settings.OPENAI_API_KEY else 'Not set'}")

@cli.command()
@click.option('--port', default=8080, help='Port for config generator')
@click.pass_context
def config_generator(ctx, port):
    """Start the web-based configuration generator"""
    click.echo(f"🌐 Starting configuration generator on port {port}")
    
    try:
        from ..config_generator.app import app
        uvicorn.run(app, host="0.0.0.0", port=port)
    except ImportError:
        click.echo("❌ Configuration generator not available")
        sys.exit(1)

if __name__ == '__main__':
    cli()