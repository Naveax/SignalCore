#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "benchmarks" / "hardening_v3_benchmark.py"
RECEIPTS_ROOT = ROOT / "benchmarks" / "results" / "real-tasks"


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one benchmark match, found {count}: {old!r}")
    return text.replace(old, new, 1)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def replace_strings(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        return replacements.get(value, value)
    if isinstance(value, list):
        return [replace_strings(item, replacements) for item in value]
    if isinstance(value, dict):
        return {
            key: replace_strings(item, replacements)
            for key, item in value.items()
        }
    return value


def seal_receipt(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    artifacts = payload["artifacts"]
    replacements: dict[str, str] = {}

    patch_info = artifacts["patch"]
    patch_path = path.parent / patch_info["path"]
    patch_info["bytes"] = patch_path.stat().st_size
    patch_info["sha256"] = sha256_file(patch_path)

    for row in artifacts["evidence"]:
        source = path.parent / row["path"]
        digest = sha256_file(source)
        destination = source.parent / f"{digest}{source.suffix}"
        if source != destination:
            if destination.exists():
                if sha256_file(destination) != digest:
                    raise RuntimeError(f"evidence destination collision: {destination}")
                source.unlink()
            else:
                os.replace(source, destination)
        old_handle = str(row.get("handle", ""))
        new_handle = f"sc://sha256/{digest}"
        if old_handle:
            replacements[old_handle] = new_handle
        row["path"] = destination.relative_to(path.parent).as_posix()
        row["bytes"] = destination.stat().st_size
        row["sha256"] = digest
        row["handle"] = new_handle

    payload = replace_strings(payload, replacements)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def integrate_benchmark() -> None:
    text = TARGET.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "from signalcore_runtime.readiness_gate import ReadinessEvidence, SignalCoreReadinessGate\n",
        "from signalcore_runtime.readiness_gate import ReadinessEvidence, SignalCoreReadinessGate\n"
        "from signalcore_runtime.real_task_receipts import load_verified_real_tasks\n",
    )
    text = replace_once(
        text,
        "        evidence_gate = ReadinessEvidence(\n",
        "        real_tasks = load_verified_real_tasks(\n"
        "            ROOT / 'benchmarks' / 'results' / 'real-tasks'\n"
        "        )\n\n"
        "        evidence_gate = ReadinessEvidence(\n",
    )
    text = replace_once(
        text,
        "            real_repository_tasks=0,\n",
        "            real_repository_tasks=real_tasks['verified_count'],\n",
    )
    text = replace_once(
        text,
        '            "boundary": "Internal hardening benchmark. Real repository tasks and external competitor arms are intentionally zero and cannot satisfy the 10/10 gate.",\n',
        '            "boundary": "Internal hardening benchmark with cryptographically verified real-task receipts. External competitor arms remain zero, so superiority is not proven.",\n',
    )
    text = replace_once(
        text,
        '            "externalization_stats": stats,\n',
        '            "externalization_stats": stats,\n'
        '            "real_repository_tasks": real_tasks,\n',
    )
    TARGET.write_text(text, encoding="utf-8")


def main() -> int:
    for receipt in sorted(RECEIPTS_ROOT.glob("*/receipt.json")):
        seal_receipt(receipt)
    integrate_benchmark()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
