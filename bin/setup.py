#!/usr/bin/env python3
"""
DRMS Setup Script
Automated setup and configuration for DRMS
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, Any, Optional

class DRMSSetup:
    def __init__(self):
        self.system = platform.system().lower()
        self.home_dir = Path.home()
        self.drms_dir = self.home_dir / '.drms'
        self.config_dir = self.drms_dir / 'config'
        
    def check_requirements(self) -> bool:
        """Check system requirements"""
        print("🔍 Checking system requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print(f"❌ Python 3.8+ required. Current: {sys.version}")
            return False
        print(f"✅ Python {sys.version.split()[0]}")
        
        # Check pip
        try:
            subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                         check=True, capture_output=True)
            print("✅ pip available")
        except subprocess.CalledProcessError:
            print("❌ pip not available")
            return False
            
        # Check git (optional)
        try:
            subprocess.run(['git', '--version'], check=True, capture_output=True)
            print("✅ git available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  git not available (optional)")
            
        return True
    
    def create_directories(self):
        """Create necessary directories"""
        print("📁 Creating directories...")
        self.drms_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        (self.drms_dir / 'data').mkdir(exist_ok=True)
        (self.drms_dir / 'logs').mkdir(exist_ok=True)
        print("✅ Directories created")
    
    def setup_virtual_environment(self):
        """Set up Python virtual environment"""
        venv_dir = self.drms_dir / 'venv'
        
        if venv_dir.exists():
            print("📦 Virtual environment already exists")
            return
            
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', str(venv_dir)], check=True)
        
        # Activate and upgrade pip
        if self.system == 'windows':
            pip_cmd = str(venv_dir / 'Scripts' / 'pip.exe')
        else:
            pip_cmd = str(venv_dir / 'bin' / 'pip')
            
        subprocess.run([pip_cmd, 'install', '--upgrade', 'pip'], check=True)
        print("✅ Virtual environment created")
    
    def install_dependencies(self):
        """Install Python dependencies"""
        print("📦 Installing dependencies...")
        venv_dir = self.drms_dir / 'venv'
        
        if self.system == 'windows':
            pip_cmd = str(venv_dir / 'Scripts' / 'pip.exe')
        else:
            pip_cmd = str(venv_dir / 'bin' / 'pip')
        
        # Install from requirements.txt if available
        if Path('requirements.txt').exists():
            subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], check=True)
        else:
            # Install minimal requirements
            deps = [
                'mcp>=1.0.0',
                'chromadb>=0.4.0',
                'openai>=1.0.0',
                'fastapi>=0.104.0',
                'uvicorn>=0.24.0',
                'requests>=2.31.0',
                'python-dotenv>=1.0.0'
            ]
            subprocess.run([pip_cmd, 'install'] + deps, check=True)
        
        print("✅ Dependencies installed")
    
    def configure_environment(self):
        """Configure environment variables"""
        print("🔧 Configuring environment...")
        
        env_file = self.drms_dir / '.env'
        if env_file.exists():
            print("⚠️  .env file already exists, skipping")
            return
        
        # Get OpenAI API key
        api_key = input("🔑 Enter OpenAI API Key (optional, press Enter to skip): ").strip()
        
        env_content = f"""# DRMS Configuration
DRMS_HOME={self.drms_dir}
DRMS_DATA_DIR={self.drms_dir / 'data'}
DRMS_LOG_LEVEL=INFO
DRMS_HOST=localhost
DRMS_PORT=8000

# OpenAI Configuration
OPENAI_API_KEY={api_key if api_key else ''}

# Vector Database
CHROMA_DB_PATH={self.drms_dir / 'data' / 'chroma_db'}

# Cache Settings
CACHE_DIR={self.drms_dir / 'data' / 'cache'}
CACHE_SIZE_MB=1000
"""
        
        env_file.write_text(env_content)
        print("✅ Environment configured")
    
    def create_config_templates(self):
        """Create configuration templates"""
        print("📝 Creating configuration templates...")
        
        # MCP server config
        mcp_config = {
            "mcpServers": {
                "drms": {
                    "command": "drms",
                    "args": ["start"],
                    "env": {
                        "DRMS_LOG_LEVEL": "INFO"
                    }
                }
            }
        }
        
        (self.config_dir / 'mcp_config.json').write_text(
            json.dumps(mcp_config, indent=2)
        )
        
        # IDE integration configs
        ide_configs = {
            'cursor': {
                'name': 'DRMS - Documentation RAG',
                'command': 'drms',
                'args': ['start'],
                'description': 'Real-time documentation access'
            },
            'vscode': {
                'name': 'drms',
                'command': 'drms',
                'args': ['start'],
                'transport': 'stdio'
            }
        }
        
        for ide, config in ide_configs.items():
            (self.config_dir / f'{ide}_config.json').write_text(
                json.dumps(config, indent=2)
            )
        
        print("✅ Configuration templates created")
    
    def create_cli_wrapper(self):
        """Create CLI wrapper script"""
        print("🔧 Creating CLI wrapper...")
        
        bin_dir = self.home_dir / '.local' / 'bin'
        bin_dir.mkdir(parents=True, exist_ok=True)
        
        if self.system == 'windows':
            script_path = bin_dir / 'drms.bat'
            script_content = f"""@echo off
set DRMS_HOME={self.drms_dir}
call "{self.drms_dir}\\venv\\Scripts\\activate.bat"
cd /d "{self.drms_dir}"
python -m drms %*
"""
        else:
            script_path = bin_dir / 'drms'
            script_content = f"""#!/bin/bash
export DRMS_HOME="{self.drms_dir}"
source "{self.drms_dir}/venv/bin/activate"
cd "{self.drms_dir}"
python -m drms "$@"
"""
        
        script_path.write_text(script_content)
        if self.system != 'windows':
            script_path.chmod(0o755)
        
        print("✅ CLI wrapper created")
    
    def show_completion_message(self):
        """Show setup completion message"""
        print("\n" + "="*50)
        print("🎉 DRMS Setup Complete!")
        print("="*50)
        print(f"📍 Installation: {self.drms_dir}")
        print(f"🔧 Configuration: {self.config_dir}")
        print(f"📝 Environment: {self.drms_dir}/.env")
        print("\n🚀 Quick Start:")
        print("   drms --help")
        print("   drms start")
        print("\n📚 Next Steps:")
        print("   1. Configure your IDE with the config files in ~/.drms/config/")
        print("   2. Add documentation sources with 'drms add-source <url>'")
        print("   3. Start the server with 'drms start'")
        print("\n🔗 Documentation: https://github.com/pate0304/DRMS")
    
    def run(self):
        """Run the complete setup process"""
        print("🚀 DRMS Setup Starting...")
        print("="*50)
        
        try:
            if not self.check_requirements():
                sys.exit(1)
            
            self.create_directories()
            self.setup_virtual_environment()
            self.install_dependencies()
            self.configure_environment()
            self.create_config_templates()
            self.create_cli_wrapper()
            self.show_completion_message()
            
        except KeyboardInterrupt:
            print("\n❌ Setup cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            sys.exit(1)

if __name__ == '__main__':
    setup = DRMSSetup()
    setup.run()