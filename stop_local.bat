@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "VENV_DIR=%ROOT_DIR%.venv"

echo [shutdown] Stopping services...

:: Kill processes bound to backend/frontend ports and any CoverOCR python/node tasks
powershell -NoLogo -NoProfile -Command ^
  "$ports = 8000,5173;" ^
  "$pids = @();" ^
  "foreach($p in $ports){$pids += Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue | Select-Object -Expand OwningProcess -Unique};" ^
  "$procs = Get-Process python,pythonw,uvicorn,node,npm -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path -like '*CoverOCR*' };" ^
  "$ids = ($pids + $procs.Id) | Sort-Object -Unique | Where-Object { $_ -gt 0 };" ^
  "if(-not $ids){ Write-Host '[shutdown] No matching processes found'; } else { $ids | ForEach-Object { Write-Host \"[shutdown] Killing PID $_\"; Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } }"

:: Also close windows started by start_local
taskkill /f /fi "WINDOWTITLE eq CoverOCR Backend" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq CoverOCR Frontend" >nul 2>&1

echo.
echo [shutdown] Done.
pause
