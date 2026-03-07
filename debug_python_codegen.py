#!/usr/bin/env python3

import sys
from pathlib import Path

# Add ASTRA to path dynamically
astra_root = Path(__file__).resolve().parent
sys.path.insert(0, str(astra_root))

from astra.parser import parse
from astra.semantic import analyze
from astra.codegen import to_python

# Test Python code generation
src = """
fn parse(v Int) Int | none{
  if v > 0 {
    return v;
  }
  else {}
  return none;
}

fn helper(v Int) Int | none{
  x = parse(v)!;
  print("after");
  return x + 1;
}

fn main() Int{
  _ = helper(0);
  _ = helper(1);
  return 0;
}
"""

prog = parse(src)
analyze(prog)
py_code = to_python(prog)

print("Generated Python code:")
print(py_code[:500] + "..." if len(py_code) > 500 else py_code)
