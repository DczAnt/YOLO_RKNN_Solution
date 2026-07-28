# YOLO-RKNN Solution

YOLO模型转RKNN格式转换平台，支持在瑞芯微RK3566/RK3568/RK3588等芯片上部署YOLOv8模型。

## 项目简介

本项目提供了一个完整的YOLO模型转换和部署解决方案，可以将训练好的YOLO模型（.pt格式）转换为RKNN格式，在瑞芯微NPU上进行高效推理。

### 主要功能

- ✅ **模型转换**
  - PT模型转ONNX格式
  - ONNX模型转RKNN格式
  - 支持FP16和INT8量化
  - 支持RK3566/RK3568/RK3588/RK3576等芯片

- ✅ **模型验证**
  - PT模型验证
  - ONNX模型验证
  - RKNN模型验证（在RK主板上）
  - 实时显示检测结果

- ✅ **Web管理界面**
  - 模型上传和管理
  - 转换任务管理
  - 实时进度显示
  - 结果可视化

## 系统架构

```
┌─────────────────────────────────────────┐
│         Windows 11 开发机                │
│                                          │
│  ┌────────────────┐  ┌────────────────┐ │
│  │  前端 (Vue3)   │  │  WSL Ubuntu    │ │
│  │  Port: 3000    │  │  后端(FastAPI) │ │
│  └────────────────┘  │  Port: 8000    │ │
│                      └────────────────┘ │
└─────────────────────────────────────────┘
                ↓ SSH
┌─────────────────────────────────────────┐
│       RK3568/RK3588 目标板               │
│       RKNN Runtime + NPU                 │
└─────────────────────────────────────────┘
```

## 技术栈

### 后端
- **FastAPI** - 现代高性能Web框架
- **RKNN Toolkit2** - 瑞芯微模型转换工具
- **Ultralytics** - YOLOv8训练和推理
- **ONNX** - 开放神经网络交换格式

### 前端
- **Vue 3** - 渐进式JavaScript框架
- **Element Plus** - UI组件库
- **Vite** - 下一代前端构建工具
- **Axios** - HTTP客户端

### 部署
- **WSL Ubuntu** - Windows子系统
- **RKNN Runtime** - RK芯片推理引擎
- **NPU** - 神经网络处理器

## 快速开始

### 1. 环境准备

#### Windows环境
```bash
# 安装Node.js (18.x或20.x)
# 下载：https://nodejs.org/

# 安装WSL Ubuntu
wsl --install -d Ubuntu
```

#### WSL环境
```bash
# 安装Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
~/miniconda3/bin/conda init bash
source ~/.bashrc

# 创建虚拟环境
conda create -n rknn_env python=3.8 -y
conda activate rknn_env

# 安装依赖
pip install ultralytics onnx onnxruntime opencv-python numpy pillow
pip install rknn-toolkit2==2.3.2
pip install fastapi uvicorn[standard] python-multipart aiofiles websockets pydantic

# 安装系统包
sudo apt-get update
sudo apt-get install -y sshpass
```

### 2. 启动服务

#### 方式1：一键启动
```bash
# Windows
E:\AIcomm\YOLO_RKNN_Solution\web\start_all.bat
```

#### 方式2：分别启动
```bash
# 启动后端
E:\AIcomm\YOLO_RKNN_Solution\web\start_backend.bat

# 启动前端
E:\AIcomm\YOLO_RKNN_Solution\web\start_frontend.bat
```

### 3. 访问界面

打开浏览器访问：http://localhost:3000

## 使用指南

### 模型转换流程

```
PT模型 → ONNX模型 → RKNN模型
  ↓         ↓         ↓
验证PT    验证ONNX   验证RKNN
```

#### 1. PT转ONNX
1. 上传PT模型文件
2. 设置参数（输入尺寸、opset版本）
3. 点击"转换为ONNX"
4. 下载转换后的ONNX模型

#### 2. ONNX转RKNN
1. 选择ONNX模型
2. 选择目标平台（RK3568/RK3588）
3. 选择精度（FP16/INT8）
4. 点击"转换为RKNN"
5. 下载RKNN模型

#### 3. 验证模型
1. 选择模型和测试图片
2. 点击"验证"按钮
3. 查看检测结果和性能指标

### RK主板配置

#### 安装RKNN Runtime
```bash
# 在RK板上执行
wget https://github.com/rockchip-linux/rknpu2/releases/download/v2.3.2/rknn-api-v2.3.2.tar.gz
tar -xzf rknn-api-v2.3.2.tar.gz -C /
ldconfig
```

#### 安装Python依赖
```bash
apt-get update
apt-get install -y python3 python3-pip python3-opencv python3-pil python3-numpy
```

## 支持的模型

### YOLO系列
- YOLOv8n/s/m/l/x
- YOLOv5n/s/m/l/x
- 自定义YOLO模型

### 支持的芯片

| 芯片 | NPU算力 | 推荐精度 |
|------|---------|----------|
| RK3566 | 0.8 TOPS | FP16 |
| RK3568 | 0.8 TOPS | FP16 |
| RK3588 | 6 TOPS | FP16/INT8 |
| RK3576 | 6 TOPS | FP16/INT8 |

## 性能参考

### RK3568 (FP16)

| 模型 | 输入尺寸 | 推理时间 | FPS |
|------|----------|----------|-----|
| YOLOv8n | 640×640 | ~30ms | ~33 |
| YOLOv8s | 640×640 | ~50ms | ~20 |
| YOLOv8m | 640×640 | ~80ms | ~12 |

### RK3588 (FP16)

| 模型 | 输入尺寸 | 推理时间 | FPS |
|------|----------|----------|-----|
| YOLOv8n | 640×640 | ~10ms | ~100 |
| YOLOv8s | 640×640 | ~15ms | ~66 |
| YOLOv8m | 640×640 | ~25ms | ~40 |

## 项目结构

```
YOLO_RKNN_Solution/
├── models/              # 模型文件目录
├── data/                # 数据目录
│   ├── images/         # 测试图片
│   └── results/        # 结果输出
├── docs/               # 文档
│   ├── ENVIRONMENT_SETUP.md
│   ├── DEPLOYMENT.md
│   └── DEPLOYMENT_CHECKLIST.md
├── scripts/            # 脚本
│   ├── convert_onnx.py
│   ├── convert_rknn.py
│   └── check_environment.py
├── web/                # Web应用
│   ├── backend/       # FastAPI后端
│   │   └── main.py
│   ├── frontend/      # Vue3前端
│   │   └── src/
│   └── *.bat          # 启动脚本
└── README.md
```

## 常见问题

### Q1: WSL启动失败
```bash
# 检查WSL状态
wsl --list --verbose

# 重启WSL
wsl --shutdown
wsl -d Ubuntu
```

### Q2: RKNN转换失败
确保安装了正确版本的rknn-toolkit2：
```bash
pip install rknn-toolkit2==2.3.2
```

### Q3: RK板连接失败
检查网络和SSH：
```bash
# 测试连接
ssh root@192.168.1.100

# 检查RKNN库
ssh root@192.168.1.100 "ls -l /usr/lib/librknnrt.so"
```

### Q4: 检测结果为0
确保验证脚本支持多类别模型（已修复）。

## 更新日志

### v1.0.0 (2026-07-28)
- ✅ 初始版本发布
- ✅ 支持PT/ONNX/RKNN模型转换
- ✅ Web管理界面
- ✅ 修复RKNN多类别检测问题

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

本项目采用 AGPL-3.0 许可证。

## 联系方式

- 作者：DczAnt
- 邮箱：357510007@qq.com
- GitHub：https://github.com/DczAnt/YOLO_RKNN_Solution

## 致谢

- [Ultralytics](https://github.com/ultralytics/ultralytics) - YOLOv8
- [Rockchip](https://github.com/rockchip-linux/rknpu2) - RKNN Toolkit2
- [FastAPI](https://fastapi.tiangolo.com/) - Web框架
- [Vue.js](https://vuejs.org/) - 前端框架