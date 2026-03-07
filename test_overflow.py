#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pedro/rust-projects/language/ASTRA')

from astra.parser import parse
from astra.semantic import analyze
from astra.llvm_codegen import to_llvm_ir


def test_overflow_intrinsics():
    """Test overflow intrinsics for arbitrary widths"""
    print("Testing overflow intrinsics for arbitrary widths...")
    
    test_cases = [
        ("u7", "i7", False),
        ("i13", "i13", True),
        ("u23", "i23", False),
        ("u99", "i99", False),
    ]
    
    for width, llvm_type, signed in test_cases:
        print(f"\n--- Testing {width} ---")
        
        # Test debug mode generates overflow intrinsics
        src = f"""
        fn test(x: {width}) {width} {{
            return x + 1;
        }}
        """
        prog = parse(src)
        analyze(prog)
        ir = to_llvm_ir(prog, overflow_mode="trap")
        
        # Verify overflow intrinsic is present
        intrinsic = f"@llvm.{'u' if not signed else 's'}add.with.overflow.{llvm_type}"
        if intrinsic in ir:
            print(f"✅ PASS: Found {intrinsic}")
        else:
            print(f"❌ FAIL: Missing {intrinsic}")
        
        # Verify conditional branch pattern
        if "br i1" in ir:
            print("✅ PASS: Found conditional branch")
        else:
            print("❌ FAIL: Missing conditional branch")
        
        if "overflow_trap" in ir:
            print("✅ PASS: Found overflow trap block")
        else:
            print("❌ FAIL: Missing overflow trap block")
        
        if "call void @llvm.trap()" in ir:
            print("✅ PASS: Found llvm.trap call")
        else:
            print("❌ FAIL: Missing llvm.trap call")
        
        # Test release mode generates plain arithmetic
        release_ir = to_llvm_ir(prog, overflow_mode="wrap")
        if intrinsic not in release_ir:
            print(f"✅ PASS: No {intrinsic} in release mode")
        else:
            print(f"❌ FAIL: {intrinsic} present in release mode")
        
        if f"add {llvm_type}" in release_ir:
            print(f"✅ PASS: Plain add {llvm_type} in release")
        else:
            print(f"❌ FAIL: Missing plain add {llvm_type} in release")
        
        if "br i1" not in release_ir:
            print("✅ PASS: No conditional branch in release")
        else:
            print("❌ FAIL: Conditional branch in release")


if __name__ == "__main__":
    test_overflow_intrinsics()
