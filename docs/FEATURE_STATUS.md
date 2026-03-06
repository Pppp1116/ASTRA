# Feature Status Matrix

This document tracks ASTRA implementation status against a minimally complete systems-language baseline.

Status labels:

- `stable`: implemented and broadly verified in tests
- `partial`: implemented but limited in depth or backend parity
- `experimental`: available but semantics/tooling are still evolving
- `planned`: not yet implemented

## Language and Compiler

| Area | Status | Current State | Next Concrete Step | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| Syntax and parsing | stable | Core syntax, async/await keywords, unsafe, generics, match are parsed. | Keep grammar docs synced with parser changes. | Parser + formatter + syntax docs updated in same PR. |
| Semantic typing | partial | Generics with `where`-bounded resolution are implemented in semantic analysis/type checking. | Add fuller trait/coherence diagnostics and richer generic resolution failure reporting. | Constrained-generic and coherence diagnostics tests pass with actionable overlap/bound errors. |
| Generics | partial | Parametric overload specialization exists with `where` trait bounds for overload resolution and return-type substitution from inferred type vars. | Expand to full coherence rules and richer trait-driven resolution diagnostics (candidate/bound mismatch detail). | Coherence, method resolution, and generic diagnostics tests pass. |
| Pattern matching | partial | Wildcards, Bool, enum variants, guards, and destructuring are implemented. | Expand deeper exhaustiveness coverage and structural analysis for nested enum/struct/tuple patterns and arm redundancy. | Exhaustiveness/redundancy suite for deeper nested structural patterns passes. |
| Ownership/borrow safety | partial | Move-by-default semantics are enforced, with copy behavior for numerics/`Bool`/`&T`, plus a basic lifetime-like return rule. | Expand region/lifetime reasoning and diagnostics with clearer origin/outlives notes. | Borrow/lifetime regression suite covers escapes, aliasing edges, and improved diagnostics. |
| Error handling ergonomics | partial | Union-based error/nullable model exists (`A | B`, `T?`, `none`), with `!` propagation and `??` coalescing in semantic analysis plus Python and LLVM/native lowering. | Add richer union ergonomics (`map`, destructuring helpers) and diagnostics polish. | `!`/`??` behavior is parity-tested across Python and native backends. |
| Compile-time evaluation | experimental | `comptime` infra exists and is tested for basic cases. | Expand deterministic CTFE boundaries + diagnostics. | CTFE failure diagnostics include stable spans and notes. |
| GPU programming subsystem | partial | First-class `gpu fn` kernels, GPU memory types, host/device transfer APIs, kernel launch validation, kernel IR lowering, and runtime stub execution path are integrated. | Complete direct CUDA execution bridge and broaden kernel language surface (shared memory/atomics). | `tests/gpu/*` parser/semantic/launch/integration suites pass; docs/gpu matrix matches implementation. |

## Runtime and Backends

| Area | Status | Current State | Next Concrete Step | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| Python backend | partial | Broad hosted feature support; fast dev loop backend. | Keep behavior aligned with documented semantics. | Golden semantic behavior stays consistent across releases. |
| LLVM IR backend | partial | Extensive IR lowering and validation pipeline, with ongoing py/native parity hardening for hosted runtime APIs (`std.net`, `std.thread`, `std.crypto`, `std.serde`, `std.process`). | Continue parity hardening for hosted runtime APIs and close remaining backend behavior gaps. | Backend parity tests cover builtins used by hosted stdlib wrappers with documented known gaps. |
| Native runtime helpers | partial | Runtime includes memory/file/process/time helpers and TCP shims for POSIX and Windows paths, but Windows parity is not complete. | Harden Windows-native parity for runtime helpers and networking with dedicated CI/runtime coverage. | Native helper/network tests pass on Linux/macOS, with explicit Windows parity closure criteria tracked in CI. |
| Async/concurrency runtime | partial | Async support is currently thread-based (`spawn`/`join`) and does not define a full scheduler contract. | Extend async coverage beyond thread spawn/join while preserving a lightweight (no full scheduler) contract. | Async/threading docs and stress tests cover the expanded no-scheduler model. |
| GPU runtime/backends | partial | GPU runtime API is available in Python backend, with CUDA capability probing, runtime JIT launch bridge for supported kernels, and deterministic CPU stub fallback. | Expand CUDA kernel-shape coverage and add backend parity testing lanes. | CUDA-enabled environments execute supported kernels through native backend; unsupported forms fall back deterministically. |
| Cross-platform target matrix | partial | LLVM target triple support exists and CI runs on Ubuntu/macOS/Windows for core workflows. | Expand tier target policy into native-runtime parity lanes per OS. | CI executes core suite on declared tier-1 targets. |

## Tooling and Ecosystem

| Area | Status | Current State | Next Concrete Step | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| CLI/build/check/test/fmt | stable | Core commands exist and are exercised by tests. | Improve UX consistency and error messages. | Tooling snapshots stay stable across fixtures. |
| LSP/IDE | partial | Hover/definition/rename/format/code actions exist. | Add deeper quick-fix coverage and diagnostic actions. | LSP integration tests cover multi-file quick fixes. |
| Package manager (`astpm`) | partial | Add/remove/list/search/update/publish/lock/verify available with semver-aware transitive lock solving, source/checksum metadata, and registry cache fallback for offline use. | Improve conflict diagnostics for complex transitive constraints and workspace-scale dependency ergonomics. | Lockfile includes deterministic transitive graph, and `astpm verify` validates cached package integrity. |
| Incremental builds/cache | partial | Hash-based build caching exists; native sanitizer toggles are integrated into build cache keys and CLI flags. | Add finer-grained invalidation and module-level cache keys. | Incremental rebuild tests verify minimal recompilation. |
| Self-hosting | planned | Placeholder command/file-copy behavior only. | Replace with staged real self-host toolchain path. | `astra selfhost` builds compiler artifact end-to-end. |

## Standard Library

| Area | Status | Current State | Next Concrete Step | Acceptance Criteria |
| --- | --- | --- | --- | --- |
| `std.core` / checked numerics | stable | Union/nullable model (`A | B`, `T?`, `none`) and checked int helpers are in place. | Continue ergonomic helpers on top of union-based errors/nullability. | Core error-handling examples compile and pass. |
| Collections | experimental | Dynamic list/map wrappers over runtime `Any`. | Add typed containers + iterator abstractions with generic constraints. | Typed container API has unit, semantic, and inference/diagnostic tests. |
| Concurrency helpers | partial | `std.thread` spawn/join and `std.atomic` are runtime-backed (OS threads + seq-cst atomics); `std.sync`/`std.channel` are still cooperative wrappers. | Replace cooperative sync/channel wrappers with runtime-backed primitives. | Thread/atomic behavior and sync/channel semantics are parity-tested with stress coverage. |
| Networking | experimental | TCP helper wrappers implemented for hosted backends with parity coverage for connect/send/recv/close success + failure paths (Windows CI parity still limited). | Add richer socket/error model, non-blocking options, and Windows parity hardening. | TCP tests include connect/send/recv/close success + failures across POSIX + Windows lanes. |
| Serde | experimental | JSON serialize/deserialize wrappers for dynamic values. | Add typed decode and derive hooks with richer type-mismatch diagnostics. | Typed serde roundtrip tests and derive diagnostics pass. |
| Crypto | experimental | SHA-256 and HMAC-SHA256 wrappers. | Add RNG/KDF/AEAD APIs with safer typed contracts and nonce/key misuse diagnostics. | Crypto API tests include misuse-resistant RNG/KDF/AEAD paths. |
| Math | stable | Pure integer helper functions. | Expand float/trig utilities as separate stable module. | Math docs + tests for new APIs pass in hosted/freestanding modes. |

## Execution Order

1. Backend/runtime parity and status documentation truth.
2. Trait coherence, richer generic-resolution diagnostics, and deep pattern exhaustiveness.
3. Lifetime/region reasoning + diagnostics and error ergonomics (`?`).
4. Async beyond thread spawn/join (without a full scheduler contract) and stdlib deepening.
5. Windows-native runtime/networking parity, cross-platform CI tiers, and self-hosting milestone.
