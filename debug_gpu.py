#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pedro/rust-projects/language/ASTRA')

from astra.parser import parse
from astra.semantic import analyze
from astra.gpu.kernel_lowering import lower_gpu_kernels

# Test GPU kernel lowering
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
gpu_ir_payload = lower_gpu_kernels(prog).to_dict()

print(f"GPU IR payload: {gpu_ir_payload}")
print(f"Has GPU kernels: {bool(gpu_ir_payload)}")
