#!/usr/bin/env node

/**
 * DRMS Smart Installer
 * Automatically handles Python dependencies and cross-platform setup
 */

const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

class DRMSInstaller {
    constructor() {
        this.platform = process.platform;
        this.isWindows = this.platform === 'win32';
        this.homeDir = os.homedir();
        this.drmsHome = path.join(this.homeDir, '.drms');
        this.drmsEnvPath = path.join(this.drmsHome, 'venv');
        this.pythonCmd = this.isWindows ? 'python' : 'python3';
        this.pipCmd = this.isWindows ? 'pip' : 'pip3';
        this.venvActivate = this.isWindows 
            ? path.join(this.drmsEnvPath, 'Scripts', 'activate.bat')
            : path.join(this.drmsEnvPath, 'bin', 'activate');
        this.venvPython = this.isWindows
            ? path.join(this.drmsEnvPath, 'Scripts', 'python.exe')
            : path.join(this.drmsEnvPath, 'bin', 'python');
    }

    log(message, type = 'info') {
        const symbols = {
            info: '📋',
            success: '✅',
            warning: '⚠️',
            error: '❌',
            progress: '🔄'
        };
        console.log(`${symbols[type]} ${message}`);
    }

    async runCommand(command, options = {}) {
        return new Promise((resolve, reject) => {
            const [cmd, ...args] = command.split(' ');
            const child = spawn(cmd, args, {
                stdio: options.silent ? 'pipe' : 'inherit',
                shell: this.isWindows,
                ...options
            });

            let stdout = '';
            let stderr = '';

            if (options.silent) {
                child.stdout?.on('data', (data) => stdout += data.toString());
                child.stderr?.on('data', (data) => stderr += data.toString());
            }

            child.on('close', (code) => {
                if (code === 0) {
                    resolve({ code, stdout, stderr });
                } else {
                    reject({ code, stdout, stderr, command });
                }
            });

            child.on('error', reject);
        });
    }

    async checkPython() {
        this.log('Checking Python installation...', 'progress');
        
        const pythonCandidates = this.isWindows 
            ? ['python', 'py', 'python3']
            : ['python3', 'python'];

        for (const cmd of pythonCandidates) {
            try {
                const result = await this.runCommand(`${cmd} --version`, { silent: true });
                const version = result.stdout.trim();
                this.log(`Found Python: ${version}`, 'success');
                this.pythonCmd = cmd;
                return true;
            } catch (error) {
                continue;
            }
        }

        throw new Error('Python 3.8+ not found. Please install Python from https://python.org');
    }

    async checkPip() {
        this.log('Checking pip availability...', 'progress');
        
        try {
            await this.runCommand(`${this.pythonCmd} -m pip --version`, { silent: true });
            this.log('pip is available', 'success');
            return true;
        } catch (error) {
            throw new Error('pip not found. Please ensure pip is installed with Python');
        }
    }

    async createVirtualEnvironment() {
        this.log('Creating Python virtual environment...', 'progress');
        
        // Ensure DRMS home directory exists
        if (!fs.existsSync(this.drmsHome)) {
            fs.mkdirSync(this.drmsHome, { recursive: true });
        }
        
        if (fs.existsSync(this.drmsEnvPath)) {
            this.log('Virtual environment already exists, skipping creation', 'info');
            return;
        }

        try {
            await this.runCommand(`${this.pythonCmd} -m venv "${this.drmsEnvPath}"`);
            this.log(`Virtual environment created at ${this.drmsEnvPath}`, 'success');
        } catch (error) {
            throw new Error(`Failed to create virtual environment: ${error.stderr || error.message}`);
        }
    }

    async installPythonDependencies() {
        this.log('Installing Python dependencies...', 'progress');
        
        const dependencies = [
            'mcp>=1.0.0',
            'chromadb>=0.4.0', 
            'sentence-transformers>=2.2.0',
            'requests>=2.31.0',
            'beautifulsoup4>=4.12.0',
            'pydantic-settings>=2.5.0'
        ];

        try {
            // Use the virtual environment python
            const installCmd = this.isWindows
                ? `"${this.venvPython}" -m pip install ${dependencies.join(' ')}`
                : `"${this.venvPython}" -m pip install ${dependencies.join(' ')}`;
                
            await this.runCommand(installCmd);
            this.log('Python dependencies installed successfully', 'success');
        } catch (error) {
            throw new Error(`Failed to install dependencies: ${error.stderr || error.message}`);
        }
    }

    async testInstallation() {
        this.log('Testing installation...', 'progress');
        
        try {
            // Test Python imports
            const testScript = `
import mcp
import chromadb
import sentence_transformers
import requests
import bs4
import pydantic_settings
print("All dependencies imported successfully")
            `;
            
            const testCmd = this.isWindows
                ? `"${this.venvPython}" -c "${testScript.replace(/\n/g, '; ')}"`
                : `"${this.venvPython}" -c "${testScript}"`;
                
            await this.runCommand(testCmd, { silent: true });
            this.log('All Python dependencies are working correctly', 'success');
            return true;
        } catch (error) {
            this.log('Dependency test failed, but installation may still work', 'warning');
            return false;
        }
    }

    generateConfiguration() {
        this.log('Generating IDE configuration...', 'progress');
        
        const nodeModulesPath = path.dirname(path.dirname(__filename));
        const mcpServerPath = path.join(nodeModulesPath, 'mcp_server.py');
        const srcPath = path.join(nodeModulesPath, 'src');
        
        const config = {
            mcpServers: {
                drms: {
                    command: this.venvPython,
                    args: ['mcp_server.py'],
                    cwd: nodeModulesPath,
                    env: {
                        PYTHONPATH: srcPath,
                        DRMS_LOG_LEVEL: 'INFO'
                    }
                }
            }
        };

        this.log('📋 CONFIGURATION FOR YOUR IDE:', 'info');
        console.log('Copy this into your IDE\'s MCP settings:\n');
        console.log(JSON.stringify(config, null, 2));
        console.log('\n📍 Configuration saved to: ~/.drms-config.json');
        
        // Save config to file
        const configPath = path.join(this.homeDir, '.drms-config.json');
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
        
        return config;
    }

    showNextSteps() {
        this.log('🎉 DRMS Installation Complete!', 'success');
        console.log('\n📋 NEXT STEPS:');
        console.log('1. Copy the configuration above into your IDE\'s MCP settings');
        console.log('2. Restart your IDE (Cursor, Windsurf, Claude Code, etc.)');
        console.log('3. Start asking for documentation: "How do I use React hooks?"');
        console.log('\n🔧 USEFUL COMMANDS:');
        console.log('• drms config     - Generate configuration again');
        console.log('• drms doctor     - Diagnose installation issues');
        console.log('• drms --help     - Show all available commands');
        console.log('\n📞 NEED HELP?');
        console.log('• GitHub Issues: https://github.com/pate0304/DRMS/issues');
        console.log('• NPM Package: https://www.npmjs.com/package/drms-mcp-server');
    }

    async install() {
        try {
            console.log('🚀 DRMS Smart Installer Starting...\n');
            
            await this.checkPython();
            await this.checkPip();
            await this.createVirtualEnvironment();
            await this.installPythonDependencies();
            await this.testInstallation();
            
            this.generateConfiguration();
            this.showNextSteps();
            
        } catch (error) {
            this.log(`Installation failed: ${error.message}`, 'error');
            console.log('\n🆘 TROUBLESHOOTING:');
            console.log('• Ensure Python 3.8+ is installed: python --version');
            console.log('• Check pip is available: pip --version'); 
            console.log('• Try manual setup: drms config');
            console.log('• Get help: https://github.com/pate0304/DRMS/issues');
            process.exit(1);
        }
    }
}

// Run installer when called directly
if (require.main === module) {
    const installer = new DRMSInstaller();
    installer.install();
}

module.exports = { DRMSInstaller };