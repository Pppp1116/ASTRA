#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pedro/rust-projects/language/ASTRA')

from astra.parser import Parser

# Test the problematic line
src = "mut step = target_ms - now;"

print(f"Testing parser on: '{src}'")
parser = Parser(src)
print(f"Current token: {parser.cur().kind} '{parser.cur().text}'")
print(f"Looks like binding start: {parser._looks_like_binding_start()}")

if parser._looks_like_binding_start():
    try:
        result = parser.parse_stmt()
        print(f"✅ Parsed successfully: {result}")
    except Exception as e:
        print(f"❌ Parse failed: {e}")
else:
    print("❌ Not recognized as binding start")
