# SignalCore 0.0.1

SignalCore is an unreleased, local-first Agent Skill that coordinates coding-agent
context, repository evidence, state, and telemetry under a success-first policy.

## Status

- Version: **0.0.1**
- Stage: **pre-release / frontier core**
- Runtime: Python 3.11+ standard library
- External engines: optional; not vendored
- Superiority claims: not established without paired provider benchmarks

## Repository layout

```text
skills/signal-core/
├── SKILL.md
├── data/
│   └── lexicon.json
└── scripts/
    ├── common.py
    ├── evidence.py
    ├── posterior.py
    ├── routing.py
    ├── store.py
    ├── task_state.py
    └── telemetry.py
```

## Quick checks

```bash
python -m compileall -q skills/signal-core/scripts
python skills/signal-core/scripts/routing.py \
  "Find the exact root cause, callers, and narrow verifier"
```

## Design rules

- Correctness and verifier coverage outrank token reduction.
- Exact/security evidence is never silently summarized.
- Large evidence is stored by hash and retrieved through bounded handles.
- SQLite state uses WAL, migrations, bounded transactions, and no pickle/eval.
- Provider usage is normalized before efficiency comparisons.
- Forecasts are not market or Token Savior dominance proof.

## Installation

Copy `skills/signal-core` into the skill directory supported by your coding agent.
For Codex user scope on Windows:

```powershell
Copy-Item -Recurse -Force ".\skills\signal-core" "$HOME\.codex\skills\signal-core"
```

Restart the client after installation.
