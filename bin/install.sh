#!/bin/bash

set -e

DRMS_VERSION="1.0.0"
INSTALL_DIR="${HOME}/.drms"
BIN_DIR="${HOME}/.local/bin"

echo "🚀 Installing DRMS v${DRMS_VERSION}..."

# Create directories
mkdir -p "${INSTALL_DIR}" "${BIN_DIR}"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ "$(printf '%s\n' "3.8" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.8" ]]; then
    echo "❌ Python 3.8+ is required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Check Node.js version (optional)
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v | sed 's/v//')
    if [[ "$(printf '%s\n' "16.0.0" "$NODE_VERSION" | sort -V | head -n1)" != "16.0.0" ]]; then
        echo "⚠️  Node.js 16+ recommended. Current version: $NODE_VERSION"
    fi
fi

# Create virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv "${INSTALL_DIR}/venv"
source "${INSTALL_DIR}/venv/bin/activate"

# Install pip dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip

# Check if we're installing from source or release
if [[ -f "requirements.txt" ]]; then
    # Installing from source
    pip install -r requirements.txt
    cp -r . "${INSTALL_DIR}/src"
else
    # Installing from PyPI (future)
    pip install drms-mcp-server
fi

# Create CLI wrapper script
echo "🔧 Creating CLI wrapper..."
cat > "${BIN_DIR}/drms" << 'EOF'
#!/bin/bash
DRMS_HOME="${HOME}/.drms"
source "${DRMS_HOME}/venv/bin/activate"

if [[ -f "${DRMS_HOME}/src/mcp_server.py" ]]; then
    # Source installation
    cd "${DRMS_HOME}/src"
    exec python mcp_server.py "$@"
else
    # PyPI installation
    exec drms-server "$@"
fi
EOF

chmod +x "${BIN_DIR}/drms"

# Create uninstall script
cat > "${INSTALL_DIR}/uninstall.sh" << 'EOF'
#!/bin/bash
echo "🗑️  Uninstalling DRMS..."
rm -rf "${HOME}/.drms"
rm -f "${HOME}/.local/bin/drms"
echo "✅ DRMS uninstalled successfully"
EOF

chmod +x "${INSTALL_DIR}/uninstall.sh"

# Create config directory
mkdir -p "${INSTALL_DIR}/config"

# Copy example configs
if [[ -d "configs" ]]; then
    cp -r configs/* "${INSTALL_DIR}/config/"
fi

# Add to PATH if not already there
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo "📝 Adding ${BIN_DIR} to PATH..."
    
    # Detect shell
    if [[ -n "$ZSH_VERSION" ]]; then
        SHELL_RC="${HOME}/.zshrc"
    elif [[ -n "$BASH_VERSION" ]]; then
        SHELL_RC="${HOME}/.bashrc"
    else
        SHELL_RC="${HOME}/.profile"
    fi
    
    echo "export PATH=\"${BIN_DIR}:\$PATH\"" >> "$SHELL_RC"
    echo "⚠️  Please restart your shell or run: source $SHELL_RC"
fi

echo ""
echo "✅ DRMS installed successfully!"
echo ""
echo "📍 Installation directory: ${INSTALL_DIR}"
echo "🔧 Configuration directory: ${INSTALL_DIR}/config"
echo "🗑️  To uninstall: ${INSTALL_DIR}/uninstall.sh"
echo ""
echo "🎯 Quick start:"
echo "   drms --help"
echo "   drms start"
echo ""
echo "🔗 For more information: https://github.com/pate0304/DRMS"