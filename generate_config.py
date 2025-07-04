#!/usr/bin/env python3
"""
DRMS Configuration Generator
Generates IDE configuration files for MCP integration
"""

import json
import os
import sys
import platform
from pathlib import Path

def find_python_executable():
    """Find the best Python executable to use"""
    drms_home = Path.home() / '.drms'
    venv_path = drms_home / 'venv'
    
    if platform.system() == 'Windows':
        venv_python = venv_path / 'Scripts' / 'python.exe'
    else:
        venv_python = venv_path / 'bin' / 'python'
    
    if venv_python.exists():
        return str(venv_python)
    
    # Fall back to system Python
    return 'python3'

def find_mcp_server():
    """Find the MCP server script"""
    script_dir = Path(__file__).parent
    
    # Check if we're in an npm package
    mcp_server_path = script_dir / 'mcp_server.py'
    if mcp_server_path.exists():
        return str(mcp_server_path)
    
    # Check DRMS home source installation
    drms_home = Path.home() / '.drms'
    source_path = drms_home / 'src' / 'mcp_server.py'
    if source_path.exists():
        return str(source_path)
    
    # Fall back to current directory
    return str(script_dir / 'mcp_server.py')

def generate_config():
    """Generate MCP configuration"""
    python_exe = find_python_executable()
    mcp_server = find_mcp_server()
    script_dir = Path(__file__).parent
    
    # Set up environment
    env = {
        'PYTHONPATH': str(script_dir / 'src'),
        'DRMS_LOG_LEVEL': 'INFO'
    }
    
    # Add virtual environment to PATH if it exists
    drms_home = Path.home() / '.drms'
    venv_path = drms_home / 'venv'
    if venv_path.exists():
        env['VIRTUAL_ENV'] = str(venv_path)
        if platform.system() == 'Windows':
            env['PATH'] = f"{venv_path / 'Scripts'};{os.environ.get('PATH', '')}"
        else:
            env['PATH'] = f"{venv_path / 'bin'}:{os.environ.get('PATH', '')}"
    
    config = {
        'mcpServers': {
            'drms': {
                'command': python_exe,
                'args': [mcp_server],
                'cwd': str(script_dir),
                'env': env
            }
        }
    }
    
    return config

def main():
    """Main function"""
    print("🔧 DRMS Configuration Generator")
    print("=" * 50)
    
    try:
        config = generate_config()
        
        # Pretty print the configuration
        print("\n📋 MCP Configuration:")
        print(json.dumps(config, indent=2))
        
        # Save to file
        config_path = Path.home() / '.drms-config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n✅ Configuration saved to: {config_path}")
        print("\n📝 Next steps:")
        print("1. Copy the configuration above into your IDE's MCP settings")
        print("2. Restart your IDE (Cursor, Windsurf, Claude Code, etc.)")
        print("3. Start using DRMS for documentation queries")
        
    except Exception as e:
        print(f"❌ Error generating configuration: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()