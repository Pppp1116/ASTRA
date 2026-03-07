#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pedro/rust-projects/language/ASTRA')

from astra.parser import parse
from astra.semantic import analyze
from astra.llvm_codegen import to_llvm_ir


def debug_literal_compilation():
    """Debug literal compilation process"""
    print("Debugging literal compilation...")
    
    # Test 1: Simple u7 literal
    src1 = """
    fn main() u7 {
        return 42u7;
    }
    """
    
    prog1 = parse(src1)
    analyze(prog1)
    ir1 = to_llvm_ir(prog1)
    
    print("Test 1: Direct return of 42u7")
    print("=" * 50)
    print(ir1)
    print("=" * 50)
    
    # Test 2: Variable assignment
    src2 = """
    fn main() u7 {
        x: u7 = 42u7;
        return x;
    }
    """
    
    prog2 = parse(src2)
    analyze(prog2)
    ir2 = to_llvm_ir(prog2)
    
    print("\nTest 2: Variable assignment of 42u7")
    print("=" * 50)
    print(ir2)
    print("=" * 50)
    
    # Look for truncation patterns
    print("\nLooking for truncation patterns:")
    if "trunc i64" in ir2:
        print("❌ FOUND: 'trunc i64' - literals being widened then truncated")
        # Find the exact line
        for line in ir2.split('\n'):
            if 'trunc i64' in line:
                print(f"   {line.strip()}")
    else:
        print("✅ GOOD: No 'trunc i64' found")
    
    if "i7 42" in ir2:
        print("✅ GOOD: Found 'i7 42' - literal directly as i7")
    else:
        print("❌ MISSING: No 'i7 42' found")


if __name__ == "__main__":
    debug_literal_compilation()
