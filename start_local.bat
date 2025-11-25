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

if not exist "%VENV_DIR%" (
    echo [setup] Creating Python virtual environment...
    python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"

:: 2. Backend Deps
:: Changed marker to v2 to force re-install for users with broken v1 installs
if not exist "%VENV_DIR%\.deps_installed_v2" (
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
    
    type nul > "%VENV_DIR%\.deps_installed_v2"
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
start "CoverOCR Backend" cmd /k "call "%VENV_DIR%\Scripts\activate.bat" && cd /d "%ROOT_DIR%" && uvicorn backend.app.main:app --reload --reload-dir backend --host 0.0.0.0 --port 8000"

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
