# std.serde

Source: `stdlib/serde.astra`

Status: `experimental` (hosted runtime wrapper)

Functions:

- `to_json(v Any) -> String`
- `from_json(v String) -> Any`

Backend support:

- Python backend: supported
- Native backend (LLVM + runtime): supported
- Freestanding mode: not supported

Current scope:

- JSON encode/decode for dynamic `Any` values
- Useful for debugging and loose interoperability

Current limits:

- No typed decode API
- No derive/auto-impl support
- No streaming parser/encoder
- No structured error location information

Near-term direction:

- Add typed decode entrypoints and derive-based serialization hooks
- Improve diagnostics for schema/type mismatches during decode
