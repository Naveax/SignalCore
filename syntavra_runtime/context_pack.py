from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .competitive_fabric import StructuralNavigator
from .structural import StructuralIndex
from .token_attribution import TokenEstimator
from .util import canonical_json, sha256_bytes


@dataclass(frozen=True)
class ContextPackItem:
    tier: str
    kind: str
    path: str
    start_line: int
    end_line: int
    text: str
    tokens: int
    token_confidence: str
    file_hash: str
    reason: str


@dataclass(frozen=True)
class TaskContextPack:
    query: str
    budget_tokens: int
    used_tokens: int
    items: tuple[ContextPackItem, ...]
    affected_paths: tuple[str, ...]
    affected_tests: tuple[str, ...]
    required_verifiers: tuple[str, ...]
    recoverable_paths: tuple[str, ...]
    pack_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TaskContextAssembler:
    """Assemble minimum exact repository context for one coding task."""

    def __init__(self, index: StructuralIndex, navigator: StructuralNavigator):
        self.index = index
        self.navigator = navigator

    def _item(self, *, tier: str, kind: str, path: str, start: int, end: int, reason: str) -> ContextPackItem:
        source = self.navigator.read_range(path, start_line=start, end_line=end, max_bytes=48 * 1024)
        tokens, confidence = TokenEstimator.text(source["text"])
        return ContextPackItem(
            tier=tier,
            kind=kind,
            path=path,
            start_line=int(source["start_line"]),
            end_line=int(source["end_line"]),
            text=str(source["text"]),
            tokens=tokens,
            token_confidence=confidence,
            file_hash=str(source["file_hash"]),
            reason=reason,
        )

    def assemble(
        self,
        query: str,
        *,
        changed_paths: Iterable[str] = (),
        token_budget: int = 8_000,
        max_depth: int = 4,
    ) -> TaskContextPack:
        if not query.strip():
            raise ValueError("context query is required")
        if token_budget < 256:
            raise ValueError("token_budget must be at least 256")
        self.index.index()
        impact = self.index.inspect_impact(query, max_depth=max_depth)
        changed = tuple(dict.fromkeys(str(path) for path in changed_paths))
        path_impact = self.index.impacted_by_paths(changed, max_depth=max_depth) if changed else {
            "affected_paths": [], "affected_tests": [], "required_verifiers": []
        }
        repository_map = self.index.repository_map(query, token_budget=max(256, token_budget // 3), max_depth=max_depth)

        candidates: list[ContextPackItem] = []
        seen_ranges: set[tuple[str, int, int]] = set()

        for definition in impact.get("definitions", []):
            start = max(1, int(definition.get("line", 1)) - 2)
            end = int(definition.get("end_line") or definition.get("line") or start) + 2
            key = (str(definition["path"]), start, end)
            if key not in seen_ranges:
                candidates.append(self._item(
                    tier="mandatory", kind="definition", path=key[0], start=start, end=end,
                    reason=f"exact definition for {definition.get('qualified_name') or definition.get('name')}",
                ))
                seen_ranges.add(key)

        for row in repository_map.get("selected", []):
            start = max(1, int(row.get("line", 1)) - 1)
            end = int(row.get("end_line") or row.get("line") or start) + 1
            key = (str(row["path"]), start, end)
            if key in seen_ranges:
                continue
            tier = "likely" if row["path"] in impact.get("affected_paths", []) else "optional"
            candidates.append(self._item(
                tier=tier, kind=str(row.get("kind", "symbol")), path=key[0], start=start, end=end,
                reason="graph-ranked affected symbol" if tier == "likely" else "query-ranked repository symbol",
            ))
            seen_ranges.add(key)

        tier_order = {"mandatory": 0, "likely": 1, "optional": 2}
        candidates.sort(key=lambda item: (tier_order[item.tier], item.tokens, item.path, item.start_line))
        selected: list[ContextPackItem] = []
        used = 0
        for item in candidates:
            if used + item.tokens > token_budget and item.tier != "mandatory":
                continue
            if used + item.tokens > token_budget and selected:
                continue
            selected.append(item)
            used += item.tokens

        affected_paths = tuple(sorted(set(impact.get("affected_paths", [])) | set(path_impact.get("affected_paths", []))))
        affected_tests = tuple(sorted(set(impact.get("affected_tests", [])) | set(path_impact.get("affected_tests", []))))
        verifiers = tuple(sorted(set(impact.get("required_verifiers", [])) | set(path_impact.get("required_verifiers", []))))
        included_paths = {item.path for item in selected}
        recoverable = tuple(path for path in affected_paths if path not in included_paths)
        body = {
            "query": query,
            "budget_tokens": token_budget,
            "used_tokens": used,
            "items": [asdict(item) for item in selected],
            "affected_paths": affected_paths,
            "affected_tests": affected_tests,
            "required_verifiers": verifiers,
            "recoverable_paths": recoverable,
        }
        return TaskContextPack(
            query=query,
            budget_tokens=token_budget,
            used_tokens=used,
            items=tuple(selected),
            affected_paths=affected_paths,
            affected_tests=affected_tests,
            required_verifiers=verifiers,
            recoverable_paths=recoverable,
            pack_hash=sha256_bytes(canonical_json(body)),
        )
