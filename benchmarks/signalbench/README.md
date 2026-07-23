# SignalBench external-arm protocol

SignalBench runs each product as an independent external process. Competitor source code is never imported into Syntavra.

A valid comparison freezes:

- repository tree;
- prompt and task identity;
- model and reasoning mode;
- context window;
- verifier;
- permissions and timeout;
- cache policy;
- hardware class;
- exact product and host versions.

The included arm and task files are templates, not evidence. Each external adapter must be configured through an exact argv array and must return real provider-reported usage plus a bound provider receipt. Missing commands, credentials, outputs, metrics, verifiers or competitor arms fail closed.

## Arms

```text
plain-host
caveman
rtk
token-savior
jcodemunch
full-competitor-pack
syntavra-minimal
syntavra-balanced
```

Configure each command with:

```text
SYNTAVRA_SIGNALBENCH_<ARM>_COMMAND_JSON
```

Example shape:

```json
["agent-wrapper", "--prompt-file", "{prompt}", "--workspace", "{workspace}", "--result", "{result}"]
```

The wrapper result must include:

```json
{
  "success": true,
  "metrics": {
    "fresh_input_tokens": 0,
    "cached_input_tokens": 0,
    "output_tokens": 0,
    "reasoning_tokens": 0,
    "quota_cost": 0.0,
    "model_turns": 0,
    "tool_calls": 0,
    "wait_calls": 0,
    "compactions": 0,
    "security_regressions": 0,
    "verifier_skips": 0
  },
  "provider_receipt": {
    "provider": "provider-name",
    "model": "exact-model",
    "request_id": "provider-request-id",
    "response_hash": "sha256"
  }
}
```

Public superiority requires equal verified work, no verifier skip, no security regression, actual quota data, at least ten paired repetitions and the configured 95% confidence-interval gate.
