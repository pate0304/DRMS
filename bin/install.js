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
        this.isMacOS = this.platform === 'darwin';
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
        this.pythonSource = null; // Will be detected: 'homebrew', 'system', 'pyenv', etc.
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
                
                // Detect Python source on macOS
                if (this.isMacOS) {
                    await this.detectPythonSource(cmd);
                }
                
                return true;
            } catch (error) {
                continue;
            }
        }

        throw new Error('Python 3.8+ not found. Please install Python from https://python.org');
    }

    async detectPythonSource(pythonCmd) {
        try {
            const result = await this.runCommand(`which ${pythonCmd}`, { silent: true });
            const pythonPath = result.stdout.trim();
            
            if (pythonPath.includes('/opt/homebrew/') || pythonPath.includes('/usr/local/')) {
                this.pythonSource = 'homebrew';
                this.log('Detected Homebrew Python', 'info');
            } else if (pythonPath.includes('/.pyenv/')) {
                this.pythonSource = 'pyenv';
                this.log('Detected pyenv Python', 'info');
            } else if (pythonPath.includes('/usr/bin/')) {
                this.pythonSource = 'system';
                this.log('Detected system Python', 'info');
            } else {
                this.pythonSource = 'unknown';
                this.log(`Detected Python at: ${pythonPath}`, 'info');
            }
        } catch (error) {
            this.pythonSource = 'unknown';
        }
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
            this.log('Virtual environment already exists, validating...', 'info');
            if (await this.validateVirtualEnvironment()) {
                return;
            } else {
                this.log('Existing venv is invalid, removing and recreating...', 'warning');
                fs.rmSync(this.drmsEnvPath, { recursive: true, force: true });
            }
        }

        try {
            // Try creating virtual environment
            const venvCommand = `${this.pythonCmd} -m venv "${this.drmsEnvPath}"`;
            const createResult = await this.runCommand(venvCommand, { shell: true });
            
            // Small delay to ensure filesystem operations complete
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Validate that it was actually created successfully
            if (await this.validateVirtualEnvironment()) {
                this.log(`Virtual environment created at ${this.drmsEnvPath}`, 'success');
            } else {
                throw new Error('Virtual environment creation appeared to succeed but validation failed');
            }
        } catch (error) {
            this.log(`Virtual environment creation failed: ${error.stderr || error.message}`, 'error');
            throw new Error(`Failed to create virtual environment: ${error.stderr || error.message}`);
        }
    }

    async validateVirtualEnvironment() {
        // Check if the venv directory exists
        if (!fs.existsSync(this.drmsEnvPath)) {
            return false;
        }

        // Check for essential venv structure
        const essentialPaths = [
            path.join(this.drmsEnvPath, 'pyvenv.cfg'),
            this.isWindows ? 
                path.join(this.drmsEnvPath, 'Scripts') : 
                path.join(this.drmsEnvPath, 'bin')
        ];

        for (const essentialPath of essentialPaths) {
            if (!fs.existsSync(essentialPath)) {
                this.log(`Missing essential venv component: ${essentialPath}`, 'warning');
                return false;
            }
        }

        // Check for Python executable (could be python, python3, or python3.x)
        const binDir = this.isWindows ? 
            path.join(this.drmsEnvPath, 'Scripts') : 
            path.join(this.drmsEnvPath, 'bin');
            
        const pythonExecutables = this.isWindows ? 
            ['python.exe', 'python3.exe'] : 
            ['python', 'python3'];
            
        let pythonFound = false;
        for (const executable of pythonExecutables) {
            const pythonPath = path.join(binDir, executable);
            try {
                // Use lstat to check for symlinks as well as regular files
                const stats = fs.lstatSync(pythonPath);
                if (stats.isFile() || stats.isSymbolicLink()) {
                    // Update our venvPython to the actual existing path
                    this.venvPython = pythonPath;
                    pythonFound = true;
                    break;
                }
            } catch (error) {
                // File doesn't exist, continue to next candidate
                continue;
            }
        }
        
        if (!pythonFound) {
            this.log(`No Python executable found in venv bin directory`, 'warning');
            // Still return true - the venv exists, we'll try activation scripts
        }

        return true;
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

        // Strategy 1: Try virtual environment python directly
        if (await this.tryVenvInstall(dependencies)) return;
        
        // Strategy 2: Try shell activation
        if (await this.tryShellActivation(dependencies)) return;
        
        // Strategy 3: Try system python with --user (macOS with break-system-packages)
        if (await this.trySystemInstallWithUser(dependencies)) return;
        
        // Strategy 4: Try with --break-system-packages for Homebrew Python
        if (this.isMacOS && this.pythonSource === 'homebrew') {
            if (await this.tryBreakSystemPackages(dependencies)) return;
        }
        
        // Strategy 5: Suggest pipx installation
        this.suggestPipxAlternative(dependencies);
        throw new Error('All installation strategies failed. Please see suggestions above.');
    }

    async tryVenvInstall(dependencies) {
        if (!fs.existsSync(this.venvPython)) {
            this.log(`Virtual environment Python not found at ${this.venvPython}`, 'warning');
            return false;
        }

        try {
            this.log('Trying virtual environment installation...', 'progress');
            const installCmd = `"${this.venvPython}" -m pip install ${dependencies.join(' ')}`;
            await this.runCommand(installCmd);
            this.log('✅ Dependencies installed in virtual environment', 'success');
            return true;
        } catch (error) {
            this.log(`Virtual environment installation failed: ${error.message}`, 'warning');
            return false;
        }
    }

    async tryShellActivation(dependencies) {
        if (!fs.existsSync(this.venvActivate)) {
            this.log(`Activation script not found at ${this.venvActivate}`, 'warning');
            return false;
        }

        try {
            this.log('Trying shell activation method...', 'progress');
            const activateCmd = this.isWindows
                ? `"${this.venvActivate}" && pip install ${dependencies.join(' ')}`
                : `source "${this.venvActivate}" && pip install ${dependencies.join(' ')}`;
                
            await this.runCommand(activateCmd, { shell: true });
            this.log('✅ Dependencies installed via shell activation', 'success');
            return true;
        } catch (error) {
            this.log(`Shell activation failed: ${error.message}`, 'warning');
            return false;
        }
    }

    async trySystemInstallWithUser(dependencies) {
        try {
            this.log('Trying system Python with --user flag...', 'progress');
            const userCmd = `${this.pythonCmd} -m pip install --user ${dependencies.join(' ')}`;
            await this.runCommand(userCmd);
            this.log('✅ Dependencies installed with system Python (--user)', 'success');
            return true;
        } catch (error) {
            this.log(`System Python --user installation failed: ${error.message}`, 'warning');
            return false;
        }
    }

    async tryBreakSystemPackages(dependencies) {
        try {
            this.log('Trying Homebrew Python with --break-system-packages...', 'progress');
            const breakCmd = `${this.pythonCmd} -m pip install --break-system-packages ${dependencies.join(' ')}`;
            await this.runCommand(breakCmd);
            this.log('✅ Dependencies installed with --break-system-packages', 'success');
            return true;
        } catch (error) {
            this.log(`Break-system-packages installation failed: ${error.message}`, 'warning');
            return false;
        }
    }

    suggestPipxAlternative(dependencies) {
        this.log('🚨 All automatic installation methods failed', 'error');
        this.log('', 'info');
        this.log('💡 MANUAL INSTALLATION OPTIONS:', 'info');
        this.log('', 'info');
        
        if (this.isMacOS) {
            this.log('📋 Option 1: Use pipx (Recommended for macOS)', 'info');
            console.log('   brew install pipx');
            dependencies.forEach(dep => {
                console.log(`   pipx install ${dep.split('>=')[0]}`);
            });
            this.log('', 'info');
            
            this.log('📋 Option 2: Manual virtual environment', 'info');
            console.log(`   python3 -m venv ${this.drmsEnvPath}`);
            console.log(`   source ${this.drmsEnvPath}/bin/activate`);
            console.log(`   pip install ${dependencies.join(' ')}`);
            this.log('', 'info');
        }
        
        this.log('📋 Option 3: Use system Python with override', 'info');
        console.log(`   ${this.pythonCmd} -m pip install --break-system-packages ${dependencies.join(' ')}`);
        this.log('', 'info');
        this.log('⚠️  After manual installation, run: drms config', 'warning');
    }

    async testInstallation() {
        this.log('Testing installation...', 'progress');
        
        const testScript = `
import mcp
import chromadb
import sentence_transformers
import requests
import bs4
import pydantic_settings
print("All dependencies imported successfully")
        `;
        
        // Try different Python environments in order of preference
        const testMethods = [
            // 1. Virtual environment python
            {
                name: 'virtual environment',
                cmd: fs.existsSync(this.venvPython) ? this.venvPython : null
            },
            // 2. Shell activation
            {
                name: 'shell activation',
                cmd: fs.existsSync(this.venvActivate) ? 
                    (this.isWindows ? 
                        `"${this.venvActivate}" && python` : 
                        `source "${this.venvActivate}" && python`) : null
            },
            // 3. System python
            {
                name: 'system Python',
                cmd: this.pythonCmd
            }
        ];

        for (const method of testMethods) {
            if (!method.cmd) continue;
            
            try {
                const testCmd = method.cmd.includes('&&') ? 
                    `${method.cmd} -c "${testScript}"` :
                    `"${method.cmd}" -c "${testScript}"`;
                    
                await this.runCommand(testCmd, { 
                    silent: true, 
                    shell: method.cmd.includes('&&')
                });
                
                this.log(`✅ Dependencies working correctly via ${method.name}`, 'success');
                return true;
            } catch (error) {
                this.log(`${method.name} test failed: ${error.message}`, 'warning');
                continue;
            }
        }
        
        this.log('⚠️ Dependency tests failed, but installation may still work in IDE', 'warning');
        this.log('Try running: drms config', 'info');
        return false;
    }

    generateConfiguration() {
        this.log('Generating IDE configuration...', 'progress');
        
        const nodeModulesPath = path.dirname(path.dirname(__filename));
        const srcPath = path.join(nodeModulesPath, 'src');
        
        // Use virtual environment python if it exists, otherwise system python
        const pythonExecutable = fs.existsSync(this.venvPython) ? this.venvPython : this.pythonCmd;
        
        const config = {
            mcpServers: {
                drms: {
                    command: pythonExecutable,
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