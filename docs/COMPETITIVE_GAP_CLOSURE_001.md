# Syntavra 0.0.1 — Competitive Gap Closure Plan and Completion Record

Status: **technical plan implemented; external evidence gates remain closed**.

## Objective

Close the concrete technical gaps identified against Token Savior, jCodeMunch, RTK, 9Router, Claude-specific cache tools, Caveman, and Cavemem without turning unexecuted external work into claims. Version remains `0.0.1 / pre-release`.

## P0 — Security and deterministic operation

1. Remove CodeQL alert #6 (`py/redos`) from agent-config path discovery.
2. Replace hardcoded CodeQL alert enumeration with paginated state-aware export.
3. Add adversarial long-input regression coverage.
4. Keep generated manifests and branch preparation deterministic.

**Implemented:** linear token scanning replaced the vulnerable nested-quantifier regex; security triage enumerates open/fixed/dismissed alerts through the GitHub API.

## P1 — RTK and Token Savior parity

1. Increase command-specific compactors beyond 100.
2. Increase fail-closed pre-execution rewrites beyond 100.
3. Support common safe shell wrappers and environment assignments.
4. Keep ambiguous shell composition and wrapper options fail closed.
5. Preserve exact stdout/stderr artifacts and recovery handles.

**Implemented:** 131 compactors and 118 rewrite rules, wrapper-aware parsing, transcript coverage measurement, and exact recovery.

## P2 — jCodeMunch code-intelligence depth

1. Add a broad language registry and optional real parser backend.
2. Attach backend and confidence to every indexed symbol.
3. Add implementation discovery and blast-radius analysis.
4. Cache per-file parse results for deterministic incremental reindex.
5. Preserve explicit fallback boundaries instead of calling lexical output AST-exact.

**Implemented:** 30-language registry, optional tree-sitter backend, confidence receipts, implementation/blast-radius queries, and incremental cache reuse.

## P3 — 9Router provider-account operation

1. Add multi-account state without persisting raw credentials.
2. Add subscription and priority-aware selection.
3. Add quota reset, rate-limit, latency, model allowlist, health and circuit-breaker state.
4. Route to healthy backup accounts after repeated failure.
5. Expose the pool through CLI and MCP audit surfaces.

**Implemented:** credential-reference-only account pool, failover receipts, CLI actions, and MCP controls. Live OAuth/account certification remains external.

## P4 — Claude cache/session depth

1. Cover the full host hook lifecycle.
2. Surface cache health and recommended action at session/prompt boundaries.
3. Retain multi-host operation instead of hard-coding Claude-only behavior.

**Implemented:** seven lifecycle hooks plus cache health/action integration.

## P5 — Product evidence

1. Enforce the technical closure in repository/runtime validators.
2. Run three verification rounds: local, PR CI, final-main CI.
3. Require CodeQL to report no new alert and alert #6 to transition to fixed.
4. Keep registry publication, provider-billed SignalBench, independent validation, and maturity gated until real receipts exist.

## Completion criteria

- `tools/validate_competitive_gap_closure.py` passes.
- Repository, runtime, release and manifest validators pass.
- Full Python/npm/TypeScript/VS Code/Rust/package matrices pass.
- CodeQL alert #6 is fixed on final `main`.
- Final `main` contains the exact thrice-verified tree.
- No temporary PR or branch remains.
