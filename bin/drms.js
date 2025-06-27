#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const DRMS_HOME = path.join(os.homedir(), '.drms');
const VENV_PATH = path.join(DRMS_HOME, 'venv');

function findPythonExecutable() {
    const isWindows = process.platform === 'win32';
    
    // Check if DRMS venv exists
    if (fs.existsSync(VENV_PATH)) {
        if (isWindows) {
            return path.join(VENV_PATH, 'Scripts', 'python.exe');
        } else {
            return path.join(VENV_PATH, 'bin', 'python');
        }
    }
    
    // Fall back to system Python
    return 'python3';
}

function findMCPServer() {
    // Check if source installation exists
    const sourcePath = path.join(DRMS_HOME, 'src', 'mcp_server.py');
    if (fs.existsSync(sourcePath)) {
        return { type: 'source', path: sourcePath };
    }
    
    // Check for npm package installation (resolve from this script's location)
    try {
        const scriptPath = path.dirname(__filename);
        const npmServerPath = path.join(scriptPath, '..', 'mcp_server.py');
        if (fs.existsSync(npmServerPath)) {
            return { type: 'npm', path: npmServerPath };
        }
    } catch (e) {
        // Ignore resolution errors
    }
    
    // Fall back to installed package
    return { type: 'package', path: 'drms' };
}

function showHelp() {
    console.log(`
DRMS - Documentation RAG MCP Server v1.0.0

Usage: drms [command] [options]

Commands:
  start           Start the MCP server
  api            Start the REST API server
  add-source     Add a documentation source
  list-sources   List configured sources
  search         Search documentation
  test           Run tests
  setup          Run interactive setup
  config         Show configuration
  version        Show version

Options:
  --help, -h     Show this help message
  --port, -p     Specify port (default: 8000)
  --host         Specify host (default: localhost)
  --log-level    Set log level (DEBUG, INFO, WARNING, ERROR)

Examples:
  drms start
  drms api --port 8001
  drms add-source https://docs.python.org
  drms search "async functions"

For more information: https://github.com/pate0304/DRMS
`);
}

function main() {
    const args = process.argv.slice(2);
    
    if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
        showHelp();
        return;
    }
    
    const command = args[0];
    const pythonExe = findPythonExecutable();
    const server = findMCPServer();
    
    // Check if we can find a Python executable (for venv) or if python3 exists (for system)
    if (pythonExe !== 'python3' && !fs.existsSync(pythonExe)) {
        console.error('❌ DRMS not properly installed. Run: npm install -g drms-mcp-server');
        process.exit(1);
    }
    
    let pythonArgs;
    let workingDir;
    
    if (server.type === 'source') {
        pythonArgs = [server.path, ...args];
        workingDir = path.dirname(server.path);
    } else if (server.type === 'npm') {
        pythonArgs = [server.path, ...args];
        workingDir = path.dirname(server.path);
    } else {
        pythonArgs = ['-m', server.path, ...args];
        workingDir = DRMS_HOME;
    }
    
    // Set up environment
    const env = {
        ...process.env,
        DRMS_HOME: DRMS_HOME
    };
    
    // Add Python path for source and npm installations
    if (server.type === 'source' || server.type === 'npm') {
        const srcPath = path.join(path.dirname(server.path), 'src');
        env.PYTHONPATH = srcPath;
    }
    
    // Spawn Python process
    const child = spawn(pythonExe, pythonArgs, {
        cwd: workingDir,
        stdio: 'inherit',
        env: env
    });
    
    child.on('close', (code) => {
        if (code !== 0) {
            console.error(`❌ DRMS process exited with code ${code}`);
        }
        process.exit(code);
    });
    
    child.on('error', (err) => {
        console.error('❌ Failed to start DRMS:', err.message);
        process.exit(1);
    });
    
    // Handle Ctrl+C
    process.on('SIGINT', () => {
        child.kill('SIGINT');
    });
    
    process.on('SIGTERM', () => {
        child.kill('SIGTERM');
    });
}

if (require.main === module) {
    main();
}

module.exports = { main };