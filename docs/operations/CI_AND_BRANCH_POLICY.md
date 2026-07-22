# CI and branch policy

## Canonical integration path

`main` is the canonical product branch. Development starts from `main` on a focused branch and returns through a pull request. The v0.0.1 product line is not maintained as a second divergent release branch.

## Required checks

A merge candidate must pass:

- repository manifest and hygiene validation;
- Python 3.11–3.13 on Ubuntu, Windows and macOS;
- full runtime and adapter tests;
- clean wheel installation;
- TypeScript SDK on supported Node versions with `npm ci`, type-check, tests and package inspection;
- one-command installer tests;
- CodeQL and dependency review;
- artifact, SBOM, checksum, reproducibility and provenance generation.

## Manifest rule

`MANIFEST.sha256` is refreshed inside the development branch. CI verifies it but never commits or pushes to `main`. This keeps the reviewed SHA identical to the validated SHA and removes the historical bot-commit failure pattern.

## Merge rule

Use squash merge for the hardening branch after all required checks pass. Do not rewrite old public commits merely to change historical check icons. Historical intermediate commits may remain red because they represented incomplete states; the supported state is the final reviewed commit.

## Claims

P0–P2 code and evidence-collection infrastructure may be merged together. External superiority, live certification, public adoption, SWE-bench, OOLONG and 90-day maturity remain fail-closed until real receipts satisfy their gates.
