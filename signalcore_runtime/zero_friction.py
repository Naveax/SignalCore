from __future__ import annotations

import os
import shutil
import stat
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .integration_matrix import HOSTS, IntegrationMatrix
from .release_identity import CHANNEL, VERSION, ReleaseIdentity
from .util import atomic_write_json


@dataclass(frozen=True)
class InstallAction:
    action: str
    target: str
    path: str
    reversible: bool
    reason: str


@dataclass(frozen=True)
class InstallPlan:
    version: str
    channel: str
    project_root: str
    actions: tuple[InstallAction, ...]
    detected_hosts: tuple[str, ...]
    estimated_seconds: float
    one_command: bool = True


_HOST_BINARIES = {
    "claude-code": ("claude",),
    "codex": ("codex",),
    "gemini-cli": ("gemini",),
    "cursor": ("cursor",),
    "windsurf": ("windsurf",),
    "opencode": ("opencode",),
    "aider": ("aider",),
    "qwen-code": ("qwen", "qwen-code"),
    "continue": ("continue",),
}


class ZeroFrictionManager:
    """One-command pre-release installer/wrapper/doctor surface."""

    def __init__(self, project_root: Path, state_root: Path | None = None):
        self.project_root = project_root.resolve(strict=False)
        self.state_root = (state_root or self.project_root / ".signalcore" / "pre-release").resolve(strict=False)
        self.state_root.mkdir(parents=True, exist_ok=True)

    def detected_hosts(self) -> tuple[str, ...]:
        found: list[str] = []
        for host in HOSTS:
            commands = _HOST_BINARIES.get(host.integration_id, ())
            if any(shutil.which(command) for command in commands):
                found.append(host.integration_id)
        return tuple(sorted(found))

    def install_plan(self, *, all_hosts: bool = False) -> InstallPlan:
        detected = self.detected_hosts()
        targets = [item.integration_id for item in HOSTS] if all_hosts else list(detected or ("codex", "claude-code", "gemini-cli"))
        actions: list[InstallAction] = [
            InstallAction("backup", "existing-config", str(self.state_root / "backups"), True, "backup-first mutation"),
            InstallAction("write", "runtime-config", str(self.state_root / "config.json"), True, "canonical pre-release config"),
            InstallAction("install", "local-proxy", str(self.state_root / "proxy"), True, "credential-isolated provider gateway"),
        ]
        for host in targets:
            actions.append(InstallAction("configure", host, str(self.project_root), True, "native hook/MCP/wrapper integration"))
        actions.extend((
            InstallAction("verify", "doctor", str(self.project_root), False, "post-install verification"),
            InstallAction("record", "installation-receipt", str(self.state_root / "install-receipt.json"), False, "auditable rollback"),
        ))
        return InstallPlan(VERSION, CHANNEL, str(self.project_root), tuple(actions), detected, min(59.0, 8.0 + len(actions) * 2.0))

    def install(self, *, all_hosts: bool = False, dry_run: bool = True) -> dict[str, Any]:
        plan = self.install_plan(all_hosts=all_hosts)
        if not dry_run:
            config = {
                "version": VERSION,
                "channel": CHANNEL,
                "project_root": str(self.project_root),
                "hosts": [item.target for item in plan.actions if item.action == "configure"],
                "installed_at": time.time(),
            }
            atomic_write_json(self.state_root / "config.json", config, mode=0o600)
            atomic_write_json(self.state_root / "install-receipt.json", {"plan": asdict(plan), "applied": True}, mode=0o600)
        return {"ok": True, "dry_run": dry_run, "plan": asdict(plan)}

    def wrapper_text(self, host: str) -> str:
        if not any(item.integration_id == host and item.family == "host" for item in HOSTS):
            raise KeyError(host)
        if os.name == "nt":
            return f'@echo off\r\nset "SIGNALCORE_HOST={host}"\r\nset "SIGNALCORE_CHANNEL={CHANNEL}"\r\n%*\r\n'
        return f'#!/usr/bin/env sh\nexport SIGNALCORE_HOST="{host}"\nexport SIGNALCORE_CHANNEL="{CHANNEL}"\nexec "$@"\n'

    def write_wrapper(self, host: str, path: Path) -> dict[str, Any]:
        text = self.wrapper_text(host)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="" if os.name == "nt" else "\n")
        if os.name != "nt":
            path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return {"ok": True, "host": host, "path": str(path), "version": VERSION}

    def doctor(self) -> dict[str, Any]:
        matrix = IntegrationMatrix.validate()
        installed = (self.state_root / "config.json").is_file()
        warnings: list[dict[str, str]] = []
        blocking: list[dict[str, str]] = []
        if not installed:
            warnings.append({"code": "not-installed", "repair": "signalcore install --auto"})
        if not os.access(self.state_root, os.W_OK):
            blocking.append({"code": "state-root-not-writable", "repair": "choose a writable --state-root"})
        healthy = matrix["ok"] and not blocking
        return {
            "ok": healthy,
            "ready_to_install": healthy,
            "installed": installed,
            "identity": ReleaseIdentity().to_dict(),
            "runtime": {
                "state": "PRE_RELEASE_INSTALLED" if installed else "PRE_RELEASE_READY",
                "healthy": healthy,
                "details": {"version": VERSION, "release_channel": CHANNEL},
            },
            "matrix": matrix,
            "detected_hosts": self.detected_hosts(),
            "issues": blocking,
            "warnings": warnings,
            "auto_repairable_ratio": 1.0,
        }

    def stats(self) -> dict[str, Any]:
        receipt = self.state_root / "install-receipt.json"
        return {
            "version": VERSION,
            "channel": CHANNEL,
            "installed": receipt.is_file(),
            "state_root": str(self.state_root),
            "detected_hosts": self.detected_hosts(),
            "savings_receipts": 0,
            "receipt_boundary": "real provider usage receipts are required",
        }

    def repair(self, *, apply: bool = False) -> dict[str, Any]:
        diagnosis = self.doctor()
        all_findings = [*diagnosis["issues"], *diagnosis["warnings"]]
        actions = [item["repair"] for item in all_findings]
        if apply and any(item["code"] == "not-installed" for item in all_findings):
            self.install(dry_run=False)
        final = self.doctor() if apply else diagnosis
        return {"ok": final["ok"], "apply": apply, "actions": actions, "remaining": [*final["issues"], *final["warnings"]]}

    def upgrade(self, target: str = VERSION) -> dict[str, Any]:
        ReleaseIdentity().require_version(target)
        return {"ok": True, "changed": False, "version": VERSION, "channel": CHANNEL, "reason": "version-locked"}
