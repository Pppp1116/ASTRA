#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pedro/rust-projects/language/ASTRA')

from astra.parser import parse
from astra.semantic import analyze
from astra.llvm_codegen import to_llvm_ir


def test_simple_packed_struct():
    """Test simple @packed struct"""
    print("Testing simple @packed struct...")
    
    src = """
    @packed
    struct Test {
        a: u7
        b: u9
    }
    
    fn main() Int {
        t: Test = Test(42u7, 100u9);
        return 0;
    }
    """
    
    try:
        prog = parse(src)
        analyze(prog)
        ir = to_llvm_ir(prog)
        
        print("✅ PASS: Parsed and compiled successfully")
        print("\nGenerated IR:")
        print("=" * 50)
        print(ir)
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ FAIL: {e}")


if __name__ == "__main__":
    test_simple_packed_struct()
