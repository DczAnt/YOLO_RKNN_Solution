#!/usr/bin/env python3
"""
YOLO PT to ONNX conversion script
"""
import argparse
import sys
import shutil
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Convert YOLO PT to ONNX')
    parser.add_argument('--model', required=True, help='Input PT model path')
    parser.add_argument('--output', required=True, help='Output ONNX path')
    parser.add_argument('--imgsz', type=int, default=640, help='Input image size')
    parser.add_argument('--opset', type=int, default=12, help='ONNX opset version')
    parser.add_argument('--simplify', action='store_true', help='Simplify ONNX model')
    parser.add_argument('--dynamic', action='store_true', help='Dynamic batch size')
    
    args = parser.parse_args()
    
    try:
        from ultralytics import YOLO
        
        print(f"Loading model: {args.model}")
        model = YOLO(args.model)
        
        print(f"Exporting to ONNX...")
        export_path = model.export(
            format='onnx',
            imgsz=args.imgsz,
            opset=args.opset,
            simplify=args.simplify,
            dynamic=args.dynamic
        )
        
        export_path = Path(export_path)
        output_path = Path(args.output)
        
        if export_path != output_path:
            shutil.move(str(export_path), str(output_path))
            print(f"Moved to: {output_path}")
        
        print(f"Successfully exported to: {output_path}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())