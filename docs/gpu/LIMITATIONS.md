# Current Limitations

- Single-process runtime model with CPU stub fallback path.
- CUDA execution currently supports the subset of kernel forms representable by the runtime CUDA lowerer; unsupported kernels transparently fall back to CPU stub execution.
- Shared memory is not exposed yet.
- Atomic GPU operations are not implemented yet.
- Async streams and events are not implemented.
- Multi-GPU scheduling is not implemented.
- Kernel debugging/profiling tooling is not integrated yet.
- Kernel parameter generics and where-clause constraints are not supported.
- Kernel function-pointer calls are not supported.
