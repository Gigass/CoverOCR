@echo off
echo [shutdown] Stopping services...

:: Kill process on port 8000 (Backend)
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo Killing process on port 8000 (PID: %%a)...
    taskkill /f /pid %%a >nul 2>&1
)

:: Kill process on port 5173 (Frontend)
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5173" ^| find "LISTENING"') do (
    echo Killing process on port 5173 (PID: %%a)...
    taskkill /f /pid %%a >nul 2>&1
)

echo [shutdown] Done.
pause
