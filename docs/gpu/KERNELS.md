# Kernel Functions

Declare kernels with `gpu fn`:

```astra
gpu fn vec_add(a GpuSlice<Float>, b GpuSlice<Float>, out GpuMutSlice<Float>) Void{
  i = gpu.global_id();
  if i < out.len() {
    out[i] = a[i] + b[i];
  }
}
```

Kernel rules:
- kernels must return `Void`
- kernels cannot be `async` or `unsafe`
- kernel parameters must be GPU-safe (scalars, GPU-safe structs, or GPU views)
- kernels cannot be called directly from host code; use `gpu.launch`

Inside kernels, supported operations include:
- integer/float arithmetic
- comparisons and control flow (`if`, `while`, `for`)
- indexing into GPU memory views
- calls to kernel-safe builtins and `gpu.*` thread-index builtins
