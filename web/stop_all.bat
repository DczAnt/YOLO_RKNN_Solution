@echo off
chcp 65001 >nul

echo ========================================
echo Stop YOLO-RKNN All Services
echo ========================================

echo.
echo [1/2] Stopping backend service...
wsl -- bash -c "pkill -f 'uvicorn.*main:app' 2>/dev/null || true"
wsl -- bash -c "pkill -f 'python.*main.py' 2>/dev/null || true"
echo [OK] Backend stopped

echo.
echo [2/2] Stopping frontend service...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *vite*" 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)
echo [OK] Frontend stopped

echo.
echo ========================================
echo All Services Stopped
echo ========================================
echo.

pause