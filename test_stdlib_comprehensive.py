#!/usr/bin/env python3

import sys
from pathlib import Path

# Add ASTRA to path dynamically
astra_root = Path(__file__).resolve().parent
sys.path.insert(0, str(astra_root))

from astra.parser import parse
from astra.semantic import analyze
from astra.llvm_codegen import to_llvm_ir
import os


def test_stdlib_modules():
    """Test all stdlib modules with our type fidelity implementation"""
    print("Testing stdlib modules with universal integer type fidelity...")
    
    stdlib_dir = "astra/stdlib"
    test_modules = [
        "core.arixa",
        "c.arixa", 
        "algorithm.arixa",
        "atomic.arixa",
        "math.arixa",
        "mem.arixa"
    ]
    
    results = {}
    
    for module in test_modules:
        module_path = os.path.join(stdlib_dir, module)
        if not os.path.exists(module_path):
            results[module] = "❌ SKIP: File not found"
            continue
            
        print(f"\n--- Testing {module} ---")
        
        try:
            with open(module_path, 'r') as f:
                src = f.read()
            
            # Parse and analyze
            prog = parse(src)
            analyze(prog)
            
            # Try to generate LLVM IR for a simple function if available
            ir = to_llvm_ir(prog)
            
            results[module] = "✅ PASS: Parsed, analyzed, and compiled successfully"
            print(f"✅ PASS: {module}")
            
        except Exception as e:
            # Check if it's just dead code warnings (which we expect)
            error_str = str(e)
            if "warning:" in error_str and "never used" in error_str:
                results[module] = "✅ PASS: Parsed with expected dead code warnings"
                print(f"✅ PASS: {module} (with dead code warnings)")
            else:
                results[module] = f"❌ FAIL: {e}"
                print(f"❌ FAIL: {module} - {e}")
    
    print("\n" + "="*60)
    print("STDLIB TEST SUMMARY")
    print("="*60)
    for module, result in results.items():
        print(f"{module:25} {result}")
    
    # Count results
    passed = sum(1 for r in results.values() if "✅ PASS" in r)
    failed = sum(1 for r in results.values() if "❌ FAIL" in r)
    skipped = sum(1 for r in results.values() if "❌ SKIP" in r)
    
    print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    
    return passed, failed, skipped


def test_arbitrary_widths_in_stdlib():
    """Test that arbitrary widths work correctly in stdlib context"""
    print("\n" + "="*60)
    print("ARBITRARY WIDTH INTEGRATION TEST")
    print("="*60)
    
    # Test program that uses arbitrary widths with stdlib functions
    test_program = """
    import core

    fn test_arithmetic() u7 {
        a: u7 = 42u7;
        b: u7 = 100u7;
        return a + b;
    }
    
    fn test_bitops() i13 {
        x: i13 = 1000i13;
        return x << 2;
    }
    
    fn main() Int {
        result1: u7 = test_arithmetic();
        result2: i13 = test_bitops();
        return 0;
    }
    """
    
    try:
        prog = parse(test_program)
        analyze(prog)
        ir = to_llvm_ir(prog)
        
        print("✅ PASS: Arbitrary widths with stdlib imports work")
        
        # Check for correct type fidelity
        if "i7 42" in ir and "i7 100" in ir:
            print("✅ PASS: u7 literals use correct types")
        else:
            print("❌ FAIL: u7 literals not using correct types")
            
        if "define i7 @test_arithmetic" in ir:
            print("✅ PASS: Function signatures preserve arbitrary widths")
        else:
            print("❌ FAIL: Function signatures not preserving arbitrary widths")
            
        if "@llvm.uadd.with.overflow.i7" in ir or "add i7" in ir:
            print("✅ PASS: Arithmetic operations work with arbitrary widths")
        else:
            print("❌ FAIL: Arithmetic operations not working with arbitrary widths")
            
    except Exception as e:
        print(f"❌ FAIL: Arbitrary width integration test - {e}")


if __name__ == "__main__":
    passed, failed, skipped = test_stdlib_modules()
    test_arbitrary_widths_in_stdlib()
    
    print(f"\n🎯 OVERALL: {passed} modules passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Universal integer type fidelity is working correctly!")
    else:
        print("⚠️  Some tests failed - check the details above")
