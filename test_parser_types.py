#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pedro/rust-projects/language/ASTRA')

from astra.parser import parse
from astra.semantic import analyze


def test_simple_types():
    """Test parsing of different integer types"""
    
    # Test with known working type first
    working_cases = [
        "fn test(x: i32) i32 { return x + 1; }",
        "fn test(x: u64) u64 { return x + 1; }",
    ]
    
    for src in working_cases:
        print(f"Testing: {src}")
        try:
            prog = parse(src)
            analyze(prog)
            print("✅ PASS")
        except Exception as e:
            print(f"❌ FAIL: {e}")
    
    # Test with arbitrary width
    arbitrary_cases = [
        "fn test(x: u7) u7 { return x + 1; }",
        "fn test(x: i13) i13 { return x + 1; }",
    ]
    
    for src in arbitrary_cases:
        print(f"\nTesting: {src}")
        try:
            prog = parse(src)
            analyze(prog)
            print("✅ PASS")
        except Exception as e:
            print(f"❌ FAIL: {e}")


if __name__ == "__main__":
    test_simple_types()
