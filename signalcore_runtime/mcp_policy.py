from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from .release_identity import CHANNEL, VERSION
from .util import canonical_json, sha256_bytes


PROFILE_ALIASES: dict[str, str] = {
    "minimal": "tiny",
    "balanced": "optimized",
    "audit": "full",
    "tiny": "tiny",
    "optimized": "optimized",
    "full": "full",
    "auto": "auto",
}


@dataclass(frozen=True)
class MCPAuthorizationDecision:
    allowed: bool
    tool: str
    profile: str
    legacy_profile: str
    risk: str
    reason: str
    listed: bool
    user_authorized: bool
    exact_evidence: bool
    sandboxed: bool
    receipt_hash: str


class MCPToolPolicy:
    """Fail-closed MCP visibility and call authorization.

    Tool discovery is not treated as security. Every tools/call request is checked
    against the currently exposed catalog and then against operation risk.
    """

    SAFE_STATE_WRITES = {
        "signalcore.session.open",
        "signalcore.session.append",
        "signalcore.session.compact",
        "signalcore.session.checkpoint",
        "signalcore.session.fork",
        "signalcore.session.merge",
        "signalcore.output.capture",
        "signalcore.usage.record",
    }
    SANDBOX_EXECUTION = {
        "signalcore.sandbox.execute",
        "signalcore.sandbox.batch",
    }
    UNSANDBOXED_EXECUTION = {
        "signalcore.process.submit",
    }
    DESTRUCTIVE_EXACT = {
        "signalcore.evidence.rotate_key",
        "signalcore.backup.create",
    }

    def __init__(self, profile: str | None = None):
        requested = (profile or os.environ.get("SIGNALCORE_MCP_PROFILE", "minimal")).strip().casefold() or "minimal"
        if requested not in PROFILE_ALIASES:
            raise ValueError(f"unknown SignalCore MCP profile: {requested}")
        self.profile = requested
        self.legacy_profile = PROFILE_ALIASES[requested]

    @staticmethod
    def normalize_profile(profile: str) -> str:
        value = profile.strip().casefold()
        if value not in PROFILE_ALIASES:
            raise ValueError(f"unknown SignalCore MCP profile: {profile}")
        return PROFILE_ALIASES[value]

    @staticmethod
    def _authorization(arguments: Mapping[str, Any]) -> tuple[bool, bool, bool]:
        raw = arguments.get("_signalcore_authorization") or {}
        if not isinstance(raw, Mapping):
            raw = {}
        user_authorized = bool(raw.get("user_authorized") or arguments.get("_approved"))
        exact_evidence = bool(raw.get("exact_evidence", True))
        sandboxed = bool(raw.get("sandboxed", False))
        return user_authorized, exact_evidence, sandboxed

    @classmethod
    def risk(cls, tool: str, arguments: Mapping[str, Any]) -> str:
        if tool in cls.SAFE_STATE_WRITES:
            return "safe-state-write"
        if tool in cls.SANDBOX_EXECUTION:
            return "sandbox-execute"
        if tool in cls.UNSANDBOXED_EXECUTION:
            return "unsandboxed-execute"
        if tool in cls.DESTRUCTIVE_EXACT:
            return "destructive"
        if tool == "signalcore.evidence.gc" and not bool(arguments.get("dry_run", True)):
            return "destructive"
        if any(part in tool for part in ("provider.invoke", "provider.request", "network.")):
            return "network"
        if any(part in tool for part in (".install", ".uninstall", ".rollback", ".migrate", ".apply")):
            return "destructive"
        return "read-or-plan"

    def authorize(
        self,
        tool: str,
        arguments: Mapping[str, Any],
        *,
        exposed_tools: Iterable[str],
    ) -> MCPAuthorizationDecision:
        exposed = {str(item) for item in exposed_tools}
        listed = tool in exposed
        user_authorized, exact_evidence, declared_sandboxed = self._authorization(arguments)
        risk = self.risk(tool, arguments)
        sandboxed = declared_sandboxed or tool in self.SANDBOX_EXECUTION
        allowed = listed
        reason = "profile-listed"

        if not listed:
            allowed = False
            reason = "tool-not-exposed-by-active-profile"
        elif risk in {"destructive", "network", "sandbox-execute", "unsandboxed-execute"}:
            if not exact_evidence:
                allowed = False
                reason = "exact-evidence-required"
            elif not user_authorized:
                allowed = False
                reason = "explicit-user-authorization-required"
            elif risk == "sandbox-execute" and not sandboxed:
                allowed = False
                reason = "sandbox-required"
            elif risk == "unsandboxed-execute" and os.environ.get("SIGNALCORE_ALLOW_UNSANDBOXED_PROCESS") != "1":
                allowed = False
                reason = "unsandboxed-process-disabled"
            else:
                reason = "authorized-risky-operation"
        elif risk == "safe-state-write" and not exact_evidence:
            allowed = False
            reason = "exact-evidence-required"

        body = {
            "version": VERSION,
            "channel": CHANNEL,
            "tool": tool,
            "profile": self.profile,
            "legacy_profile": self.legacy_profile,
            "risk": risk,
            "allowed": allowed,
            "reason": reason,
            "listed": listed,
            "user_authorized": user_authorized,
            "exact_evidence": exact_evidence,
            "sandboxed": sandboxed,
        }
        return MCPAuthorizationDecision(
            allowed=allowed,
            tool=tool,
            profile=self.profile,
            legacy_profile=self.legacy_profile,
            risk=risk,
            reason=reason,
            listed=listed,
            user_authorized=user_authorized,
            exact_evidence=exact_evidence,
            sandboxed=sandboxed,
            receipt_hash=sha256_bytes(canonical_json(body)),
        )

    @staticmethod
    def serializable(decision: MCPAuthorizationDecision) -> dict[str, Any]:
        return asdict(decision)
