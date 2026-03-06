# Launching Kernels

Launch syntax:

```astra
gpu.launch(kernel_fn, grid_size, block_size, arg0, arg1, ...)
```

Semantics:
- `kernel_fn` must be a `gpu fn`
- `grid_size` and `block_size` are required integers
- remaining launch arguments map positionally to kernel parameters
- compiler validates launch argument compatibility (`GpuBuffer<T>` to `GpuSlice<T>`/`GpuMutSlice<T>` as needed)

Thread indexing in kernel code:
- `gpu.global_id()`
- `gpu.thread_id()`
- `gpu.block_id()`
- `gpu.block_dim()`
- `gpu.grid_dim()`
