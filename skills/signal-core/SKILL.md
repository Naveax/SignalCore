---
name: signal-core
version: "0.0.1"
description: >
  Route complex coding-agent work through minimal verified context, conservative
  posterior decisions, exact evidence, deduplicated state, and normalized usage
  telemetry. Use for repository exploration, debugging, long sessions, large
  outputs, tool overload, and token-efficiency analysis. Skip trivial requests.
metadata:
  author: Naveax
  status: pre-release
---

# SignalCore

SignalCore is a single Agent Skill for reducing coding-agent context, tool, retry,
and verification cost without treating lower token count as more important than
correctness.

## Operating contract

1. Encode task, repository, session, model, and active-engine state.
2. Select the smallest route that clears conservative success and evidence gates.
3. Prefer exact retrieval before broad or semantic retrieval.
4. Store large exact evidence by hash and expose compact recovery handles.
5. Deduplicate repeated claims, ranges, and tool results before context injection.
6. Measure actual provider usage, retries, evidence quality, latency, and cost.
7. Stop when exact source, impact boundary, and a runnable verifier are sufficient.
8. Do not claim superiority from forecasts or local unit tests alone.

## Core scripts

- `scripts/task_state.py` — repository/session-aware task state.
- `scripts/routing.py` — multilingual activation and integrity routing.
- `scripts/posterior.py` — conservative posterior utilities.
- `scripts/store.py` — SQLite WAL state and migrations.
- `scripts/evidence.py` — content-addressed exact evidence.
- `scripts/telemetry.py` — normalized provider and tool telemetry.

## Version

Public pre-release version: **0.0.1**.
