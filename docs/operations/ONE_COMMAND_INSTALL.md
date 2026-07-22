# One-command installation

SignalCore remains **0.0.1 / pre-release**.

## Public package command

After the installer package is published under the pre-release `next` tag:

```bash
npx @signalcore/install
```

The installer detects Python 3.11 or newer, installs SignalCore from the selected Git ref without shell-string execution, applies the `minimal` MCP profile to detected hosts and runs `signalcore status`.

## Repository command available before registry publication

```bash
npx github:Naveax/SignalCore
```

## Safe inspection

Print the exact executable and argument arrays without changing the machine:

```bash
npx github:Naveax/SignalCore -- --plan
```

Options:

```text
--project <path>
--profile minimal|balanced|audit
--ref <git-ref>
--python <executable>
--no-setup
--skip-status
```

The installer never accepts provider credentials and never changes the SignalCore version. Host changes remain backup-first, transactional, verified and rollback-capable through `signalcore setup`.
