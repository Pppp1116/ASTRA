# Installation (Linux)

```bash
git clone <repo>
cd programming-language-
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Requirements:
- `clang` for `--target native`
- `llvmlite` (installed via project dependency) for LLVM IR generation

Verify:
```bash
astra check examples/hello.astra
astra build examples/hello.astra -o build/hello.py
python build/hello.py
```
