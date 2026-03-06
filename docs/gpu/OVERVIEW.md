# Overview

ASTRA GPU support uses explicit host/device separation.

Host-side responsibilities:
- allocate/copy/read device memory
- configure launch shape
- submit kernels through `gpu.launch`

Kernel-side responsibilities:
- read thread indices from `gpu.*` builtins
- operate on GPU-safe scalar/struct values
- index device views (`GpuSlice<T>`, `GpuMutSlice<T>`)

Current execution model:
- compiler lowers kernels into GPU kernel IR metadata
- runtime probes CUDA backend availability
- runtime executes through CPU stub backend for deterministic MVP behavior
- CUDA backend metadata pipeline is present and designed for incremental NVRTC execution enablement
