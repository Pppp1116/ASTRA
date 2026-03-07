#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pedro/rust-projects/language/ASTRA')

from astra.parser import parse
from astra.semantic import analyze
from astra.llvm_codegen import to_llvm_ir


def test_universal_literal_fidelity():
    """Test literal fidelity for multiple arbitrary widths"""
    print("Testing universal literal type fidelity...")
    
    test_cases = [
        ("u7", "42u7", "i7 42"),
        ("i13", "3000i13", "i13 3000"),  # i13 range: -4096 to 4095
        ("u23", "1000000u23", "i23 1000000"),  # u23 range: 0 to 8,388,607
        ("u99", "123456789u99", "i99 123456789"),  # u99 range: 0 to huge
    ]
    
    for width, literal, expected_pattern in test_cases:
        print(f"\n--- Testing {width} ---")
        
        src = f"""
        fn main() {width} {{
            return {literal};
        }}
        """
        
        prog = parse(src)
        analyze(prog)
        ir = to_llvm_ir(prog)
        
        # Check for correct pattern
        if expected_pattern in ir:
            print(f"✅ PASS: Found '{expected_pattern}'")
        else:
            print(f"❌ FAIL: Missing '{expected_pattern}'")
        
        # Check for no truncation
        if "trunc i64" in ir:
            print(f"❌ FAIL: Found 'trunc i64' - should not truncate")
            for line in ir.split('\n'):
                if 'trunc i64' in line:
                    print(f"   {line.strip()}")
        else:
            print("✅ PASS: No 'trunc i64' found")


if __name__ == "__main__":
    test_universal_literal_fidelity()
