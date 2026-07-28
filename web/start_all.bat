@echo off
chcp 65001 >nul

echo ========================================
echo YOLO-RKNN Platform Quick Start
echo ========================================

echo.
echo [1/3] Starting backend service...
start "YOLO-RKNN Backend" cmd /c "cd /d %~dp0 && start_backend.bat"
timeout /t 3 /nobreak >nul

echo.
echo [2/3] Starting frontend service...
start "YOLO-RKNN Frontend" cmd /c "cd /d %~dp0 && start_frontend.bat"
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Checking service status...
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo ========================================
echo Start Complete!
echo ========================================
echo.
echo Tips:
echo - Backend and frontend are running in separate windows
echo - Close the window to stop the service
echo - Or run stop_all.bat to stop all services
echo.

REM Auto open browser
timeout /t 3 /nobreak >nul
start http://localhost:3000

pause