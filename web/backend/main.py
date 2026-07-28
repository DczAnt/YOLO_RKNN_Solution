"""
YOLO-RKNN Web后端服务

功能:
- 模型转换API
- 环境检查API
- 文件管理API
- WebSocket实时进度推送
"""
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import json
import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import uuid

# 检测是否在WSL中运行
IN_WSL = "microsoft" in os.uname().release.lower() or "WSL" in os.uname().release

app = FastAPI(title="YOLO-RKNN Web API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置路径
# 后端在 web/backend/ 目录，需要回到项目根目录
BASE_DIR = Path(__file__).parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
SCRIPTS_DIR = BASE_DIR / "scripts"

# 确保目录存在
MODELS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()


# 数据模型
class ConvertOnnxRequest(BaseModel):
    pt_model: str
    imgsz: int = 640
    opset: int = 12
    simplify: bool = True
    dynamic: bool = False

class ConvertRknnRequest(BaseModel):
    onnx_model: str
    platform: str = "rk3588"
    precision: str = "fp16"
    quantize_dataset: Optional[str] = None
    mean_values: List[float] = [0, 0, 0]
    std_values: List[float] = [255, 255, 255]

class TaskProgress(BaseModel):
    task_id: str
    task_type: str  # convert_onnx, convert_rknn, validate_pt, validate_onnx, validate_rknn
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    message: str
    created_at: str  # 创建时间
    result: Optional[dict] = None


# 任务存储
tasks = {}


# API路由
@app.get("/")
async def root():
    return {"message": "YOLO-RKNN Web API", "version": "1.0.0"}


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/models")
async def list_models():
    """列出所有模型"""
    models = []
    
    # PT模型
    for file in MODELS_DIR.glob("*.pt"):
        models.append({
            "name": file.name,
            "type": "pt",
            "size": file.stat().st_size,
            "mtime": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
        })
    
    # ONNX模型
    for file in MODELS_DIR.glob("*.onnx"):
        models.append({
            "name": file.name,
            "type": "onnx",
            "size": file.stat().st_size,
            "mtime": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
        })
    
    # RKNN模型
    for file in MODELS_DIR.glob("*.rknn"):
        models.append({
            "name": file.name,
            "type": "rknn",
            "size": file.stat().st_size,
            "mtime": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
        })
    
    return {"models": models}


@app.post("/api/upload")
async def upload_model(file: UploadFile = File(...)):
    """上传模型文件"""
    # 检查文件类型
    if not (file.filename.endswith('.pt') or file.filename.endswith('.onnx')):
        raise HTTPException(status_code=400, detail="只支持.pt和.onnx文件")
    
    # 保存文件
    file_path = MODELS_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {
        "filename": file.filename,
        "size": file_path.stat().st_size,
        "path": str(file_path)
    }


@app.get("/api/models/{filename}")
async def download_model(filename: str):
    """下载模型文件"""
    file_path = MODELS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


@app.delete("/api/models/{filename}")
async def delete_model(filename: str):
    """删除模型文件"""
    file_path = MODELS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    file_path.unlink()
    return {"message": "删除成功"}


@app.post("/api/convert/onnx")
async def convert_to_onnx(request: ConvertOnnxRequest):
    """PT转ONNX"""
    task_id = str(uuid.uuid4())
    
    # 创建任务
    tasks[task_id] = TaskProgress(
        task_id=task_id,
        task_type="convert_onnx",
        status="pending",
        progress=0,
        message="等待执行",
        created_at=datetime.now().isoformat()
    )
    
    # 启动异步任务
    asyncio.create_task(run_convert_onnx(task_id, request))
    
    return {"task_id": task_id}


async def run_convert_onnx(task_id: str, request: ConvertOnnxRequest):
    """执行PT转ONNX"""
    tasks[task_id].status = "running"
    tasks[task_id].message = "开始转换..."
    
    try:
        # 发送进度
        await manager.broadcast(tasks[task_id].dict())
        
        # 生成带时间戳的输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pt_name = Path(request.pt_model).stem
        output_name = f"{pt_name}_{timestamp}.onnx"
        output_path = MODELS_DIR / output_name
        
        # 构建命令
        script_path = str(SCRIPTS_DIR / "convert_onnx.py")
        model_path = str(MODELS_DIR / request.pt_model)
        
        if IN_WSL:
            # 在WSL中直接执行
            cmd = [
                "python3", script_path,
                "--model", model_path,
                "--output", str(output_path),
                "--imgsz", str(request.imgsz),
                "--opset", str(request.opset)
            ]
            if request.simplify:
                cmd.append("--simplify")
            if request.dynamic:
                cmd.append("--dynamic")
        else:
            # 在Windows中通过WSL执行
            wsl_cmd = f"source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn_env && " \
                      f"python3 {script_path} --model {model_path} --output {output_path} " \
                      f"--imgsz {request.imgsz} --opset {request.opset}"
            if request.simplify:
                wsl_cmd += " --simplify"
            if request.dynamic:
                wsl_cmd += " --dynamic"
            cmd = ["wsl", "-d", "Ubuntu", "--", "bash", "-c", wsl_cmd]
        
        # 执行命令
        tasks[task_id].progress = 20
        tasks[task_id].message = "正在转换..."
        await manager.broadcast(tasks[task_id].dict())
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            tasks[task_id].status = "completed"
            tasks[task_id].progress = 100
            tasks[task_id].message = f"转换成功: {output_name}"
            tasks[task_id].result = {
                "output": stdout.decode('utf-8', errors='replace'),
                "output_file": output_name
            }
        else:
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"转换失败: {stderr.decode('utf-8', errors='replace')}"
        
    except Exception as e:
        tasks[task_id].status = "failed"
        tasks[task_id].message = f"执行错误: {str(e)}"
    
    await manager.broadcast(tasks[task_id].dict())


@app.post("/api/convert/rknn")
async def convert_to_rknn(request: ConvertRknnRequest):
    """ONNX转RKNN"""
    task_id = str(uuid.uuid4())
    
    tasks[task_id] = TaskProgress(
        task_id=task_id,
        task_type="convert_rknn",
        status="pending",
        progress=0,
        message="等待执行",
        created_at=datetime.now().isoformat()
    )
    
    asyncio.create_task(run_convert_rknn(task_id, request))
    
    return {"task_id": task_id}


async def run_convert_rknn(task_id: str, request: ConvertRknnRequest):
    """执行ONNX转RKNN"""
    tasks[task_id].status = "running"
    tasks[task_id].message = "开始转换..."
    
    try:
        await manager.broadcast(tasks[task_id].dict())
        
        # 生成带时间戳和芯片类型的输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        onnx_name = Path(request.onnx_model).stem
        output_name = f"{onnx_name}_{request.platform}_{request.precision}_{timestamp}.rknn"
        output_path = MODELS_DIR / output_name
        
        # 构建命令
        script_path = str(SCRIPTS_DIR / "convert_rknn.py")
        model_path = str(MODELS_DIR / request.onnx_model)
        mean_str = " ".join(map(str, request.mean_values))
        std_str = " ".join(map(str, request.std_values))
        
        if IN_WSL:
            # 在WSL中直接执行
            cmd = [
                "python3", script_path,
                "--model", model_path,
                "--output", str(output_path),
                "--platform", request.platform,
                "--precision", request.precision,
                "--mean", *map(str, request.mean_values),
                "--std", *map(str, request.std_values)
            ]
            if request.precision == "int8" and request.quantize_dataset:
                cmd.extend(["--quantize-dataset", str(DATA_DIR / request.quantize_dataset)])
        else:
            # 在Windows中通过WSL执行
            wsl_cmd = f"source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn_env && " \
                      f"python3 {script_path} --model {model_path} --output {output_path} " \
                      f"--platform {request.platform} --precision {request.precision} " \
                      f"--mean {mean_str} --std {std_str}"
            if request.precision == "int8" and request.quantize_dataset:
                wsl_cmd += f" --quantize-dataset {DATA_DIR / request.quantize_dataset}"
            cmd = ["wsl", "-d", "Ubuntu", "--", "bash", "-c", wsl_cmd]
        
        # 执行命令
        tasks[task_id].progress = 20
        tasks[task_id].message = f"正在转换 ({request.platform} {request.precision})..."
        await manager.broadcast(tasks[task_id].dict())
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            tasks[task_id].status = "completed"
            tasks[task_id].progress = 100
            tasks[task_id].message = f"转换成功: {output_name}"
            tasks[task_id].result = {
                "output": stdout.decode('utf-8', errors='replace'),
                "output_file": output_name
            }
        else:
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"转换失败: {stderr.decode('utf-8', errors='replace')}"
        
    except Exception as e:
        tasks[task_id].status = "failed"
        tasks[task_id].message = f"执行错误: {str(e)}"
    
    await manager.broadcast(tasks[task_id].dict())


@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return tasks[task_id].dict()


@app.get("/api/tasks")
async def list_tasks():
    """列出所有任务"""
    return {"tasks": [task.dict() for task in tasks.values()]}


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    del tasks[task_id]
    return {"message": "删除成功"}


@app.get("/api/environment/check")
async def check_environment():
    """检查环境"""
    try:
        script_path = str(SCRIPTS_DIR / "check_environment.py")
        
        if IN_WSL:
            cmd = ["python3", script_path, "--check-pt-onnx"]
        else:
            wsl_cmd = f"source ~/miniconda3/etc/profile.d/conda.sh && conda activate rknn_env && python3 {script_path} --check-pt-onnx"
            cmd = ["wsl", "-d", "Ubuntu", "--", "bash", "-c", wsl_cmd]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        return {
            "success": process.returncode == 0,
            "output": stdout.decode('utf-8', errors='replace'),
            "error": stderr.decode('utf-8', errors='replace')
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/platforms")
async def get_supported_platforms():
    """获取支持的RK芯片平台列表"""
    platforms = [
        {
            "id": "rk3566",
            "name": "RK3566",
            "description": "Cortex-A55四核，NPU 0.8 TOPS",
            "memory": "2GB",
            "recommended": False
        },
        {
            "id": "rk3568",
            "name": "RK3568",
            "description": "Cortex-A55四核，NPU 0.8 TOPS",
            "memory": "8GB",
            "recommended": False
        },
        {
            "id": "rk3588",
            "name": "RK3588",
            "description": "Cortex-A76/A55八核，NPU 6 TOPS",
            "memory": "16GB",
            "recommended": True
        },
        {
            "id": "rv1126",
            "name": "RV1126",
            "description": "Cortex-A7四核，NPU 2 TOPS",
            "memory": "2GB",
            "recommended": False
        }
    ]
    return {"platforms": platforms}


class ValidatePtRequest(BaseModel):
    model: str
    image: str
    conf_threshold: float = 0.25
    iou_threshold: float = 0.45

class ValidateOnnxRequest(BaseModel):
    model: str
    image: str
    conf_threshold: float = 0.25

class ValidateRknnRequest(BaseModel):
    model: str
    image: str
    host: str
    username: str
    password: str
    conf_threshold: float = 0.25


@app.post("/api/validate/pt")
async def validate_pt_model(request: ValidatePtRequest):
    """验证PT模型"""
    task_id = str(uuid.uuid4())
    
    tasks[task_id] = TaskProgress(
        task_id=task_id,
        task_type="validate_pt",
        status="pending",
        progress=0,
        message="等待验证",
        created_at=datetime.now().isoformat()
    )
    
    asyncio.create_task(run_validate_pt(task_id, request))
    
    return {"task_id": task_id}


async def run_validate_pt(task_id: str, request: ValidatePtRequest):
    """执行PT模型验证"""
    tasks[task_id].status = "running"
    tasks[task_id].message = "开始验证..."
    
    try:
        await manager.broadcast(tasks[task_id].dict())
        
        model_path = MODELS_DIR / request.model
        image_path = DATA_DIR / "images" / request.image
        
        if not model_path.exists():
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"模型不存在: {request.model}"
            await manager.broadcast(tasks[task_id].dict())
            return
        
        if not image_path.exists():
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"图片不存在: {request.image}"
            await manager.broadcast(tasks[task_id].dict())
            return
        
        # 创建验证脚本
        result_dir = DATA_DIR / "results" / task_id
        result_dir.mkdir(parents=True, exist_ok=True)
        
        validate_script = f"""
import sys
import json
import time
import os
from pathlib import Path

# Force CPU mode (avoid CUDA compatibility issues)
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

from ultralytics import YOLO

# 加载模型
model = YOLO('{model_path}')

# 预热推理
_ = model.predict('{image_path}', conf={request.conf_threshold}, verbose=False)

# 正式推理（计时）
start_time = time.time()
results = model.predict(
    '{image_path}',
    conf={request.conf_threshold},
    iou={request.iou_threshold},
    save=True,
    project='{result_dir}',
    name='result',
    exist_ok=True
)
inference_time = (time.time() - start_time) * 1000  # ms

# 提取检测结果
detections = []
for r in results:
    for box in r.boxes:
        detections.append({{
            'class': r.names[int(box.cls[0])],
            'confidence': float(box.conf[0]),
            'bbox': [float(x) for x in box.xyxy[0].tolist()]
        }})

# 统计类别
class_count = {{}}
for det in detections:
    cls = det['class']
    class_count[cls] = class_count.get(cls, 0) + 1

# 性能指标
result = {{
    'detections': detections,
    'count': len(detections),
    'inference_time_ms': round(inference_time, 2),
    'fps': round(1000 / inference_time, 2),
    'class_count': class_count,
    'model': '{request.model}',
    'image': '{request.image}'
}}

print(json.dumps(result))
"""
        
        script_path = DATA_DIR / f"validate_pt_{task_id}.py"
        script_path.write_text(validate_script)
        
        tasks[task_id].progress = 30
        tasks[task_id].message = "正在推理..."
        await manager.broadcast(tasks[task_id].dict())
        
        # 执行验证
        process = await asyncio.create_subprocess_exec(
            "python3", str(script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # 清理脚本
        script_path.unlink(missing_ok=True)
        
        if process.returncode == 0:
            output = stdout.decode('utf-8', errors='replace')
            try:
                # 移除ANSI颜色代码
                import re
                clean_output = re.sub(r'\x1b\[[0-9;]*m', '', output)
                
                # 查找JSON行（从后往前找）
                result_data = None
                for line in reversed(clean_output.split('\n')):
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        result_data = json.loads(line)
                        break
                
                if result_data:
                    # 查找结果图片
                    result_image = None
                    for ext in ['.jpg', '.png', '.jpeg']:
                        img_path = result_dir / "result" / f"{Path(request.image).stem}{ext}"
                        if img_path.exists():
                            result_image = f"/api/results/{task_id}/result/{img_path.name}"
                            break
                    
                    tasks[task_id].status = "completed"
                    tasks[task_id].progress = 100
                    tasks[task_id].message = f"验证成功，检测到 {result_data.get('count', 0)} 个目标"
                    tasks[task_id].result = {
                        **result_data,
                        "result_image": result_image
                    }
                else:
                    raise ValueError("未找到JSON结果")
            except Exception as e:
                tasks[task_id].status = "completed"
                tasks[task_id].progress = 100
                tasks[task_id].message = "验证完成"
                tasks[task_id].result = {"output": output, "error": str(e)}
        else:
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"验证失败: {stderr.decode('utf-8', errors='replace')}"
        
    except Exception as e:
        tasks[task_id].status = "failed"
        tasks[task_id].message = f"执行错误: {str(e)}"
    
    await manager.broadcast(tasks[task_id].dict())


@app.post("/api/validate/onnx")
async def validate_onnx_model(request: ValidateOnnxRequest):
    """验证ONNX模型"""
    task_id = str(uuid.uuid4())
    
    tasks[task_id] = TaskProgress(
        task_id=task_id,
        task_type="validate_onnx",
        status="pending",
        progress=0,
        message="等待验证",
        created_at=datetime.now().isoformat()
    )
    
    asyncio.create_task(run_validate_onnx(task_id, request))
    
    return {"task_id": task_id}


async def run_validate_onnx(task_id: str, request: ValidateOnnxRequest):
    """执行ONNX模型验证"""
    tasks[task_id].status = "running"
    tasks[task_id].message = "开始验证..."
    
    try:
        await manager.broadcast(tasks[task_id].dict())
        
        model_path = MODELS_DIR / request.model
        image_path = DATA_DIR / "images" / request.image
        
        if not model_path.exists():
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"模型不存在: {request.model}"
            await manager.broadcast(tasks[task_id].dict())
            return
        
        if not image_path.exists():
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"图片不存在: {request.image}"
            await manager.broadcast(tasks[task_id].dict())
            return
        
        # 创建结果目录
        result_dir = DATA_DIR / "results" / task_id
        result_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建验证脚本
        validate_script = f"""
import numpy as np
import onnxruntime as ort
from PIL import Image
import json
import time
import cv2

# 加载模型
session = ort.InferenceSession('{model_path}')
input_name = session.get_inputs()[0].name
output_names = [o.name for o in session.get_outputs()]

# 读取原始图片
img_original = cv2.imread('{image_path}')
img_rgb = cv2.cvtColor(img_original, cv2.COLOR_BGR2RGB)
orig_h, orig_w = img_original.shape[:2]

# 预处理图片
img = Image.open('{image_path}').convert('RGB')
img_resized = img.resize((640, 640))
img_np = np.array(img_resized).astype(np.float32) / 255.0
img_np = np.transpose(img_np, (2, 0, 1))
img_np = np.expand_dims(img_np, 0)

# 预热推理
_ = session.run(output_names, {{input_name: img_np}})

# 正式推理（计时）
start_time = time.time()
outputs = session.run(output_names, {{input_name: img_np}})
inference_time = (time.time() - start_time) * 1000

# 后处理（YOLOv8格式）
# 输出格式: [1, 7, 8400] 或 [1, 84, 8400]
output = outputs[0]  # [1, C, 8400]
output = np.squeeze(output, axis=0)  # [C, 8400]

# 检测结果
detections = []
conf_threshold = 0.25
iou_threshold = 0.45

if output.shape[0] == 7:
    # 单类别: [7, 8400] -> (x, y, w, h, obj_conf, cls_conf, final_conf)
    # 行6是最终置信度（已经过sigmoid处理）
    boxes = output[:4, :].T  # [8400, 4]
    scores = output[6, :]  # [8400] - 最终置信度
    
    # 过滤低置信度
    mask = scores > conf_threshold
    boxes = boxes[mask]
    scores = scores[mask]
    
    # NMS（非极大值抑制）
    if len(boxes) > 0:
        # 转换为角点格式
        x1 = boxes[:, 0] - boxes[:, 2] / 2
        y1 = boxes[:, 1] - boxes[:, 3] / 2
        x2 = boxes[:, 0] + boxes[:, 2] / 2
        y2 = boxes[:, 1] + boxes[:, 3] / 2
        
        # 按置信度排序
        order = scores.argsort()[::-1]
        
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            
            if order.size == 1:
                break
            
            # 计算IoU
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h
            
            area_i = (x2[i] - x1[i]) * (y2[i] - y1[i])
            area_others = (x2[order[1:]] - x1[order[1:]]) * (y2[order[1:]] - y1[order[1:]])
            iou = inter / (area_i + area_others - inter)
            
            # 保留IoU小于阈值的框
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]
        
        boxes = boxes[keep]
        scores = scores[keep]
    
    for i in range(len(boxes)):
        x, y, w, h = boxes[i]
        conf = float(scores[i])
        
        # 转换为原图坐标 (中心点格式转角点格式)
        x1 = int((x - w/2) * orig_w / 640)
        y1 = int((y - h/2) * orig_h / 640)
        x2 = int((x + w/2) * orig_w / 640)
        y2 = int((y + h/2) * orig_h / 640)
        
        detections.append({{
            'class': 'tires',
            'confidence': conf,
            'bbox': [x1, y1, x2, y2]
        }})
        
        # 绘制框
        cv2.rectangle(img_original, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img_original, f'tires {{conf:.2f}}', (x1, y1-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

elif output.shape[0] > 7:
    # 多类别: [84, 8400] -> (x, y, w, h, conf1, conf2, ..., conf80)
    boxes = output[:4, :].T  # [8400, 4]
    class_scores = output[4:, :].T  # [8400, num_classes]
    
    # 获取每个框的最大类别分数和类别索引
    class_ids = np.argmax(class_scores, axis=1)
    scores = np.max(class_scores, axis=1)
    
    # 过滤低置信度
    mask = scores > conf_threshold
    boxes = boxes[mask]
    scores = scores[mask]
    class_ids = class_ids[mask]
    
    for i in range(len(boxes)):
        x, y, w, h = boxes[i]
        conf = float(scores[i])
        cls_id = int(class_ids[i])
        
        # 转换为原图坐标
        x1 = int((x - w/2) * orig_w / 640)
        y1 = int((y - h/2) * orig_h / 640)
        x2 = int((x + w/2) * orig_w / 640)
        y2 = int((y + h/2) * orig_h / 640)
        
        detections.append({{
            'class': f'class_{{cls_id}}',
            'confidence': conf,
            'bbox': [x1, y1, x2, y2]
        }})
        
        # 绘制框
        cv2.rectangle(img_original, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img_original, f'{{cls_id}} {{conf:.2f}}', (x1, y1-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

# 保存结果图片
result_img_path = '{result_dir}/result.jpg'
cv2.imwrite(result_img_path, img_original)

# 统计类别
class_count = {{}}
for det in detections:
    cls = det['class']
    class_count[cls] = class_count.get(cls, 0) + 1

result = {{
    'detections': detections,
    'count': len(detections),
    'inference_time_ms': round(inference_time, 2),
    'fps': round(1000 / inference_time, 2),
    'class_count': class_count,
    'model': '{request.model}',
    'image': '{request.image}',
    'output_shape': [list(o.shape) for o in outputs]
}}

print(json.dumps(result))
"""
        
        script_path = DATA_DIR / f"validate_onnx_{task_id}.py"
        script_path.write_text(validate_script)
        
        tasks[task_id].progress = 30
        tasks[task_id].message = "正在推理..."
        await manager.broadcast(tasks[task_id].dict())
        
        # 执行验证
        process = await asyncio.create_subprocess_exec(
            "python3", str(script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # 清理脚本
        script_path.unlink(missing_ok=True)
        
        if process.returncode == 0:
            output = stdout.decode('utf-8', errors='replace')
            try:
                # 移除ANSI颜色代码
                import re
                clean_output = re.sub(r'\\x1b\\[[0-9;]*m', '', output)
                
                # 查找JSON结果
                result_data = None
                for line in reversed(clean_output.split('\n')):
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            result_data = json.loads(line)
                            break
                        except:
                            continue
                
                if result_data:
                    # 查找结果图片
                    result_image = None
                    img_path = result_dir / "result.jpg"
                    if img_path.exists():
                        # 使用统一的URL格式（不需要folder参数）
                        result_image = f"/api/results/{task_id}/result.jpg"
                    
                    tasks[task_id].status = "completed"
                    tasks[task_id].progress = 100
                    tasks[task_id].message = f"验证成功，检测到 {result_data.get('count', 0)} 个目标"
                    tasks[task_id].result = {
                        **result_data,
                        "result_image": result_image
                    }
                else:
                    raise ValueError("未找到JSON结果")
            except Exception as e:
                tasks[task_id].status = "completed"
                tasks[task_id].progress = 100
                tasks[task_id].message = "验证完成"
                tasks[task_id].result = {"output": output, "error": str(e)}
        else:
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"验证失败: {stderr.decode('utf-8', errors='replace')}"
        
    except Exception as e:
        tasks[task_id].status = "failed"
        tasks[task_id].message = f"执行错误: {str(e)}"
    
    await manager.broadcast(tasks[task_id].dict())


@app.post("/api/validate/rknn")
async def validate_rknn_model(request: ValidateRknnRequest):
    """验证RKNN模型（在RK主板上）"""
    task_id = str(uuid.uuid4())
    
    tasks[task_id] = TaskProgress(
        task_id=task_id,
        task_type="validate_rknn",
        status="pending",
        progress=0,
        message="等待验证",
        created_at=datetime.now().isoformat()
    )
    
    asyncio.create_task(run_validate_rknn(task_id, request))
    
    return {"task_id": task_id}


async def run_validate_rknn(task_id: str, request: ValidateRknnRequest):
    """执行RKNN模型验证（SSH到RK主板）"""
    tasks[task_id].status = "running"
    tasks[task_id].message = "检查依赖..."
    
    try:
        await manager.broadcast(tasks[task_id].dict())
        
        # 检查sshpass是否安装
        check_sshpass = await asyncio.create_subprocess_exec(
            "which", "sshpass",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await check_sshpass.communicate()
        
        if check_sshpass.returncode != 0:
            tasks[task_id].status = "failed"
            tasks[task_id].message = "sshpass未安装，请运行: sudo apt-get install sshpass"
            await manager.broadcast(tasks[task_id].dict())
            return
        
        # 检查模型和图片是否存在
        model_path = MODELS_DIR / request.model
        image_path = DATA_DIR / "images" / request.image
        
        if not model_path.exists():
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"模型不存在: {request.model}"
            await manager.broadcast(tasks[task_id].dict())
            return
        
        if not image_path.exists():
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"图片不存在: {request.image}"
            await manager.broadcast(tasks[task_id].dict())
            return
        
        tasks[task_id].progress = 10
        tasks[task_id].message = "创建验证脚本..."
        await manager.broadcast(tasks[task_id].dict())
        
        # 创建验证脚本（在RK主板上执行）
        validate_script = f"""
import numpy as np
from rknnlite.api import RKNNLite
from PIL import Image
import json
import cv2
import time

# 加载模型
rknn = RKNNLite()
ret = rknn.load_rknn('/tmp/{request.model}')
if ret != 0:
    print(json.dumps({{'status': 'error', 'message': 'Load RKNN failed'}}))
    import sys
    sys.exit(1)

ret = rknn.init_runtime()
if ret != 0:
    print(json.dumps({{'status': 'error', 'message': 'Init runtime failed'}}))
    import sys
    sys.exit(1)

# 读取原始图片
img_original = cv2.imread('/tmp/{request.image}')
orig_h, orig_w = img_original.shape[:2]

# 预处理图片
img = Image.open('/tmp/{request.image}').convert('RGB')
img_resized = img.resize((640, 640))
img_np = np.array(img_resized)

# 添加batch维度（RKNN需要4维输入: BHWC）
img_input = np.expand_dims(img_np, 0)

# 预热推理
_ = rknn.inference(inputs=[img_input])

# 正式推理（计时）
start_time = time.time()
outputs = rknn.inference(inputs=[img_input])
inference_time = (time.time() - start_time) * 1000

rknn.release()

# 后处理（YOLOv8格式）
output = outputs[0]  # [C, 8400] 或 [1, C, 8400]
if len(output.shape) == 3:
    output = output.squeeze(0)  # [C, 8400]

output = output.transpose(1, 0)  # [8400, C]

# 检测结果
detections = []
conf_threshold = 0.25
iou_threshold = 0.45

# COCO类别名称
coco_names = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
    'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
    'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
    'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
    'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
    'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]

if output.shape[1] == 7:
    # 单类别: [8400, 7] -> (x, y, w, h, obj_conf, cls_conf, final_conf)
    boxes = output[:, :4]  # [8400, 4]
    scores = output[:, 6]  # [8400] - 最终置信度
    
    # 过滤低置信度
    mask = scores > conf_threshold
    boxes = boxes[mask]
    scores = scores[mask]
    
    # NMS
    if len(boxes) > 0:
        # 转换为角点格式
        x1 = boxes[:, 0] - boxes[:, 2] / 2
        y1 = boxes[:, 1] - boxes[:, 3] / 2
        x2 = boxes[:, 0] + boxes[:, 2] / 2
        y2 = boxes[:, 1] + boxes[:, 3] / 2
        
        # 按置信度排序
        order = scores.argsort()[::-1]
        
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            
            if order.size == 1:
                break
            
            # 计算IoU
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h
            
            area_i = (x2[i] - x1[i]) * (y2[i] - y1[i])
            area_others = (x2[order[1:]] - x1[order[1:]]) * (y2[order[1:]] - y1[order[1:]])
            iou = inter / (area_i + area_others - inter + 1e-10)
            
            # 保留IoU小于阈值的框
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]
        
        boxes = boxes[keep]
        scores = scores[keep]
    
    for i in range(len(boxes)):
        x, y, w, h = boxes[i]
        conf = float(scores[i])
        
        # 转换为原图坐标
        x1 = int((x - w/2) * orig_w / 640)
        y1 = int((y - h/2) * orig_h / 640)
        x2 = int((x + w/2) * orig_w / 640)
        y2 = int((y + h/2) * orig_h / 640)
        
        detections.append({{
            'class': 'tires',
            'confidence': conf,
            'bbox': [x1, y1, x2, y2]
        }})
        
        # 绘制框
        cv2.rectangle(img_original, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img_original, f'tires {{conf:.2f}}', (x1, y1-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

elif output.shape[1] > 7:
    # 多类别: [8400, 84] -> (x, y, w, h, conf1, conf2, ..., conf80)
    boxes = output[:, :4]  # [8400, 4]
    class_scores = output[:, 4:]  # [8400, num_classes]
    
    # 获取每个框的最大类别分数和类别索引
    class_ids = np.argmax(class_scores, axis=1)
    scores = np.max(class_scores, axis=1)
    
    # 过滤低置信度
    mask = scores > conf_threshold
    boxes = boxes[mask]
    scores = scores[mask]
    class_ids = class_ids[mask]
    
    # NMS
    if len(boxes) > 0:
        # 转换为角点格式
        x1 = boxes[:, 0] - boxes[:, 2] / 2
        y1 = boxes[:, 1] - boxes[:, 3] / 2
        x2 = boxes[:, 0] + boxes[:, 2] / 2
        y2 = boxes[:, 1] + boxes[:, 3] / 2
        
        # 按置信度排序
        order = scores.argsort()[::-1]
        
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            
            if order.size == 1:
                break
            
            # 计算IoU
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h
            
            area_i = (x2[i] - x1[i]) * (y2[i] - y1[i])
            area_others = (x2[order[1:]] - x1[order[1:]]) * (y2[order[1:]] - y1[order[1:]])
            iou = inter / (area_i + area_others - inter + 1e-10)
            
            # 保留IoU小于阈值的框
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]
        
        boxes = boxes[keep]
        scores = scores[keep]
        class_ids = class_ids[keep]
    
    for i in range(len(boxes)):
        x, y, w, h = boxes[i]
        conf = float(scores[i])
        cls_id = int(class_ids[i])
        cls_name = coco_names[cls_id] if cls_id < len(coco_names) else f'class_{{cls_id}}'
        
        # 转换为原图坐标
        x1 = int((x - w/2) * orig_w / 640)
        y1 = int((y - h/2) * orig_h / 640)
        x2 = int((x + w/2) * orig_w / 640)
        y2 = int((y + h/2) * orig_h / 640)
        
        detections.append({{
            'class': cls_name,
            'confidence': conf,
            'bbox': [x1, y1, x2, y2]
        }})
        
        # 绘制框
        cv2.rectangle(img_original, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img_original, f'{{cls_name}} {{conf:.2f}}', (x1, y1-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

# 保存结果图片
cv2.imwrite('/tmp/result.jpg', img_original)

# 统计类别
class_count = {{}}
for det in detections:
    cls = det['class']
    class_count[cls] = class_count.get(cls, 0) + 1

result = {{
    'detections': detections,
    'count': len(detections),
    'inference_time_ms': round(inference_time, 2),
    'fps': round(1000 / inference_time, 2),
    'class_count': class_count,
    'model': '{request.model}',
    'image': '{request.image}',
    'output_shape': list(output.shape)
}}

print(json.dumps(result))
"""
        
        # 保存脚本
        script_path = DATA_DIR / f"validate_rknn_{task_id}.py"
        script_path.write_text(validate_script)
        
        tasks[task_id].progress = 20
        tasks[task_id].message = f"上传模型到 {request.host}..."
        await manager.broadcast(tasks[task_id].dict())
        
        # 上传模型（使用sshpass提供密码）
        upload_model_cmd = [
            "sshpass", "-p", request.password,
            "scp", "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            str(model_path),
            f"{request.username}@{request.host}:/tmp/"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *upload_model_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='replace')
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"上传模型失败: {error_msg}"
            tasks[task_id].result = {
                "error_type": "upload_model_failed",
                "error_detail": error_msg,
                "command": " ".join(upload_model_cmd)
            }
            await manager.broadcast(tasks[task_id].dict())
            return
        
        tasks[task_id].progress = 30
        tasks[task_id].message = "上传测试图片..."
        await manager.broadcast(tasks[task_id].dict())
        
        # 上传图片
        upload_image_cmd = [
            "sshpass", "-p", request.password,
            "scp", "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            str(image_path),
            f"{request.username}@{request.host}:/tmp/"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *upload_image_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='replace')
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"上传图片失败: {error_msg}"
            tasks[task_id].result = {
                "error_type": "upload_image_failed",
                "error_detail": error_msg,
                "command": " ".join(upload_image_cmd)
            }
            await manager.broadcast(tasks[task_id].dict())
            return
        
        tasks[task_id].progress = 40
        tasks[task_id].message = "上传验证脚本..."
        await manager.broadcast(tasks[task_id].dict())
        
        # 上传脚本
        upload_script_cmd = [
            "sshpass", "-p", request.password,
            "scp", "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            str(script_path),
            f"{request.username}@{request.host}:/tmp/"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *upload_script_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='replace')
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"上传脚本失败: {error_msg}"
            tasks[task_id].result = {
                "error_type": "upload_script_failed",
                "error_detail": error_msg,
                "command": " ".join(upload_script_cmd)
            }
            await manager.broadcast(tasks[task_id].dict())
            return
        
        tasks[task_id].progress = 50
        tasks[task_id].message = "在RK主板上执行推理..."
        await manager.broadcast(tasks[task_id].dict())
        
        # SSH执行验证脚本
        ssh_cmd = [
            "sshpass", "-p", request.password,
            "ssh", "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            f"{request.username}@{request.host}",
            f"python3 /tmp/validate_rknn_{task_id}.py"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *ssh_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # 清理脚本
        script_path.unlink(missing_ok=True)
        
        if process.returncode == 0:
            output = stdout.decode('utf-8', errors='replace')
            try:
                # 移除ANSI颜色代码
                import re
                clean_output = re.sub(r'\\x1b\\[[0-9;]*m', '', output)
                
                # 查找JSON结果
                result_data = None
                for line in reversed(clean_output.split('\n')):
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            result_data = json.loads(line)
                            break
                        except:
                            continue
                
                if result_data:
                    # 下载结果图片
                    result_dir = DATA_DIR / "results" / task_id
                    result_dir.mkdir(parents=True, exist_ok=True)
                    
                    download_result_cmd = [
                        "sshpass", "-p", request.password,
                        "scp", "-o", "StrictHostKeyChecking=no",
                        f"{request.username}@{request.host}:/tmp/result.jpg",
                        str(result_dir / "result.jpg")
                    ]
                    
                    process = await asyncio.create_subprocess_exec(
                        *download_result_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await process.communicate()
                    
                    # 设置结果图片URL
                    result_image = None
                    if (result_dir / "result.jpg").exists():
                        result_image = f"/api/results/{task_id}/result.jpg"
                    
                    tasks[task_id].status = "completed"
                    tasks[task_id].progress = 100
                    tasks[task_id].message = f"验证成功，检测到 {result_data.get('count', 0)} 个目标"
                    tasks[task_id].result = {
                        **result_data,
                        "result_image": result_image
                    }
                else:
                    raise ValueError("未找到JSON结果")
            except Exception as e:
                tasks[task_id].status = "completed"
                tasks[task_id].progress = 100
                tasks[task_id].message = "验证完成"
                tasks[task_id].result = {"output": output, "error": str(e)}
        else:
            error_msg = stderr.decode('utf-8', errors='replace')
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"验证失败: {error_msg}"
            tasks[task_id].result = {
                "error_type": "inference_failed",
                "error_detail": error_msg,
                "stdout": stdout.decode('utf-8', errors='replace')
            }
        
    except Exception as e:
        import traceback
        tasks[task_id].status = "failed"
        tasks[task_id].message = f"执行错误: {str(e)}"
        tasks[task_id].result = {
            "error_type": "exception",
            "error_detail": str(e),
            "traceback": traceback.format_exc()
        }
    
    await manager.broadcast(tasks[task_id].dict())


@app.post("/api/images/upload")
async def upload_test_image(file: UploadFile = File(...)):
    """上传测试图片"""
    images_dir = DATA_DIR / "images"
    images_dir.mkdir(exist_ok=True)
    
    file_path = images_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {
        "filename": file.filename,
        "size": file_path.stat().st_size,
        "path": str(file_path)
    }


@app.get("/api/images")
async def list_test_images():
    """列出测试图片"""
    images_dir = DATA_DIR / "images"
    images_dir.mkdir(exist_ok=True)
    
    images = []
    for file in images_dir.glob("*"):
        if file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
            images.append({
                "name": file.name,
                "size": file.stat().st_size,
                "mtime": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })
    
    return {"images": images}


@app.get("/api/results/{task_id}/{filename}")
async def get_result_image_simple(task_id: str, filename: str):
    """获取验证结果图片（简化路径）"""
    result_path = DATA_DIR / "results" / task_id / filename
    
    if not result_path.exists():
        raise HTTPException(status_code=404, detail=f"图片不存在: {result_path}")
    
    return FileResponse(
        path=result_path,
        media_type='image/jpeg'
    )


@app.get("/api/results/{task_id}/{folder}/{filename}")
async def get_result_image(task_id: str, folder: str, filename: str):
    """获取验证结果图片"""
    result_path = DATA_DIR / "results" / task_id / folder / filename
    
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")
    
    return FileResponse(
        path=result_path,
        media_type='image/jpeg'
    )


# WebSocket路由
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 可以处理客户端消息
            await websocket.send_json({"message": f"收到: {data}"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)