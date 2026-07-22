#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

from signalcore_runtime.competitive_runtime_v7 import CompetitiveRuntimeV7, ContextIRItem


def timed(callable_):
    started = time.perf_counter()
    value = callable_()
    return value, (time.perf_counter() - started) * 1000.0


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        project = root / "repo"
        project.mkdir()
        for index in range(60):
            next_name = f"f{index + 1}" if index < 59 else "leaf"
            (project / f"module_{index}.py").write_text(
                f"def f{index}(value):\n    return {next_name}(value) if value else {index}\n",
                encoding="utf-8",
            )
        runtime = CompetitiveRuntimeV7(project, root / "state")

        log = "\n".join(["test_example ... ok"] * 5000 + ["FAILED tests/test_example.py:42 assertion error"])
        firewall, firewall_ms = timed(lambda: runtime.firewall.capture("pytest", log, exit_code=1))

        items = [
            ContextIRItem("system", "system", "text", "system", "Safety policy\n" * 100, 1.0, True),
            ContextIRItem("repo", "repository", "source", "repo-map", "\n".join(f"module_{i}.py f{i}" for i in range(60)) * 20, 0.8, True),
            ContextIRItem("tool", "task", "diagnostic", "pytest", log, 1.0, False),
            ContextIRItem("user", "user", "text", "user", "Fix the failing assertion", 1.0, False),
        ]
        context, context_ms = timed(lambda: runtime.context.compile(items, provider="openai", model="benchmark", budget_tokens=4096))
        raw_tokens = sum(max(1, len(item.content.encode("utf-8")) // 4) for item in items)

        graph, graph_ms = timed(lambda: runtime.graph.index_repository(project))
        query, query_ms = timed(lambda: runtime.graph.query("f42", limit=10))

        session = runtime.memory.open("benchmark", metadata={"goal": "repair"})
        for index in range(200):
            kind = "test-failure" if index % 19 == 0 else "decision" if index % 7 == 0 else "change"
            runtime.memory.append(session["session_id"], kind, {"index": index, "file": f"module_{index % 60}.py", "error": "boom" if kind == "test-failure" else ""})
        compact, compact_ms = timed(lambda: runtime.memory.compact(session["session_id"]))
        retrieval, retrieval_ms = timed(lambda: runtime.memory.retrieve(session["session_id"], "boom module_19"))

        decisions, decision_ms = timed(lambda: [
            runtime.security.decide("terminal.exec", {"argv": ["pytest", "-q"]}, sandboxed=True, user_authorized=True)
            for _ in range(1000)
        ])

        result = {
            "version": "0.0.1",
            "channel": "pre-release",
            "claim": "INTERNAL_FUNCTIONAL_MEASUREMENT_ONLY",
            "external_superiority": False,
            "firewall": {
                **asdict(firewall),
                "wall_time_ms": firewall_ms,
            },
            "context": {
                "raw_estimated_tokens": raw_tokens,
                "compiled_tokens": context.used_tokens,
                "reduction_ratio": 1.0 - context.used_tokens / max(1, raw_tokens),
                "omitted_items": len(context.omitted),
                "artifact_count": len(context.artifacts),
                "wall_time_ms": context_ms,
            },
            "graph": {
                **graph,
                "query_results": len(query),
                "index_wall_time_ms": graph_ms,
                "query_wall_time_ms": query_ms,
            },
            "memory": {
                "events": compact["events"],
                "summary_views": len(compact["summaries"]),
                "retrieval_results": len(retrieval["results"]),
                "compact_wall_time_ms": compact_ms,
                "retrieval_wall_time_ms": retrieval_ms,
                "exact_recovery": retrieval["exact_recovery"],
            },
            "security": {
                "decisions": len(decisions),
                "allowed": sum(item.allowed for item in decisions),
                "wall_time_ms": decision_ms,
            },
            "adapters": runtime.status()["adapters"],
        }
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
