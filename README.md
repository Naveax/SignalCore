# SignalCore v0.0.1 — Pre-Release Unified Agent Runtime

SignalCore is a local-first control plane for AI coding agents. The repository version is intentionally locked to **0.0.1** and the release channel remains **pre-release / pre-alpha** until the owner explicitly authorizes a change.

> **Public competitor claim: `EXTERNAL_SUPERIORITY_NOT_PROVEN`.** Internal tests and benchmark machinery are not external competitor evidence.
>
> **Context claim:** `UNBOUNDED_EXTERNAL_HISTORY_WITH_BOUNDED_ACTIVE_WINDOW`. SignalCore does not claim that a model provider accepts infinite prompt tokens.
>
> **Product maturity claim:** `PUBLIC_PRODUCT_MATURITY_NOT_PROVEN` until real 90-day external receipts pass the maturity gate.

## Unified capabilities

### Zero-friction product surface

- Plan-first and backup-first `install`, `wrap`, `doctor`, `stats`, `upgrade`, and `repair` commands.
- Ten provider contracts, fifteen framework contracts, eighteen host contracts, and at least fourteen automatic host plans.
- Version-locked upgrades: a target other than `0.0.1` fails closed.
- Live integration certification requires external receipts; internal contracts are not mislabeled as live production proof.

### Structural Intelligence V2

- Multi-language nodes with exact evidence ranges.
- Calls, imports, inheritance, implementations, overrides, reads/writes, data flow, taint flow, tests, build targets, dependencies, stack traces, ownership, rename history, and change-frequency signals.
- Query-adaptive lexical, path, ownership, centrality, and change ranking.
- Reverse impact and affected-test traversal.

### Secure execution and reversible context

- Encrypted exact evidence and byte-exact restoration.
- Authenticated provider control plane and commit-before-forward streaming.
- Docker, Podman, bubblewrap, and explicitly degraded local-restricted sandbox contracts.
- Bounded model-visible output with exact recovery references.

### Unbounded external session history

- Immutable exact history and recursive summary DAGs.
- A strictly bounded active model window over externally stored history.
- Current temporal truth selection and exact reference fallback.
- Recursive map/reduce workers with duplicate suppression, retry bounds, per-worker evidence, and global provenance.
- Committed stress tiers: 32K, 64K, 128K, 256K, 512K, 1M, 2M, and 10M virtual history tokens.

### SignalBench 2.0

- 150 coding-task slots across nine task categories and ten languages.
- Six isolated external arms: plain baseline, SignalCore, Token Savior, Context Mode, Headroom, and Volt/LCM.
- Thirty deterministic paired repetitions, producing 27,000 scheduled runs.
- Identical model, provider, reasoning, context, permission, verifier, and repository-tree requirements.
- Synthetic slots and missing provider receipts cannot open a superiority claim.

### Public proof and release discipline

- Twelve workload families covering coding, operations, structured data, retrieval, agents, long context, and multimodal documents.
- Distribution targets for PyPI, npm, GHCR, Homebrew, Winget, and standalone binaries.
- SBOM, provenance, reproducibility, signed-tag, migration, and rollback gates.
- Ninety-day, 1,000-receipt, 100-repository, 50-user fail-closed maturity gate.

## Quick start

```bash
signalcore version
signalcore install --auto
signalcore doctor
signalcore integrations
signalcore context-stress --max-tier 10000000
signalcore signalbench2 plan --repetitions 30
signalcore proof status
```

Existing compatibility commands remain available:

```bash
signalcore inspect map "authentication failure" --token-budget 2000
signalcore sandbox plan --network none -- pytest -q
signalcore compress put build.log --budget 4096
signalcore session open --metadata '{"goal":"release audit"}'
signalcore output govern --profile compact --contract implementation --payload result.json
```

## Validation

```bash
python -m compileall -q signalcore_runtime skills/signal-core tools tests benchmarks
python -m unittest discover -s tests/runtime -q
python -m unittest tests.test_platforms tests.test_roblox_profile_gate -q
python -m unittest discover -s tests/roblox_profile -q
python tools/validate.py
python tools/validate_runtime.py
python benchmarks/v001_pre_release_benchmark.py --output benchmarks/results/v001-pre-release/internal.json
```

CI runs the combined suite on Ubuntu, Windows, and macOS with Python 3.11, 3.12, and 3.13.

## Benchmark boundary

The committed v0.0.1 benchmark validates integration targets, Structural Intelligence V2, a 150-task/30-repetition schedule, recursive execution, and 32K–10M context planning. It does not execute external competitor products and therefore cannot prove competitor superiority.

## Version policy

`VERSION`, Python, TypeScript, skill, marketplace, extension, CodeMeta, CLI, and validation metadata must remain synchronized at **0.0.1**. Packages must remain marked as pre-release until the owner explicitly changes this policy.

## Roblox Studio governed profile

The Roblox Studio orchestration profile remains hidden and fail-closed. Internal and simulated results do not establish live Studio execution, generic provider savings, or competitor superiority.

| Capability | Governed maturity | Boundary |
|---|---|---|
| Signed activation [claim:roblox.activation] | **INTERNALLY_VERIFIED** | Process attestation is exercised through the injected test contract. |
| TaskState V2 [claim:roblox.task_state] | **INTERNALLY_VERIFIED** | Deterministic schema and migration behavior are covered by profile tests. |
| Capability graph [claim:roblox.capabilities] | **INTERNALLY_VERIFIED** | Planner, execution, and validation records remain governed by the artifact registry. |
| Simulated orchestration [claim:roblox.simulated] | **SIMULATED** | The committed benchmark artifact uses simulated external engines. |
| Transcript adapter [claim:roblox.transcript] | **IMPLEMENTED** | The contract exists; no sanitized real transcript is claimed. |
| Live Studio bridge [claim:roblox.live] | **PLANNED** | Live execution remains disabled. |
| DataStore migration execution [claim:roblox.datastore] | **PLANNED** | External validation boundary only. |
| Asset, animation, and Blender engines [claim:roblox.external_engines] | **PLANNED** | External engine contracts only. |
| Profile test suite [claim:roblox.tests] | **INTERNALLY_VERIFIED** | The governed profile test suite remains bound to the artifact registry. |

