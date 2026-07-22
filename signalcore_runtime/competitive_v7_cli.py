from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .competitive_runtime_v7 import (
    CompetitiveRuntimeV7,
    ContextIRItem,
    SecretlessProviderGatewayV2,
    UniversalAdapterRegistryV2,
    manifest,
)

ACTIONS = {
    "competitive-status", "competitive-doctor", "competitive-manifest",
    "context-compile", "output-capture",
    "artifact-put", "artifact-query", "artifact-verify", "artifact-stats",
    "graph-index", "graph-query", "graph-impact",
    "memory-open", "memory-append", "memory-compact", "memory-retrieve",
    "memory-checkpoint", "memory-fork", "memory-merge", "memory-restore", "memory-verify",
    "capability-decide", "capability-issue", "capability-verify",
    "gateway-plan", "adapters", "agent-plan",
}


def _load(value: str) -> Any:
    path = Path(value)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(value)


def add_run_subcommands(run_sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    run_sub.add_parser("competitive-status")
    run_sub.add_parser("competitive-doctor")
    run_sub.add_parser("competitive-manifest")

    context = run_sub.add_parser("context-compile")
    context.add_argument("items", help="JSON list or path")
    context.add_argument("--provider", default="generic")
    context.add_argument("--model", default="unknown")
    context.add_argument("--budget", type=int, default=32000)
    context.add_argument("--previous", default="{}")

    output = run_sub.add_parser("output-capture")
    output.add_argument("tool")
    output.add_argument("input", help="text file path or literal text")
    output.add_argument("--exit-code", type=int, default=0)
    output.add_argument("--duration-ms", type=float, default=0.0)
    output.add_argument("--media-type", default="text/plain")

    artifact_put = run_sub.add_parser("artifact-put")
    artifact_put.add_argument("input")
    artifact_put.add_argument("--kind", default="generic")
    artifact_put.add_argument("--media-type", default="text/plain")
    artifact_query = run_sub.add_parser("artifact-query")
    artifact_query.add_argument("artifact_id")
    artifact_query.add_argument("--mode", choices=("head", "tail", "errors", "failures", "regex", "json"), default="head")
    artifact_query.add_argument("--expression", default="")
    artifact_query.add_argument("--limit", type=int, default=80)
    artifact_verify = run_sub.add_parser("artifact-verify")
    artifact_verify.add_argument("artifact_id", nargs="?")
    run_sub.add_parser("artifact-stats")

    graph_index = run_sub.add_parser("graph-index")
    graph_index.add_argument("--max-file-bytes", type=int, default=2_000_000)
    graph_query = run_sub.add_parser("graph-query")
    graph_query.add_argument("query")
    graph_query.add_argument("--limit", type=int, default=20)
    graph_impact = run_sub.add_parser("graph-impact")
    graph_impact.add_argument("node_id")
    graph_impact.add_argument("--max-depth", type=int, default=6)

    memory_open = run_sub.add_parser("memory-open")
    memory_open.add_argument("--session-id")
    memory_open.add_argument("--parent", action="append", default=[])
    memory_open.add_argument("--metadata", default="{}")
    memory_append = run_sub.add_parser("memory-append")
    memory_append.add_argument("session_id")
    memory_append.add_argument("event_type")
    memory_append.add_argument("payload")
    memory_compact = run_sub.add_parser("memory-compact")
    memory_compact.add_argument("session_id")
    memory_compact.add_argument("--view", action="append", default=[])
    memory_retrieve = run_sub.add_parser("memory-retrieve")
    memory_retrieve.add_argument("session_id")
    memory_retrieve.add_argument("query")
    memory_retrieve.add_argument("--limit", type=int, default=12)
    memory_checkpoint = run_sub.add_parser("memory-checkpoint")
    memory_checkpoint.add_argument("session_id")
    memory_checkpoint.add_argument("--label", default="")
    memory_fork = run_sub.add_parser("memory-fork")
    memory_fork.add_argument("session_id")
    memory_fork.add_argument("--label", default="")
    memory_merge = run_sub.add_parser("memory-merge")
    memory_merge.add_argument("session_id", nargs="+")
    memory_merge.add_argument("--label", default="")
    memory_restore = run_sub.add_parser("memory-restore")
    memory_restore.add_argument("checkpoint_id")
    memory_verify = run_sub.add_parser("memory-verify")
    memory_verify.add_argument("session_id")

    capability_decide = run_sub.add_parser("capability-decide")
    capability_decide.add_argument("tool")
    capability_decide.add_argument("arguments")
    capability_decide.add_argument("--resource", default="workspace:/")
    capability_decide.add_argument("--sandboxed", action="store_true")
    capability_decide.add_argument("--user-authorized", action="store_true")
    capability_decide.add_argument("--network-host", action="append", default=[])
    capability_issue = run_sub.add_parser("capability-issue")
    capability_issue.add_argument("session_id")
    capability_issue.add_argument("tool")
    capability_issue.add_argument("arguments")
    capability_issue.add_argument("--resource", default="workspace:/")
    capability_issue.add_argument("--permission", action="append", default=[])
    capability_issue.add_argument("--ttl", type=int, default=300)
    capability_issue.add_argument("--reusable", action="store_true")
    capability_verify = run_sub.add_parser("capability-verify")
    capability_verify.add_argument("token")
    capability_verify.add_argument("tool")
    capability_verify.add_argument("arguments")
    capability_verify.add_argument("--resource", default="workspace:/")
    capability_verify.add_argument("--no-consume", action="store_true")

    gateway = run_sub.add_parser("gateway-plan")
    gateway.add_argument("provider")
    gateway.add_argument("--upstream", default="")
    gateway.add_argument("--credential-source", default="os-broker")

    adapters = run_sub.add_parser("adapters")
    adapters.add_argument("--detect", action="store_true")

    agent = run_sub.add_parser("agent-plan")
    agent.add_argument("task")
    agent.add_argument("--session-id")
    agent.add_argument("--max-symbols", type=int, default=12)
    agent.add_argument("--index", action="store_true")


def _input(value: str) -> str:
    path = Path(value)
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else value


def handle(args: argparse.Namespace, *, project: Path, state: Path) -> dict[str, Any] | None:
    if getattr(args, "action", "") not in ACTIONS:
        return None
    runtime = CompetitiveRuntimeV7(project, state / "competitive-v7")
    action = args.action
    if action == "competitive-status":
        return runtime.status()
    if action == "competitive-doctor":
        return runtime.doctor()
    if action == "competitive-manifest":
        return manifest()
    if action == "context-compile":
        rows = _load(args.items)
        if not isinstance(rows, list):
            raise ValueError("context items must be a JSON list")
        items = [ContextIRItem(**row) for row in rows]
        previous = _load(args.previous)
        if not isinstance(previous, dict):
            raise ValueError("previous context must be a JSON object")
        return asdict(runtime.context.compile(items, provider=args.provider, model=args.model, budget_tokens=args.budget, previous=previous))
    if action == "output-capture":
        return asdict(runtime.firewall.capture(args.tool, _input(args.input), exit_code=args.exit_code, duration_ms=args.duration_ms, media_type=args.media_type))
    if action == "artifact-put":
        return asdict(runtime.artifacts.put(_input(args.input), media_type=args.media_type, kind=args.kind))
    if action == "artifact-query":
        return runtime.artifacts.query(args.artifact_id, mode=args.mode, expression=args.expression, limit=args.limit)
    if action == "artifact-verify":
        return runtime.artifacts.verify(args.artifact_id)
    if action == "artifact-stats":
        return runtime.artifacts.stats()
    if action == "graph-index":
        return runtime.graph.index_repository(project, max_file_bytes=args.max_file_bytes)
    if action == "graph-query":
        return {"query": args.query, "results": runtime.graph.query(args.query, limit=args.limit)}
    if action == "graph-impact":
        return runtime.graph.impact(args.node_id, max_depth=args.max_depth)
    if action == "memory-open":
        metadata = _load(args.metadata)
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")
        return runtime.memory.open(args.session_id, parents=args.parent, metadata=metadata)
    if action == "memory-append":
        payload = _load(args.payload)
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        return runtime.memory.append(args.session_id, args.event_type, payload)
    if action == "memory-compact":
        return runtime.memory.compact(args.session_id, views=args.view or None)
    if action == "memory-retrieve":
        return runtime.memory.retrieve(args.session_id, args.query, limit=args.limit)
    if action == "memory-checkpoint":
        return runtime.memory.checkpoint(args.session_id, args.label)
    if action == "memory-fork":
        return runtime.memory.fork(args.session_id, label=args.label)
    if action == "memory-merge":
        return runtime.memory.merge(args.session_id, label=args.label)
    if action == "memory-restore":
        return runtime.memory.restore(args.checkpoint_id)
    if action == "memory-verify":
        return runtime.memory.verify(args.session_id)
    if action == "capability-decide":
        arguments = _load(args.arguments)
        return asdict(runtime.security.decide(args.tool, arguments, resource=args.resource, sandboxed=args.sandboxed, user_authorized=args.user_authorized, network_allowlist=args.network_host))
    if action == "capability-issue":
        arguments = _load(args.arguments)
        token = runtime.security.issue(session_id=args.session_id, tool=args.tool, arguments=arguments, resource=args.resource, permissions=args.permission, ttl_seconds=args.ttl, single_use=not args.reusable)
        return {"ok": True, "token": token, "single_use": not args.reusable}
    if action == "capability-verify":
        arguments = _load(args.arguments)
        return runtime.security.verify(args.token, tool=args.tool, arguments=arguments, resource=args.resource, consume=not args.no_consume)
    if action == "gateway-plan":
        return SecretlessProviderGatewayV2.plan(args.provider, upstream=args.upstream, credential_source=args.credential_source)
    if action == "adapters":
        return {"validation": UniversalAdapterRegistryV2.validate(), "adapters": UniversalAdapterRegistryV2.detect(project=project) if args.detect else UniversalAdapterRegistryV2.records()}
    if action == "agent-plan":
        if args.index:
            runtime.graph.index_repository(project)
        return runtime.agent.plan(args.task, session_id=args.session_id, max_symbols=args.max_symbols)
    raise RuntimeError(action)
