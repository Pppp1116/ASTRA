#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pedro/rust-projects/language/ASTRA')

from astra.parser import parse
from astra.semantic import analyze, SemanticError
from astra.llvm_codegen import to_llvm_ir


def test_constant_range_validation():
    """Test that out-of-range literals are caught at compile time"""
    print("Testing constant range validation...")
    
    # Test 1: u8 should reject 300
    try:
        src = """
        fn main() u8 {
            return 300u8;
        }
        """
        prog = parse(src)
        analyze(prog)
        print("❌ FAIL: u8 should reject 300")
    except SemanticError as e:
        if "literal 300 out of range for u8" in str(e):
            print("✅ PASS: u8 correctly rejects 300")
        else:
            print(f"❌ FAIL: u8 rejected 300 with wrong error: {e}")
    
    # Test 2: u7 should reject -5
    try:
        src = """
        fn main() u7 {
            return -5u7;
        }
        """
        prog = parse(src)
        analyze(prog)
        print("❌ FAIL: u7 should reject -5")
    except SemanticError as e:
        if "literal -5 out of range for u7" in str(e):
            print("✅ PASS: u7 correctly rejects -5")
        else:
            print(f"❌ FAIL: u7 rejected -5 with wrong error: {e}")
    
    # Test 3: i13 should reject 5000 (range is -4096 to 4095)
    try:
        src = """
        fn main() i13 {
            return 5000i13;
        }
        """
        prog = parse(src)
        analyze(prog)
        print("❌ FAIL: i13 should reject 5000")
    except SemanticError as e:
        if "literal 5000 out of range for i13" in str(e):
            print("✅ PASS: i13 correctly rejects 5000")
        else:
            print(f"❌ FAIL: i13 rejected 5000 with wrong error: {e}")
    
    # Test 4: Valid cases should work
    try:
        src = """
        fn main() u7 {
            return 42u7;
        }
        """
        prog = parse(src)
        analyze(prog)
        print("✅ PASS: u7 accepts 42")
    except SemanticError as e:
        print(f"❌ FAIL: u7 should accept 42: {e}")


def test_llvm_ir_emission():
    """Test LLVM IR emission for arbitrary widths"""
    print("\nTesting LLVM IR emission...")
    
    # Test u7 variable allocation
    try:
        src = """
        fn main() u7 {
            x: u7 = 42u7;
            return x;
        }
        """
        prog = parse(src)
        analyze(prog)
        ir = to_llvm_ir(prog)
        
        print("LLVM IR for u7 variable:")
        print("=" * 50)
        print(ir)
        print("=" * 50)
        
        # Check for i7 allocation
        if "%x = alloca i7" in ir:
            print("✅ PASS: u7 variable allocated as i7")
        else:
            print("❌ FAIL: u7 variable not allocated as i7")
            if "%x = alloca i64" in ir:
                print("   (Found i64 allocation instead)")
        
        # Check function signature
        if "define i7 @main()" in ir:
            print("✅ PASS: Function signature uses i7")
        else:
            print("❌ FAIL: Function signature doesn't use i7")
            if "define i64 @main()" in ir:
                print("   (Found i64 signature instead)")
                
    except Exception as e:
        print(f"❌ FAIL: Error in LLVM IR emission: {e}")


if __name__ == "__main__":
    test_constant_range_validation()
    test_llvm_ir_emission()
