#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pedro/rust-projects/language/ASTRA')

from astra.parser import parse
from astra.semantic import analyze
from astra.llvm_codegen import to_llvm_ir, _llvm_type, _ModuleCtx, _int_info


def debug_llvm_types():
    """Debug what _llvm_type returns for arbitrary widths"""
    print("Debugging LLVM type generation...")
    
    # Create a minimal module context
    prog = parse("fn main() Int { return 0; }")
    analyzed = analyze(prog)
    ctx = _ModuleCtx(analyzed, "test", "x86_64-unknown-linux-gnu", False)
    
    # Test different types
    test_types = ["Int", "u7", "i13", "u23", "u99", "i32", "u64"]
    
    for typ in test_types:
        print(f"\n--- Testing {typ} ---")
        
        # Test _int_info
        info = _int_info(typ)
        print(f"_int_info('{typ}') = {info}")
        
        # Test _llvm_type
        try:
            llty = _llvm_type(ctx, typ)
            print(f"_llvm_type('{typ}') = {llty}")
            print(f"  isinstance(llty, ir.IntType) = {isinstance(llty, llty.__class__)}")
            if hasattr(llty, 'width'):
                print(f"  llty.width = {llty.width}")
        except Exception as e:
            print(f"_llvm_type('{typ}') ERROR: {e}")


def debug_literal_compilation():
    """Debug literal compilation process"""
    print("\n\nDebugging literal compilation...")
    
    src = """
    fn main() u7 {
        x: u7 = 42u7;
        return x;
    }
    """
    
    prog = parse(src)
    analyzed = analyze(prog)
    ir = to_llvm_ir(prog)
    
    print("Generated LLVM IR:")
    print("=" * 50)
    print(ir)
    print("=" * 50)


if __name__ == "__main__":
    debug_llvm_types()
    debug_literal_compilation()
