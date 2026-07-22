# Competitive Runtime V7 Measurement Protocol

## Internal functional benchmark

`benchmarks/competitive_runtime_v7_benchmark.py` measures only the local implementation:

- exact-output bytes versus compact-view bytes;
- raw estimated context tokens versus compiled context tokens;
- graph indexing and query wall-time;
- memory compaction, retrieval, and exact recovery;
- capability decision throughput;
- adapter contract coverage.

The output claim is always:

```text
INTERNAL_FUNCTIONAL_MEASUREMENT_ONLY
```

It is not evidence that SignalCore beats Token Savior, Context Mode, Headroom, Volt/LCM, Aider, OpenHands, or any other product.

## External comparison gate

A competitor claim requires paired runs with:

- identical repository commit;
- identical task text and verifier;
- identical provider and model configuration;
- cold and warm cache arms;
- repeated randomized schedules;
- provider-native token and cost receipts;
- wall-time from the same harness boundary;
- task success and result-quality verification;
- pinned competitor and SignalCore commits;
- immutable output artifacts and hashes.

Until those receipts exist, the correct statuses remain:

```text
EXTERNAL_SUPERIORITY_NOT_PROVEN
MEASURED_AGENT_BENCHMARK_NOT_PROVEN
LONG_CONTEXT_QUALITY_NOT_PROVEN
LIVE_INTEGRATION_CERTIFICATION_NOT_PROVEN
```

## Capability comparison

V7 is designed to close capability gaps without assuming benchmark results:

| Area | V7 capability |
|---|---|
| Token/context control | Typed IR, delta context, stable prefix, deterministic budget |
| Tool-output | Typed pre-context interception and exact recovery |
| Long sessions | Exact hash chain plus multi-view summary DAG |
| Code graph | Incremental AST/syntax graph with evidence confidence |
| MCP/tool safety | Argument/resource-bound signed capabilities |
| Credentials | Secretless agent environment and transport-only injection |
| Installation | Portable artifact workflow plus Python fallback |
| Cross-agent | CLI and non-CLI adapter contract |
| Agent runtime | Worktree-oriented reference planner |
| Operations | One status/doctor facade and content-free metrics |
