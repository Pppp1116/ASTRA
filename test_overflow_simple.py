#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pedro/rust-projects/language/ASTRA')

from astra.parser import parse
from astra.semantic import analyze
from astra.llvm_codegen import to_llvm_ir


def test_overflow_intrinsics():
    """Test overflow intrinsics for arbitrary widths"""
    print("Testing overflow intrinsics for arbitrary widths...")
    
    # Test with a simple case first
    width = "u7"
    src = f"""
    fn test(x: {width}) {width} {{
        return x + 1;
    }}
    """
    
    print(f"Source code:\n{src}")
    
    try:
        prog = parse(src)
        analyze(prog)
        ir = to_llvm_ir(prog, overflow_mode="trap")
        
        print("LLVM IR:")
        print("=" * 50)
        print(ir)
        print("=" * 50)
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_overflow_intrinsics()
