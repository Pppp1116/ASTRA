#!/usr/bin/env python3

import sys
from pathlib import Path

# Add ASTRA to path dynamically
astra_root = Path(__file__).resolve().parent
sys.path.insert(0, str(astra_root))

from astra.lexer import lex

# Test lexer tokenization of just the parameter part
src = "(x: i13)"
tokens = lex(src)

print("Tokens for '(x: i13)':")
for token in tokens:
    print(f"  {token.kind}: {token.text} (line {token.line}, col {token.col})")
