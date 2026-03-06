# GPU Examples

Repository examples are under `examples/gpu/`:
- `vector_add.astra`
- `saxpy.astra`
- `vector_scale.astra`
- `elementwise_mul.astra`

Each example demonstrates:
- host array setup
- `gpu.copy` transfer to device buffers
- `gpu.alloc` output buffer allocation
- `gpu.launch` kernel submission
- `gpu.read` result transfer back to host

Quick run (Python backend):

```bash
astra build examples/gpu/vector_add.astra -o .astra-build/vector_add.py --target py
python .astra-build/vector_add.py
```
