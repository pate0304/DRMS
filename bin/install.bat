@echo off
setlocal enabledelayedexpansion

set DRMS_VERSION=1.0.0
set INSTALL_DIR=%USERPROFILE%\.drms
set BIN_DIR=%USERPROFILE%\.local\bin

echo 🚀 Installing DRMS v%DRMS_VERSION%...

REM Create directories
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 3 is required but not installed.
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
echo Found Python %PYTHON_VERSION%

REM Create virtual environment
echo 📦 Creating Python virtual environment...
python -m venv "%INSTALL_DIR%\venv"
call "%INSTALL_DIR%\venv\Scripts\activate.bat"

REM Install pip dependencies
echo 📦 Installing Python dependencies...
python -m pip install --upgrade pip

REM Check if we're installing from source
if exist "requirements.txt" (
    pip install -r requirements.txt
    xcopy /E /I /Y . "%INSTALL_DIR%\src"
) else (
    pip install drms-mcp-server
)

REM Create CLI wrapper batch file
echo 🔧 Creating CLI wrapper...
(
echo @echo off
echo set DRMS_HOME=%%USERPROFILE%%\.drms
echo call "%%DRMS_HOME%%\venv\Scripts\activate.bat"
echo if exist "%%DRMS_HOME%%\src\mcp_server.py" ^(
echo     cd /d "%%DRMS_HOME%%\src"
echo     python mcp_server.py %%*
echo ^) else ^(
echo     drms-server %%*
echo ^)
) > "%BIN_DIR%\drms.bat"

REM Create uninstall script
(
echo @echo off
echo echo 🗑️  Uninstalling DRMS...
echo rmdir /s /q "%%USERPROFILE%%\.drms"
echo del "%%USERPROFILE%%\.local\bin\drms.bat"
echo echo ✅ DRMS uninstalled successfully
echo pause
) > "%INSTALL_DIR%\uninstall.bat"

REM Create config directory
if not exist "%INSTALL_DIR%\config" mkdir "%INSTALL_DIR%\config"

REM Copy example configs
if exist "configs" (
    xcopy /E /I /Y configs "%INSTALL_DIR%\config"
)

REM Check if BIN_DIR is in PATH
echo %PATH% | find /i "%BIN_DIR%" >nul
if errorlevel 1 (
    echo 📝 Adding %BIN_DIR% to PATH...
    setx PATH "%PATH%;%BIN_DIR%"
    echo ⚠️  Please restart your command prompt for PATH changes to take effect
)

echo.
echo ✅ DRMS installed successfully!
echo.
echo 📍 Installation directory: %INSTALL_DIR%
echo 🔧 Configuration directory: %INSTALL_DIR%\config
echo 🗑️  To uninstall: %INSTALL_DIR%\uninstall.bat
echo.
echo 🎯 Quick start:
echo    drms --help
echo    drms start
echo.
echo 🔗 For more information: https://github.com/pate0304/DRMS

pause