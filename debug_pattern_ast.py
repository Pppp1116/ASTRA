#!/usr/bin/env python3

import sys
from pathlib import Path

# Add ASTRA to path dynamically
astra_root = Path(__file__).resolve().parent
sys.path.insert(0, str(astra_root))

from astra.parser import parse
from astra.ast import *

# Test AST structure for enum pattern matching
src = """
enum E {
  A(Int),
  B,
}
fn main() Int{
  v: E = E.A(7);
  match v {
    E.A(x) => { return x; }
    E.B => { return 0; }
  }
  return 0;
}
"""

prog = parse(src)
main_fn = prog.items[1]  # main function
match_stmt = main_fn.body[1]  # match statement
pattern = match_stmt.arms[0][0]  # E.A(x) pattern

print(f"Pattern type: {type(pattern)}")
print(f"Pattern: {pattern}")

if hasattr(pattern, 'fn'):
    print(f"Pattern.fn type: {type(pattern.fn)}")
    print(f"Pattern.fn: {pattern.fn}")

if hasattr(pattern, 'args'):
    print(f"Pattern.args: {pattern.args}")
