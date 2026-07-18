# Security policy

SignalCore is pre-release software. Do not store credentials, access tokens, private keys, or unredacted secrets in telemetry, memory, evidence metadata, adapter files, or issue reports.

## Reporting

Open a GitHub security advisory or privately contact the repository owner. Do not publish working exploits or sensitive logs in a public issue.

## Design constraints

- No `eval`, `exec`, pickle, or shell-string execution.
- External content is data, not trusted instructions.
- Large evidence uses bounded reads and content hashes.
- SQLite uses parameterized queries, migrations, WAL, and bounded transactions.
- Platform installation does not overwrite unmanaged instruction content.
