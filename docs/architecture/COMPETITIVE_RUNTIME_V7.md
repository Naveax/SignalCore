# SignalCore Competitive Runtime V7

SignalCore remains **0.0.1 / pre-release**. Competitive Runtime V7 implements the capability layer needed to challenge specialized context, memory, graph, proxy, security, and coding-agent products without treating internal fixtures as external proof.

## Public mental model

The public product remains four commands:

```text
signalcore setup
signalcore status
signalcore run
signalcore prove
```

V7 capabilities are operations under `signalcore run`; they do not create a second product surface.

## Components

### Context Compiler V2

The compiler uses a typed Context IR, stable-prefix ordering, content deduplication, delta views, provider-family token estimates, deterministic serialization, priority-aware budgeting, and exact artifact references for large inputs.

### Universal Output Firewall V2

Tool output is classified before it enters model context. JSON, diffs, tests, search results, source files, and general shell logs receive type-specific views. Original bytes are committed to the artifact store first and can be queried by head, tail, errors, failures, regex, or JSON path.

### Content-Addressed Artifact Store V2

Artifacts are addressed by SHA-256, written atomically, indexed in SQLite/WAL, deduplicated, integrity checked, and exposed only through bounded views by default.

### Incremental Code Intelligence Graph V3

The index tracks file hashes and updates changed files only. Python uses AST extraction; supported non-Python languages use conservative syntax extraction with lower confidence. Nodes retain evidence hashes. Query and reverse-impact traversal never present unresolved edges as exact facts.

### Session Memory DAG V2

Exact events use a hash chain. Compaction creates separate task, decision, change, failure, security, and dependency views. Checkpoint, fork, merge, retrieve, restore, and verify operations preserve the exact event history.

### Capability Security V2

Risky operations are evaluated at tool, argument, and resource scope. Capabilities are HMAC-signed, expiring, argument-bound, resource-bound, and single-use by default. Destructive execution and writes outside `workspace:` fail closed.

### Secretless Provider Gateway V2

Provider credentials are transport-only. Agent environments are sanitized, child-process inheritance is denied, and provider injection plans identify the credential source without returning credential values.

### Universal Adapter Contract V2

CLI availability is not required for official support. IDEs, IDE extensions, desktop applications, and platforms can be represented by config, plugin, MCP, hook, provider-proxy, or SDK surfaces. Each adapter declares a capability level and exact interception properties.

### Reference Coding Agent V2

The reference agent composes graph retrieval, memory, capability decisions, worktree isolation, affected-test planning, and receipt output. It is plan-only until mutating operations receive explicit authorization.

## Invariants

1. No large output is silently discarded.
2. Compact views always retain an exact artifact reference.
3. Summary loss cannot destroy exact session history.
4. Unknown tools fail closed.
5. Provider secrets are not placed in agent-visible state.
6. Non-CLI integrations are first-class when the platform exposes a supported integration surface.
7. All package identities remain `0.0.1` and the channel remains `pre-release`.
8. External superiority remains unproven until paired receipts pass the public proof gates.
