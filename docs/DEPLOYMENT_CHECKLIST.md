# 部署清单（快速参考）

## 快速部署（5分钟）

### 1. 环境检查（自动安装）
```cmd
E:\AIcomm\YOLO_RKNN_Solution\web\check_env.bat
```

### 2. 启动服务
```cmd
E:\AIcomm\YOLO_RKNN_Solution\web\start_all.bat
```

### 3. 访问界面
```
http://localhost:3000
```

---

## 环境要求

### Windows
- Windows 11 64位
- Node.js 18.x/20.x

### WSL
- Ubuntu 22.04
- Miniconda
- Python 3.8
- rknn-toolkit2 2.3.2

### RK板
- RKNN Runtime 2.3.2
- Python 3.8+

---

## 核心命令

| 操作 | 命令 |
|------|------|
| 环境检查 | `check_env.bat` |
| 启动服务 | `start_all.bat` |
| 停止服务 | `stop_all.bat` |
| 单独启动后端 | `start_backend.bat` |
| 单独启动前端 | `start_frontend.bat` |

---

## 端口配置

| 服务 | 端口 | URL |
|------|------|-----|
| 前端 | 3000 | http://localhost:3000 |
| 后端 | 8000 | http://localhost:8000 |
| API文档 | 8000 | http://localhost:8000/docs |

---

## 配置文件

### 主板配置
```
web/backend/board_config.json
```

```json
{
  "host": "192.168.1.100",
  "username": "root",
  "password": "rockchip",
  "port": 22,
  "platform": "rk3568"
}
```

---

## 故障排查

### WSL问题
```cmd
wsl --shutdown
wsl -d Ubuntu
```

### 端口占用
```cmd
netstat -ano | findstr :8000
netstat -ano | findstr :3000
```

### 重装依赖
```cmd
# Python
pip install -r requirements.txt --force-reinstall

# Node.js
rmdir /s node_modules
npm install
```

---

## 验证检查

### 后端
```cmd
curl http://localhost:8000/docs
```

### 前端
```cmd
curl http://localhost:3000
```

### RKNN环境
```bash
python -c "from rknn.api import RKNN; print('OK')"
```

---

## 完整文档

详细部署方案请查看：
- **部署方案**: `docs/DEPLOYMENT.md`
- **环境配置**: `docs/ENVIRONMENT_SETUP.md`
- **项目报告**: `PROJECT_REPORT.md`