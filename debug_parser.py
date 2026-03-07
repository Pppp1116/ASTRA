#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pedro/rust-projects/language/ASTRA')

from astra.parser import parse

# Test parsing of function with i13 return type
src = """
fn test_func(x: i13) i13 {
    return x + 1i13;
}
"""

try:
    prog = parse(src)
    print("✅ Parsing succeeded")
    print(f"Program: {prog}")
except Exception as e:
    print(f"❌ Parsing failed: {e}")
