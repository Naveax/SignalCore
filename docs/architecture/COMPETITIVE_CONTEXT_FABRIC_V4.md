# Competitive Context Fabric V4

## Objective

Competitive Context Fabric V4 turns SignalCore from a tool-output compactor into a unified local runtime for coding-agent context economy, exact evidence, long-session memory, structural navigation, provider caching and secure execution.

It is designed to make separate context/token skills optional without copying their implementations. The system remains clean-room and fail-closed: capability may be implemented before external superiority is proven, but public superiority claims still require identical-arm evidence.

## Unified control plane

The fabric combines:

- task-conditioned MCP profiles (`tiny`, `optimized`, `full`);
- automatic command-family routing for tests, builds, reads, searches, package managers, network tools, containers and cloud CLIs;
- exact output externalization with searchable and progressively revealable evidence;
- deterministic command-family compactors that retain failures, locations, summaries and security signals;
- stable provider-prefix fingerprints and provider-native prompt-cache controls;
- immutable session history, summary DAG expansion, checkpoints, forks and merges;
- exact structural symbol/source/range retrieval;
- strict sandbox routing for untrusted network commands;
- persistent savings, latency, cache and reliability analytics;
- installation and enforcement plans across registered coding-agent hosts.

## Provider gateway

`ProviderGateway` supports OpenAI, Anthropic, Gemini and OpenAI-compatible request families. It:

- rejects credentials embedded in request JSON;
- stores exact request evidence;
- removes volatile transport identifiers from request fingerprints;
- prepares provider-native prompt-cache controls;
- permits exact response replay only for deterministic, non-streaming, tool-free requests by default;
- stores exact provider responses and redacted model-visible previews;
- normalizes provider usage and can append HMAC-attested usage receipts;
- verifies request/response evidence and replay-cache integrity.

## Transparent provider proxy

`ProviderProxyRuntime` adds an optional local reverse proxy for clients that cannot call the gateway API directly.

Security properties:

- the upstream origin is fixed in configuration; absolute proxy targets are rejected;
- HTTPS is mandatory except for explicit local/test configurations;
- client credential headers are discarded;
- provider credentials are loaded only from an environment variable;
- remote listening is disabled unless explicitly enabled with a control token;
- request and buffered-response limits are enforced;
- streaming responses are forwarded incrementally and captured byte-for-byte after completion;
- non-streaming successful deterministic responses can be replayed without another provider request.

The proxy never returns redacted content in place of the provider response. Redaction applies only to local previews and indexes; exact transport evidence remains immutable.

## CLI

The primary direct surfaces are:

```text
signalcore fabric profile --task "run tests and inspect auth failures"
signalcore fabric route -- pytest -q
signalcore fabric compact --stdout-file test.log -- pytest -q
signalcore fabric cache-align --input request.json
signalcore fabric platform-plan --all
signalcore fabric doctor
signalcore fabric insights

signalcore provider capabilities openai
signalcore provider prepare openai --input request.json --output plan.json
signalcore provider capture --plan plan.json --response response.json --output capture.json
signalcore provider replay --cache-key <sha256>
signalcore provider stats
signalcore provider verify
signalcore provider proxy --provider openai --upstream <fixed-origin> --credential-env OPENAI_API_KEY
```

## Claim boundary

Internal tests can prove implementation properties such as exact reconstruction, cache-key stability, credential isolation, replay safety, streaming passthrough and database integrity. They cannot prove that SignalCore beats every external product in real coding tasks.

External superiority still requires:

- a real repository-task corpus;
- executable competitor arms;
- identical model/provider permissions;
- randomized paired repetitions;
- provider usage receipts;
- pass-rate, latency, cost, security and recall evaluation.
