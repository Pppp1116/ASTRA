## Dev Baseline – March 1, 2026

This document captures the initial baseline for the `mega-improve` branch before making language and tooling changes.

### Environment

- **OS**: Arch Linux x86_64 (kernel 6.18.13-zen1-1-zen)
- **Python**: 3.14.3 (virtualenv `.venv`)
- **Repo**: `Pppp1116/ASTRA` (`mega-improve` branch, based on `main`)

### Commands and outcomes

| Command | Outcome | Notes |
| --- | --- | --- |
| `python -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"` | ✅ pass | Editable install of `astra-lang 0.2.0` with dev dependencies completed successfully. |
| `.venv/bin/astra test` | ✅ pass | All Astra CLI tests passed: `355 passed, 2 deselected in 10.70s`. |
| `.venv/bin/pytest` | ✅ pass | Full Python test suite passed: `357 passed in 18.54s` (per `pyproject.toml` config). |
| `.venv/bin/astra fmt --check` | ⚠️ fail | Exited with code 2 and usage error: `astra fmt: error: the following arguments are required: files`. Current CLI requires explicit file arguments; `astra fmt --check` with no files is not accepted yet. |
| `.venv/bin/astlint .` | ⚠️ fail | Exited with `IsADirectoryError` when reading `"."`. Current `astlint` expects a file path via `--file`/positional, not a directory. |
| `.venv/bin/astra build examples/hello.astra -o build/hello.py --target py && .venv/bin/python build/hello.py` | ✅ pass | Build status `built`; running `hello.py` printed `hello from astra` and exited successfully. |
| `.venv/bin/astra build examples/hello.astra -o build/hello.ll --target llvm` | ✅ pass | Build status `built`; LLVM IR file `build/hello.ll` was created. (Execution of IR is not part of the baseline.) |
| `.venv/bin/astra build examples/hello.astra -o build/hello.native --target native && chmod +x build/hello.native && ./build/hello.native` | ✅ pass | Native build status `built`; running the executable printed `hello from astra` and exited with code 0. |

### Immediate follow-ups implied by baseline

- **Formatter UX**: `astra fmt --check` without explicit files currently errors; target is to support the UX requested in the project README and in this baseline checklist (likely defaulting to the workspace or to `.astra` files under `.`).
- **Linter UX**: `astlint` currently does not accept a directory argument; improving this to lint a tree (or wiring a helper that discovers Astra files) will be part of dev experience work.

