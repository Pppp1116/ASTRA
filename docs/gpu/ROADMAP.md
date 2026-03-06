# GPU Roadmap

Near-term:
- broaden direct CUDA execution coverage beyond current runtime-lowered kernel subset
- shared memory surface in kernel language
- atomic operations for key scalar types
- asynchronous stream launch and synchronization primitives

Mid-term:
- multi-GPU device selection and scheduling APIs
- SPIR-V backend for broader vendor coverage
- Metal backend for Apple platforms

Long-term:
- kernel debugging support (source/IR mapping, thread-state inspection)
- kernel profiling hooks (timing, occupancy, launch diagnostics)
- richer auto-tuning and launch configuration tooling
