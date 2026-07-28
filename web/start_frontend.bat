@echo off
chcp 65001 >nul
REM 启动前端服务

echo ========================================
echo 启动 YOLO-RKNN Web 前端服务
echo ========================================

REM 检查node_modules是否存在
if not exist "%~dp0frontend\node_modules" (
    echo [警告] node_modules不存在，正在安装依赖...
    cd /d "%~dp0frontend"
    call npm install
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo 启动前端服务（端口: 3000）
echo 访问地址: http://localhost:3000
echo.
echo 按 Ctrl+C 停止服务
echo ========================================

REM 启动前端开发服务器
cd /d "%~dp0frontend"
call npm run dev