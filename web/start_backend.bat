@echo off
chcp 65001 >nul

echo ========================================
echo Start YOLO-RKNN Backend Service
echo ========================================

REM Check if WSL is running
wsl -- bash -c "echo 'WSL OK'" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] WSL is not running, starting now...
    wsl -- bash -c "echo 'WSL started'" 2>nul
    timeout /t 2 /nobreak >nul
)

REM Check WSL again
wsl -- bash -c "echo 'WSL OK'" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start WSL
    echo Please check if WSL is installed: wsl --list
    pause
    exit /b 1
)
echo [OK] WSL is running

echo.
echo Starting backend service (port: 8000)
echo Access URL: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop
echo ========================================

REM Start backend in WSL with conda environment
wsl -- bash -c "source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn_env && cd /mnt/e/AIcomm/YOLO_RKNN_Solution/web/backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"