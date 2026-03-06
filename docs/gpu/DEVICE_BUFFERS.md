# Device Buffers

Allocation and transfer patterns:

```astra
x = [1.0, 2.0, 3.0, 4.0];
dx = gpu.copy(x);
dout: GpuBuffer<Float> = gpu.alloc(len(x));
result = gpu.read(dout);
```

Guidelines:
- annotate `gpu.alloc` targets when type inference would otherwise produce `GpuBuffer<Any>`
- pass `GpuBuffer<T>` directly to `gpu.launch`; compiler validates conversion to kernel parameter view types
- readback is explicit (`gpu.read`) and returns host array values
