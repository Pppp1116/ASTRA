import shutil
import subprocess
from pathlib import Path

import pytest

from astra.build import build


def test_build_py(tmp_path: Path):
    src = tmp_path / 'a.astra'
    src.write_text('fn main() -> Int { print("ok"); return 0; }')
    out = tmp_path / 'a.py'
    st = build(str(src), str(out), 'py')
    assert st in {'built','cached'}
    assert out.exists()


def test_build_emit_ir(tmp_path: Path):
    src = tmp_path / "a.astra"
    src.write_text("fn main() -> Int { let x = 1 + 2; return x; }")
    out = tmp_path / "a.py"
    ir = tmp_path / "a.ir.json"
    st = build(str(src), str(out), "py", emit_ir=str(ir))
    assert st in {"built", "cached"}
    assert ir.exists()
    assert '"name": "main"' in ir.read_text()


@pytest.mark.skipif(
    shutil.which("nasm") is None or shutil.which("ld") is None,
    reason="native target requires nasm and ld",
)
def test_build_native_executable(tmp_path: Path):
    src = tmp_path / "main.astra"
    out = tmp_path / "main.exe"
    src.write_text("fn main() -> Int { return 7; }")
    st = build(str(src), str(out), "native")
    assert st in {"built", "cached"}
    assert out.exists()
    assert out.stat().st_mode & 0o111
    rc = subprocess.call([str(out)])
    assert rc == 7
