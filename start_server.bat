@echo off
echo Starting Endstone MCP Server...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if MCP is installed
python -c "import mcp" >nul 2>&1
if errorlevel 1 (
    echo Installing MCP dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo MCP Server is starting...
echo Press Ctrl+C to stop the server
echo.

python endstone_mcp_server.py

echo.
echo MCP Server stopped.
pause