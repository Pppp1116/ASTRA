#!/usr/bin/env python3

import sys
from pathlib import Path

# Add ASTRA to path dynamically
astra_root = Path(__file__).resolve().parent
sys.path.insert(0, str(astra_root))

from astra.parser import parse
from astra.semantic import analyze

# Test enum variant with payload
src = """
enum Inner {
  X,
  Y,
}
enum Outer {
  A(Inner, Inner),
}
fn main() Int{
  v: Outer = Outer.A(Inner.X, Inner.Y);
  return 0;
}
"""

print("Testing enum variant with payload...")
try:
    prog = parse(src)
    analyze(prog)
    print("✅ Analysis succeeded")
except Exception as e:
    print(f"❌ Analysis failed: {e}")
