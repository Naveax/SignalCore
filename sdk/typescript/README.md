# @syntavra/sdk

Typed ESM/TypeScript client and receipt validators for Syntavra 0.0.1 pre-release.
Syntavra is a token and context optimization Agent Skill/runtime middleware for existing AI coding tools. Provider credentials remain in the proxy process; the client rejects credential-shaped request fields and provider authorization headers.

```ts
import {SyntavraClient} from "@syntavra/sdk";
import {validateTokenAttributionReceipt} from "@syntavra/sdk/receipts";

const client = new SyntavraClient({
  baseUrl: "http://127.0.0.1:8787",
  controlToken: process.env.SYNTAVRA_PROXY_CONTROL_TOKEN,
});

const response = await client.openAI({model: "gpt-5", input: "Inspect this repository"});
console.log(response.data, response.evidenceHandle, response.requestId);
```

The receipt module validates provider usage and source-attribution receipts while preserving the distinction between provider-observed, locally tokenized, estimated and unknown values. Remote connections require HTTPS. The client includes bounded retries, timeout/abort handling, typed SSE iteration and provider-compatible helpers without bundling credentials.
