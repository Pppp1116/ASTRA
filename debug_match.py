#!/usr/bin/env python3

import sys
from pathlib import Path

# Add ASTRA to path dynamically
astra_root = Path(__file__).resolve().parent
sys.path.insert(0, str(astra_root))

from astra.parser import parse
from astra.semantic import analyze

# Debug the enum pattern matching issue
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

print("Testing basic enum usage...")
try:
    prog = parse(src)
    analyze(prog)
    print("✅ Basic enum usage works")
except Exception as e:
    print(f"❌ Basic enum usage failed: {e}")

# Test the match statement specifically
src2 = """
enum Color {
  Red,
  Green,
  Blue,
}
fn main() Int{
  c: Color = Color.Red;
  match c {
    Color.Red => { return 1; }
    Color.Green => { return 2; }
    Color.Blue => { return 3; }
  }
  return 0;
}
"""

print("\nTesting complete match...")
try:
    prog = parse(src2)
    analyze(prog)
    print("✅ Complete match works")
except Exception as e:
    print(f"❌ Complete match failed: {e}")
