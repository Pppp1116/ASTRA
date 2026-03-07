#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from astra.parser import Parser
from astra.lexer import lex

# Test the problematic line
src = "mut step = target_ms - now;"

print(f"Testing lexer on: '{src}'")
tokens = lex(src)
for i, token in enumerate(tokens):
    print(f"  {i}: {token.kind}: '{token.text}'")

print("\nTesting parser...")
parser = Parser(src)
print(f"Current token: {parser.cur().kind} '{parser.cur().text}'")
print(f"Next token: {parser.peek().kind} '{parser.peek().text}'")
if len(parser.toks) > 2:
    print(f"Next next token: {parser.toks[2].kind} '{parser.toks[2].text}'")
if len(parser.toks) > 3:
    print(f"Next next next token: {parser.toks[3].kind} '{parser.toks[3].text}'")

# Debug the _looks_like_binding_start logic
j = parser.i
if parser.toks[j].kind == "mut":
    print("✓ Found 'mut'")
    j += 1
else:
    print("✗ No 'mut' found")

if parser.toks[j].kind != "IDENT":
    print(f"✗ Next token is not IDENT: {parser.toks[j].kind}")
else:
    print(f"✓ Found IDENT: {parser.toks[j].text}")
    j += 1

if parser.toks[j].kind == ":":
    print("Found ':' - checking for type")
else:
    print(f"No ':' found, checking if '=': {parser.toks[j].kind == '='}")

print(f"Final result: {parser._looks_like_binding_start()}")
