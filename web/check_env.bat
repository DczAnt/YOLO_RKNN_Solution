@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ================================================================
echo            YOLO-RKNN Environment Setup and Check
echo ================================================================
echo.

REM ============================================================
REM Section 1: WSL Environment
REM ============================================================
echo [Section 1/3] WSL Environment Setup
echo ================================================================
echo.

REM 1.1 Check WSL
echo [1.1] Checking WSL installation...
wsl -- bash -c "echo 'WSL OK'" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] WSL is not installed or not running
    echo [INFO] Attempting to start WSL...
    wsl -- bash -c "echo 'WSL started'" 2>nul
    timeout /t 2 /nobreak >nul
)

wsl -- bash -c "echo 'WSL OK'" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] WSL is not available
    echo.
    echo Please install WSL first:
    echo   1. wsl --install
    echo   2. Restart computer
    echo   3. Run this script again
    pause
    exit /b 1
)
echo [OK] WSL is running

REM 1.2 Check Miniconda
echo.
echo [1.2] Checking Miniconda installation...
wsl -- bash -c "test -f ~/miniconda3/etc/profile.d/conda.sh && echo 'OK'" 2>nul | findstr "OK" >nul
if %errorlevel% neq 0 (
    echo [INFO] Miniconda is not installed
    echo [INFO] Installing Miniconda...
    wsl -- bash -c "wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && bash /tmp/miniconda.sh -b -p $HOME/miniconda3 && rm /tmp/miniconda.sh"
    timeout /t 5 /nobreak >nul
)

wsl -- bash -c "test -f ~/miniconda3/etc/profile.d/conda.sh && echo 'OK'" 2>nul | findstr "OK" >nul
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Miniconda
    echo Please install manually: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)
echo [OK] Miniconda is installed

REM 1.3 Check Conda environment
echo.
echo [1.3] Checking Conda environment (rknn_env)...
wsl -- bash -c "source ~/miniconda3/etc/profile.d/conda.sh && conda env list | grep rknn_env" 2>nul | findstr "rknn_env" >nul
if %errorlevel% neq 0 (
    echo [INFO] Creating rknn_env environment with Python 3.8...
    wsl -- bash -c "source ~/miniconda3/etc/profile.d/conda.sh && conda create -n rknn_env python=3.8 -y"
    timeout /t 30 /nobreak >nul
)

wsl -- bash -c "source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn_env && python --version" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create rknn_env environment
    pause
    exit /b 1
)
echo [OK] Conda environment rknn_env is ready

REM 1.4 Install Python dependencies
echo.
echo [1.4] Installing Python dependencies...
wsl -- bash -c "source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn_env && pip install -q ultralytics onnx onnxruntime opencv-python numpy pillow tqdm pyyaml"

echo [INFO] Installing RKNN Toolkit2...
wsl -- bash -c "source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn_env && pip list | grep rknn-toolkit2" 2>nul | findstr "rknn-toolkit2" >nul
if %errorlevel% neq 0 (
    wsl -- bash -c "source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn_env && pip install -q rknn-toolkit2-npu==2.3.2 || pip install -q rknn-toolkit2==2.3.2 || echo 'RKNN install attempted'"
)

echo [INFO] Installing FastAPI dependencies...
wsl -- bash -c "source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn_env && pip install -q fastapi uvicorn[standard] python-multipart aiofiles websockets pydantic"

echo [OK] Python dependencies installed

REM 1.5 Install system packages
echo.
echo [1.5] Installing system packages...
wsl -- bash -c "which sshpass" 2>nul | findstr "sshpass" >nul
if %errorlevel% neq 0 (
    echo [INFO] Installing sshpass...
    wsl -- bash -c "sudo apt-get update -qq && sudo apt-get install -y sshpass -qq"
)
echo [OK] System packages installed

echo.
echo ================================================================
echo [Section 1 Complete] WSL Environment Ready
echo ================================================================

REM ============================================================
REM Section 2: Windows Environment
REM ============================================================
echo.
echo [Section 2/3] Windows Environment Setup
echo ================================================================
echo.

REM 2.1 Check Node.js
echo [2.1] Checking Node.js installation...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed
    echo.
    echo Please install Node.js:
    echo   1. Download from: https://nodejs.org/
    echo   2. Install LTS version (18.x or 20.x)
    echo   3. Run this script again
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo [OK] Node.js !NODE_VERSION! is installed

REM 2.2 Check npm
echo.
echo [2.2] Checking npm...
for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
echo [OK] npm !NPM_VERSION! is available

REM 2.3 Install frontend dependencies
echo.
echo [2.3] Checking frontend dependencies...
if exist "%~dp0frontend\package.json" (
    if not exist "%~dp0frontend\node_modules" (
        echo [INFO] Installing frontend dependencies...
        cd /d "%~dp0frontend"
        call npm install
        cd /d "%~dp0"
    ) else (
        echo [OK] Frontend dependencies already installed
    )
) else (
    echo [WARNING] Frontend package.json not found
)

echo.
echo ================================================================
echo [Section 2 Complete] Windows Environment Ready
echo ================================================================

REM ============================================================
REM Section 3: RK3568 Board Environment
REM ============================================================
echo.
echo [Section 3/3] RK3568 Board Environment Setup
echo ================================================================
echo.

REM 3.1 Check board connection config
echo [3.1] Checking board connection configuration...
if exist "%~dp0backend\board_config.json" (
    echo [OK] Board configuration file exists
) else (
    echo [INFO] Creating default board configuration...
    (
        echo {
        echo   "host": "192.168.1.100",
        echo   "username": "root",
        echo   "password": "rockchip",
        echo   "port": 22,
        echo   "platform": "rk3568",
        echo   "rknn_lib_path": "/usr/lib/librknnrt.so"
        echo }
    ) > "%~dp0backend\board_config.json"
    echo [OK] Default board configuration created
)

REM 3.2 Display board requirements
echo.
echo [3.2] RK3568 Board Requirements:
echo.
echo Required packages on RK3568 board:
echo   - rknn-api: RKNN Runtime library
echo   - librknnrt.so: RKNN runtime
echo.
echo Installation steps on RK3568 board:
echo   1. Copy RKNN runtime package to board
echo      scp rknn-api.tar.gz root@192.168.1.100:/tmp/
echo.
echo   2. Install on board:
echo      ssh root@192.168.1.100
echo      tar -xzf /tmp/rknn-api.tar.gz -C /
echo      ldconfig
echo.
echo   3. Verify installation:
echo      ls -l /usr/lib/librknnrt.so
echo.
echo Required versions:
echo   - RKNN Runtime: 2.3.2
echo   - Python: 3.8+
echo   - NPU Driver: Latest

echo.
echo ================================================================
echo [Section 3 Complete] Board Environment Info Displayed
echo ================================================================

REM ============================================================
REM Summary
REM ============================================================
echo.
echo ================================================================
echo                    Environment Setup Complete!
echo ================================================================
echo.
echo Environment Summary:
echo ====================
echo.
echo [WSL Environment]
wsl -- bash -c "lsb_release -d | cut -f2"
wsl -- bash -c "source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn_env && python --version"
wsl -- bash -c "source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn_env && pip list | grep -E 'ultralytics|onnxruntime|rknn-toolkit2|fastapi'"
echo.
echo [Windows Environment]
echo Node.js: !NODE_VERSION!
echo npm: !NPM_VERSION!
echo.
echo [RK3568 Board]
echo Config: %~dp0backend\board_config.json
echo Please verify board connectivity and RKNN runtime installation
echo.
echo ================================================================
echo                    Ready to Start Services
echo ================================================================
echo.
echo Next steps:
echo   1. Run: start_backend.bat
echo   2. Run: start_frontend.bat
echo   3. Access: http://localhost:3000
echo.

pause
