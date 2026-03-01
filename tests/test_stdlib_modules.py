from pathlib import Path

import pytest

from astra.ast import EnumDecl, FnDecl, StructDecl, TypeAliasDecl
from astra.parser import parse
from astra.semantic import SemanticError, analyze


def _load(path: str) -> str:
    return Path(path).read_text()


def test_core_stdlib_module_analyzes_in_freestanding_mode():
    module = "stdlib/core.astra"
    src = _load(module)
    prog = parse(src, filename=module)
    analyze(prog, filename=module, freestanding=True)


def test_hosted_stdlib_modules_are_rejected_in_freestanding_mode():
    modules = [
        "stdlib/collections.astra",
        "stdlib/crypto.astra",
        "stdlib/io.astra",
        "stdlib/net.astra",
        "stdlib/process.astra",
        "stdlib/serde.astra",
        "stdlib/time.astra",
    ]
    for module in modules:
        src = _load(module)
        prog = parse(src, filename=module)
        with pytest.raises(SemanticError, match="freestanding mode forbids builtin"):
            analyze(prog, filename=module, freestanding=True)


def test_extended_stdlib_exports_exist():
    checks = {
        "stdlib/core.astra": {"Option", "Result", "Bytes", "add_checked", "sub_checked", "mul_checked", "div_checked"},
        "stdlib/time.astra": {"now_ms", "sleep_seconds"},
        "stdlib/io.astra": {"read_or"},
        "stdlib/collections.astra": {"map_get_or"},
        "stdlib/net.astra": {"tcp_send_line"},
        "stdlib/process.astra": {"env_or", "run_ok"},
        "stdlib/crypto.astra": {"digest_pair"},
    }
    for path, expected in checks.items():
        prog = parse(_load(path), filename=path)
        exported = {item.name for item in prog.items if isinstance(item, FnDecl)}
        exported |= {item.name for item in prog.items if isinstance(item, EnumDecl)}
        exported |= {item.name for item in prog.items if isinstance(item, StructDecl)}
        exported |= {item.name for item in prog.items if isinstance(item, TypeAliasDecl)}
        assert expected.issubset(exported)
