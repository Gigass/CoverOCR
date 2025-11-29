@echo off
setlocal enabledelayedexpansion

echo [shutdown] Stopping services...

:: Kill process on port 8000 (Backend)
set "FOUND_8000=0"
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING" 2^>nul') do (
    echo [shutdown] Killing process on port 8000 (PID: %%a)...
    taskkill /f /pid %%a >nul 2>&1
    set "FOUND_8000=1"
)
if !FOUND_8000!==0 echo [shutdown] No process found on port 8000

:: Kill process on port 5173 (Frontend)
set "FOUND_5173=0"
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5173" ^| find "LISTENING" 2^>nul') do (
    echo [shutdown] Killing process on port 5173 (PID: %%a)...
    taskkill /f /pid %%a >nul 2>&1
    set "FOUND_5173=1"
)
if !FOUND_5173!==0 echo [shutdown] No process found on port 5173

echo.
echo [shutdown] Done.
pause
