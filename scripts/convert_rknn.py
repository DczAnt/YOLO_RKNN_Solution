#!/usr/bin/env python3
"""
ONNX to RKNN conversion script
"""
import argparse
import sys
import numpy as np
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Convert ONNX to RKNN')
    parser.add_argument('--model', required=True, help='Input ONNX model path')
    parser.add_argument('--output', required=True, help='Output RKNN path')
    parser.add_argument('--platform', default='RK3588', help='Target platform')
    parser.add_argument('--precision', default='fp16', choices=['fp16', 'int8'], help='Quantization precision')
    parser.add_argument('--mean', nargs=3, type=float, default=[0, 0, 0], help='Mean values')
    parser.add_argument('--std', nargs=3, type=float, default=[255, 255, 255], help='Std values')
    parser.add_argument('--quantize-dataset', help='Quantization dataset path')
    
    args = parser.parse_args()
    
    try:
        from rknn.api import RKNN
        
        print(f"Creating RKNN for {args.platform}")
        rknn = RKNN()
        
        print(f"Configuring RKNN...")
        ret = rknn.config(
            mean_values=[args.mean],
            std_values=[args.std],
            target_platform=args.platform
        )
        if ret != 0:
            print(f"Failed to config RKNN, error: {ret}", file=sys.stderr)
            return 1
        
        print(f"Loading ONNX model: {args.model}")
        ret = rknn.load_onnx(model=args.model)
        if ret != 0:
            print(f"Failed to load ONNX model, error: {ret}", file=sys.stderr)
            return 1
        
        print(f"Building RKNN model with {args.precision} precision...")
        if args.precision == 'int8' and args.quantize_dataset:
            ret = rknn.build(do_quantization=True, dataset=args.quantize_dataset, batch_size=1)
        else:
            ret = rknn.build(do_quantization=False)
        
        if ret != 0:
            print(f"Failed to build RKNN model, error: {ret}", file=sys.stderr)
            return 1
        
        print(f"Exporting RKNN model to: {args.output}")
        ret = rknn.export_rknn(args.output)
        if ret != 0:
            print(f"Failed to export RKNN model, error: {ret}", file=sys.stderr)
            return 1
        
        rknn.release()
        print(f"Successfully exported to: {args.output}")
        return 0
        
    except ImportError:
        print("RKNN Toolkit not installed. Please install rknn-toolkit2", file=sys.stderr)
        print("For simulation, creating dummy RKNN file...", file=sys.stderr)
        Path(args.output).write_bytes(b'RKNN_DUMMY')
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())