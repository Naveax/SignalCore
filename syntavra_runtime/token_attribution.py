from __future__ import annotations

import json
import math
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .util import canonical_json, sha256_bytes


TOKEN_SOURCES: tuple[str, ...] = (
    "system",
    "skill_description",
    "skill_body",
    "tool_schema",
    "repository_context",
    "tool_output",
    "memory",
    "conversation_history",
    "user_prompt",
    "assistant_output",
    "reasoning",
    "cached",
)

CONFIDENCE_LEVELS: tuple[str, ...] = (
    "PROVIDER_OBSERVED",
    "LOCALLY_TOKENIZED",
    "ESTIMATED",
    "UNKNOWN",
)


@dataclass(frozen=True)
class TokenAttributionReceipt:
    receipt_id: str
    task_id: str
    arm_id: str
    repetition: int
    session_id: str
    provider: str
    model: str
    request_id_hash: str
    provider_receipt_hash: str
    sources: dict[str, int]
    confidence: dict[str, str]
    baseline_tokens: int | None
    baseline_confidence: str
    created_at: float
    receipt_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def observed_tokens(self) -> int:
        return sum(max(0, int(value)) for value in self.sources.values())

    @property
    def avoided_tokens(self) -> int | None:
        if self.baseline_tokens is None:
            return None
        return max(0, int(self.baseline_tokens) - self.observed_tokens)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["observed_tokens"] = self.observed_tokens
        value["avoided_tokens"] = self.avoided_tokens
        return value


class TokenEstimator:
    @staticmethod
    def text(text: str) -> tuple[int, str]:
        try:
            import tiktoken  # type: ignore

            encoder = tiktoken.get_encoding("o200k_base")
            return len(encoder.encode(text)), "LOCALLY_TOKENIZED"
        except (ImportError, KeyError, UnicodeError):
            return max(0, math.ceil(len(text.encode("utf-8")) / 4)), "ESTIMATED"

    @classmethod
    def mapping(cls, values: Mapping[str, str]) -> tuple[dict[str, int], dict[str, str]]:
        sources: dict[str, int] = {}
        confidence: dict[str, str] = {}
        for source, text in values.items():
            if source not in TOKEN_SOURCES:
                raise ValueError(f"unknown token source: {source}")
            count, level = cls.text(str(text))
            sources[source] = count
            confidence[source] = level
        return sources, confidence


class TokenAttributionLedger:
    """Append-only token-source attribution stored beside provider receipts."""

    schema_version = 1

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=30.0, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=30000")
        return db

    @contextmanager
    def _db(self):
        db = self._connect()
        try:
            yield db
        finally:
            db.close()

    def _initialize(self) -> None:
        with self._db() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS token_attribution_receipts(
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id TEXT NOT NULL UNIQUE,
                    task_id TEXT NOT NULL,
                    arm_id TEXT NOT NULL,
                    repetition INTEGER NOT NULL,
                    session_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    request_id_hash TEXT NOT NULL,
                    provider_receipt_hash TEXT NOT NULL,
                    sources_json TEXT NOT NULL,
                    confidence_json TEXT NOT NULL,
                    baseline_tokens INTEGER,
                    baseline_confidence TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    receipt_hash TEXT NOT NULL UNIQUE,
                    UNIQUE(task_id,arm_id,repetition,request_id_hash)
                );
                CREATE INDEX IF NOT EXISTS token_attribution_session_idx
                    ON token_attribution_receipts(session_id,created_at);
                CREATE INDEX IF NOT EXISTS token_attribution_task_idx
                    ON token_attribution_receipts(task_id,arm_id,repetition);
                """
            )

    @staticmethod
    def _normalize_sources(values: Mapping[str, Any]) -> dict[str, int]:
        result = {source: 0 for source in TOKEN_SOURCES}
        for source, value in values.items():
            name = str(source)
            if name not in result:
                raise ValueError(f"unknown token source: {name}")
            count = int(value)
            if count < 0:
                raise ValueError(f"token source must be non-negative: {name}")
            result[name] = count
        if sum(result.values()) <= 0:
            raise ValueError("token attribution contains no positive token counts")
        return result

    @staticmethod
    def _normalize_confidence(values: Mapping[str, Any], sources: Mapping[str, int]) -> dict[str, str]:
        result: dict[str, str] = {}
        for source in TOKEN_SOURCES:
            level = str(values.get(source, "UNKNOWN")).upper()
            if level not in CONFIDENCE_LEVELS:
                raise ValueError(f"unknown confidence level for {source}: {level}")
            if sources.get(source, 0) > 0:
                result[source] = level
        return result

    def record(
        self,
        *,
        task_id: str,
        arm_id: str,
        repetition: int,
        session_id: str,
        provider: str,
        model: str,
        request_id_hash: str,
        provider_receipt_hash: str,
        sources: Mapping[str, Any],
        confidence: Mapping[str, Any],
        baseline_tokens: int | None = None,
        baseline_confidence: str = "UNKNOWN",
        metadata: Mapping[str, Any] | None = None,
    ) -> TokenAttributionReceipt:
        if not task_id or not arm_id or repetition <= 0 or not session_id:
            raise ValueError("token attribution identity is incomplete")
        for field_name, value in (("request_id_hash", request_id_hash), ("provider_receipt_hash", provider_receipt_hash)):
            normalized = str(value).casefold()
            if len(normalized) != 64 or any(ch not in "0123456789abcdef" for ch in normalized):
                raise ValueError(f"{field_name} must be lowercase sha256")
        normalized_sources = self._normalize_sources(sources)
        normalized_confidence = self._normalize_confidence(confidence, normalized_sources)
        if baseline_tokens is not None and int(baseline_tokens) < sum(normalized_sources.values()):
            raise ValueError("baseline_tokens cannot be lower than observed attributed tokens")
        baseline_level = str(baseline_confidence).upper()
        if baseline_level not in CONFIDENCE_LEVELS:
            raise ValueError("invalid baseline confidence")
        created_at = time.time()
        body = {
            "schema_version": self.schema_version,
            "task_id": task_id,
            "arm_id": arm_id,
            "repetition": int(repetition),
            "session_id": session_id,
            "provider": provider,
            "model": model,
            "request_id_hash": request_id_hash,
            "provider_receipt_hash": provider_receipt_hash,
            "sources": normalized_sources,
            "confidence": normalized_confidence,
            "baseline_tokens": baseline_tokens,
            "baseline_confidence": baseline_level,
            "metadata": dict(metadata or {}),
            "created_at": created_at,
        }
        receipt_hash = sha256_bytes(canonical_json(body))
        receipt_id = f"attr-{receipt_hash[:24]}"
        receipt = TokenAttributionReceipt(
            receipt_id=receipt_id,
            task_id=task_id,
            arm_id=arm_id,
            repetition=int(repetition),
            session_id=session_id,
            provider=provider,
            model=model,
            request_id_hash=request_id_hash,
            provider_receipt_hash=provider_receipt_hash,
            sources=normalized_sources,
            confidence=normalized_confidence,
            baseline_tokens=int(baseline_tokens) if baseline_tokens is not None else None,
            baseline_confidence=baseline_level,
            created_at=created_at,
            receipt_hash=receipt_hash,
            metadata=dict(metadata or {}),
        )
        with self._db() as db:
            try:
                db.execute(
                    """
                    INSERT INTO token_attribution_receipts(
                        receipt_id,task_id,arm_id,repetition,session_id,provider,model,
                        request_id_hash,provider_receipt_hash,sources_json,confidence_json,
                        baseline_tokens,baseline_confidence,metadata_json,created_at,receipt_hash
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        receipt.receipt_id, receipt.task_id, receipt.arm_id, receipt.repetition,
                        receipt.session_id, receipt.provider, receipt.model, receipt.request_id_hash,
                        receipt.provider_receipt_hash,
                        json.dumps(receipt.sources, sort_keys=True, separators=(",", ":")),
                        json.dumps(receipt.confidence, sort_keys=True, separators=(",", ":")),
                        receipt.baseline_tokens, receipt.baseline_confidence,
                        json.dumps(receipt.metadata, sort_keys=True, separators=(",", ":"), default=str),
                        receipt.created_at, receipt.receipt_hash,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("duplicate or conflicting token attribution receipt") from exc
        return receipt

    def receipts(self, *, session_id: str | None = None) -> list[TokenAttributionReceipt]:
        sql = "SELECT * FROM token_attribution_receipts"
        params: list[Any] = []
        if session_id:
            sql += " WHERE session_id=?"
            params.append(session_id)
        sql += " ORDER BY sequence"
        with self._db() as db:
            rows = db.execute(sql, params).fetchall()
        result: list[TokenAttributionReceipt] = []
        for row in rows:
            result.append(TokenAttributionReceipt(
                receipt_id=str(row["receipt_id"]), task_id=str(row["task_id"]),
                arm_id=str(row["arm_id"]), repetition=int(row["repetition"]),
                session_id=str(row["session_id"]), provider=str(row["provider"]),
                model=str(row["model"]), request_id_hash=str(row["request_id_hash"]),
                provider_receipt_hash=str(row["provider_receipt_hash"]),
                sources=json.loads(str(row["sources_json"])),
                confidence=json.loads(str(row["confidence_json"])),
                baseline_tokens=int(row["baseline_tokens"]) if row["baseline_tokens"] is not None else None,
                baseline_confidence=str(row["baseline_confidence"]),
                metadata=json.loads(str(row["metadata_json"])),
                created_at=float(row["created_at"]), receipt_hash=str(row["receipt_hash"]),
            ))
        return result

    def summary(self, *, session_id: str | None = None) -> dict[str, Any]:
        rows = self.receipts(session_id=session_id)
        source_totals = {source: 0 for source in TOKEN_SOURCES}
        confidence_counts = {level: 0 for level in CONFIDENCE_LEVELS}
        observed = 0
        baseline = 0
        baseline_rows = 0
        for row in rows:
            observed += row.observed_tokens
            for source, count in row.sources.items():
                source_totals[source] += int(count)
                if count > 0:
                    confidence_counts[row.confidence.get(source, "UNKNOWN")] += 1
            if row.baseline_tokens is not None:
                baseline += row.baseline_tokens
                baseline_rows += 1
        return {
            "schema_version": self.schema_version,
            "receipts": len(rows),
            "session_id": session_id,
            "observed_tokens": observed,
            "baseline_tokens": baseline if baseline_rows == len(rows) and rows else None,
            "avoided_tokens": max(0, baseline - observed) if baseline_rows == len(rows) and rows else None,
            "sources": source_totals,
            "confidence": confidence_counts,
            "claim_boundary": "Provider-observed totals and locally attributed sources remain distinct.",
        }
