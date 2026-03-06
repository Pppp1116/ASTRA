# GPU Feature Matrix

| Feature | Description | Status | Notes |
| --- | --- | --- | --- |
| Kernel functions | `gpu fn` parsing/AST/semantic classification | ✔ Implemented | Kernel declaration and validation integrated in compiler pipeline. |
| Thread indexing | `gpu.global_id/thread_id/block_id/block_dim/grid_dim` | ✔ Implemented | Available only inside kernels. |
| Device buffers | `GpuBuffer<T>`, `GpuSlice<T>`, `GpuMutSlice<T>` types | ✔ Implemented | Semantic typing + runtime memory wrappers. |
| Host-device copies | `gpu.copy`, `gpu.read` | ✔ Implemented | Explicit transfer model with type checks. |
| Kernel launch | `gpu.launch(kernel, grid, block, ...args)` | ✔ Implemented | Launch signature and kernel arg compatibility validated semantically. |
| Shared memory | On-chip shared memory declarations/access | ✖ Not implemented | Planned after CUDA execution bridge completion. |
| Atomic operations | Device atomic intrinsics and memory ordering | ✖ Not implemented | Planned in roadmap. |
| Barriers | `gpu.barrier()` synchronization primitive | ⚠ Partial | Semantically available; runtime stub currently no-op. |
| Multi GPU | Device selection and multi-device dispatch | ✖ Not implemented | Runtime currently single-backend execution path. |
| Async streams | Stream/event async launch model | ✖ Not implemented | Planned. |
| SPIR-V backend | Vulkan/SPIR-V kernel backend | ⏳ Planned | Roadmap target. |
| CUDA backend | NVIDIA backend pipeline | ⚠ Partial | Direct runtime launch bridge implemented for supported kernels via Numba CUDA JIT, with automatic CPU stub fallback for unsupported kernels/environments. |
| Metal backend | Apple Metal backend | ⏳ Planned | Roadmap target. |
| Kernel debugging | Source-level kernel debug tooling | ✖ Not implemented | Planned. |
| Kernel profiling | Runtime profiling/telemetry for launches | ✖ Not implemented | Planned. |
