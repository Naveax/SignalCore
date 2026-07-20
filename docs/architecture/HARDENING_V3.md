# SignalCore Hardening V3

## Status

Hardening V3 closes the highest-risk gaps identified after Tool-Output Externalization V2. It is an implementation and validation layer, not a marketing score override. Competitor scores are never reduced without identical-arm evidence.

## Mandatory host-output interception

`HostOutputPipeline` is the single post-tool path for hook and MCP outputs. It:

- captures direct strings, bytes and recognized nested output fields;
- stores exact raw evidence before replacing model-visible content;
- emits stable artifact, Merkle and evidence references;
- records session lineage when a session id is present;
- refuses to truncate a large output when externalization fails;
- skips only SignalCore retrieval and receipt tools to avoid recursive capture.

## Provider usage receipts

`UsageReceiptLedger` normalizes common provider usage shapes and creates the existing hardened SignalBench `UsageReceipt`. Each receipt is also stored in an append-only SQLite/WAL ledger with:

- request and provider-response hashes;
- raw usage hash;
- previous ledger hash;
- current chain hash;
- optional HMAC-SHA256 attestation from `SIGNALCORE_RECEIPT_SIGNING_KEY`.

Public superiority must require HMAC-attested receipts. Hash-chain-only receipts remain useful local evidence but are not sufficient for a public 10/10 claim.

## Semantic and temporal session retrieval

`SessionSemanticRetriever` ranks exact events with direct tokens, deterministic alias expansion, character similarity, event importance and recency. It also resolves:

- explicit `supersedes` and `replaces` links;
- explicit revoked or obsolete status;
- newer authoritative decisions for the same subject;
- optional retrieval of superseded history for audits.

The result is query-conditioned context without replacing exact session history.

## Security scanning

The untrusted-output scanner performs Unicode NFKC normalization, ANSI and zero-width removal, structured secret redaction, multilingual instruction-injection detection and bounded base64 inspection. Exact evidence is unchanged; only indexed and model-visible forms are redacted.

Recognized secret classes include generic assignments, AWS access keys, GitHub tokens, JWTs, database URIs and private-key blocks.

## Fail-closed 10/10 readiness gate

`SignalCoreReadinessGate` does not award 10/10 from internal byte reduction. It requires all of the following:

- at least 95% host interception coverage;
- at least 50 real repository tasks;
- at least three executable competitor arms;
- at least 30 valid paired repetitions;
- at least 99% provider-receipt coverage;
- at least 90% semantic recall@5;
- at least 95% temporal-truth accuracy;
- at least 99.9% concurrency success;
- 100% exact roundtrip;
- zero security regressions;
- no pass-rate regression;
- p95 latency no greater than 250 ms.

Until external arms and real tasks satisfy those gates, the public claim remains `SUPERIORITY_NOT_PROVEN`.
