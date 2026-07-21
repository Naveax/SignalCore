# SignalCore v0.0.1 — Pre-Release Coding-Agent Runtime

SignalCore is a local-first control plane for coding agents. It combines a credential-isolated provider proxy, bounded context, exact session history, tool-routing enforcement, platform adapters, Python/TypeScript libraries and receipt-based benchmarking.

> **Version lock:** the repository and packages remain **0.0.1 / pre-release** until the owner explicitly authorizes another version.
>
> **Claim boundary:** external superiority, public adoption, live certification, SWE-bench performance, OOLONG performance and production maturity are **not proven** without external receipts.

## The product in four commands

```bash
signalcore setup   # detect, plan, install or repair
signalcore status  # health, sessions, metrics and proof gates
signalcore run     # proxy, routing and session operations
signalcore prove   # receipt and benchmark validation
```

Legacy commands remain available for compatibility, but these four commands are the primary mental model.

## Install from the repository

```bash
git clone https://github.com/Naveax/SignalCore.git
cd SignalCore
python -m pip install -e .
signalcore setup --apply --mcp-profile minimal
signalcore status
```

The installer is backup-first and records its measured wall-time. `minimal` is the default MCP profile for daily coding-agent use; `balanced` and `audit` expose progressively broader tool surfaces.

## Daily workflow

```bash
# Show the exact product surface
signalcore run manifest

# Verify that a read tool is allowed
signalcore run route repo.search

# An execution tool fails closed without sandbox + explicit authorization
signalcore run route terminal.exec
signalcore run route terminal.exec --sandboxed --user-authorized

# Plan a credential-isolated provider proxy
signalcore run proxy-plan openai
signalcore run proxy-plan azure-openai --upstream https://YOUR-RESOURCE.openai.azure.com

# Open, append, compact and restore a durable session
signalcore run session-open --session-id my-session --metadata '{"goal":"repair repository"}'
signalcore run session-append my-session decision '{"decision":"run focused tests"}'
signalcore run session-compact my-session
signalcore run session-continuity my-session
```

## Proxy product surface

SignalCore's proxy enforces:

- provider credentials remain transport-only;
- control endpoints require a separate token;
- remote bindings require TLS;
- streaming uses commit-before-forward semantics;
- exact response evidence is committed before client delivery;
- provider token/cost usage can be attached to claim-bearing receipts.

Ten provider families have explicit presets. OpenAI, Anthropic, Gemini and compatible API families can use direct proxy paths. SigV4, OAuth2 and non-compatible request families are marked adapter-required rather than presented as zero-code support.

## Python library

```python
from signalcore_runtime import (
    ProviderUsageReceipt,
    ReceiptValidator,
    SessionContinuityController,
    SignalCoreClient,
    ToolRoutingEnforcer,
)

route = ToolRoutingEnforcer.decide("repo.search")
assert route.allowed

client = SignalCoreClient(".signalcore/sdk", project=".")
```

The dependency-free Python SDK accepts caller-supplied sync or async provider transports and adds request stabilization, exact evidence, safe replay and normalized usage capture.

## TypeScript library

```bash
cd sdk/typescript
npm install
npm run check
npm run build
```

```ts
import { SignalCoreClient } from "@signalcore/client";
import {
  validateProviderUsageReceipt,
  type ProviderUsageReceipt
} from "@signalcore/client/receipts";

const client = new SignalCoreClient({
  baseUrl: "http://127.0.0.1:8787",
  controlToken: process.env.SIGNALCORE_PROXY_CONTROL_TOKEN
});
```

The package includes typed proxy calls, SSE parsing, retries, timeouts, control-plane health methods and receipt validation.

## Platform and framework coverage

The current contract matrix contains:

- **10 provider families**;
- **15 framework surfaces**;
- **18 coding-agent hosts**;
- **18 concrete platform-adapter contracts**.

Platform records include command detection and candidate config paths for Claude Code, Codex, Gemini CLI, GitHub Copilot, Cursor, Windsurf, OpenCode, Cline, Roo Code, Qwen Code, Kiro, Zed, Pi, OMP, OpenClaw, Aider and Continue.

A contract is not a live certification. `signalcore integrations` reports this boundary explicitly.

## Sessions, async compaction and continuity

The session engine provides:

- append-only hash-chained events;
- recursive summary DAGs with exact source ranges;
- background compaction that does not block foreground appends;
- checkpoints, fork, merge, export and import;
- bounded active context over exact external history;
- measured compaction wall-time and continuity receipts;
- exact summary expansion with no forced restart claim.

The architecture claim is:

```text
UNBOUNDED_EXTERNAL_HISTORY_WITH_BOUNDED_ACTIVE_WINDOW
```

It is not a claim that a provider accepts infinite prompt tokens.

## Metrics and analytics

`signalcore status` and `signalcore stats` expose:

- onboarding wall-time;
- input, cached-input, billable-input and output tokens;
- provider cost and request wall-time;
- session and repository counts;
- compaction wall-time and continuity restores;
- denied tool routes;
- unresolved proof-gate reasons.

The default analytics log is local and content-free. Prompt and response bodies are not written to the analytics stream.

## Real benchmark protocol

```bash
signalcore prove plan
signalcore prove schema
signalcore prove receipts receipts.json
signalcore prove benchmark receipts.json
signalcore prove long-context long-context-receipts.json
python benchmarks/measured_agent_benchmark.py receipts.json --output result.json
```

Claim-bearing coding-agent runs require paired baseline/SignalCore provider receipts with measured tokens, cost, wall-time, success and quality. The committed gate requires at least 30 pairs, 5 repositories, 10 tasks and 3 workload families, with quality and success non-inferiority.

The OOLONG-like long-context gate measures required-fact recall, stale-fact rejection, evidence precision, exact recovery, session continuity, tokens and wall-time. A manifest or synthetic run cannot open the gate.

## What is not yet externally proven

- real competitor superiority;
- public SWE-bench success rate;
- public OOLONG quality result;
- live certification for every platform/provider adapter;
- public package adoption and user count;
- 90-day operational maturity.

These remain measurable external gates, not README claims.

## Validation

```bash
python -m compileall -q signalcore_runtime skills/signal-core tools tests benchmarks
python -m unittest discover -s tests/runtime -q
python tools/validate.py
python tools/validate_runtime.py

cd sdk/typescript
npm install --ignore-scripts --no-audit --no-fund
npm run check
npm run build
```

CI runs Python tests across Ubuntu, Windows and macOS on Python 3.11–3.13, validates the four-command workflow, builds the wheel in a clean environment, type-checks the TypeScript SDK and creates pre-release artifact/SBOM bundles.

## Documentation

- `docs/architecture/DAILY_AGENT_PRODUCT_001.md`
- `docs/benchmark/MEASURED_AGENT_PROOF_001.md`
- `schemas/provider-usage-receipt-v1.json`

## Version policy

`VERSION`, Python, TypeScript, skill, marketplace, extension, CodeMeta, CLI, workflows and artifact metadata must remain synchronized at **0.0.1** and **pre-release** until the owner explicitly changes the version policy.
