# Backend Architecture

Compiler subsystem files:
- `astra/gpu/kernel_ir.py`: kernel metadata IR datamodel
- `astra/gpu/kernel_lowering.py`: kernel extraction/lowering from AST
- `astra/gpu/backend_cuda.py`: CUDA backend probe + IR compilation stubs
- `astra/gpu/backend_stub.py`: deterministic CPU fallback execution backend
- `astra/gpu/runtime.py`: host runtime API, launch context, backend dispatch

Current backend behavior:
- compile pipeline lowers `gpu fn` declarations into kernel IR metadata
- generated Python backend registers kernel IR and kernel signatures with runtime
- runtime attempts CUDA backend dispatch when available
- supported kernels are translated into Python CUDA-kernel source and JIT-compiled through Numba CUDA at runtime
- runtime falls back to CPU stub backend for execution

CUDA status:
- device probing, kernel metadata staging, and direct launch bridge are implemented
- current CUDA execution coverage is limited to kernel forms supported by the runtime CUDA lowerer; unsupported forms fall back to CPU stub execution
