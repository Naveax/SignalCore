from __future__ import annotations

import base64
import hashlib
import hmac
import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .errors import ActivationError, ReplayDetected

PROFILE_ID = "roblox_studio"
PROFILE_VERSION = "0.0.1"
ENVELOPE_SCHEMA_VERSION = 2
HOST = "roblox_studio"
TRANSPORT = "roblox_studio_bridge"
_MAX_ENVELOPE_BYTES = 16_384
_REQUIRED_FIELDS = {
    "schema_version", "profile_id", "profile_version", "host", "transport",
    "transport_identity", "studio_session_id", "place_id", "project_id",
    "project_fingerprint", "studio_process_id", "capabilities", "issued_at",
    "expires_at", "nonce", "signature",
}


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_payload(payload: Mapping[str, Any], key: bytes) -> str:
    if len(key) < 32:
        raise ActivationError("pairing key must contain at least 32 bytes")
    return _b64e(hmac.new(key, _canonical(payload), hashlib.sha256).digest())


@dataclass(frozen=True, slots=True)
class AuthorizedSession:
    session_id: str
    place_id: str
    project_id: str
    project_fingerprint: str
    studio_process_id: int
    capabilities: tuple[str, ...]
    transport_identity: str
    issued_at: int
    expires_at: int
    nonce: str


class ReplayStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def consume(self, nonce: str, session_id: str, expires_at: int, now: int) -> None:
        nonce_hash = hashlib.sha256(nonce.encode("utf-8")).hexdigest()
        connection = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA busy_timeout=15000")
            connection.execute("CREATE TABLE IF NOT EXISTS nonces(hash TEXT PRIMARY KEY, session_id TEXT NOT NULL, expires_at INTEGER NOT NULL, consumed_at INTEGER NOT NULL)")
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM nonces WHERE expires_at < ?", (now - 300,))
            try:
                connection.execute("INSERT INTO nonces VALUES(?,?,?,?)", (nonce_hash, session_id, expires_at, now))
            except sqlite3.IntegrityError as exc:
                connection.execute("ROLLBACK")
                raise ReplayDetected("activation nonce was already consumed") from exc
            connection.execute("COMMIT")
        finally:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            connection.close()


def mint_envelope(
    *, key: bytes, session_id: str, place_id: str, project_id: str,
    project_fingerprint: str, studio_process_id: int, capabilities: Iterable[str],
    transport_identity: str, now: int | None = None, ttl_seconds: int = 60,
    nonce: str | None = None,
) -> dict[str, Any]:
    if not 1 <= ttl_seconds <= 120:
        raise ActivationError("ttl_seconds must be in [1, 120]")
    issued = int(time.time()) if now is None else int(now)
    payload = {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "profile_id": PROFILE_ID,
        "profile_version": PROFILE_VERSION,
        "host": HOST,
        "transport": TRANSPORT,
        "transport_identity": str(transport_identity),
        "studio_session_id": str(session_id),
        "place_id": str(place_id),
        "project_id": str(project_id),
        "project_fingerprint": str(project_fingerprint),
        "studio_process_id": int(studio_process_id),
        "capabilities": sorted(set(map(str, capabilities))),
        "issued_at": issued,
        "expires_at": issued + ttl_seconds,
        "nonce": nonce or hashlib.sha256(f"{session_id}:{issued}:{time.time_ns()}".encode()).hexdigest(),
    }
    return {**payload, "signature": sign_payload(payload, key)}


def verify_envelope(
    envelope: Mapping[str, Any] | None, *, key: bytes, replay_store: ReplayStore,
    allowed_capabilities: Iterable[str], expected_transport_identity: str,
    expected_process_id: int, expected_place_id: str, expected_project_id: str,
    expected_project_fingerprint: str, process_attestor: Callable[[int], bool],
    now: int | None = None, clock_skew_seconds: int = 5,
) -> AuthorizedSession:
    if not envelope:
        raise ActivationError("signed Roblox Studio activation envelope required")
    try:
        encoded_size = len(json.dumps(envelope, ensure_ascii=False).encode("utf-8"))
    except (TypeError, ValueError) as exc:
        raise ActivationError("activation envelope is not JSON serializable") from exc
    if encoded_size > _MAX_ENVELOPE_BYTES:
        raise ActivationError("activation envelope is oversized")
    if set(envelope) != _REQUIRED_FIELDS:
        raise ActivationError("activation envelope fields are invalid")
    payload = {key_name: envelope[key_name] for key_name in envelope if key_name != "signature"}
    supplied = str(envelope["signature"])
    if not hmac.compare_digest(supplied, sign_payload(payload, key)):
        raise ActivationError("activation signature mismatch")
    if payload["schema_version"] != ENVELOPE_SCHEMA_VERSION:
        raise ActivationError("unsupported activation schema")
    if payload["profile_id"] != PROFILE_ID or payload["profile_version"] != PROFILE_VERSION:
        raise ActivationError("cross-profile activation rejected")
    if payload["host"] != HOST or payload["transport"] != TRANSPORT:
        raise ActivationError("ordinary CLI or IDE activation is forbidden")
    if payload["transport_identity"] != expected_transport_identity:
        raise ActivationError("transport identity mismatch")
    current = int(time.time()) if now is None else int(now)
    issued, expires = int(payload["issued_at"]), int(payload["expires_at"])
    if issued > current + clock_skew_seconds:
        raise ActivationError("activation was issued in the future")
    if expires < current - clock_skew_seconds:
        raise ActivationError("activation expired")
    if expires <= issued or expires - issued > 120:
        raise ActivationError("activation TTL is invalid")
    process_id = int(payload["studio_process_id"])
    if process_id != expected_process_id or not process_attestor(process_id):
        raise ActivationError("Studio process attestation failed")
    if str(payload["place_id"]) != str(expected_place_id):
        raise ActivationError("place identity mismatch")
    if str(payload["project_id"]) != str(expected_project_id):
        raise ActivationError("project identity mismatch")
    if str(payload["project_fingerprint"]) != str(expected_project_fingerprint):
        raise ActivationError("project fingerprint mismatch")
    capabilities_raw = payload["capabilities"]
    if not isinstance(capabilities_raw, list) or len(capabilities_raw) > 64:
        raise ActivationError("malformed capability set")
    capabilities = tuple(sorted(set(map(str, capabilities_raw))))
    if not capabilities or not set(capabilities).issubset(set(map(str, allowed_capabilities))):
        raise ActivationError("capability escalation rejected")
    nonce = str(payload["nonce"])
    session_id = str(payload["studio_session_id"])
    if min(len(nonce), len(session_id), len(str(payload["project_fingerprint"]))) < 8:
        raise ActivationError("activation identity fields are incomplete")
    replay_store.consume(nonce, session_id, expires, current)
    return AuthorizedSession(
        session_id=session_id,
        place_id=str(payload["place_id"]),
        project_id=str(payload["project_id"]),
        project_fingerprint=str(payload["project_fingerprint"]),
        studio_process_id=process_id,
        capabilities=capabilities,
        transport_identity=str(payload["transport_identity"]),
        issued_at=issued,
        expires_at=expires,
        nonce=nonce,
    )
