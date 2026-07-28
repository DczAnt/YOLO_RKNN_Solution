# RKNN模型转换示例

## 转换流程

```
ONNX模型 → 量化数据集 → RKNN模型
    ↓           ↓           ↓
  加载ONNX   准备图片    量化转换
```

## 量化数据集准备

### 1. 数据集要求

- **数量**: 100-300张图片
- **格式**: JPG/PNG
- **内容**: 覆盖实际应用场景
- **尺寸**: 不限（会自动调整）

### 2. 创建数据集

```python
#!/usr/bin/env python3
"""
创建量化数据集
"""
import os
import cv2
import random
from pathlib import Path

def create_quantize_dataset(
    source_dir,
    output_dir,
    num_images=200,
    output_txt='quantize_images.txt'
):
    """
    创建量化数据集
    
    Args:
        source_dir: 源图片目录
        output_dir: 输出目录
        num_images: 图片数量
        output_txt: 输出文本文件
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取所有图片
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
        image_files.extend(Path(source_dir).glob(ext))
    
    print(f"找到 {len(image_files)} 张图片")
    
    # 随机选择
    if len(image_files) > num_images:
        image_files = random.sample(image_files, num_images)
    
    # 复制图片
    quantize_list = []
    for i, img_path in enumerate(image_files):
        # 读取图片
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        
        # 保存到输出目录
        output_path = os.path.join(output_dir, f'img_{i:04d}.jpg')
        cv2.imwrite(output_path, img)
        quantize_list.append(output_path)
    
    # 写入文本文件
    with open(output_txt, 'w') as f:
        for path in quantize_list:
            f.write(path + '\n')
    
    print(f"创建 {len(quantize_list)} 张量化图片")
    print(f"保存到: {output_txt}")

if __name__ == '__main__':
    create_quantize_dataset(
        source_dir='/mnt/e/AIcomm/tire_images',
        output_dir='quantize_images',
        num_images=266
    )
```

## ONNX转RKNN

### 1. 基础转换

```python
#!/usr/bin/env python3
"""
ONNX转RKNN基础示例
"""
from rknn.api import RKNN

def convert_onnx_to_rknn(onnx_path, rknn_path, quantize_txt, target_platform='rk3568'):
    """
    ONNX转RKNN
    
    Args:
        onnx_path: ONNX模型路径
        rknn_path: RKNN模型路径
        quantize_txt: 量化数据集文本文件
        target_platform: 目标平台
    """
    # 创建RKNN对象
    rknn = RKNN()
    
    # 配置模型
    print(f"配置模型: {onnx_path}")
    ret = rknn.config(
        mean_values=[[0, 0, 0]],
        std_values=[[255, 255, 255]],
        target_platform=target_platform
    )
    if ret != 0:
        print("配置失败!")
        return False
    
    # 加载ONNX模型
    print("加载ONNX模型...")
    ret = rknn.load_onnx(model=onnx_path)
    if ret != 0:
        print("加载ONNX失败!")
        return False
    
    # 构建模型（INT8量化）
    print("构建RKNN模型（INT8量化）...")
    ret = rknn.build(
        do_quantization=True,
        dataset=quantize_txt,
        batch_size=1
    )
    if ret != 0:
        print("构建失败!")
        return False
    
    # 导出RKNN模型
    print(f"导出RKNN模型: {rknn_path}")
    ret = rknn.export_rknn(rknn_path)
    if ret != 0:
        print("导出失败!")
        return False
    
    # 释放资源
    rknn.release()
    
    print("转换成功!")
    return True

if __name__ == '__main__':
    # 检测模型
    convert_onnx_to_rknn(
        onnx_path='detecttires.onnx',
        rknn_path='detecttires_int8.rknn',
        quantize_txt='quantize_detect.txt'
    )
    
    # 分类模型
    convert_onnx_to_rknn(
        onnx_path='clstires.onnx',
        rknn_path='clstires_int8.rknn',
        quantize_txt='quantize_cls.txt'
    )
```

### 2. FLOAT16转换

```python
#!/usr/bin/env python3
"""
ONNX转RKNN (FLOAT16)
"""
from rknn.api import RKNN

def convert_to_float16(onnx_path, rknn_path, target_platform='rk3568'):
    """
    ONNX转RKNN (FLOAT16)
    
    Args:
        onnx_path: ONNX模型路径
        rknn_path: RKNN模型路径
        target_platform: 目标平台
    """
    rknn = RKNN()
    
    # 配置模型
    ret = rknn.config(
        mean_values=[[0, 0, 0]],
        std_values=[[255, 255, 255]],
        target_platform=target_platform
    )
    
    # 加载ONNX模型
    ret = rknn.load_onnx(model=onnx_path)
    if ret != 0:
        print("加载ONNX失败!")
        return False
    
    # 构建模型（不量化，使用FLOAT16）
    print("构建RKNN模型（FLOAT16）...")
    ret = rknn.build(do_quantization=False)
    if ret != 0:
        print("构建失败!")
        return False
    
    # 导出RKNN模型
    ret = rknn.export_rknn(rknn_path)
    if ret != 0:
        print("导出失败!")
        return False
    
    rknn.release()
    print("转换成功!")
    return True

if __name__ == '__main__':
    # 检测模型
    convert_to_float16(
        onnx_path='detecttires.onnx',
        rknn_path='detecttires_fp16.rknn'
    )
    
    # 分类模型
    convert_to_float16(
        onnx_path='clstires.onnx',
        rknn_path='clstires_fp16.rknn'
    )
```

### 3. 高级配置

```python
#!/usr/bin/env python3
"""
RKNN转换高级配置
"""
from rknn.api import RKNN

def convert_advanced(onnx_path, rknn_path, quantize_txt):
    """
    高级配置转换
    """
    rknn = RKNN()
    
    # 详细配置
    ret = rknn.config(
        mean_values=[[0, 0, 0]],           # 均值
        std_values=[[255, 255, 255]],      # 标准差
        target_platform='rk3568',          # 目标平台
        optimization_level=3,              # 优化级别 (0-3)
        output_optimize=1,                 # 输出优化
        quantized_dtype='asymmetric_quantized-u8',  # 量化类型
        quantized_algorithm='normal',      # 量化算法
        single_core_mode=True              # 单核模式
    )
    
    # 加载ONNX
    ret = rknn.load_onnx(model=onnx_path)
    
    # 构建模型
    ret = rknn.build(
        do_quantization=True,
        dataset=quantize_txt,
        batch_size=1,
        rknn_batch_size=1
    )
    
    # 导出RKNN
    ret = rknn.export_rknn(rknn_path)
    
    # 打印模型信息
    ret = rknn.eval_perf(target='rk3568')
    
    rknn.release()
    return ret == 0
```

## 精度对比测试

### 1. INT8 vs FLOAT16

```python
#!/usr/bin/env python3
"""
精度对比测试
"""
import numpy as np
import cv2
from rknn.api import RKNN

def test_precision(onnx_path, rknn_int8, rknn_fp16, test_image):
    """
    对比INT8和FLOAT16精度
    """
    # 读取测试图片
    img = cv2.imread(test_image)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (640, 640))
    img = np.expand_dims(img, 0)
    
    # 测试INT8
    rknn = RKNN()
    rknn.load_rknn(rknn_int8)
    rknn.init_runtime(target=None)
    out_int8 = rknn.inference(inputs=[img])
    rknn.release()
    
    # 测试FLOAT16
    rknn = RKNN()
    rknn.load_rknn(rknn_fp16)
    rknn.init_runtime(target=None)
    out_fp16 = rknn.inference(inputs=[img])
    rknn.release()
    
    # 计算差异
    diff = np.abs(out_int8[0] - out_fp16[0])
    print(f"最大差异: {diff.max()}")
    print(f"平均差异: {diff.mean()}")
    
    return diff

if __name__ == '__main__':
    test_precision(
        onnx_path='detecttires.onnx',
        rknn_int8='detecttires_int8.rknn',
        rknn_fp16='detecttires_fp16.rknn',
        test_image='test.jpg'
    )
```

## 完整转换流程

```python
#!/usr/bin/env python3
"""
完整转换流程
"""
import os
from rknn.api import RKNN

class RKNNConverter:
    def __init__(self, target_platform='rk3568'):
        self.target_platform = target_platform
    
    def convert(self, onnx_path, rknn_path, quantize_txt=None, precision='int8'):
        """
        转换模型
        
        Args:
            onnx_path: ONNX模型路径
            rknn_path: RKNN模型路径
            quantize_txt: 量化数据集
            precision: 精度 (int8/fp16)
        """
        print(f"\n{'='*60}")
        print(f"转换: {os.path.basename(onnx_path)}")
        print(f"精度: {precision.upper()}")
        print(f"{'='*60}\n")
        
        rknn = RKNN()
        
        # 配置
        ret = rknn.config(
            mean_values=[[0, 0, 0]],
            std_values=[[255, 255, 255]],
            target_platform=self.target_platform
        )
        if ret != 0:
            print("配置失败!")
            return False
        
        # 加载ONNX
        print("1. 加载ONNX模型...")
        ret = rknn.load_onnx(model=onnx_path)
        if ret != 0:
            print("加载失败!")
            return False
        
        # 构建
        if precision == 'int8':
            print("2. 构建RKNN模型（INT8量化）...")
            ret = rknn.build(
                do_quantization=True,
                dataset=quantize_txt,
                batch_size=1
            )
        else:
            print("2. 构建RKNN模型（FLOAT16）...")
            ret = rknn.build(do_quantization=False)
        
        if ret != 0:
            print("构建失败!")
            return False
        
        # 导出
        print("3. 导出RKNN模型...")
        ret = rknn.export_rknn(rknn_path)
        if ret != 0:
            print("导出失败!")
            return False
        
        # 性能评估
        print("4. 性能评估...")
        ret = rknn.eval_perf(target=self.target_platform)
        
        rknn.release()
        
        print(f"\n✓ 转换成功: {rknn_path}")
        print(f"  大小: {os.path.getsize(rknn_path) / 1024 / 1024:.2f} MB")
        
        return True

if __name__ == '__main__':
    converter = RKNNConverter(target_platform='rk3568')
    
    # 检测模型 (INT8)
    converter.convert(
        onnx_path='detecttires.onnx',
        rknn_path='detecttires_int8.rknn',
        quantize_txt='quantize_detect.txt',
        precision='int8'
    )
    
    # 检测模型 (FLOAT16)
    converter.convert(
        onnx_path='detecttires.onnx',
        rknn_path='detecttires_fp16.rknn',
        precision='fp16'
    )
    
    # 分类模型 (INT8)
    converter.convert(
        onnx_path='clstires.onnx',
        rknn_path='clstires_int8.rknn',
        quantize_txt='quantize_cls.txt',
        precision='int8'
    )
    
    # 分类模型 (FLOAT16)
    converter.convert(
        onnx_path='clstires.onnx',
        rknn_path='clstires_fp16.rknn',
        precision='fp16'
    )
```

## 模型信息

| 模型 | ONNX大小 | INT8大小 | FP16大小 | 输入尺寸 |
|------|----------|----------|----------|----------|
| detecttires | 47.86MB | 23.78MB | 23.78MB | 640x640 |
| clstires | 45.32MB | 22.23MB | 22.23MB | 224x224 |

## 注意事项

1. **量化数据集**: INT8量化必须提供量化数据集
2. **精度选择**: 先测试INT8，精度不足则用FLOAT16
3. **模型大小**: INT8和FP16模型大小相近
4. **推理速度**: INT8略快于FP16
5. **精度损失**: INT8可能有精度损失，FP16精度高

---
**说明**: 本项目最终使用FLOAT16精度，INT8量化精度损失严重