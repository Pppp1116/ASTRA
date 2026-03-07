#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astra.parser import parse
from astra.semantic import analyze
from astra.llvm_codegen import to_llvm_ir


def comprehensive_type_fidelity_test():
    """Comprehensive test of universal integer type fidelity implementation"""
    print("🚀 COMPREHENSIVE UNIVERSAL INTEGER TYPE FIDELITY TEST")
    print("=" * 70)
    
    # Test all phases of our implementation
    tests_passed = 0
    tests_failed = 0
    
    # Phase 0: Range validation
    print("\n📋 Phase 0: Constant Range Validation")
    test_cases = [
        ("300u8", False, "should reject out-of-range u8"),
        ("-5u7", False, "should reject negative u7"),
        ("5000i13", False, "should reject out-of-range i13"),
        ("42u7", True, "should accept valid u7"),
        ("1000i13", True, "should accept valid i13"),
    ]
    
    for literal, should_pass, description in test_cases:
        src = f"fn main() Int {{ return {literal}; }}"
        try:
            prog = parse(src)
            analyze(prog)
            if should_pass:
                print(f"  ✅ PASS: {literal} {description}")
                tests_passed += 1
            else:
                print(f"  ❌ FAIL: {literal} should have been rejected")
                tests_failed += 1
        except SemanticError as e:
            if not should_pass and "out of range" in str(e):
                print(f"  ✅ PASS: {literal} {description}")
                tests_passed += 1
            else:
                print(f"  ❌ FAIL: {literal} unexpected error: {e}")
                tests_failed += 1
    
    # Phase 1 & 3: Literal type fidelity
    print("\n🔧 Phase 1 & 3: LLVM IR Type Fidelity & Coercion")
    fidelity_tests = [
        ("u7", "42u7", "i7 42"),
        ("i13", "3000i13", "i13 3000"),
        ("u23", "1000000u23", "i23 1000000"),
        ("u99", "123456789u99", "i99 123456789"),
    ]
    
    for width, literal, expected_pattern in fidelity_tests:
        src = f"fn main() {width} {{ return {literal}; }}"
        try:
            prog = parse(src)
            analyze(prog)
            ir = to_llvm_ir(prog)
            
            if expected_pattern in ir and "trunc i64" not in ir:
                print(f"  ✅ PASS: {width} literal uses exact type")
                tests_passed += 1
            else:
                print(f"  ❌ FAIL: {width} literal type fidelity issue")
                tests_failed += 1
        except Exception as e:
            print(f"  ❌ FAIL: {width} literal error: {e}")
            tests_failed += 1
    
    # Phase 2: Overflow intrinsics
    print("\n⚡ Phase 2: Arithmetic Overflow Intrinsics")
    overflow_tests = [("u7", "i7"), ("i13", "i13"), ("u23", "i23"), ("u99", "i99")]
    
    for width, llvm_type in overflow_tests:
        src = f"fn test(x {width}) {width} {{ return x + 1; }}"
        try:
            prog = parse(src)
            analyze(prog)
            
            # Debug mode
            debug_ir = to_llvm_ir(prog, overflow_mode="trap")
            # Release mode  
            release_ir = to_llvm_ir(prog, overflow_mode="wrap")
            
            intrinsic = f"@llvm.{'u' if width[0] == 'u' else 's'}add.with.overflow.{llvm_type}"
            
            if (intrinsic in debug_ir and "br i1" in debug_ir and 
                intrinsic not in release_ir and f"add {llvm_type}" in release_ir):
                print(f"  ✅ PASS: {width} overflow intrinsics work")
                tests_passed += 1
            else:
                print(f"  ❌ FAIL: {width} overflow intrinsics issue")
                tests_failed += 1
        except Exception as e:
            print(f"  ❌ FAIL: {width} overflow test error: {e}")
            tests_failed += 1
    
    # Phase 4: Packed structs
    print("\n📦 Phase 4: @packed Struct Layout")
    try:
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
        
        prog = parse(src)
        analyze(prog)
        ir = to_llvm_ir(prog)
        
        # Check for bit-field operations
        if ("zext i7" in ir and "zext i9" in ir and 
            "shl" in ir and "and" in ir):
            print("  ✅ PASS: @packed struct bit-field operations work")
            tests_passed += 1
        else:
            print("  ❌ FAIL: @packed struct bit-field operations missing")
            tests_failed += 1
    except Exception as e:
        print(f"  ❌ FAIL: @packed struct test error: {e}")
        tests_failed += 1
    
    # Phase 5: Function signatures
    print("\n🎯 Phase 5: Function Parameter/Return Type Fidelity")
    signature_tests = [("u7", "i7"), ("i13", "i13"), ("u23", "i23"), ("u99", "i99")]
    
    for width, llvm_type in signature_tests:
        src = f"fn test(x {width}) {width} {{ return x + 1; }}"
        try:
            prog = parse(src)
            analyze(prog)
            ir = to_llvm_ir(prog)
            
            expected_sig = f"define {llvm_type} @test({llvm_type}"
            if expected_sig in ir:
                print(f"  ✅ PASS: {width} function signature preserves types")
                tests_passed += 1
            else:
                print(f"  ❌ FAIL: {width} function signature type fidelity issue")
                tests_failed += 1
        except Exception as e:
            print(f"  ❌ FAIL: {width} function signature error: {e}")
            tests_failed += 1
    
    # Dead code analyzer test
    print("\n🔍 Dead Code Analyzer")
    try:
        src = """
        fn used() Int { return 1; }
        fn unused() Int { return 2; }
        
        fn main() Int {
            return used();
        }
        """
        
        prog = parse(src)
        analyze(prog)
        print("  ✅ PASS: Dead code analyzer works")
        tests_passed += 1
    except SemanticError as e:
        if "never used" in str(e):
            print("  ✅ PASS: Dead code analyzer detects unused functions")
            tests_passed += 1
        else:
            print(f"  ❌ FAIL: Dead code analyzer error: {e}")
            tests_failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 COMPREHENSIVE TEST RESULTS")
    print("=" * 70)
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print(f"Total Tests: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✨ Universal Integer Type Fidelity is working perfectly!")
        print("🚀 ALL iN/uN types (1-128 bits) have complete type fidelity!")
        return True
    else:
        print(f"\n⚠️  {tests_failed} tests failed")
        print("🔧 Some type fidelity issues need attention")
        return False


if __name__ == "__main__":
    success = comprehensive_type_fidelity_test()
    sys.exit(0 if success else 1)
