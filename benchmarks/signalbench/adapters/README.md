# External SignalBench adapters

Each arm runs as an independent process. Syntavra never imports competitor code.

`external_cli.py` reads an argv array from an arm-specific environment variable:

```text
SYNTAVRA_SIGNALBENCH_<ARM>_COMMAND_JSON
```

The command must write the bound `{result}` JSON with real provider-reported usage and a provider receipt. Missing commands, metrics, receipts or results fail the arm; they are never replaced by synthetic values.
