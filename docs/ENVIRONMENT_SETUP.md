# 环境配置完整指南

## 概述

本项目需要三个环境：
1. **WSL环境** - 模型转换和后端服务
2. **Windows环境** - 前端开发
3. **RK3568主板环境** - 模型推理

---

## 一、WSL环境配置

### 1.1 安装WSL

```powershell
# 在Windows PowerShell (管理员) 中运行
wsl --install -d Ubuntu
```

重启电脑后完成安装。

### 1.2 安装Miniconda

```bash
# 在WSL Ubuntu中运行
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
rm Miniconda3-latest-Linux-x86_64.sh

# 初始化conda
~/miniconda3/bin/conda init bash
source ~/.bashrc
```

### 1.3 创建虚拟环境

```bash
# 创建rknn_env环境 (Python 3.8)
conda create -n rknn_env python=3.8 -y
conda activate rknn_env
```

### 1.4 安装Python依赖

```bash
conda activate rknn_env

# 核心依赖
pip install ultralytics onnx onnxruntime opencv-python numpy pillow tqdm pyyaml

# RKNN Toolkit2 (模型转换)
pip install rknn-toolkit2-npu==2.3.2
# 或
pip install rknn-toolkit2==2.3.2

# FastAPI后端
pip install fastapi uvicorn[standard] python-multipart aiofiles websockets pydantic
```

### 1.5 安装系统包

```bash
# sshpass (用于SSH连接主板)
sudo apt-get update
sudo apt-get install -y sshpass
```

### 1.6 验证安装

```bash
conda activate rknn_env
python -c "from ultralytics import YOLO; print('Ultralytics OK')"
python -c "from rknn.api import RKNN; print('RKNN OK')"
python -c "import fastapi; print('FastAPI OK')"
```

---

## 二、Windows环境配置

### 2.1 安装Node.js

下载并安装：https://nodejs.org/

推荐版本：LTS 18.x 或 20.x

验证：
```cmd
node --version
npm --version
```

### 2.2 安装前端依赖

```cmd
cd E:\AIcomm\YOLO_RKNN_Solution\web\frontend
npm install
```

---

## 三、RK3568主板环境配置

### 3.1 系统要求

- 系统：Ubuntu 20.04 / Debian 10+
- 内存：≥1GB
- 存储：≥2GB可用空间

### 3.2 安装RKNN Runtime

**方法1：从官方仓库安装**

```bash
# 在RK3568板上执行
wget https://github.com/rockchip-linux/rknpu2/releases/download/v2.3.2/rknn-api-v2.3.2.tar.gz
tar -xzf rknn-api-v2.3.2.tar.gz -C /
ldconfig
```

**方法2：从本地复制**

```bash
# 在Windows上
scp rknn-api.tar.gz root@192.168.1.100:/tmp/

# 在RK3568板上
ssh root@192.168.1.100
tar -xzf /tmp/rknn-api.tar.gz -C /
ldconfig
```

### 3.3 安装Python依赖

```bash
# 在RK3568板上
apt-get update
apt-get install -y python3 python3-pip

pip3 install numpy opencv-python
```

### 3.4 验证安装

```bash
# 检查RKNN库
ls -l /usr/lib/librknnrt.so

# 检查NPU
cat /sys/class/misc/rknpu/version

# Python测试
python3 -c "from rknn.api import RKNN; print('RKNN OK')"
```

### 3.5 运行环境检查脚本

```bash
# 将检查脚本复制到主板
scp scripts/check_board_env.sh root@192.168.1.100:/tmp/

# 在主板上运行
ssh root@192.168.1.100
bash /tmp/check_board_env.sh
```

---

## 四、一键环境检查

### Windows端

```cmd
E:\AIcomm\YOLO_RKNN_Solution\web\check_env.bat
```

此脚本会自动：
1. 检查并启动WSL
2. 安装Miniconda（如未安装）
3. 创建conda虚拟环境
4. 安装所有Python依赖
5. 安装系统包
6. 检查Windows Node.js
7. 安装前端依赖
8. 生成主板配置文件

---

## 五、依赖版本清单

### WSL环境

| 包名 | 版本 | 用途 |
|------|------|------|
| Python | 3.8 | 运行环境 |
| ultralytics | latest | YOLO模型 |
| onnx | latest | ONNX格式 |
| onnxruntime | latest | ONNX推理 |
| rknn-toolkit2 | 2.3.2 | RKNN转换 |
| fastapi | 0.115.0 | Web后端 |
| uvicorn | 0.30.6 | ASGI服务器 |
| opencv-python | latest | 图像处理 |

### Windows环境

| 包名 | 版本 | 用途 |
|------|------|------|
| Node.js | 18.x/20.x | 前端运行 |
| npm | latest | 包管理 |

### RK3568环境

| 包名 | 版本 | 用途 |
|------|------|------|
| librknnrt.so | 2.3.2 | RKNN运行时 |
| numpy | latest | 数值计算 |
| opencv-python | latest | 图像处理 |

---

## 六、常见问题

### Q1: WSL启动失败

```cmd
# 检查WSL状态
wsl --list --verbose

# 重启WSL
wsl --shutdown
wsl -d Ubuntu
```

### Q2: CUDA不兼容

已在代码中设置强制CPU模式：
```python
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
```

### Q3: RKNN转换失败

确保安装了正确版本的rknn-toolkit2：
```bash
pip install rknn-toolkit2-npu==2.3.2
```

### Q4: 主板连接失败

检查网络和SSH：
```bash
# 测试连接
ssh root@192.168.1.100

# 检查RKNN库
ssh root@192.168.1.100 "ls -l /usr/lib/librknnrt.so"
```

---

## 七、配置文件

### 主板配置 (board_config.json)

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

修改配置后重启后端服务。

---

## 八、启动服务

```cmd
# 检查环境
check_env.bat

# 启动后端
start_backend.bat

# 启动前端
start_frontend.bat

# 或一键启动
start_all.bat
```

访问：http://localhost:3000