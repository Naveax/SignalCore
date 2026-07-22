#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.0.1"
CHANNEL = "pre-release"


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def check_repository() -> dict:
    failures: list[str] = []

    root_package = load_json("package.json")
    root_lock = load_json("package-lock.json")
    sdk_package = load_json("sdk/typescript/package.json")
    sdk_lock = load_json("sdk/typescript/package-lock.json")
    release = load_json("release/pre-release.json")

    identities = {
        "installer-package": root_package.get("version"),
        "installer-lock": root_lock.get("version"),
        "typescript-package": sdk_package.get("version"),
        "typescript-lock": sdk_lock.get("version"),
        "release": release.get("version"),
        "version-file": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
    }
    failures.extend(
        f"wrong-version:{name}:{value}"
        for name, value in identities.items()
        if value != VERSION
    )
    if root_package.get("name") != "@signalcore/install":
        failures.append("missing-installer-package-identity")
    if sdk_package.get("name") != "@signalcore/client":
        failures.append("missing-typescript-client-identity")
    if release.get("channel") != CHANNEL or release.get("version_locked") is not True:
        failures.append("release-policy-not-locked")

    sdk_typescript = (
        sdk_lock.get("packages", {})
        .get("node_modules/typescript", {})
        .get("version")
    )
    if sdk_typescript != "6.0.3":
        failures.append("typescript-lock-not-pinned")
    if sdk_package.get("scripts", {}).get("test", "").find("node --test") < 0:
        failures.append("typescript-tests-not-wired")

    required = [
        "install/index.mjs",
        "install/index.test.mjs",
        "CONTRIBUTING.md",
        "SUPPORT.md",
        "CODE_OF_CONDUCT.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/dependabot.yml",
        ".github/workflows/codeql.yml",
        ".github/workflows/dependency-review.yml",
        "docs/operations/ONE_COMMAND_INSTALL.md",
        "docs/operations/CI_AND_BRANCH_POLICY.md",
    ]
    failures.extend(f"missing:{path}" for path in required if not (ROOT / path).is_file())

    workflows = list((ROOT / ".github" / "workflows").glob("*.yml"))
    workflow_text = "\n".join(path.read_text(encoding="utf-8") for path in workflows)
    if "git push origin HEAD:main" in workflow_text:
        failures.append("workflow-direct-main-push")
    if "npm ci" not in workflow_text:
        failures.append("npm-ci-not-enforced")
    if "npm test" not in workflow_text:
        failures.append("npm-tests-not-enforced")
    if "attest-build-provenance" not in workflow_text:
        failures.append("artifact-provenance-not-enforced")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "npx @signalcore/install" not in readme:
        failures.append("one-command-install-not-documented")
    if "0.0.1 / pre-release" not in readme:
        failures.append("version-lock-not-documented")

    return {
        "ok": not failures,
        "version": VERSION,
        "channel": CHANNEL,
        "failures": failures,
        "checks": {
            "identities": identities,
            "required_files": len(required),
            "workflow_files": len(workflows),
            "typescript": sdk_typescript,
        },
    }


def main() -> int:
    result = check_repository()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
