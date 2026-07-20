#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "signalcore_runtime" / "tool_externalization.py"


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one compatibility match, found {count}: {old[:100]!r}")
    return text.replace(old, new, 1)


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "from typing import Any, Iterable, Mapping\n",
        "from typing import Any, Iterable, Mapping, Sequence\n",
    )
    text = replace_once(
        text,
        "    EvidenceLike, ExternalizationPolicy, ExternalizedArtifact, RevealPage,\n    SegmentHit, ToolPayload, _INJECTION, _Segment, _canonical, _merkle,\n",
        "    EvidenceLike, ExternalizationPolicy, ExternalizedArtifact, RevealPage, SearchPack,\n    SegmentHit, ToolPayload, _INJECTION, _Segment, _canonical, _merkle,\n",
    )
    old = '''    def search_pack(self, query: str, *, scope_key: str | None = None, artifact_id: str | None = None, budget_bytes: int = 8192, limit: int = 32) -> dict[str, Any]:
        hits = self.search(query, artifact_id=artifact_id, scope_key=scope_key, limit=limit)
        output: list[str] = []
        handles: list[str] = []
        used = 0
        seen: set[tuple[str, int]] = set()
        for hit in hits:
            key = (hit.artifact_id, hit.segment_index)
            if key in seen:
                continue
            seen.add(key)
            section = f"[artifact={hit.artifact_id} segment={hit.segment_index} lines={hit.start_line}-{hit.end_line} kind={hit.kind} score={hit.score:.2f}]\\n{hit.text}"
            encoded = section.encode("utf-8")
            separator = b"\\n---\\n" if output else b""
            if used + len(separator) + len(encoded) > budget_bytes:
                remaining = budget_bytes - used - len(separator)
                if remaining > 80:
                    section = encoded[:remaining].decode("utf-8", errors="ignore")
                    output.append(section); used += len(separator) + len(section.encode("utf-8")); handles.append(hit.segment_handle)
                break
            output.append(section); handles.append(hit.segment_handle); used += len(separator) + len(encoded)
        return {"query": query, "content": "\\n---\\n".join(output), "visible_bytes": used, "segment_handles": handles, "hit_count": len(output), "exact_artifact_handles": sorted({hit.artifact_handle for hit in hits})}
'''
    new = '''    @staticmethod
    def verify_segment_proof(leaf_hash: str, proof: Sequence[Mapping[str, str]], merkle_root: str) -> bool:
        return _verify_merkle_proof(leaf_hash, proof, merkle_root)

    def lineage(self, artifact_id: str, *, limit: int = 128) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        seen: set[str] = set()
        current: str | None = artifact_id
        while current and len(output) < max(1, limit):
            if current in seen:
                raise ValueError("artifact lineage cycle detected")
            seen.add(current)
            value = self.artifact(current)
            output.append({
                "artifact_id": current,
                "baseline_artifact_id": value["baseline_artifact_id"],
                "content_hash": value["content_hash"],
                "mode": value["mode"],
                "original_bytes": value["original_bytes"],
                "created_at": value["created_at"],
            })
            current = value["baseline_artifact_id"]
        return output

    def search_pack(
        self,
        query: str,
        *,
        artifact_id: str | None = None,
        scope_key: str | None = None,
        budget_bytes: int = 4096,
        limit: int = 32,
    ) -> SearchPack:
        if budget_bytes < 256:
            raise ValueError("search pack budget too small")
        hits = self.search(query, artifact_id=artifact_id, scope_key=scope_key, limit=limit)
        sections: list[str] = []
        used = 0
        selected: list[SegmentHit] = []
        fingerprints: set[str] = set()
        complete = True
        for hit in hits:
            normalized = re.sub(r"\\b(?:0x[0-9a-f]+|\\d+(?:\\.\\d+)?)\\b", "<n>", hit.text, flags=re.I)
            fingerprint = _sha256(normalized.encode("utf-8"))
            if fingerprint in fingerprints:
                continue
            fingerprints.add(fingerprint)
            section = (
                f"[artifact={hit.artifact_id} segment={hit.segment_index} "
                f"lines={hit.start_line}-{hit.end_line} kind={hit.kind} score={hit.score:.2f}]\\n"
                f"{self._redact(hit.text)}"
            )
            encoded = section.encode("utf-8")
            separator = b"\\n---\\n" if sections else b""
            if used + len(separator) + len(encoded) > budget_bytes:
                complete = False
                break
            sections.append(section)
            selected.append(hit)
            used += len(separator) + len(encoded)
        content = "\\n---\\n".join(sections)
        return SearchPack(
            query,
            content,
            len(content.encode("utf-8")),
            len(selected),
            tuple(dict.fromkeys(hit.artifact_id for hit in selected)),
            tuple(dict.fromkeys(hit.segment_handle for hit in selected)),
            complete,
        )
'''
    text = replace_once(text, old, new)
    TARGET.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
