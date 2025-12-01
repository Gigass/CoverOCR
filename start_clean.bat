@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "FORCE=%1"

echo [clean] Forcing a fresh setup: will remove the Python venv and frontend node_modules, then rerun start_local.bat.

:: Ensure running services are stopped before deleting files
if exist "%ROOT_DIR%stop_local.bat" (
    echo [clean] Stopping running services...
    call "%ROOT_DIR%stop_local.bat"
)

if /I "%FORCE%"=="--yes" goto :confirmed

echo.
echo This will DELETE:
echo   %ROOT_DIR%.venv
if exist "%ROOT_DIR%frontend\node_modules" echo   %ROOT_DIR%frontend\node_modules
echo   dependency markers (.deps_installed_v3 / .deps_installed_v1)
echo.
choice /C YN /M "Proceed?"
if errorlevel 2 (
    echo [clean] Aborted.
    exit /b 1
)

:confirmed
if exist "%ROOT_DIR%.venv" (
    echo [clean] Removing .venv...
    rmdir /s /q "%ROOT_DIR%.venv"
    if exist "%ROOT_DIR%.venv" (
        echo [clean] .venv still exists, forcing removal via PowerShell...
        powershell -NoLogo -NoProfile -Command "Remove-Item -Recurse -Force '%ROOT_DIR%.venv' -ErrorAction SilentlyContinue"
        if exist "%ROOT_DIR%.venv" (
            echo [clean] .venv is still locked. Close any python/uvicorn processes (run stop_local.bat or end from Task Manager) then rerun this script.
            pause
            exit /b 1
        )
    )
)

if exist "%ROOT_DIR%frontend\node_modules" (
    echo [clean] Removing frontend\node_modules...
    rmdir /s /q "%ROOT_DIR%frontend\node_modules"
)

if exist "%ROOT_DIR%.venv\.deps_installed_v3" del /f /q "%ROOT_DIR%.venv\.deps_installed_v3"
if exist "%ROOT_DIR%frontend\.deps_installed_v1" del /f /q "%ROOT_DIR%frontend\.deps_installed_v1"

echo [clean] Running start_local.bat for a fresh install...
call "%ROOT_DIR%start_local.bat"

endlocal
