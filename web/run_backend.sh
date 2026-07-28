#!/bin/bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate rknn_env
cd /mnt/e/AIcomm/YOLO_RKNN_Solution/web/backend
exec uvicorn main:app --host 0.0.0.0 --port 8000