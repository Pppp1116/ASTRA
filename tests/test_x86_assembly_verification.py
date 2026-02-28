import pytest

from astra.codegen import to_x86_64
from astra.parser import parse
from astra.asm_assert import assert_valid_x86_64_assembly


X86_PROGRAMS = [
    "fn main() -> Int { return 0; }",
    "fn inc(x: Int) -> Int { return x + 1; } fn main() -> Int { return inc(9); }",
    "fn main() -> Int { let mut x = 0; while x < 4 { x += 1; } return x; }",
    "fn main() -> Int { let x = 7; if x > 3 { return 1; } return 0; }",
]


@pytest.mark.parametrize("src", X86_PROGRAMS)
def test_x86_output_is_always_validated(src: str):
    asm = to_x86_64(parse(src))
    assert_valid_x86_64_assembly(asm)


def test_x86_freestanding_output_is_validated():
    src = "fn _start() -> Int { return 0; }"
    asm = to_x86_64(parse(src), freestanding=True)
    assert_valid_x86_64_assembly(asm, freestanding=True)
    assert "global _start" in asm
    assert "_start:" in asm
