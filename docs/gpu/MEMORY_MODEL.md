# Memory Model

ASTRA GPU memory is explicit and typed:
- `GpuBuffer<T>`: owning device allocation handle
- `GpuSlice<T>`: immutable device view
- `GpuMutSlice<T>`: mutable device view

Host and device memory are distinct:
- host arrays/slices are regular ASTRA values (`[T]`, `Vec<T>`)
- device data lives in GPU buffers/views

Transfer APIs:
- `gpu.copy(host_values)` -> `GpuBuffer<T>`
- `gpu.read(device_memory)` -> `[T]`

Kernel parameters should use slice/view types instead of host containers.
