from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .adaptive_provider_router import AdaptiveProviderRouter, ProviderCandidate, ProviderRoute
from .state import StateDB
from .util import canonical_json, sha256_bytes

_CREDENTIAL_REFERENCE = re.compile(r"^(?:env|file|keyring|oauth-profile):[A-Za-z0-9_.@/:-]{1,240}$")
_SECRET_SHAPES = re.compile(r"(?i)(?:sk-[A-Za-z0-9_-]{16,}|gh[opusr]_[A-Za-z0-9]{20,}|bearer\s+\S+)")


@dataclass(frozen=True)
class ProviderAccount:
    provider: str
    account: str
    credential_ref: str
    subscription: bool
    priority: int
    quota_remaining: float
    quota_reset_at: float
    rate_limited_until: float
    circuit_open_until: float
    latency_ewma_ms: float
    success_count: int
    failure_count: int
    disabled: bool
    model_allowlist: tuple[str, ...]
    updated_at: float

    @property
    def health_ratio(self) -> float:
        total = self.success_count + self.failure_count
        return 1.0 if total == 0 else self.success_count / total


class ProviderAccountPool:
    """Persistent provider-account health, quota and failover state.

    Only credential *references* are stored. Raw API keys, bearer tokens and OAuth
    access tokens are rejected before persistence.
    """

    schema_version = 1

    def __init__(self, path: Path):
        self.state = StateDB(path)
        with self.state.transaction(immediate=True) as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS provider_accounts(
                    provider TEXT NOT NULL,
                    account TEXT NOT NULL,
                    credential_ref TEXT NOT NULL,
                    subscription INTEGER NOT NULL DEFAULT 0,
                    priority INTEGER NOT NULL DEFAULT 0,
                    quota_remaining REAL NOT NULL DEFAULT 1.0,
                    quota_reset_at REAL NOT NULL DEFAULT 0.0,
                    rate_limited_until REAL NOT NULL DEFAULT 0.0,
                    circuit_open_until REAL NOT NULL DEFAULT 0.0,
                    latency_ewma_ms REAL NOT NULL DEFAULT 0.0,
                    success_count INTEGER NOT NULL DEFAULT 0,
                    failure_count INTEGER NOT NULL DEFAULT 0,
                    consecutive_failures INTEGER NOT NULL DEFAULT 0,
                    disabled INTEGER NOT NULL DEFAULT 0,
                    model_allowlist_json TEXT NOT NULL DEFAULT '[]',
                    updated_at REAL NOT NULL,
                    PRIMARY KEY(provider,account)
                );
                CREATE INDEX IF NOT EXISTS provider_accounts_health_idx
                    ON provider_accounts(provider,disabled,rate_limited_until,circuit_open_until);
                """
            )

    @staticmethod
    def _normalize(provider: str, account: str) -> tuple[str, str]:
        provider_name = provider.strip().casefold()
        account_name = account.strip()
        if not provider_name or not account_name:
            raise ValueError("provider and account are required")
        if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}", provider_name):
            raise ValueError("provider contains unsupported characters")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}", account_name):
            raise ValueError("account contains unsupported characters")
        return provider_name, account_name

    @staticmethod
    def _credential_reference(value: str) -> str:
        reference = value.strip()
        if _SECRET_SHAPES.search(reference) or not _CREDENTIAL_REFERENCE.fullmatch(reference):
            raise ValueError("credential_ref must be a non-secret env/file/keyring/oauth-profile reference")
        return reference

    @staticmethod
    def _row(row) -> ProviderAccount:
        return ProviderAccount(
            provider=str(row["provider"]),
            account=str(row["account"]),
            credential_ref=str(row["credential_ref"]),
            subscription=bool(row["subscription"]),
            priority=int(row["priority"]),
            quota_remaining=float(row["quota_remaining"]),
            quota_reset_at=float(row["quota_reset_at"]),
            rate_limited_until=float(row["rate_limited_until"]),
            circuit_open_until=float(row["circuit_open_until"]),
            latency_ewma_ms=float(row["latency_ewma_ms"]),
            success_count=int(row["success_count"]),
            failure_count=int(row["failure_count"]),
            disabled=bool(row["disabled"]),
            model_allowlist=tuple(json.loads(row["model_allowlist_json"] or "[]")),
            updated_at=float(row["updated_at"]),
        )

    def register(
        self,
        provider: str,
        account: str,
        *,
        credential_ref: str,
        subscription: bool = False,
        priority: int = 0,
        quota_remaining: float = 1.0,
        quota_reset_at: float = 0.0,
        model_allowlist: Iterable[str] = (),
    ) -> ProviderAccount:
        provider_name, account_name = self._normalize(provider, account)
        reference = self._credential_reference(credential_ref)
        quota = min(1.0, max(0.0, float(quota_remaining)))
        models = tuple(sorted(set(str(model).strip() for model in model_allowlist if str(model).strip())))
        now = time.time()
        with self.state.transaction(immediate=True) as db:
            db.execute(
                """
                INSERT INTO provider_accounts(
                    provider,account,credential_ref,subscription,priority,quota_remaining,
                    quota_reset_at,model_allowlist_json,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(provider,account) DO UPDATE SET
                    credential_ref=excluded.credential_ref,
                    subscription=excluded.subscription,
                    priority=excluded.priority,
                    quota_remaining=excluded.quota_remaining,
                    quota_reset_at=excluded.quota_reset_at,
                    model_allowlist_json=excluded.model_allowlist_json,
                    disabled=0,
                    updated_at=excluded.updated_at
                """,
                (
                    provider_name,
                    account_name,
                    reference,
                    int(subscription),
                    int(priority),
                    quota,
                    float(quota_reset_at),
                    json.dumps(models),
                    now,
                ),
            )
        return self.get(provider_name, account_name)

    def get(self, provider: str, account: str) -> ProviderAccount:
        provider_name, account_name = self._normalize(provider, account)
        with self.state.transaction() as db:
            row = db.execute(
                "SELECT * FROM provider_accounts WHERE provider=? AND account=?",
                (provider_name, account_name),
            ).fetchone()
        if row is None:
            raise KeyError(f"{provider_name}/{account_name}")
        return self._row(row)

    def list(self, *, provider: str | None = None) -> list[ProviderAccount]:
        with self.state.transaction() as db:
            if provider:
                rows = db.execute(
                    "SELECT * FROM provider_accounts WHERE provider=? ORDER BY priority DESC,account",
                    (provider.casefold(),),
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT * FROM provider_accounts ORDER BY provider,priority DESC,account"
                ).fetchall()
        return [self._row(row) for row in rows]

    def record_result(
        self,
        provider: str,
        account: str,
        *,
        success: bool,
        latency_ms: float = 0.0,
        quota_remaining: float | None = None,
        quota_reset_at: float | None = None,
        retry_after_seconds: float = 0.0,
        now: float | None = None,
    ) -> ProviderAccount:
        provider_name, account_name = self._normalize(provider, account)
        timestamp = time.time() if now is None else float(now)
        with self.state.transaction(immediate=True) as db:
            row = db.execute(
                "SELECT * FROM provider_accounts WHERE provider=? AND account=?",
                (provider_name, account_name),
            ).fetchone()
            if row is None:
                raise KeyError(f"{provider_name}/{account_name}")
            previous_latency = float(row["latency_ewma_ms"])
            observed_latency = max(0.0, float(latency_ms))
            latency = observed_latency if previous_latency <= 0 else previous_latency * 0.8 + observed_latency * 0.2
            failures = 0 if success else int(row["consecutive_failures"]) + 1
            circuit_open_until = float(row["circuit_open_until"])
            if success:
                circuit_open_until = 0.0
            elif failures >= 3:
                circuit_open_until = max(circuit_open_until, timestamp + min(900.0, 30.0 * (2 ** min(5, failures - 3))))
            rate_limited_until = max(float(row["rate_limited_until"]), timestamp + max(0.0, float(retry_after_seconds)))
            quota = float(row["quota_remaining"]) if quota_remaining is None else min(1.0, max(0.0, float(quota_remaining)))
            reset_at = float(row["quota_reset_at"]) if quota_reset_at is None else float(quota_reset_at)
            db.execute(
                """
                UPDATE provider_accounts SET
                    quota_remaining=?, quota_reset_at=?, rate_limited_until=?, circuit_open_until=?,
                    latency_ewma_ms=?, success_count=success_count+?, failure_count=failure_count+?,
                    consecutive_failures=?, updated_at=?
                WHERE provider=? AND account=?
                """,
                (
                    quota,
                    reset_at,
                    rate_limited_until,
                    circuit_open_until,
                    latency,
                    int(success),
                    int(not success),
                    failures,
                    timestamp,
                    provider_name,
                    account_name,
                ),
            )
        return self.get(provider_name, account_name)

    def candidates(
        self,
        model_rows: Iterable[Mapping[str, Any]],
        *,
        now: float | None = None,
    ) -> list[ProviderCandidate]:
        timestamp = time.time() if now is None else float(now)
        accounts = {(row.provider, row.account): row for row in self.list()}
        candidates: list[ProviderCandidate] = []
        for model_row in model_rows:
            provider = str(model_row.get("provider") or "").casefold()
            model = str(model_row.get("model") or "")
            for (account_provider, _), account in accounts.items():
                if account_provider != provider or account.disabled:
                    continue
                if account.model_allowlist and model not in account.model_allowlist:
                    continue
                reset_quota = 1.0 if account.quota_reset_at and account.quota_reset_at <= timestamp else account.quota_remaining
                candidates.append(
                    ProviderCandidate(
                        provider=provider,
                        model=model,
                        available=account.circuit_open_until <= timestamp,
                        quota_remaining=reset_quota,
                        rate_limited_until=account.rate_limited_until,
                        input_cost_per_million=float(model_row.get("input_cost_per_million", 0.0)),
                        output_cost_per_million=float(model_row.get("output_cost_per_million", 0.0)),
                        latency_ms=account.latency_ewma_ms or float(model_row.get("latency_ms", 0.0)),
                        quality=float(model_row.get("quality", 0.5)) * (0.75 + 0.25 * account.health_ratio),
                        max_complexity=str(model_row.get("max_complexity", "reasoning")),
                        context_window=int(model_row.get("context_window", 0)),
                        account=account.account,
                        subscription=account.subscription,
                        priority=account.priority,
                    )
                )
        return candidates

    def route(
        self,
        task: str,
        model_rows: Iterable[Mapping[str, Any]],
        *,
        changed_files: int = 0,
        token_estimate: int = 0,
        now: float | None = None,
        prefer_subscription: bool = True,
    ) -> ProviderRoute:
        candidates = self.candidates(model_rows, now=now)
        subscriptions = {(row.provider, row.account) for row in self.list() if row.subscription}
        adjusted = [
            ProviderCandidate(
                **(
                    asdict(candidate)
                    | {
                        "input_cost_per_million": 0.0,
                        "output_cost_per_million": 0.0,
                    }
                    if (candidate.provider, candidate.account) in subscriptions and prefer_subscription
                    else asdict(candidate)
                )
            )
            for candidate in candidates
        ]
        return AdaptiveProviderRouter(adjusted).route(
            task,
            changed_files=changed_files,
            token_estimate=token_estimate,
            now=now,
            prefer_subscription=prefer_subscription,
        )

    def receipt(self) -> dict[str, Any]:
        rows = [asdict(row) | {"health_ratio": row.health_ratio} for row in self.list()]
        body = {"schema_version": self.schema_version, "accounts": rows}
        body["receipt_hash"] = sha256_bytes(canonical_json(body))
        return body
