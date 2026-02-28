from pathlib import Path

from astra.ast import EnumDecl, FnDecl, StructDecl, TypeAliasDecl
from astra.parser import parse
from astra.semantic import analyze


def _load(path: str) -> str:
    return Path(path).read_text()


def test_all_stdlib_modules_parse_and_analyze_in_freestanding_mode():
    modules = [
        "stdlib/core.astra",
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
        analyze(prog, filename=module, freestanding=True)


def test_extended_stdlib_exports_exist():
    checks = {
        "stdlib/core.astra": {"Option", "Result", "Vec", "Bytes"},
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
