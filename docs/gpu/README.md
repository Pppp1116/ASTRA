# ASTRA GPU Programming

ASTRA includes a first-class GPU subsystem for explicit compute programming.

Core capabilities:
- `gpu fn` kernel declarations
- explicit device buffer management (`GpuBuffer<T>`, `GpuSlice<T>`, `GpuMutSlice<T>`)
- host/device transfer APIs (`gpu.copy`, `gpu.read`)
- explicit launch control (`gpu.launch(kernel, grid_size, block_size, ...)`)
- kernel thread-index builtins (`gpu.global_id`, `gpu.thread_id`, `gpu.block_id`, `gpu.block_dim`, `gpu.grid_dim`)

This subsystem is integrated into parser, AST, semantic analysis, code generation, and runtime.

See:
- `OVERVIEW.md`
- `KERNELS.md`
- `MEMORY_MODEL.md`
- `LAUNCHING.md`
- `BACKEND.md`
- `SAFETY_RULES.md`
- `FEATURE_MATRIX.md`
