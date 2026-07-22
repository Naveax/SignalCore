#!/usr/bin/env python3
from __future__ import annotations

import json
import py_compile
import re
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "syntavra"
EXPECTED_VERSION = "0.0.1"
EXPECTED_CHANNEL = "pre-release"

REQUIRED = [
    ROOT / "README.md",
    ROOT / "CHANGELOG.md",
    ROOT / "LICENSE",
    ROOT / "MANIFEST.sha256",
    ROOT / "COMPATIBILITY.md",
    ROOT / "AGENTS.md",
    ROOT / "llms.txt",
    ROOT / "gemini-extension.json",
    ROOT / ".claude-plugin" / "marketplace.json",
    ROOT / "pyproject.toml",
    ROOT / "BENCHMARKS.md",
    ROOT / "release" / "pre-release.json",
    ROOT / "docs" / "architecture" / "PRE_RELEASE_DOMINANCE_001.md",
    ROOT / "docs" / "benchmark" / "INFINITE_CONTEXT_001.md",
    ROOT / "docs" / "benchmark" / "PROTOCOL.md",
    ROOT / "docs" / "security" / "THREAT_MODEL.md",
    ROOT / "benchmarks" / "runtime_v03_benchmark.py",
    ROOT / "benchmarks" / "v001_pre_release_benchmark.py",
    ROOT / "benchmarks" / "signalbench" / "README.md",
    ROOT / "benchmarks" / "signalbench" / "tasks.example.json",
    ROOT / "benchmarks" / "signalbench" / "arms.example.json",
    ROOT / "docs" / "architecture" / "UNIFIED_RUNTIME_V03.md",
    ROOT / "docs" / "architecture" / "UNIFIED_PRODUCTION_CORE_V6.md",
    ROOT / "benchmarks" / "v6_production_core_benchmark.py",
    ROOT / "syntavra_runtime" / "runtime_pipeline.py",
    ROOT / "syntavra_runtime" / "unified_config.py",
    ROOT / "syntavra_runtime" / "crypto.py",
    ROOT / "syntavra_runtime" / "backup.py",
    ROOT / "syntavra_runtime" / "identity.py",
    ROOT / "syntavra_runtime" / "observability.py",
    ROOT / "syntavra_runtime" / "migrations.py",
    ROOT / "syntavra_runtime" / "plugin_sdk.py",
    ROOT / "syntavra_runtime" / "job_scheduler.py",
    ROOT / "syntavra_runtime" / "policy_rollout.py",
    ROOT / "syntavra_runtime" / "streaming.py",
    ROOT / "syntavra_runtime" / "unified_cli.py",
    ROOT / "syntavra_runtime" / "prerelease_cli.py",
    ROOT / "syntavra_runtime" / "release_identity.py",
    ROOT / "syntavra_runtime" / "integration_matrix.py",
    ROOT / "syntavra_runtime" / "zero_friction.py",
    ROOT / "syntavra_runtime" / "semantic_structure.py",
    ROOT / "syntavra_runtime" / "paired_benchmark.py",
    ROOT / "syntavra_runtime" / "infinite_context.py",
    ROOT / "syntavra_runtime" / "public_proof.py",
    ROOT / "tests" / "runtime" / "test_v001_pre_release_dominance.py",
    ROOT / "docs" / "operations" / "INSTALLER_AND_SANDBOX.md",
    ROOT / "docs" / "benchmark" / "SIGNALBENCH.md",
    SKILL / "SKILL.md",
    SKILL / "data" / "platforms.json",
    SKILL / "scripts" / "platforms.py",
    SKILL / "scripts" / "profile_loader.py",
    SKILL / "profiles" / "roblox_studio" / "profile.json",
    SKILL / "profiles" / "roblox_studio" / "activation.py",
    ROOT / "ROBLOX_STUDIO_MODE.md",
    ROOT / "syntavra_runtime" / "cli.py",
    ROOT / "syntavra_runtime" / "hooks.py",
    ROOT / "syntavra_runtime" / "mcp_server.py",
    ROOT / "syntavra_runtime" / "structural_parsers.py",
    ROOT / "syntavra_runtime" / "installer.py",
    ROOT / "syntavra_runtime" / "sandbox.py",
    ROOT / "syntavra_runtime" / "compression.py",
    ROOT / "syntavra_runtime" / "session_runtime.py",
    ROOT / "syntavra_runtime" / "output_governor.py",
    ROOT / "syntavra_runtime" / "signalbench.py",
    ROOT / "syntavra_runtime" / "bundled_skill" / "SKILL.md",
    ROOT / "syntavra_runtime" / "bundled_skill" / "hosts.json",
    ROOT / "tools" / "validate_runtime.py",
    ROOT / "tools" / "validate_release.py",
]

ACTUAL_SECRET = re.compile(r"(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{20,})")
MATERIALIZER_WORKFLOW = re.compile(r"(?i)(materializ|reconstruct|source[-_]?transfer|payload[-_]?apply|import[-_]?bundle)")


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _skill_version(text: str) -> str | None:
    match = re.search(r'^version:\s*["\']?([^"\'\s]+)', text, flags=re.MULTILINE)
    return match.group(1) if match else None


def _source_files() -> list[Path]:
    roots = [SKILL / "scripts", SKILL / "profiles", ROOT / "syntavra_runtime", ROOT / "tools", ROOT / "benchmarks"]
    return sorted({path for base in roots if base.exists() for path in base.rglob("*.py")})


GENERATED_FILES = {"fusion-release-smoke.json", "release-smoke.json", "platform-registry.json", "native-dry-run.json"}


def _is_generated_path(relative: Path) -> bool:
    parts = relative.parts
    return (
        bool(parts) and parts[0] in {".git", ".syntavra", "build", "dist"}
    ) or any(part in {"__pycache__", ".pytest_cache"} or part.endswith(".egg-info") for part in parts)


def _scan_files() -> list[Path]:
    skipped_suffixes = {".pyc", ".sqlite3", ".db", ".log", ".zip", ".gz", ".xz", ".png", ".jpg", ".jpeg", ".webp"}
    return [path for path in ROOT.rglob("*") if path.is_file() and not _is_generated_path(path.relative_to(ROOT)) and path.suffix.casefold() not in skipped_suffixes]


def _manifest_candidates() -> list[Path]:
    candidates: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if _is_generated_path(relative):
            continue
        if (path.name == "MANIFEST.sha256" and path.parent == ROOT) or path.name in GENERATED_FILES or path.suffix == ".pyc":
            continue
        candidates.append(path)
    return sorted(candidates, key=lambda value: value.relative_to(ROOT).as_posix())


def _verify_manifest() -> tuple[bool, str]:
    import hashlib
    manifest = ROOT / "MANIFEST.sha256"
    failures: list[str] = []
    entries: dict[str, str] = {}
    for number, raw in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            digest, relative = raw.split("  ", 1)
        except ValueError:
            failures.append(f"malformed-line:{number}")
            continue
        if relative in entries:
            failures.append(f"duplicate:{relative}")
            continue
        entries[relative] = digest
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"missing:{relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            failures.append(f"hash-mismatch:{relative}")
    expected = {path.relative_to(ROOT).as_posix() for path in _manifest_candidates()}
    present = set(entries)
    failures.extend(f"unlisted:{relative}" for relative in sorted(expected - present))
    failures.extend(f"unexpected:{relative}" for relative in sorted(present - expected))
    return not failures, ", ".join(failures[:20])


def main() -> int:
    checks: list[tuple[str, bool, str]] = []
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.is_file()]
    checks.append(("required_files", not missing, ", ".join(missing)))

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    bundled_skill = (ROOT / "syntavra_runtime" / "bundled_skill" / "SKILL.md").read_text(encoding="utf-8")
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    marketplace = _json(ROOT / ".claude-plugin" / "marketplace.json")
    gemini = _json(ROOT / "gemini-extension.json")
    codemeta = _json(ROOT / "codemeta.json")
    typescript = _json(ROOT / "sdk" / "typescript" / "package.json")
    prerelease = _json(ROOT / "release" / "pre-release.json")

    versions = {
        "VERSION": version,
        "skill": _skill_version(skill_text),
        "bundled_skill": _skill_version(bundled_skill),
        "pyproject": pyproject.get("project", {}).get("version"),
        "typescript": typescript.get("version"),
        "marketplace": marketplace.get("version"),
        "gemini": gemini.get("version"),
        "codemeta": codemeta.get("version"),
        "prerelease": prerelease.get("version"),
    }
    checks.append(("version_consistency", all(value == EXPECTED_VERSION for value in versions.values()), json.dumps(versions, sort_keys=True)))
    checks.append(("pre_release_identity", prerelease.get("channel") == EXPECTED_CHANNEL and prerelease.get("publish_as_prerelease") is True and prerelease.get("version_locked") is True and prerelease.get("stable") is False, json.dumps(prerelease, sort_keys=True)))
    checks.append(("pre_alpha_classifier", "Development Status :: 2 - Pre-Alpha" in pyproject.get("project", {}).get("classifiers", []), "PEP 301 pre-alpha"))
    checks.append(("skill_identity", "name: syntavra" in skill_text and "version_locked: true" in skill_text, "canonical locked skill"))
    checks.append(("build_backend", pyproject.get("build-system", {}).get("build-backend") == "setuptools.build_meta", "PEP 517 wheel"))

    platforms = _json(SKILL / "data" / "platforms.json")
    ids = [item["id"] for item in platforms["platforms"]]
    checks.append(("platform_registry", len(ids) >= 20 and len(ids) == len(set(ids)), f"platform_count={len(ids)}"))
    required_hosts = {"codex", "claude-code", "gemini-cli", "antigravity", "antigravity-cli", "windsurf", "opencode", "vscode-copilot"}
    checks.append(("native_core", required_hosts.issubset(ids), f"missing={sorted(required_hosts - set(ids))}"))

    roblox = _json(SKILL / "profiles" / "roblox_studio" / "profile.json")
    activation = roblox.get("activation", {})
    checks.append(("roblox_profile_hidden", roblox.get("discoverable") is False and roblox.get("direct_invocation") is False, ""))
    checks.append(("roblox_profile_studio_only", activation.get("mode") == "signed_studio_session" and activation.get("allow_cli") is False and activation.get("allow_ide") is False, ""))
    checks.append(("roblox_profile_fail_closed", activation.get("require_process_attestation") is True and activation.get("single_use_nonce") is True, ""))
    checks.append(("pairing_key_not_vendored", not any(path.name == "pairing.key" for path in ROOT.rglob("*")), ""))

    forbidden_paths = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(part in {".git", ".syntavra"} for part in relative.parts):
            continue
        if path.name == ".syntavra-direct" or path.name == ".syntavra-transfer" or path.match("payload-*.b64"):
            forbidden_paths.append(str(relative))
    workflow_violations = [str(path.relative_to(ROOT)) for path in (ROOT / ".github" / "workflows").glob("*") if path.is_file() and MATERIALIZER_WORKFLOW.search(path.name)]
    checks.append(("no_transfer_payloads", not forbidden_paths, ", ".join(forbidden_paths)))
    checks.append(("no_source_materializers", not workflow_violations, ", ".join(workflow_violations)))

    try:
        for path in _source_files():
            py_compile.compile(str(path), doraise=True)
        compile_ok = True
        compile_detail = f"compiled={len(_source_files())}"
    except Exception as exc:
        compile_ok = False
        compile_detail = f"{type(exc).__name__}: {exc}"
    checks.append(("python_compile", compile_ok, compile_detail))

    secret_hits: list[str] = []
    for path in _scan_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if ACTUAL_SECRET.search(text):
            secret_hits.append(str(path.relative_to(ROOT)))
    checks.append(("secret_scan", not secret_hits, ", ".join(secret_hits)))

    for tier in ("1x", "20x", "30x", "100x"):
        path = ROOT / "benchmarks" / "configs" / f"{tier}.json"
        try:
            config = _json(path)
            config_ok = config.get("schema_version") == 2 and "observed_baseline" in config
            detail = f"schema={config.get('schema_version')}"
        except (OSError, json.JSONDecodeError) as exc:
            config_ok = False
            detail = str(exc)
        checks.append((f"benchmark_config_{tier}", config_ok, detail))

    manifest_ok, manifest_detail = _verify_manifest()
    checks.append(("release_manifest", manifest_ok, manifest_detail))
    result = {
        "ok": all(passed for _, passed, _ in checks),
        "version": version,
        "release_channel": EXPECTED_CHANNEL,
        "checks": [{"name": name, "passed": passed, **({"detail": detail} if detail else {})} for name, passed, detail in checks],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
