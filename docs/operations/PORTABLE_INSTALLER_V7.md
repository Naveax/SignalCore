# Portable Installer V7

The canonical command remains:

```bash
npx @signalcore/install
```

The installer uses this order:

1. signed portable release artifact for the current operating system and architecture;
2. an existing Python 3.11+ runtime;
3. a clear fail-closed diagnostic when neither route is available.

Portable artifacts are built by GitHub Actions for Windows, macOS, and Linux. Each bundle contains a self-contained launcher, SHA-256 checksum, build provenance, and the locked `0.0.1 / pre-release` identity.

The installer must verify checksums before replacement, install to a user-owned directory, preserve the previous binary for rollback, configure detected CLI or non-CLI hosts, and run `signalcore status` after installation.

Registry publication and a GitHub pre-release asset are external deployment operations. The repository can implement and test the installer path, but `npx @signalcore/install` cannot use the portable route until those artifacts are published.
