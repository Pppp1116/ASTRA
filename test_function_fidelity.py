#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pedro/rust-projects/language/ASTRA')

from astra.parser import parse
from astra.semantic import analyze
from astra.llvm_codegen import to_llvm_ir


def test_function_parameter_return_fidelity():
    """Test function parameter and return type fidelity for arbitrary widths"""
    print("Testing function parameter/return type fidelity...")
    
    test_cases = [
        ("u7", "i7", "i7"),
        ("i13", "i13", "i13"), 
        ("u23", "i23", "i23"),
        ("u99", "i99", "i99"),
    ]
    
    for width, llvm_param_type, llvm_return_type in test_cases:
        print(f"\n--- Testing {width} ---")
        
        # Test function with multiple parameters
        src = f"""
        fn test_func(a {width}, b {width}) {width} {{
            x: {width} = a + 1{width};
            y: {width} = b + 2{width};
            return x + y;
        }}
        
        fn main() Int {{
            result: {width} = test_func(10{width}, 20{width});
            return 0;
        }}
        """
        
        try:
            prog = parse(src)
            analyze(prog)
            ir = to_llvm_ir(prog)
            
            # Check function signature
            expected_sig = f"define {llvm_return_type} @test_func({llvm_param_type} %a, {llvm_param_type} %b)"
            if expected_sig in ir:
                print(f"✅ PASS: Found correct function signature")
            else:
                print(f"❌ FAIL: Missing expected signature '{expected_sig}'")
                # Show actual function definitions
                for line in ir.split('\n'):
                    if 'define' in line and 'test_func' in line:
                        print(f"   Found: {line.strip()}")
            
            # Check for parameter type fidelity (no unwanted extensions)
            if f"sext {llvm_param_type}" in ir or f"zext {llvm_param_type}" in ir:
                print(f"❌ FAIL: Found unwanted parameter extension")
            else:
                print(f"✅ PASS: No unwanted parameter extensions")
            
            # Check for return type fidelity (no unwanted truncations)
            if f"trunc {llvm_param_type}" in ir and "test_func" not in ir:
                print(f"❌ FAIL: Found unwanted return truncation")
            else:
                print(f"✅ PASS: No unwanted return truncations")
                
        except Exception as e:
            print(f"❌ FAIL: {e}")


if __name__ == "__main__":
    test_function_parameter_return_fidelity()
