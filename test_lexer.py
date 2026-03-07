#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pedro/rust-projects/language/ASTRA')

from astra.lexer import lex


def test_lexer():
    """Test if lexer correctly tokenizes u7"""
    print("Testing lexer for u7...")
    
    tokens = lex("u7")
    for token in tokens:
        print(f"Token: {token.kind} = '{token.text}'")
    
    print("\nTesting lexer for function...")
    tokens = lex("fn test(x: u7) u7 { return x + 1; }")
    for token in tokens:
        print(f"Token: {token.kind} = '{token.text}'")


if __name__ == "__main__":
    test_lexer()
