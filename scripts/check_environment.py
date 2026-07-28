#!/usr/bin/env python3
"""
Environment check script
"""
import argparse
import sys

def check_pt_onnx():
    """Check PT to ONNX conversion environment"""
    try:
        import torch
        print(f"PyTorch: {torch.__version__}")
    except ImportError:
        print("PyTorch not installed", file=sys.stderr)
        return False
    
    try:
        from ultralytics import YOLO
        print("Ultralytics: OK")
    except ImportError:
        print("Ultralytics not installed", file=sys.stderr)
        return False
    
    try:
        import onnx
        print(f"ONNX: {onnx.__version__}")
    except ImportError:
        print("ONNX not installed", file=sys.stderr)
        return False
    
    return True

def check_rknn():
    """Check RKNN conversion environment"""
    try:
        from rknn.api import RKNN
        print("RKNN Toolkit: OK")
        return True
    except ImportError:
        print("RKNN Toolkit not installed", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description='Check environment')
    parser.add_argument('--check-pt-onnx', action='store_true', help='Check PT to ONNX environment')
    parser.add_argument('--check-rknn', action='store_true', help='Check RKNN environment')
    
    args = parser.parse_args()
    
    if args.check_pt_onnx:
        if check_pt_onnx():
            print("PT to ONNX environment: OK")
            return 0
        else:
            print("PT to ONNX environment: FAILED", file=sys.stderr)
            return 1
    
    if args.check_rknn:
        if check_rknn():
            print("RKNN environment: OK")
            return 0
        else:
            print("RKNN environment: FAILED", file=sys.stderr)
            return 1
    
    print("Checking all environments...")
    pt_ok = check_pt_onnx()
    rknn_ok = check_rknn()
    
    if pt_ok and rknn_ok:
        print("All environments: OK")
        return 0
    else:
        print("Some environments: FAILED", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())