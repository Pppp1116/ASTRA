#!/usr/bin/env python3

import sys
from pathlib import Path

# Add ASTRA to path dynamically
astra_root = Path(__file__).resolve().parent
sys.path.insert(0, str(astra_root))

from astra.parser import Parser

# Test parse_expr specifically
src = "0..2"
print(f"Testing parse_expr on: '{src}'")

parser = Parser(src)
try:
    result = parser.parse_expr()
    print(f"✅ Parsed successfully: {result}")
    print(f"Next token: {parser.cur().kind}")
except Exception as e:
    print(f"❌ Parse failed: {e}")
