#!/usr/bin/env python3
from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

PROFILE_ID = "roblox_studio"
PROFILE_VERSION = "0.0.1"
HOST = "roblox_studio"
TRANSPORT = "roblox_studio_bridge"


class RobloxProfileActivationError(RuntimeError):
    code = "ROBLOX_PROFILE_ACTIVATION_FAILED"


class ProfileLockedError(RobloxProfileActivationError):
    code = "ROBLOX_STUDIO_MODE_REQUIRED"


class InvalidActivationEnvelope(RobloxProfileActivationError):
    code = "INVALID_ROBLOX_STUDIO_SESSION"


class ReplayDetected(RobloxProfileActivationError):
    code = "ROBLOX_STUDIO_SESSION_REPLAY"


@dataclass(frozen=True)
class AuthorizedRobloxStudioSession:
    profile_id: str
    profile_version: str
    studio_session_id: str
    place_id: str
    project_fingerprint: str
    studio_pid: int
    capabilities: tuple[str, ...]
    issued_at: int
    expires_at: int
    nonce: str
    issuer: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64d(text: str) -> bytes:
    try:
        return base64.urlsafe_b64decode((text + "=" * (-len(text) % 4)).encode("ascii"))
    except Exception as exc:
        raise InvalidActivationEnvelope("invalid base64") from exc


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def pairing_key_path(state_root: Path) -> Path:
    return state_root.expanduser().resolve(strict=False) / "roblox_studio" / "pairing.key"


def create_pairing_key(state_root: Path) -> Path:
    path = pairing_key_path(state_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="ascii", newline="\n") as handle:
            handle.write(_b64e(secrets.token_bytes(48)) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


def load_pairing_key(state_root: Path) -> bytes:
    path = pairing_key_path(state_root)
    if not path.is_file():
        raise ProfileLockedError("Roblox Studio bridge is not paired")
    if os.name != "nt" and (path.stat().st_mode & 0o077):
        raise ProfileLockedError("pairing key permissions are not private")
    key = _b64d(path.read_text(encoding="ascii").strip())
    if len(key) < 32:
        raise ProfileLockedError("pairing key is too short")
    return key


def sign_payload(payload: dict[str, Any], key: bytes) -> str:
    return _b64e(hmac.new(key, _canonical(payload), hashlib.sha256).digest())


def mint_studio_envelope(
    *, key: bytes, studio_session_id: str, place_id: str,
    project_fingerprint: str, studio_pid: int, capabilities: Iterable[str],
    ttl_seconds: int = 60, now: int | None = None,
) -> dict[str, Any]:
    if not 1 <= ttl_seconds <= 120:
        raise ValueError("ttl_seconds must be between 1 and 120")
    issued = int(time.time()) if now is None else int(now)
    payload: dict[str, Any] = {
        "profile_id": PROFILE_ID,
        "profile_version": PROFILE_VERSION,
        "host": HOST,
        "transport": TRANSPORT,
        "issuer": TRANSPORT,
        "studio_session_id": str(studio_session_id),
        "place_id": str(place_id),
        "project_fingerprint": str(project_fingerprint),
        "studio_pid": int(studio_pid),
        "capabilities": sorted(set(map(str, capabilities))),
        "issued_at": issued,
        "expires_at": issued + ttl_seconds,
        "nonce": secrets.token_urlsafe(24),
    }
    return {**payload, "signature": sign_payload(payload, key)}


def _process_name(pid: int) -> str:
    if pid <= 0:
        return ""
    if sys.platform.startswith("linux"):
        path = Path("/proc") / str(pid) / "comm"
        return path.read_text(encoding="utf-8", errors="replace").strip() if path.is_file() else ""
    if sys.platform == "darwin":
        result = subprocess.run(["ps", "-p", str(pid), "-o", "comm="], capture_output=True, text=True, timeout=3, check=False)
        return Path(result.stdout.strip()).name if result.returncode == 0 else ""
    if os.name == "nt":
        result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=3, check=False)
        if result.returncode == 0 and result.stdout.strip() and not result.stdout.lstrip().startswith("INFO:"):
            try:
                return next(csv.reader([result.stdout.strip().splitlines()[0]]))[0]
            except Exception:
                return ""
    return ""


class NonceStore:
    def __init__(self, state_root: Path) -> None:
        self.path = state_root.expanduser().resolve(strict=False) / "roblox_studio" / "activation.db"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def consume(self, nonce: str, session_id: str, expires_at: int, now: int) -> None:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute("PRAGMA busy_timeout=10000")
            connection.execute("CREATE TABLE IF NOT EXISTS used_nonces(nonce_hash TEXT PRIMARY KEY,session_id TEXT NOT NULL,expires_at INTEGER NOT NULL,consumed_at INTEGER NOT NULL)")
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM used_nonces WHERE expires_at < ?", (now - 300,))
            try:
                connection.execute("INSERT INTO used_nonces VALUES(?,?,?,?)", (hashlib.sha256(nonce.encode()).hexdigest(), session_id, expires_at, now))
            except sqlite3.IntegrityError as exc:
                connection.execute("ROLLBACK")
                raise ReplayDetected("activation nonce was already used") from exc
            connection.execute("COMMIT")
        finally:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            connection.close()


def verify_studio_envelope(
    envelope: dict[str, Any] | None, *, state_root: Path,
    allowed_capabilities: Iterable[str], accepted_process_names: Iterable[str],
    maximum_ttl_seconds: int = 120, clock_skew_seconds: int = 5,
    require_process_attestation: bool = True, now: int | None = None,
) -> AuthorizedRobloxStudioSession:
    if not envelope:
        raise ProfileLockedError("signed Roblox Studio session required")
    required = {"profile_id", "profile_version", "host", "transport", "issuer", "studio_session_id", "place_id", "project_fingerprint", "studio_pid", "capabilities", "issued_at", "expires_at", "nonce", "signature"}
    if set(envelope) != required:
        raise InvalidActivationEnvelope("invalid envelope fields")
    payload = {key: envelope[key] for key in envelope if key != "signature"}
    if not hmac.compare_digest(str(envelope["signature"]), sign_payload(payload, load_pairing_key(state_root))):
        raise InvalidActivationEnvelope("signature mismatch")
    if payload["profile_id"] != PROFILE_ID or payload["profile_version"] != PROFILE_VERSION:
        raise InvalidActivationEnvelope("wrong profile identity")
    if payload["host"] != HOST or payload["transport"] != TRANSPORT or payload["issuer"] != TRANSPORT:
        raise ProfileLockedError("activation is not from Roblox Studio bridge")
    current = int(time.time()) if now is None else int(now)
    issued, expires = int(payload["issued_at"]), int(payload["expires_at"])
    if issued > current + clock_skew_seconds or expires < current - clock_skew_seconds:
        raise InvalidActivationEnvelope("activation time is invalid")
    if expires <= issued or expires - issued > maximum_ttl_seconds:
        raise InvalidActivationEnvelope("activation ttl is invalid")
    identities = [str(payload[key]).strip() for key in ("studio_session_id", "place_id", "project_fingerprint", "nonce")]
    if min(map(len, identities)) < 8:
        raise InvalidActivationEnvelope("Studio/project identity is missing")
    capabilities = tuple(sorted(set(map(str, payload["capabilities"]))))
    if not capabilities or not set(capabilities).issubset(set(map(str, allowed_capabilities))):
        raise InvalidActivationEnvelope("forbidden capabilities requested")
    studio_pid = int(payload["studio_pid"])
    if require_process_attestation:
        accepted = {Path(value).name.casefold() for value in accepted_process_names}
        if Path(_process_name(studio_pid)).name.casefold() not in accepted:
            raise ProfileLockedError("Roblox Studio process attestation failed")
    NonceStore(state_root).consume(identities[3], identities[0], expires, current)
    return AuthorizedRobloxStudioSession(PROFILE_ID, PROFILE_VERSION, identities[0], identities[1], identities[2], studio_pid, capabilities, issued, expires, identities[3], TRANSPORT)
