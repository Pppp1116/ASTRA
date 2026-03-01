# Astra Runtime

- Memory model: deterministic ownership at language level plus reference-counted runtime objects in generated Python.
- Concurrency: native threads via host runtime and cooperative async through awaitable host calls.
- Error model: Result-like checked return values and panic on unrecoverable runtime faults.
- Native backend runtime entrypoints are implemented in `llvm_runtime.c` and linked by `clang` for `--target native`.
