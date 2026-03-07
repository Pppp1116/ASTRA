#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pedro/rust-projects/language/ASTRA')

from astra.parser import parse
from astra.semantic import analyze
from astra.llvm_codegen import to_llvm_ir


def test_packed_struct_layout():
    """Test @packed struct layout for arbitrary widths"""
    print("Testing @packed struct layout...")
    
    # Test case 1: { a: u1, b: u3, c: u4 } = exactly 1 byte
    src1 = """
    @packed
    struct Test1 {
        a: u1
        b: u3  
        c: u4
    }
    
    fn main() Int {
        t: Test1 = Test1 { a: 1u1, b: 5u3, c: 10u4 };
        return 0;
    }
    """
    
    print("\n--- Test 1: { u1, u3, u4 } should be 1 byte ---")
    try:
        prog1 = parse(src1)
        analyze(prog1)
        ir1 = to_llvm_ir(prog1)
        
        print("Generated IR:")
        print("=" * 50)
        # Extract struct definition
        lines = ir1.split('\n')
        for line in lines:
            if 'Test1' in line and ('=' in line or 'type' in line):
                print(line)
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test case 2: { a: u7, b: u9 } = exactly 2 bytes (7+9=16 bits)
    src2 = """
    @packed
    struct Test2 {
        a: u7
        b: u9
    }
    
    fn main() Int {
        t: Test2 = Test2 { a: 42u7, b: 100u9 };
        return 0;
    }
    """
    
    print("\n--- Test 2: { u7, u9 } should be 2 bytes ---")
    try:
        prog2 = parse(src2)
        analyze(prog2)
        ir2 = to_llvm_ir(prog2)
        
        print("Generated IR:")
        print("=" * 50)
        # Extract struct definition
        lines = ir2.split('\n')
        for line in lines:
            if 'Test2' in line and ('=' in line or 'type' in line):
                print(line)
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
    
    # Test case 3: { a: i13, b: u3, c: u12 } = exactly 3 bytes (13+3+12=28 bits)
    src3 = """
    @packed
    struct Test3 {
        a: i13
        b: u3
        c: u12
    }
    
    fn main() Int {
        t: Test3 = Test3 { a: 1000i13, b: 5u3, c: 100u12 };
        return 0;
    }
    """
    
    print("\n--- Test 3: { i13, u3, u12 } should be 3 bytes ---")
    try:
        prog3 = parse(src3)
        analyze(prog3)
        ir3 = to_llvm_ir(prog3)
        
        print("Generated IR:")
        print("=" * 50)
        # Extract struct definition
        lines = ir3.split('\n')
        for line in lines:
            if 'Test3' in line and ('=' in line or 'type' in line):
                print(line)
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ FAIL: {e}")


if __name__ == "__main__":
    test_packed_struct_layout()
