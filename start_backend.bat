@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "VENV_DIR=%ROOT_DIR%.venv"
set "BACK_REQ=%ROOT_DIR%backend\requirements.txt"
set "BACK_MARK=%VENV_DIR%\.deps_installed_v3"
set "BACK_PORT=8000"

echo [backend] Checking environment...

:: Create venv if missing
if not exist "%VENV_DIR%" (
    echo [backend] Creating Python virtual environment...
    python -m venv "%VENV_DIR%"
)

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [error] Virtual environment missing or locked.
    echo Please delete .venv manually and rerun this script.
    pause
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"

:: Backend dependencies
if not exist "%BACK_MARK%" (
    echo [backend] Installing backend dependencies...
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
    python -m pip install --upgrade pip setuptools wheel
    pip install -r "%BACK_REQ%"
    if %errorlevel% neq 0 (
        echo [error] Dependency installation failed!
        pause
        exit /b %errorlevel%
    )
    type nul > "%BACK_MARK%"
)

echo [backend] Starting FastAPI Backend (http://localhost:%BACK_PORT%/docs)...
cd /d "%ROOT_DIR%"
uvicorn backend.app.main:app --reload --reload-dir backend --host 0.0.0.0 --port %BACK_PORT%

pause
