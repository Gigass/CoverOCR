@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "VENV_DIR=%ROOT_DIR%.venv"
set "FRONT_DIR=%ROOT_DIR%frontend"
set "BACK_REQ=%ROOT_DIR%backend\requirements.txt"
set "BACK_MARK=%VENV_DIR%\.deps_installed_v3"
set "FRONT_MARK=%FRONT_DIR%\.deps_installed_v1"

echo [setup] Checking environment...

:: Ensure venv is valid; remove Linux-style venvs
if exist "%VENV_DIR%" (
    if not exist "%VENV_DIR%\Scripts\activate.bat" (
        echo [setup] Detected invalid virtual environment. Removing...
        powershell -NoLogo -NoProfile -Command "Remove-Item -Recurse -Force '%VENV_DIR%' -ErrorAction SilentlyContinue"
    )
)

:: Check Node.js exists (skip strict version parsing to avoid locale issues)
where node >nul 2>&1
if errorlevel 1 (
    echo [error] Node.js not found. Please install Node.js 18 or newer: https://nodejs.org/
    pause
    exit /b 1
)

:: Create venv if missing
if not exist "%VENV_DIR%" (
    echo [setup] Creating Python virtual environment...
    python -m venv "%VENV_DIR%"
)

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [error] Virtual environment missing or locked.
    echo Close running python/uvicorn processes ^(run stop_local.bat or kill via Task Manager^), delete .venv manually, then rerun this script.
    pause
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"

:: Backend dependencies
if not exist "%BACK_MARK%" (
    echo [setup] Installing backend dependencies...
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

:: Frontend dependencies
if not exist "%FRONT_MARK%" (
    echo [setup] Installing frontend dependencies...
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

:: Start services
echo [start] Starting FastAPI Backend...
start "CoverOCR Backend" cmd /k "call ^"%VENV_DIR%\Scripts\activate.bat^" && cd /d ^"%ROOT_DIR%^" && uvicorn backend.app.main:app --reload --reload-dir backend --host 0.0.0.0 --port 8000"

echo [start] Starting Vite Frontend...
start "CoverOCR Frontend" cmd /k "cd /d ^"%FRONT_DIR%^" && npm run dev -- --host"

echo.
echo [ready] Services are launching in new windows.
echo         Backend:  http://localhost:8000/docs
echo         Frontend: http://localhost:5173
echo.
echo To stop services, close the new windows or run stop_local.bat
pause
