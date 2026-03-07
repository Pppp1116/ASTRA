#!/usr/bin/env python3

import sys
from pathlib import Path

# Add ASTRA to path dynamically
astra_root = Path(__file__).resolve().parent
sys.path.insert(0, str(astra_root))

from astra.parser import parse

# Test basic for loop
src = """
fn main() Int {
  for i in 0..2 {
    print(i);
  }
  return 0;
}
"""

print("Testing basic for loop...")
try:
    prog = parse(src)
    print("✅ Parsed successfully")
except Exception as e:
    print(f"❌ Parse failed: {e}")

# Test with space
src2 = """
fn main() Int {
  for i in 0 .. 2 {
    print(i);
  }
  return 0;
}
"""

print("\nTesting for loop with space...")
try:
    prog2 = parse(src2)
    print("✅ Parsed successfully")
except Exception as e:
    print(f"❌ Parse failed: {e}")
