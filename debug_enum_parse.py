#!/usr/bin/env python3

import sys
from pathlib import Path

# Add ASTRA to path dynamically
astra_root = Path(__file__).resolve().parent
sys.path.insert(0, str(astra_root))

from astra.parser import parse

# Debug the enum parsing and inference
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

print("Testing enum parsing...")
prog = parse(src)

print("AST structure:")
for item in prog.items:
    print(f"  {type(item).__name__}: {item}")
    if hasattr(item, 'items'):
        for subitem in item.items:
            print(f"    {type(subitem).__name__}: {subitem}")

print("\nFunction body:")
fn = prog.items[1]  # main function
for stmt in fn.body:
    print(f"  {type(stmt).__name__}: {stmt}")
    if hasattr(stmt, 'name') and hasattr(stmt, 'type_name'):
        print(f"    name: {stmt.name}, type_name: {stmt.type_name}")
    if hasattr(stmt, 'expr'):
        print(f"    expr: {stmt.expr}")
