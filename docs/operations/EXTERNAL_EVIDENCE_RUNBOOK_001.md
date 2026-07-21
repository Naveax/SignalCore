# SignalCore External Evidence Runbook 001

## Purpose

This runbook converts SignalCore's fail-closed proof gates into repeatable external operations. It does not authorize a version change. All artifacts remain labeled **0.0.1 pre-release**.

## 1. Freeze an evaluation identity

Record and pin:

- SignalCore commit SHA;
- benchmark harness commit SHA;
- verifier commit SHA;
- dataset version;
- container image digest (`sha256:...`);
- provider, model, reasoning configuration and model-config hash;
- repository commit for coding tasks;
- timeout, retry and permission policy;
- active MCP profile;
- operating system and runtime version.

Do not use mutable labels such as `latest`, `main`, `ubuntu-latest` or an unpinned model alias in a claim-bearing receipt.

## 2. Validate installation and rollback

For each host/OS combination:

```bash
signalcore setup --apply --mcp-profile minimal
signalcore status
signalcore repair --apply
```

Capture:

- install wall-time;
- detected/configured host;
- host verification result;
- doctor result;
- rollback verification;
- sanitized config and artifact hashes.

A host should not be marked live-certified from an internal unit test.

## 3. Validate the provider proxy

```bash
signalcore run proxy-service plan openai
signalcore run proxy-service install openai --apply --activate
signalcore run proxy-service verify openai
```

Run a real non-secret test request and record:

- request/response success;
- streaming lifecycle;
- provider usage payload hash;
- normalized token and cost fields;
- end-to-end wall-time;
- committed evidence handle;
- service descriptor and config hashes.

Never include API keys in a receipt.

## 4. Validate MCP routing

Use the installed profile and test:

- one allowed read operation;
- one hidden-tool bypass attempt;
- one destructive call without authorization;
- one sandboxed execution with explicit authorization;
- one unsandboxed process attempt.

Record route receipt hashes and verify that authorization metadata is absent from the actual tool/provider payload.

## 5. Validate session continuity

```bash
signalcore run session-open --session-id external-session
signalcore run session-append external-session decision '{"decision":"continue"}'
signalcore run session-compact external-session
signalcore run session-continuity external-session
```

Restart the client/runtime between steps where supported. Record:

- hash-chain verification;
- exact recovery;
- active-context tokens;
- compaction wall-time;
- continuity restoration;
- forced-restart status.

## 6. Run paired agent tasks

Every task must have a baseline and SignalCore run under the same pinned identity. A valid pair shares:

```text
suite_id
task_id
repetition
dataset_version
harness_commit
verifier_commit
environment_image_digest
repository_commit
provider
model
model_config_hash
```

Do not rerun only the failed arm without recording the retry. Do not remove timeouts, crashes or verifier failures.

## 7. Run external suites

List the configured contracts:

```bash
signalcore prove suites
```

Validate collected receipts:

```bash
signalcore prove external-suite swe-bench-receipts.json --suite swe-bench
signalcore prove external-suite oolong-receipts.json --suite oolong
```

The external suite file must use `schemas/external-benchmark-receipt-v1.json` and preserve raw provider receipt hashes.

## 8. Validate live integrations

```bash
signalcore prove integrations live-integration-receipts.json --integration codex
```

Minimum certification requirements:

- three external, non-synthetic receipts;
- at least two operating systems;
- one pinned harness commit;
- independent environment/config/artifact hashes;
- install, doctor, request, response and rollback success;
- routing + continuity for hosts;
- provider usage + streaming for providers.

## 9. Validate product maturity

```bash
signalcore prove maturity maturity-evidence.json
```

Use externally sourced onboarding, distribution and release records. Fixtures and self-generated sample users do not count.

## 10. Review claims manually

Even a passing gate returns evidence eligibility, not an automatic marketing claim. Before publishing:

- inspect invalid and excluded rows;
- reproduce a sample of tasks;
- confirm raw receipt hashes;
- verify package/repository commit identity;
- confirm no version metadata changed from 0.0.1;
- confirm CI and repository integrity manifest pass on the exact evaluated commit.

## Stop conditions

Stop the claim review if any of the following occurs:

- model/provider parity differs between paired arms;
- harness, verifier, dataset or environment is mutable/unpinned;
- provider usage is estimated instead of receipted;
- duplicate task/arm, artifact or provider receipt appears;
- quality or success non-inferiority fails;
- exact recovery or continuity fails;
- an external competitor arm is unavailable or misconfigured;
- current CI or integrity manifest is not verified.
