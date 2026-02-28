from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path


def assert_valid_x86_64_assembly(asm: str, *, freestanding: bool = False, workdir: Path | None = None) -> None:
    lines = [line.rstrip() for line in asm.splitlines() if line.strip()]
    assert lines, "assembly output is empty"
    assert any(line == "section .text" for line in lines), "missing text section"
    assert "unsupported" not in asm
    assert "TODO" not in asm

    if not freestanding:
        assert any(line == "global _start" for line in lines), "missing runtime entry global"
        assert any(line == "_start:" for line in lines), "missing runtime entry label"

    labels = [line[:-1] for line in lines if line.endswith(":")]
    assert len(labels) == len(set(labels)), "duplicate assembly label detected"

    instr_re = re.compile(r"^[a-z]+(\s|$)")
    for line in lines:
        if line.endswith(":") or line.startswith("section ") or line.startswith("global "):
            continue
        stripped = line.strip()
        assert instr_re.match(stripped), f"invalid instruction line: {line!r}"

    nasm = shutil.which("nasm")
    if nasm is None:
        return

    out_dir = workdir or Path.cwd()
    src = out_dir / "_asm_check.s"
    obj = out_dir / "_asm_check.o"
    src.write_text(asm)
    cp = subprocess.run([nasm, "-felf64", str(src), "-o", str(obj)], capture_output=True, text=True)
    assert cp.returncode == 0, f"nasm failed: {cp.stderr or cp.stdout}"
