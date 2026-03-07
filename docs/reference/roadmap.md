# Roadmap

This roadmap reflects the current repository implementation and near-term direction.

## Current Baseline

- Working lexer/parser/semantic pipeline
- Python and LLVM backends
- Native linking via `clang`
- Hosted/freestanding compilation modes
- CLI + formatter + linter + docgen + LSP tooling

## In Progress

- Continued semantic diagnostics quality improvements
- Expanded language/server test matrix
- Better documentation and API annotation coverage
- Trait coherence hardening and generic resolution diagnostics
- Deeper pattern exhaustiveness + structural analysis
- Expanded lifetime/region reasoning diagnostics

## Next Priorities

- Broader stdlib ergonomics and examples
- Incremental compiler performance improvements
- Stronger packaging/dependency workflow (`astpm`)
- Additional backend stabilization and freestanding validation
- Async beyond `spawn/join` without introducing a full scheduler contract
- Windows-native parity for runtime helpers and networking coverage
- Typed collections plus `serde` derive and typed decode support
- `crypto` API expansion: RNG/KDF/AEAD with misuse-resistant contracts

## Longer Term

- Improve self-hosting story (current `selfhost` command is intentionally unavailable)
- Deeper optimization/lowering passes
- Expanded IDE/editor integrations
