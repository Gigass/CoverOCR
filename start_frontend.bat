@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "FRONT_DIR=%ROOT_DIR%frontend"
set "FRONT_MARK=%FRONT_DIR%\.deps_installed_v1"
set "FRONT_PORT=5173"
set "FRONT_CMD=call npm run dev -- --host --port %FRONT_PORT% || pause"

echo [frontend] Checking environment...

:: Check Node.js exists
where node >nul 2>&1
if errorlevel 1 (
    echo [error] Node.js not found. Please install Node.js 18 or newer: https://nodejs.org/
    pause
    exit /b 1
)

:: Frontend dependencies
if not exist "%FRONT_MARK%" (
    echo [frontend] Installing frontend dependencies...
    pushd "%FRONT_DIR%"
    call npm install
    if %errorlevel% neq 0 (
        echo [error] Frontend dependency installation failed!
        popd
        pause
        exit /b %errorlevel%
    )
    popd
    type nul > "%FRONT_MARK%"
)

echo [frontend] Starting Vite Frontend (http://localhost:%FRONT_PORT%)...
cd /d "%FRONT_DIR%"
%FRONT_CMD%
