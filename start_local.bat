@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "VENV_DIR=%ROOT_DIR%.venv"

echo [setup] Checking environment...

:: 1. Python Venv
:: Check if venv exists but is invalid (e.g. created by WSL/Linux)
if exist "%VENV_DIR%" (
    if not exist "%VENV_DIR%\Scripts\activate.bat" (
        echo [setup] Detected invalid or Linux-style virtual environment. Cleaning up...
        rmdir /s /q "%VENV_DIR%"
    )
)

:: Check Python version
echo [setup] Checking Python version...
for /f "tokens=2 delims= " %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [setup] Detected Python %PYTHON_VERSION%

:: Extract major and minor version
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

:: Block Python 3.13+ due to incompatibility
if %PYTHON_MAJOR% GEQ 3 if %PYTHON_MINOR% GEQ 13 (
    echo.
    echo ========================================================================
    echo [ERROR] Python %PYTHON_VERSION% is NOT supported!
    echo ========================================================================
    echo.
    echo This project requires Python 3.10, 3.11, or 3.12.
    echo.
    echo WHY: PaddlePaddle 3.1.1 requires numpy ^<2.0, but Python 3.13
    echo      only has numpy 2.x wheels available. This creates an
    echo      unsolvable dependency conflict.
    echo.
    echo SOLUTION: Please install Python 3.12 from:
    echo           https://www.python.org/downloads/
    echo.
    echo After installing Python 3.12:
    echo   1. Delete the .venv folder in this directory
    echo   2. Run this script again
    echo.
    echo ========================================================================
    pause
    exit /b 1
)

if not exist "%VENV_DIR%" (
    echo [setup] Creating Python virtual environment...
    python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"

:: 2. Backend Deps
:: Changed marker to v3 to force re-install with new numpy version
if not exist "%VENV_DIR%\.deps_installed_v3" (
    echo [setup] Installing backend dependencies...
    
    :: Configure pip to use Aliyun mirror to fix SSL/Connection issues
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
    
    :: Upgrade essential build tools first
    python -m pip install --upgrade pip setuptools wheel
    
    pip install -r "%ROOT_DIR%backend\requirements.txt"
    
    if %errorlevel% neq 0 (
        echo [error] Dependency installation failed!
        pause
        exit /b %errorlevel%
    )
    
    type nul > "%VENV_DIR%\.deps_installed_v3"
)

:: 3. Frontend Deps
if not exist "%ROOT_DIR%frontend\node_modules" (
    echo [setup] Installing frontend dependencies...
    cd "%ROOT_DIR%frontend"
    call npm install
    cd "%ROOT_DIR%"
)

:: 4. Start Services
echo [start] Starting FastAPI Backend...
:: Start in a new window, activate venv, and run uvicorn
start "CoverOCR Backend" cmd /k "call ^"%VENV_DIR%\Scripts\activate.bat^" && cd /d ^"%ROOT_DIR%^" && uvicorn backend.app.main:app --reload --reload-dir backend --host 0.0.0.0 --port 8000"

echo [start] Starting Vite Frontend...
cd "%ROOT_DIR%frontend"
start "CoverOCR Frontend" cmd /k "npm run dev -- --host"
cd "%ROOT_DIR%"

echo.
echo [ready] Services are launching in new windows.
echo         Backend:  http://localhost:8000/docs
echo         Frontend: http://localhost:5173
echo.
echo To stop services, close the new windows or run stop_local.bat
pause
