# Syntavra 0.0.1 Pre-Release — Historical P0–P2 Closure Record

This document records the repository hardening and evidence-contract work completed before the token-saver product unification. It is historical context, not an active branch plan. The supported repository line is the current `main`, and Syntavra remains **0.0.1 / pre-release**.

## P0 — Repository, CI and installation

The repository established:

- a prepared one-command npm installer and GitHub fallback;
- Python 3.11+ and portable-runtime paths;
- deterministic lockfiles and package tests;
- CodeQL, dependency review, SBOM, checksums and provenance workflows;
- version checks across Python, npm, TypeScript, skills and release metadata.

## P1 — Product surface and integration contracts

The runtime established:

- the canonical `setup`, `status`, `run`, `prove` surface;
- bounded MCP profiles and per-call enforcement;
- transactional host setup and rollback;
- exact session history, compaction and continuity receipts;
- provider usage and external-evidence schemas.

These capabilities are now positioned as internals of the Syntavra token/context optimization skill rather than as a replacement coding-agent product.

## P2 — Evidence infrastructure

Fail-closed contracts exist for paired token, cost, wall-time, success and quality measurement; repository tasks; long-context quality; competitor arms; live integration; onboarding and maturity.

## External gates that remain open

```text
EXTERNAL_SUPERIORITY_NOT_PROVEN
LONG_CONTEXT_QUALITY_NOT_PROVEN
MEASURED_AGENT_BENCHMARK_NOT_PROVEN
LIVE_INTEGRATION_CERTIFICATION_NOT_PROVEN
DAILY_CODING_AGENT_READINESS_NOT_PROVEN
PUBLIC_PRODUCT_MATURITY_NOT_PROVEN
```

They require real provider receipts, pinned external executions, live installations, real users and elapsed operating history. Internal fixtures never satisfy these gates.
