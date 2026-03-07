#!/usr/bin/env python3

import sys
from pathlib import Path

# Add ASTRA to path dynamically
astra_root = Path(__file__).resolve().parent
sys.path.insert(0, str(astra_root))

from astra.parser import parse
from astra.semantic import _infer, _analyze_program

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
prog = parse(src)

# Get the analysis results
try:
    result = _analyze_program(prog, '<input>')
    structs = result.structs
    enums = result.enums
    
    print(f"Structs: {list(structs.keys())}")
    print(f"Enums: {list(enums.keys())}")
    
    # Test inference of Color.Red
    fn = prog.items[1]  # main function
    let_stmt = fn.body[0]  # c: Color = Color.Red
    method_call = let_stmt.expr
    
    print(f"MethodCall: {method_call}")
    print(f"MethodCall.obj: {method_call.obj}")
    print(f"MethodCall.method: {method_call.method}")
    
    # Try to infer the object type
    scopes = [{}]
    mut_scopes = [{}]
    fn_groups = {}
    owned = {}
    borrow = {}
    move = {}
    
    obj_ty = _infer(method_call.obj, scopes, mut_scopes, fn_groups, structs, enums, owned, borrow, move, '<input>', 'main', False, False)
    print(f"Object type: {obj_ty}")
    
    full_ty = _infer(method_call, scopes, mut_scopes, fn_groups, structs, enums, owned, borrow, move, '<input>', 'main', False, False)
    print(f"Full type: {full_ty}")
    
except Exception as e:
    print(f"❌ Analysis failed: {e}")
    import traceback
    traceback.print_exc()
