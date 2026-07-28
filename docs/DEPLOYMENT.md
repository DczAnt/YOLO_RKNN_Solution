# YOLO-RKNN 模型转换平台部署方案

## 文档信息

- **版本**: v1.0
- **日期**: 2026-06-15
- **适用环境**: Windows 11 + WSL Ubuntu + RK3568/RK3588

---

## 一、部署架构

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户访问层                                 │
│                    http://localhost:3000                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Windows 11 开发机                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              前端服务 (Vue3 + Vite)                        │  │
│  │              端口: 3000                                    │  │
│  │              技术: Vue3 + Element Plus + Axios            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              WSL Ubuntu 环境                               │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │         后端服务 (FastAPI)                          │  │  │
│  │  │         端口: 8000                                  │  │  │
│  │  │         环境: rknn_env (conda)                      │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                          ↓                                │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │         模型转换引擎                                │  │  │
│  │  │         - Ultralytics (PT→ONNX)                     │  │  │
│  │  │         - rknn-toolkit2 (ONNX→RKNN)                 │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓ SSH
┌─────────────────────────────────────────────────────────────────┐
│                   RK3568/RK3588 目标板                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              RKNN Runtime                                 │  │
│  │              - librknnrt.so                               │  │
│  │              - NPU驱动                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 组件说明

| 组件 | 位置 | 端口 | 说明 |
|------|------|------|------|
| 前端 | Windows | 3000 | Vue3 Web界面 |
| 后端 | WSL | 8000 | FastAPI服务 |
| 模型转换 | WSL | - | Python脚本 |
| 目标板 | RK板 | 22 | SSH连接 |

### 1.3 数据流向

```
用户上传PT模型
    ↓
前端发送转换请求
    ↓
后端调用转换脚本
    ↓
PT → ONNX (Ultralytics)
    ↓
ONNX → RKNN (rknn-toolkit2)
    ↓
返回RKNN模型
    ↓
用户下载或部署到RK板
```

---

## 二、环境准备

### 2.1 硬件要求

#### Windows开发机

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 4核 | 8核+ |
| 内存 | 8GB | 16GB+ |
| 存储 | 50GB可用 | 100GB+ SSD |
| GPU | 无需GPU | RTX系列（可选） |

#### RK目标板

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 型号 | RK3566 | RK3568/RK3588 |
| 内存 | 1GB | 2GB+ |
| 存储 | 4GB | 8GB+ eMMC/SD |
| 网络 | 有线网络 | 千兆网络 |

### 2.2 软件要求

#### Windows系统

| 软件 | 版本 | 说明 |
|------|------|------|
| Windows | 11 | 64位 |
| WSL | 2 | Ubuntu 22.04 |
| Node.js | 18.x/20.x | LTS版本 |
| Git | 最新 | 版本控制 |

#### WSL Ubuntu

| 软件 | 版本 | 说明 |
|------|------|------|
| Ubuntu | 22.04 | WSL发行版 |
| Miniconda | latest | Python环境管理 |
| Python | 3.8 | 虚拟环境 |
| rknn-toolkit2 | 2.3.2 | RKNN转换工具 |

#### RK目标板

| 软件 | 版本 | 说明 |
|------|------|------|
| RKNN Runtime | 2.3.2 | 推理运行时 |
| Python | 3.8+ | 脚本运行 |
| NPU驱动 | latest | 内核驱动 |

---

## 三、安装部署

### 3.1 快速部署（推荐）

#### 步骤1：获取项目

```cmd
# 克隆或复制项目到本地
# 项目位置：E:\AIcomm\YOLO_RKNN_Solution
```

#### 步骤2：一键环境配置

```cmd
# 运行环境检查脚本（自动安装所有依赖）
E:\AIcomm\YOLO_RKNN_Solution\web\check_env.bat
```

此脚本会自动完成：
- ✅ 检查并启动WSL Ubuntu
- ✅ 安装Miniconda
- ✅ 创建conda虚拟环境 rknn_env
- ✅ 安装所有Python依赖
- ✅ 安装系统包 sshpass
- ✅ 检查Windows Node.js
- ✅ 安装前端依赖
- ✅ 生成主板配置文件

#### 步骤3：启动服务

```cmd
# 方式1：分别启动
E:\AIcomm\YOLO_RKNN_Solution\web\start_backend.bat
E:\AIcomm\YOLO_RKNN_Solution\web\start_frontend.bat

# 方式2：一键启动
E:\AIcomm\YOLO_RKNN_Solution\web\start_all.bat
```

#### 步骤4：访问验证

打开浏览器访问：
- 前端界面：http://localhost:3000
- API文档：http://localhost:8000/docs
- API接口：http://localhost:8000

---

### 3.2 手动部署

#### 3.2.1 安装WSL

```powershell
# PowerShell (管理员)
wsl --install -d Ubuntu

# 重启电脑
# 首次启动设置用户名和密码
```

#### 3.2.2 安装Miniconda

```bash
# WSL Ubuntu
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
rm Miniconda3-latest-Linux-x86_64.sh

# 初始化
~/miniconda3/bin/conda init bash
source ~/.bashrc
```

#### 3.2.3 创建虚拟环境

```bash
conda create -n rknn_env python=3.8 -y
conda activate rknn_env
```

#### 3.2.4 安装Python依赖

```bash
conda activate rknn_env

# 核心依赖
pip install ultralytics onnx onnxruntime opencv-python numpy pillow tqdm pyyaml

# RKNN工具
pip install rknn-toolkit2-npu==2.3.2

# FastAPI
pip install fastapi uvicorn[standard] python-multipart aiofiles websockets pydantic
```

#### 3.2.5 安装系统包

```bash
sudo apt-get update
sudo apt-get install -y sshpass
```

#### 3.2.6 安装Windows Node.js

1. 下载：https://nodejs.org/
2. 安装LTS版本（18.x或20.x）
3. 验证：
   ```cmd
   node --version
   npm --version
   ```

#### 3.2.7 安装前端依赖

```cmd
cd E:\AIcomm\YOLO_RKNN_Solution\web\frontend
npm install
```

---

### 3.3 RK目标板部署

#### 3.3.1 安装RKNN Runtime

```bash
# 方法1：从GitHub下载
wget https://github.com/rockchip-linux/rknpu2/releases/download/v2.3.2/rknn-api-v2.3.2.tar.gz
tar -xzf rknn-api-v2.3.2.tar.gz -C /
ldconfig

# 方法2：从本地复制
# Windows端
scp rknn-api.tar.gz root@192.168.1.100:/tmp/

# RK板端
tar -xzf /tmp/rknn-api.tar.gz -C /
ldconfig
```

#### 3.3.2 安装Python依赖

```bash
# RK板端
apt-get update
apt-get install -y python3 python3-pip
pip3 install numpy opencv-python
```

#### 3.3.3 验证安装

```bash
# 检查RKNN库
ls -l /usr/lib/librknnrt.so

# 检查NPU
cat /sys/class/misc/rknpu/version

# 运行检查脚本
bash scripts/check_board_env.sh
```

---

## 四、配置说明

### 4.1 后端配置

#### 主板连接配置

文件：`web/backend/board_config.json`

```json
{
  "host": "192.168.1.100",
  "username": "root",
  "password": "rockchip",
  "port": 22,
  "platform": "rk3568",
  "rknn_lib_path": "/usr/lib/librknnrt.so"
}
```

配置项说明：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| host | RK板IP地址 | 192.168.1.100 |
| username | SSH用户名 | root |
| password | SSH密码 | rockchip |
| port | SSH端口 | 22 |
| platform | 目标平台 | rk3568 |
| rknn_lib_path | RKNN库路径 | /usr/lib/librknnrt.so |

#### WSL配置

在前端界面配置：
- WSL用户名：tinfo
- WSL密码：123456

配置保存在浏览器 localStorage。

### 4.2 前端配置

文件：`web/frontend/vite.config.ts`

```typescript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

### 4.3 环境变量

#### 后端环境变量

```bash
# WSL中设置
export CUDA_VISIBLE_DEVICES=-1  # 强制CPU模式
export RKNN_VERBOSE=0           # 关闭RKNN详细日志
```

---

## 五、启动流程

### 5.1 标准启动

```cmd
# 1. 检查环境
check_env.bat

# 2. 启动后端
start_backend.bat
# 后端启动在 http://localhost:8000

# 3. 启动前端
start_frontend.bat
# 前端启动在 http://localhost:3000

# 4. 访问界面
# 打开浏览器访问 http://localhost:3000
```

### 5.2 一键启动

```cmd
start_all.bat
```

自动完成：
1. 启动后端服务（新窗口）
2. 启动前端服务（新窗口）
3. 等待服务就绪
4. 打开浏览器

### 5.3 停止服务

```cmd
stop_all.bat
```

### 5.4 服务状态检查

```cmd
# 检查后端
curl http://localhost:8000/docs

# 检查前端
curl http://localhost:3000

# 检查进程
netstat -ano | findstr :8000
netstat -ano | findstr :3000
```

---

## 六、验证测试

### 6.1 环境验证

```cmd
# 运行完整环境检查
check_env.bat
```

预期输出：
```
[OK] WSL Ubuntu is running
[OK] Miniconda is installed
[OK] Conda environment rknn_env is ready
[OK] Python dependencies installed
[OK] System packages installed
[OK] Node.js v18.x.x is installed
[OK] Frontend dependencies installed
```

### 6.2 功能验证

#### PT模型验证

1. 上传PT模型文件
2. 选择测试图片
3. 点击"验证PT模型"
4. 查看检测结果

#### PT转ONNX

1. 选择PT模型
2. 设置参数（imgsz, opset）
3. 点击"转换为ONNX"
4. 下载ONNX模型

#### ONNX转RKNN

1. 选择ONNX模型
2. 选择目标平台（RK3568/RK3588）
3. 选择精度（FP16/INT8）
4. 点击"转换为RKNN"
5. 下载RKNN模型

### 6.3 API测试

访问 http://localhost:8000/docs 测试API：

- `GET /api/models` - 获取模型列表
- `POST /api/convert/onnx` - PT转ONNX
- `POST /api/convert/rknn` - ONNX转RKNN
- `POST /api/validate/pt` - 验证PT模型
- `GET /api/environment/check` - 环境检查

---

## 七、生产部署

### 7.1 性能优化

#### 后端优化

```python
# main.py
# 使用多worker提高并发
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 前端优化

```cmd
# 构建生产版本
cd web/frontend
npm run build

# 使用nginx部署
```

nginx配置：
```nginx
server {
    listen 80;
    server_name localhost;
    
    location / {
        root /path/to/dist;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 7.2 安全加固

#### API安全

```python
# 添加API密钥验证
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "your-secret-key":
        raise HTTPException(status_code=403, detail="Invalid API Key")
```

#### 文件上传限制

```python
# 限制上传文件大小
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_request_size=100 * 1024 * 1024  # 100MB
)
```

### 7.3 日志管理

```python
# 配置日志
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### 7.4 监控告警

#### 进程监控

使用PM2管理进程：
```bash
npm install -g pm2

pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name backend
pm2 start "npm run dev" --name frontend

pm2 save
pm2 startup
```

#### 健康检查

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
```

---

## 八、运维管理

### 8.1 日常运维

#### 日志查看

```bash
# 后端日志
tail -f logs/backend.log

# 前端日志
# 浏览器控制台
```

#### 服务重启

```cmd
stop_all.bat
start_all.bat
```

#### 磁盘清理

```bash
# 清理临时文件
rm -rf data/temp/*
rm -rf models/*.tmp

# 清理旧模型（保留最近10个）
ls -t models/*.rknn | tail -n +11 | xargs rm -f
```

### 8.2 备份恢复

#### 备份策略

```bash
# 备份脚本
backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf backup_$DATE.tar.gz \
    models/ \
    data/ \
    web/backend/board_config.json \
    web/backend/*.db

# 保留最近7天备份
find . -name "backup_*.tar.gz" -mtime +7 -delete
```

#### 恢复流程

```bash
# 恢复备份
tar -xzf backup_20260615.tar.gz
```

### 8.3 更新升级

```bash
# 拉取最新代码
git pull

# 更新依赖
pip install -r requirements.txt --upgrade
npm update

# 重启服务
stop_all.bat
start_all.bat
```

---

## 九、故障排查

### 9.1 常见问题

#### WSL无法启动

```cmd
# 检查WSL状态
wsl --list --verbose

# 重启WSL
wsl --shutdown
wsl -d Ubuntu

# 重装WSL
wsl --unregister Ubuntu
wsl --install -d Ubuntu
```

#### 后端启动失败

```bash
# 检查Python环境
conda activate rknn_env
python --version

# 检查依赖
pip list | grep fastapi

# 检查端口占用
netstat -ano | findstr :8000
```

#### 前端无法访问

```cmd
# 检查Node.js
node --version

# 检查端口
netstat -ano | findstr :3000

# 重新安装依赖
cd web/frontend
rm -rf node_modules
npm install
```

#### 模型转换失败

```bash
# 检查rknn-toolkit2
conda activate rknn_env
python -c "from rknn.api import RKNN; print('OK')"

# 查看详细错误
export RKNN_VERBOSE=1
```

#### RK板连接失败

```bash
# 测试SSH连接
ssh root@192.168.1.100

# 检查网络
ping 192.168.1.100

# 检查RKNN库
ssh root@192.168.1.100 "ls -l /usr/lib/librknnrt.so"
```

### 9.2 错误代码

| 错误 | 原因 | 解决 |
|------|------|------|
| WSL not found | WSL未安装 | 安装WSL Ubuntu |
| Conda env not found | 虚拟环境未创建 | 运行check_env.bat |
| CUDA error | GPU不兼容 | 已自动使用CPU模式 |
| RKNN config failed | rknn-toolkit2版本错误 | 安装2.3.2版本 |
| SSH connection refused | RK板未启动或网络不通 | 检查RK板状态 |

### 9.3 日志分析

```bash
# 查看错误日志
grep -i error logs/backend.log

# 查看转换失败
grep "convert.*failed" logs/backend.log

# 实时监控
tail -f logs/backend.log | grep --color=auto ERROR
```

---

## 十、附录

### 10.1 目录结构

```
YOLO_RKNN_Solution/
├── models/                 # 模型文件目录
│   ├── *.pt               # YOLO PT模型
│   ├── *.onnx             # ONNX模型
│   └── *.rknn             # RKNN模型
├── data/                   # 数据目录
│   ├── images/            # 测试图片
│   └── quantize/          # 量化数据集
├── scripts/                # 转换脚本
│   ├── convert_onnx.py    # PT转ONNX
│   ├── convert_rknn.py    # ONNX转RKNN
│   └── check_environment.py
├── web/                    # Web应用
│   ├── backend/           # FastAPI后端
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── board_config.json
│   ├── frontend/          # Vue3前端
│   │   ├── src/
│   │   ├── package.json
│   │   └── vite.config.ts
│   ├── check_env.bat      # 环境检查
│   ├── start_backend.bat  # 启动后端
│   ├── start_frontend.bat # 启动前端
│   ├── start_all.bat      # 一键启动
│   └── stop_all.bat       # 停止服务
├── docs/                   # 文档
│   └── ENVIRONMENT_SETUP.md
└── PROJECT_REPORT.md       # 项目报告
```

### 10.2 端口说明

| 端口 | 服务 | 协议 |
|------|------|------|
| 3000 | 前端 | HTTP |
| 8000 | 后端 | HTTP |
| 22 | RK板SSH | SSH |

### 10.3 依赖版本

| 包 | 版本 | 说明 |
|---|---|---|
| Python | 3.8 | WSL虚拟环境 |
| ultralytics | latest | YOLO框架 |
| rknn-toolkit2 | 2.3.2 | RKNN转换 |
| fastapi | 0.115.0 | Web框架 |
| Node.js | 18.x/20.x | 前端运行 |
| vue | 3.x | 前端框架 |

### 10.4 快速命令参考

```cmd
# 环境检查
check_env.bat

# 启动服务
start_all.bat

# 停止服务
stop_all.bat

# 查看日志
type logs\backend.log

# 清理临时
del /q data\temp\*
```

---

## 十一、联系支持

如遇问题，请检查：
1. 环境检查脚本输出
2. 后端日志文件
3. 浏览器控制台
4. RK板系统日志

技术文档：
- 项目报告：PROJECT_REPORT.md
- 环境配置：docs/ENVIRONMENT_SETUP.md
- RKNN转换：05_RKNN_Conversion.md