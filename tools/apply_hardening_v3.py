#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one match in {path}, found {count}: {old[:80]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_hooks() -> None:
    replace_once(
        "signalcore_runtime/hooks.py",
        "from .compression import ContentRouter\nfrom .models import HookDecision\n",
        "from .compression import ContentRouter\n"
        "from .evidence import EvidenceStore\n"
        "from .host_output_pipeline import HostOutputPipeline\n"
        "from .models import HookDecision\n"
        "from .session_runtime import SessionRuntime\n"
        "from .tool_externalization import ToolOutputExternalizer\n"
        "from .tool_externalization_types import ExternalizationPolicy\n"
        "from .usage_receipt_ledger import UsageReceiptLedger\n"
        "from .util import stable_project_id\n",
    )
    replace_once(
        "signalcore_runtime/hooks.py",
        "        compressor: ContentRouter | None = None,\n    ):\n",
        "        compressor: ContentRouter | None = None,\n"
        "        state_root: Path | None = None,\n"
        "        output_pipeline: HostOutputPipeline | None = None,\n"
        "        auto_externalize: bool = True,\n"
        "    ):\n",
    )
    replace_once(
        "signalcore_runtime/hooks.py",
        "        self.compressor = compressor\n",
        "        self.compressor = compressor\n"
        "        self.output_pipeline = output_pipeline\n"
        "        if self.output_pipeline is None and auto_externalize:\n"
        "            active_state = Path(state_root).resolve(strict=False) if state_root else self.project_root / '.signalcore' / 'runtime-v3'\n"
        "            project_id = stable_project_id(self.project_root)\n"
        "            evidence = EvidenceStore(active_state / 'evidence', project_id=project_id)\n"
        "            externalizer = ToolOutputExternalizer(\n"
        "                active_state / 'tool-externalization.sqlite3',\n"
        "                evidence=evidence,\n"
        "                policy=ExternalizationPolicy.for_profile('balanced'),\n"
        "            )\n"
        "            usage = UsageReceiptLedger(active_state / 'usage-receipts.sqlite3')\n"
        "            sessions = SessionRuntime(active_state / 'sessions.sqlite3', project_id=project_id)\n"
        "            self.output_pipeline = HostOutputPipeline(externalizer, usage_ledger=usage, sessions=sessions)\n",
    )
    replace_once(
        "signalcore_runtime/hooks.py",
        "    def post_tool(self, payload: dict[str, Any]) -> dict[str, Any]:\n        result = payload.get(\"result\") or {}\n",
        "    def post_tool(self, payload: dict[str, Any]) -> dict[str, Any]:\n"
        "        if self.output_pipeline is not None:\n"
        "            return self.output_pipeline.capture_hook_payload(payload)\n"
        "        result = payload.get(\"result\") or {}\n",
    )


def patch_mcp() -> None:
    replace_once(
        "signalcore_runtime/mcp_server.py",
        "from .evidence import EvidenceStore\nfrom .host_adapters import detect_hosts\n",
        "from .evidence import EvidenceStore\n"
        "from .host_adapters import detect_hosts\n"
        "from .host_output_pipeline import HostOutputPipeline\n",
    )
    replace_once(
        "signalcore_runtime/mcp_server.py",
        "from .session_runtime import SessionRuntime\nfrom .status import inspect_runtime\n",
        "from .session_retrieval import SessionSemanticRetriever\n"
        "from .session_runtime import SessionRuntime\n"
        "from .status import inspect_runtime\n"
        "from .tool_externalization import ToolOutputExternalizer\n"
        "from .tool_externalization_types import ExternalizationPolicy, ToolPayload\n"
        "from .usage_receipt_ledger import UsageReceiptLedger\n",
    )
    replace_once(
        "signalcore_runtime/mcp_server.py",
        "        self.sessions = SessionRuntime(state_root / \"sessions.sqlite3\", project_id=project_id)\n",
        "        self.sessions = SessionRuntime(state_root / \"sessions.sqlite3\", project_id=project_id)\n"
        "        self.externalizer = ToolOutputExternalizer(\n"
        "            state_root / 'tool-externalization.sqlite3',\n"
        "            evidence=self.evidence,\n"
        "            policy=ExternalizationPolicy.for_profile('balanced'),\n"
        "        )\n"
        "        self.usage_ledger = UsageReceiptLedger(state_root / 'usage-receipts.sqlite3')\n"
        "        self.output_pipeline = HostOutputPipeline(\n"
        "            self.externalizer, usage_ledger=self.usage_ledger, sessions=self.sessions\n"
        "        )\n"
        "        self.session_retriever = SessionSemanticRetriever(self.sessions)\n",
    )
    replace_once(
        "signalcore_runtime/mcp_server.py",
        "            tool(\n                \"signalcore.output.govern\", \"Render a correctness-preserving bounded answer\",\n                {\"payload\": {\"type\": \"object\"}, \"profile\": {\"type\": \"string\"}, \"contract\": {\"type\": \"string\"}}, [\"payload\"],\n            ),\n",
        "            tool(\n"
        "                'signalcore.output.capture', 'Capture tool output through exact externalization',\n"
        "                {'stdout': {'type': 'string'}, 'stderr': {'type': 'string'}, 'command': {'type': 'string'}, 'tool_name': {'type': 'string'}, 'path': {'type': 'string'}, 'scope_key': {'type': 'string'}},\n"
        "            ),\n"
        "            tool(\n"
        "                'signalcore.output.search', 'Search exact externalized tool output',\n"
        "                {'query': {'type': 'string'}, 'artifact_id': {'type': 'string'}, 'scope_key': {'type': 'string'}, 'limit': {'type': 'integer'}}, ['query'],\n"
        "            ),\n"
        "            tool(\n"
        "                'signalcore.output.reveal', 'Progressively reveal selected externalized evidence',\n"
        "                {'artifact_id': {'type': 'string'}, 'lens': {'type': 'string'}, 'query': {'type': 'string'}, 'budget_bytes': {'type': 'integer'}, 'continuation_token': {'type': 'string'}},\n"
        "            ),\n"
        "            tool(\n"
        "                'signalcore.output.verify', 'Verify exact reconstruction and Merkle integrity',\n"
        "                {'artifact_id': {'type': 'string'}}, ['artifact_id'],\n"
        "            ),\n"
        "            tool('signalcore.output.stats', 'Inspect externalization statistics'),\n"
        "            tool(\n"
        "                'signalcore.usage.record', 'Record an attested provider usage receipt',\n"
        "                {'task_id': {'type': 'string'}, 'arm_id': {'type': 'string'}, 'repetition': {'type': 'integer'}, 'cache_mode': {'type': 'string'}, 'provider': {'type': 'string'}, 'request_id': {'type': 'string'}, 'provider_response': {'type': 'object'}, 'usage': {'type': 'object'}, 'quota_cost': {'type': 'number'}, 'hardware_hash': {'type': 'string'}},\n"
        "                ['task_id', 'arm_id', 'repetition', 'cache_mode', 'provider', 'request_id', 'provider_response', 'usage', 'quota_cost', 'hardware_hash'],\n"
        "            ),\n"
        "            tool('signalcore.usage.verify', 'Verify the provider usage hash chain and signatures', {'require_hmac': {'type': 'boolean'}}),\n"
        "            tool(\n"
        "                'signalcore.session.search', 'Semantic and temporal search over exact session events',\n"
        "                {'session_id': {'type': 'string'}, 'query': {'type': 'string'}, 'limit': {'type': 'integer'}, 'include_superseded': {'type': 'boolean'}}, ['session_id', 'query'],\n"
        "            ),\n"
        "            tool(\n"
        "                'signalcore.session.semantic_context', 'Build query-conditioned long-session context',\n"
        "                {'session_id': {'type': 'string'}, 'query': {'type': 'string'}, 'budget_bytes': {'type': 'integer'}, 'include_superseded': {'type': 'boolean'}}, ['session_id', 'query'],\n"
        "            ),\n"
        "            tool(\n"
        "                \"signalcore.output.govern\", \"Render a correctness-preserving bounded answer\",\n"
        "                {\"payload\": {\"type\": \"object\"}, \"profile\": {\"type\": \"string\"}, \"contract\": {\"type\": \"string\"}}, [\"payload\"],\n"
        "            ),\n",
    )
    replace_once(
        "signalcore_runtime/mcp_server.py",
        "        if name == \"signalcore.session.open\":\n",
        "        if name == 'signalcore.output.capture':\n"
        "            artifact = self.externalizer.externalize(ToolPayload(\n"
        "                command=str(arguments.get('command', '')), stdout=str(arguments.get('stdout', '')),\n"
        "                stderr=str(arguments.get('stderr', '')), tool_name=str(arguments.get('tool_name', 'mcp')),\n"
        "                path=str(arguments.get('path', '')), scope_key=str(arguments.get('scope_key', 'default')),\n"
        "                metadata=dict(arguments.get('metadata') or {}),\n"
        "            ))\n"
        "            return asdict(artifact)\n"
        "        if name == 'signalcore.output.search':\n"
        "            return {'hits': [asdict(hit) for hit in self.externalizer.search(\n"
        "                str(arguments['query']), artifact_id=arguments.get('artifact_id'),\n"
        "                scope_key=arguments.get('scope_key'), limit=int(arguments.get('limit', 8)),\n"
        "            )]}\n"
        "        if name == 'signalcore.output.reveal':\n"
        "            return asdict(self.externalizer.reveal(\n"
        "                arguments.get('artifact_id'), lens=str(arguments.get('lens', 'salient')),\n"
        "                query=str(arguments.get('query', '')), budget_bytes=arguments.get('budget_bytes'),\n"
        "                continuation_token=arguments.get('continuation_token'),\n"
        "            ))\n"
        "        if name == 'signalcore.output.verify':\n"
        "            return self.externalizer.verify(str(arguments['artifact_id']))\n"
        "        if name == 'signalcore.output.stats':\n"
        "            return self.externalizer.stats()\n"
        "        if name == 'signalcore.usage.record':\n"
        "            entry = self.usage_ledger.record(\n"
        "                task_id=str(arguments['task_id']), arm_id=str(arguments['arm_id']),\n"
        "                repetition=int(arguments['repetition']), cache_mode=str(arguments['cache_mode']),\n"
        "                provider=str(arguments['provider']), request_id=str(arguments['request_id']),\n"
        "                provider_response=dict(arguments['provider_response']), usage_payload=dict(arguments['usage']),\n"
        "                quota_cost=float(arguments['quota_cost']), hardware_hash=str(arguments['hardware_hash']),\n"
        "            )\n"
        "            return asdict(entry)\n"
        "        if name == 'signalcore.usage.verify':\n"
        "            return self.usage_ledger.verify(require_hmac=bool(arguments.get('require_hmac', False)))\n"
        "        if name == 'signalcore.session.search':\n"
        "            return {'hits': self.session_retriever.serializable(self.session_retriever.search(\n"
        "                str(arguments['session_id']), str(arguments['query']), limit=int(arguments.get('limit', 12)),\n"
        "                include_superseded=bool(arguments.get('include_superseded', False)),\n"
        "            ))}\n"
        "        if name == 'signalcore.session.semantic_context':\n"
        "            return asdict(self.session_retriever.context_pack(\n"
        "                str(arguments['session_id']), str(arguments['query']),\n"
        "                budget_bytes=int(arguments.get('budget_bytes', 8192)),\n"
        "                include_superseded=bool(arguments.get('include_superseded', False)),\n"
        "            ))\n"
        "        if name == \"signalcore.session.open\":\n",
    )
    replace_once(
        "signalcore_runtime/mcp_server.py",
        "                value = self.call_tool(str(params.get(\"name\")), params.get(\"arguments\") or {})\n                result = {\"content\": [{\"type\": \"text\", \"text\": json.dumps(value, ensure_ascii=False, default=str)}]}\n",
        "                tool_name = str(params.get(\"name\"))\n"
        "                arguments = params.get(\"arguments\") or {}\n"
        "                value = self.call_tool(tool_name, arguments)\n"
        "                value = self.output_pipeline.capture_mcp_result(tool_name, arguments, value)\n"
        "                result = {\"content\": [{\"type\": \"text\", \"text\": json.dumps(value, ensure_ascii=False, default=str)}]}\n",
    )


def patch_security() -> None:
    replace_once(
        "signalcore_runtime/tool_externalization_analysis.py",
        "from .tool_externalization_types import (\n",
        "from .security_scan import redact_text, scan_text\n\nfrom .tool_externalization_types import (\n",
    )
    replace_once(
        "signalcore_runtime/tool_externalization_analysis.py",
        "    @staticmethod\n    def _redact(text: str) -> str:\n        return _SECRET.sub(lambda match: f\"{match.group(1)}=<redacted>\", text)\n",
        "    @staticmethod\n    def _redact(text: str) -> str:\n        return redact_text(text)\n",
    )
    replace_once(
        "signalcore_runtime/tool_externalization_analysis.py",
        "            return bool(_ERROR.search(text) or _INJECTION.search(text))\n",
        "            return bool(_ERROR.search(text) or scan_text(text, inspect_encoded=False).injection_risk)\n",
    )
    replace_once(
        "signalcore_runtime/tool_externalization_analysis.py",
        "        injection = bool(_INJECTION.search(text))\n",
        "        injection = scan_text(text, inspect_encoded=False).injection_risk\n",
    )

    replace_once(
        "signalcore_runtime/tool_externalization.py",
        "from .tool_externalization_analysis import ExternalizationAnalysisMixin\n",
        "from .security_scan import scan_bytes\nfrom .tool_externalization_analysis import ExternalizationAnalysisMixin\n",
    )
    replace_once(
        "signalcore_runtime/tool_externalization.py",
        "        facets = self._facets(family, raw, segments, payload.path)\n        injection_risk = bool(_INJECTION.search(raw.decode(\"utf-8\", errors=\"replace\"))) if family != \"binary\" else False\n        summary = self._redact(self._summary(family, raw, facets, segments))\n",
        "        facets = self._facets(family, raw, segments, payload.path)\n"
        "        security = scan_bytes(raw) if family != 'binary' else None\n"
        "        injection_risk = bool(security and security.injection_risk)\n"
        "        summary = self._redact(self._summary(family, raw, facets, segments))\n",
    )
    replace_once(
        "signalcore_runtime/tool_externalization.py",
        "            \"unchanged_segment_ratio\": unchanged_ratio,\n            **payload.metadata,\n",
        "            \"unchanged_segment_ratio\": unchanged_ratio,\n"
        "            \"security_scan\": {\n"
        "                \"secret_types\": list(security.secret_types) if security else [],\n"
        "                \"injection_reasons\": list(security.injection_reasons) if security else [],\n"
        "                \"encoded_payloads_checked\": security.encoded_payloads_checked if security else 0,\n"
        "            },\n"
        "            **payload.metadata,\n",
    )


def main() -> int:
    patch_hooks()
    patch_mcp()
    patch_security()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
