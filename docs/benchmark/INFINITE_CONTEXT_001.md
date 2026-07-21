# Infinite Context Stress Protocol — v0.0.1 Pre-Release

## Definition

The tested property is unbounded external history with a bounded active model window. It is not a claim that a provider accepts infinite prompt tokens.

## Tiers

- 32K
- 64K
- 128K
- 256K
- 512K
- 1M
- 2M
- 10M virtual history tokens

## Mandatory assertions

For every tier:

- history token accounting is exact;
- every external segment has an exact evidence reference;
- active visible tokens are at or below the configured budget;
- no forced session restart is required;
- recursive summary depth is finite and deterministic;
- current temporal generations outrank superseded generations;
- the recovery manifest hash is deterministic.

## Recursive execution

The execution engine must provide:

- deterministic task identity;
- duplicate-work suppression;
- bounded worker concurrency;
- retry limits;
- ordered reduction;
- per-worker evidence hashes;
- one global provenance hash.

## Public boundary

This stress harness validates SignalCore’s planner and storage model. It does not establish superiority over Volt/LCM or another external product until the same workload, model, provider, and verifier are run through external arms.
