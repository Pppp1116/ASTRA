#!/usr/bin/env python3

import sys
from pathlib import Path

# Add ASTRA to path dynamically
astra_root = Path(__file__).resolve().parent
sys.path.insert(0, str(astra_root))

from astra.parser import parse

# Debug enum variant with payload
src = """
enum Outer {
  A(Inner, Inner),
}
fn main() Int{
  v: Outer = Outer.A(Inner.X, Inner.Y);
  return 0;
}
"""

print("Testing enum variant with payload...")
prog = parse(src)

print("AST structure:")
fn = prog.items[1]  # main function
let_stmt = fn.body[0]  # v: Outer = Outer.A(Inner.X, Inner.Y)
print(f"Expression type: {type(let_stmt.expr)}")
print(f"Expression: {let_stmt.expr}")

if hasattr(let_stmt.expr, 'obj'):
    print(f"obj: {let_stmt.expr.obj}")
    print(f"obj type: {type(let_stmt.expr.obj)}")
if hasattr(let_stmt.expr, 'method'):
    print(f"method: {let_stmt.expr.method}")
if hasattr(let_stmt.expr, 'args'):
    print(f"args: {let_stmt.expr.args}")
