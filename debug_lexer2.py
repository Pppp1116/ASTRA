#!/usr/bin/env python3

import sys
from pathlib import Path

# Add ASTRA to path dynamically
astra_root = Path(__file__).resolve().parent
sys.path.insert(0, str(astra_root))

from astra.lexer import lex

# Test lexer tokenization of i13
src = "fn test_func(x: i13) i13"
tokens = lex(src)

print("Tokens:")
for token in tokens:
    print(f"  {token.kind}: {token.text}")
