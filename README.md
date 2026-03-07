# Arixa

Arixa is a compact programming language ecosystem with a full compiler pipeline, CLI tooling, language server support, and a batteries-included standard library.

## Main Features

- Deterministic builds with content-based caching.
- Multiple build targets: Python, LLVM IR, and native executables via `clang`.
- Static checking pipeline with parse, compile-time, and semantic diagnostics.
- Built-in tooling: formatter (`arfmt`), linter (`arlint`), doc generator (`ardoc`), package helper (`arpm`), LSP server (`arlsp`), debugger (`ardbg`), and profiler (`arprof`).
- Hosted and freestanding compilation modes.
- First-class GPU compute subsystem with `gpu fn`, explicit device buffers, and `gpu.launch`.
- Standard library modules for core types, collections, I/O, networking, process control, serialization, crypto, and time.
- Runtime-backed builtin APIs that mirror stdlib entry points used by the current semantic/codegen pipeline.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Requirements:

- Python 3.11+
- `clang` for `--target native`
- `llvmlite` (installed via project dependencies) for LLVM backend

## Quick Example

`examples/hello_world.arixa`:

```arixa
fn main() Int{
    print("hello, arixa");
    return 0;
}
```

Build and run:

```bash
arixa check examples/hello_world.arixa
arixa build examples/hello_world.arixa -o build/hello.py
python build/hello.py
```

## Documentation

- **Getting Started**: `docs/development/getting-started.md`
- **Language Specification**: `docs/language/specification.md`
- **Language Reference**: `docs/language/`
- **Standard Library**: `docs/stdlib/`
- **Compiler Internals**: `docs/compiler/`
- **GPU Development**: `docs/gpu/`
- **Tooling & VS Code**: `docs/tools/`
- **Development Guide**: `docs/development/`
- **Reference Materials**: `docs/reference/`

Current compiler behavior note:

- import paths are resolved and validated by semantic analysis.
- most callable stdlib-facing functions are currently surfaced through builtin names.
