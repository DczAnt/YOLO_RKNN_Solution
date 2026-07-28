#!/usr/bin/env python3
"""测试 RKNN Toolkit2 安装"""
try:
    from rknn.api import RKNN
    print("✅ RKNN Toolkit2 导入成功")
    
    rknn = RKNN()
    print("✅ RKNN 对象创建成功")
    
    rknn.release()
    print("✅ RKNN 对象释放成功")
    
    print("\n验证完成！RKNN Toolkit2 2.3.2 已正确安装")
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()