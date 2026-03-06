# Semantic Analysis

Implementation: `astra/semantic.py`

Main entrypoint:

- `analyze(prog, filename=..., freestanding=..., require_entrypoint=...)`

Responsibilities:

- name resolution and symbol table checks
- type inference/validation
- borrow/move safety checks
- builtin validation and freestanding restrictions
- function/return/entrypoint validation
- pattern exhaustiveness/redundancy checks
- trait/generic constraint validation

Error type:

- `SemanticError`

Current expansion focus:

- trait coherence and richer generic-resolution diagnostics
- deeper structural pattern analysis for exhaustiveness
- expanded lifetime/region reasoning diagnostics
