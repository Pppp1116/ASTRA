# GPU Builtins

Kernel-only builtins under `gpu` namespace:
- `gpu.global_id()` -> `Int`
- `gpu.thread_id()` -> `Int`
- `gpu.block_id()` -> `Int`
- `gpu.block_dim()` -> `Int`
- `gpu.grid_dim()` -> `Int`
- `gpu.barrier()` -> `Void` (currently a no-op in stub backend)

Host-only GPU runtime APIs:
- `gpu.available()` -> `Bool`
- `gpu.device_count()` -> `Int`
- `gpu.device_name(index)` -> `String`
- `gpu.alloc(size)` -> `GpuBuffer<Any>`
- `gpu.copy(host_values)` -> `GpuBuffer<T>`
- `gpu.read(device_memory)` -> `[T]`
- `gpu.launch(kernel, grid_size, block_size, ...args)` -> `Void`
