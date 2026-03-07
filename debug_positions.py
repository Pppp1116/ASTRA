#!/usr/bin/env python3

import sys
from pathlib import Path

# Add ASTRA to path dynamically
astra_root = Path(__file__).resolve().parent
sys.path.insert(0, str(astra_root))

from astra.lexer import lex

# Test lexer tokenization with positions
src = """
fn test_func(x: i13) i13 {
    return x + 1i13;
}
"""

tokens = lex(src)

print("Tokens with positions:")
for token in tokens:
    print(f"  {token.kind}: {token.text} (line {token.line}, col {token.col})")
