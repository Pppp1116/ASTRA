#!/usr/bin/env python3

import sys
from pathlib import Path

# Add ASTRA to path dynamically
astra_root = Path(__file__).resolve().parent
sys.path.insert(0, str(astra_root))

from astra.lexer import lex

# Test the lexer on for loop
src = "for i in 0..2 {"

print("Testing lexer on: 'for i in 0..2 {'")
tokens = lex(src)
for token in tokens:
    print(f"  {token.kind}: '{token.text}'")
