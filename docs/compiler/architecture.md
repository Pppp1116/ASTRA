# Compiler Architecture

Arixa is organized as a classic compiler pipeline plus toolchain commands around that pipeline.

## High-Level Layout

- Frontend: `astra/lexer.py`, `astra/parser.py`, `astra/ast.py`
- Semantic/type layer: `astra/semantic.py`, `astra/layout.py`, `astra/int_types.py`
- Transform/lowering: `astra/for_lowering.py`, `astra/comptime.py`, `astra/optimizer.py`
- Backends: `astra/codegen.py` (Python), `astra/llvm_codegen.py` (LLVM/native)
- Build/check orchestration: `astra/build.py`, `astra/check.py`, `astra/cli.py`
- Tooling: formatter, linter, docs generator, LSP, debugger, profiler

## Pipeline Diagram

```text
source (.arixa)
    |
    v
lex -> parse -> AST
    |
    v
comptime execution
    |
    v
semantic analysis + type checks
    |
    v
lowering + optimization
    |
    +--> Python backend  -> .py artifact
    |
    +--> LLVM backend    -> .ll artifact
                     |
                     +--> native link (clang) -> executable/shared lib
```

## Modules

- AST definitions: `astra/ast.py`
- Lexer: `astra/lexer.py`
- Parser: `astra/parser.py`
- Semantic/type checks: `astra/semantic.py`
- Compile-time executor: `astra/comptime.py`
- Lowering/optimization: `astra/for_lowering.py`, `astra/optimizer.py`
- Backends: `astra/codegen.py`, `astra/llvm_codegen.py`
- GPU subsystem: `astra/gpu/kernel_ir.py`, `astra/gpu/kernel_lowering.py`, `astra/gpu/backend_cuda.py`, `astra/gpu/backend_stub.py`, `astra/gpu/runtime.py`
- Build/check orchestration: `astra/build.py`, `astra/check.py`

## Stage Flow

```text
lex -> parse -> comptime -> semantic -> lowering -> optimization -> codegen
```

## Responsibilities

- Frontend ensures syntactic correctness and AST construction.
- Semantic phase enforces type, safety, ownership/borrow, and builtin rules.
- Lowering/optimization normalize AST and simplify code paths.
- Backend emits executable representations with hosted/freestanding constraints.
- GPU path adds kernel-specific semantic validation, kernel IR lowering, and runtime backend dispatch.

## Hosted vs Freestanding

- Hosted mode allows runtime-backed builtins (`read_file`, process, sockets, etc.).
- Freestanding mode (`--freestanding`) forbids hosted runtime dependencies and enforces runtime-free output constraints for LLVM/native paths.

See `docs/compiler/overview.md` for detailed stage behavior.
