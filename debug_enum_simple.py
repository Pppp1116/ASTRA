#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pedro/rust-projects/language/ASTRA')

from astra.parser import parse
from astra.semantic import analyze

# Debug the enum inference issue
src = """
enum Color {
  Red,
  Green,
  Blue,
}
fn main() Int{
  c: Color = Color.Red;
  return 0;
}
"""

print("Testing enum inference...")
try:
    prog = parse(src)
    analyze(prog)
    print("✅ Analysis succeeded")
except Exception as e:
    print(f"❌ Analysis failed: {e}")
    
    # Let's check what the actual error is
    error_str = str(e)
    if "expected Color, got Any" in error_str:
        print("The issue is that Color.Red is being inferred as Any instead of Color")
        print("This suggests the enum variant access isn't working properly")
