from pathlib import Path

import pytest

from astra.ast import ImportDecl
from astra.module_resolver import ModuleResolutionError, resolve_import_path


def test_module_import_resolves_from_package_root(tmp_path: Path):
    root = tmp_path / "app"
    root.mkdir(parents=True)
    (root / "Astra.toml").write_text('name = "app"\n')
    (root / "lib").mkdir(parents=True)
    (root / "src").mkdir(parents=True)
    (root / "lib" / "math.astra").write_text("fn id(x Int) -> Int { return x; }\n")
    importer = root / "src" / "main.astra"
    importer.write_text("fn main() -> Int { return 0; }\n")
    resolved = resolve_import_path(ImportDecl(path=["lib", "math"]), str(importer))
    assert resolved == (root / "lib" / "math.astra").resolve()


def test_string_import_resolves_relative_to_importer(tmp_path: Path):
    root = tmp_path / "app"
    root.mkdir(parents=True)
    (root / "Astra.toml").write_text('name = "app"\n')
    (root / "src").mkdir(parents=True)
    (root / "helper.astra").write_text("fn a() -> Int { return 1; }\n")
    (root / "src" / "helper.astra").write_text("fn b() -> Int { return 2; }\n")
    importer = root / "src" / "main.astra"
    importer.write_text("fn main() -> Int { return 0; }\n")
    resolved = resolve_import_path(ImportDecl(path=[], source="helper"), str(importer))
    assert resolved == (root / "src" / "helper.astra").resolve()


def test_std_import_uses_configured_stdlib(monkeypatch, tmp_path: Path):
    stdlib = tmp_path / "custom_stdlib"
    (stdlib / "io").mkdir(parents=True)
    (stdlib / "io" / "fs.astra").write_text("fn noop() -> Int { return 0; }\n")
    monkeypatch.setenv("ASTRA_STDLIB_PATH", str(stdlib))
    resolved = resolve_import_path(ImportDecl(path=["std", "io", "fs"]), "<input>")
    assert resolved == (stdlib / "io" / "fs.astra").resolve()


def test_missing_import_is_reported(tmp_path: Path):
    importer = tmp_path / "main.astra"
    importer.write_text("fn main() -> Int { return 0; }\n")
    with pytest.raises(ModuleResolutionError, match="cannot resolve import missing.mod"):
        resolve_import_path(ImportDecl(path=["missing", "mod"]), str(importer))
