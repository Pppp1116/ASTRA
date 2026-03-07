#!/usr/bin/env python3

import sys
from pathlib import Path

# Add ASTRA to path dynamically
astra_root = Path(__file__).resolve().parent
sys.path.insert(0, str(astra_root))

from astra.parser import Parser

# Test parsing with debug output
src = """
fn test_func(x: i13) i13 {
    return x + 1i13;
}
"""

parser = Parser(src)
print(f"Initial token: {parser.cur().kind} '{parser.cur().text}'")

# Parse function name
parser.eat("fn")
name = parser.eat("IDENT").text
print(f"After function name: {parser.cur().kind} '{parser.cur().text}'")

# Parse parameters
params, variadic, param_mut = parser._parse_params()
print(f"After params: {parser.cur().kind} '{parser.cur().text}'")
print(f"starts_type: {parser._starts_type()}")

if parser._starts_type():
    ret = parser.parse_type()
    print(f"Parsed return type: {ret}")
else:
    print("No return type found")
