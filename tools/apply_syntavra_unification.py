from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "signalcore_runtime"
CANONICAL = ROOT / "syntavra_runtime"
WORKFLOW = ROOT / ".github" / "workflows" / "unified-dominance-migration.yml"

MODULE_RENAMES = {
    "competitive_common_v7.py": "platform_common.py",
    "competitive_artifacts_v7.py": "artifacts.py",
    "competitive_graph_v7.py": "semantic_intelligence.py",
    "competitive_memory_v7.py": "session_memory.py",
    "competitive_security_v7.py": "capability_security.py",
    "competitive_gateway_v7.py": "secretless_gateway.py",
    "competitive_adapters_v7.py": "adapter_platform.py",
    "competitive_runtime_v7.py": "platform.py",
    "competitive_v7_cli.py": "platform_cli.py",
    "config_v6.py": "unified_config.py",
    "retrieval_v6.py": "semantic_retrieval.py",
    "sandbox_v6_extension.py": "sandbox_extension.py",
    "provider_v6_extension.py": "provider_extension.py",
    "v6_extension.py": "production_extension.py",
    "product_v5_cli.py": "product_cli.py",
    "product_v5_extension.py": "product_extension.py",
    "signalbench_v2.py": "paired_benchmark.py",
    "structural_v2.py": "semantic_structure.py",
}

PATH_RENAMES = {
    "benchmarks/competitive_runtime_v7_benchmark.py": "benchmarks/syntavra_component_benchmark.py",
    "schemas/competitive-runtime-receipt-v1.json": "schemas/platform-receipt.json",
    "schemas/external-benchmark-receipt-v1.json": "schemas/external-benchmark-receipt.json",
    "schemas/live-integration-receipt-v1.json": "schemas/live-integration-receipt.json",
    "schemas/product-maturity-evidence-v1.json": "schemas/product-maturity-evidence.json",
    "schemas/provider-usage-receipt-v1.json": "schemas/provider-usage-receipt.json",
}

REPLACEMENTS = [
    (".competitive_common_v7", ".platform_common"),
    (".competitive_artifacts_v7", ".artifacts"),
    (".competitive_graph_v7", ".semantic_intelligence"),
    (".competitive_memory_v7", ".session_memory"),
    (".competitive_security_v7", ".capability_security"),
    (".competitive_gateway_v7", ".secretless_gateway"),
    (".competitive_adapters_v7", ".adapter_platform"),
    (".competitive_runtime_v7", ".platform"),
    (".competitive_v7_cli", ".platform_cli"),
    (".config_v6", ".unified_config"),
    (".retrieval_v6", ".semantic_retrieval"),
    (".sandbox_v6_extension", ".sandbox_extension"),
    (".provider_v6_extension", ".provider_extension"),
    (".v6_extension", ".production_extension"),
    (".product_v5_cli", ".product_cli"),
    (".product_v5_extension", ".product_extension"),
    (".signalbench_v2", ".paired_benchmark"),
    (".structural_v2", ".semantic_structure"),
    ("competitive_common_v7", "platform_common"),
    ("competitive_artifacts_v7", "artifacts"),
    ("competitive_graph_v7", "semantic_intelligence"),
    ("competitive_memory_v7", "session_memory"),
    ("competitive_security_v7", "capability_security"),
    ("competitive_gateway_v7", "secretless_gateway"),
    ("competitive_adapters_v7", "adapter_platform"),
    ("competitive_runtime_v7", "platform"),
    ("competitive_v7_cli", "platform_cli"),
    ("config_v6", "unified_config"),
    ("retrieval_v6", "semantic_retrieval"),
    ("sandbox_v6_extension", "sandbox_extension"),
    ("provider_v6_extension", "provider_extension"),
    ("product_v5_cli", "product_cli"),
    ("product_v5_extension", "product_extension"),
    ("signalbench_v2", "paired_benchmark"),
    ("structural_v2", "semantic_structure"),
    ("CompetitiveRuntimeV7", "SyntavraPlatform"),
    ("ContentAddressedArtifactStoreV2", "ArtifactStore"),
    ("ContextCompilerV2", "ContextCompiler"),
    ("ContextPackV2", "ContextPack"),
    ("FirewallReceiptV2", "FirewallReceipt"),
    ("UniversalOutputFirewallV2", "OutputFirewall"),
    ("SessionMemoryDAGV2", "SessionMemory"),
    ("CapabilityDecisionV2", "CapabilityDecision"),
    ("CapabilitySecurityV2", "CapabilitySecurity"),
    ("SecretlessProviderGatewayV2", "SecretlessProviderGateway"),
    ("AdapterContractV2", "AdapterContract"),
    ("UniversalAdapterRegistryV2", "AdapterRegistry"),
    ("ReferenceCodingAgentV2", "CodingAgent"),
    ("StructuralGraphV2", "SemanticGraph"),
    ("SignalCoreClient", "SyntavraClient"),
    ("ADAPTERS_V2", "ADAPTERS"),
    ("competitive_v7_manifest", "platform_manifest"),
    ("Competitive Runtime V7", "Unified AI Engineering Platform"),
    ("Context Compiler V2", "Context Compiler"),
    ("Universal Output Firewall V2", "Output Firewall"),
    ("Content-Addressed Artifact Store V2", "Artifact Store"),
    ("Incremental Code Intelligence Graph V3", "Semantic Intelligence"),
    ("Session Memory DAG V2", "Session Memory"),
    ("Capability Security V2", "Capability Security"),
    ("Secretless Provider Gateway V2", "Provider Gateway"),
    ("Universal Adapter Contract V2", "Adapter Platform"),
    ("Reference Coding Agent V2", "Coding Agent"),
    ("competitive-v7", "unified"),
    ("context-compiler-v2", "context-compiler"),
    ("output-firewall-v2", "output-firewall"),
    ("artifact-store-v2", "artifact-store"),
    ("code-intelligence-graph-v3", "semantic-intelligence"),
    ("session-memory-dag-v2", "session-memory"),
    ("capability-security-v2", "capability-security"),
    ("secretless-provider-gateway-v2", "provider-gateway"),
    ("universal-adapter-contract-v2", "adapter-platform"),
    ("reference-agent-v2", "coding-agent"),
    ("artifacts-v2.sqlite3", "artifacts.sqlite3"),
    ("artifacts-v2", "artifacts"),
    ("code-graph-v3.sqlite3", "semantic-graph.sqlite3"),
    ("memory-dag-v2.sqlite3", "session-memory.sqlite3"),
    ("security-v2", "security"),
    ("scheduler-v001.sqlite3", "scheduler.sqlite3"),
    ("@signalcore/install", "@syntavra/install"),
    ("@signalcore/client", "@syntavra/sdk"),
    ("@signalcore/sdk", "@syntavra/sdk"),
    ("signalcore_runtime", "syntavra_runtime"),
    ("SIGNALCORE_PORTABLE_BOOTSTRAP", "SYNTAVRA_PORTABLE_BOOTSTRAP"),
    ("SIGNALCORE_", "SYNTAVRA_"),
    ("SignalCore", "Syntavra"),
    ("signalcore-product", "syntavra-product"),
    ("signalcore-install", "syntavra-install"),
    ("signal-core", "syntavra"),
    (".signalcore", ".syntavra"),
    ("signalcore", "syntavra"),
]

README = """# Syntavra 0.0.1 — Pre-Release AI Engineering Platform

Syntavra is a local-first control plane and coding-agent runtime that unifies semantic repository intelligence, context and tool-output control, exact session continuity, capability security, provider isolation, adapters, headless execution, recovery and receipt-based benchmarking.

> The only active product identity is **0.0.1 / pre-release**. External superiority, live certification, long-context quality, adoption and production maturity remain evidence-gated.

## Install

```bash
npx @syntavra/install
```

Until registry publication:

```bash
npx github:Naveax/Syntavra
```

## Product surface

```bash
syntavra setup
syntavra status
syntavra run
syntavra prove
```

## Canonical documentation

- `docs/001_PRE_RELEASE.md`
- `docs/ARCHITECTURE.md`
- `docs/UNIFIED_PLAN.md`
- `docs/SECURITY_MODEL.md`
- `docs/ADAPTER_PLATFORM.md`
- `docs/SIGNALBENCH.md`
- `docs/OPERATIONS.md`
"""

DOCS = {
    "docs/001_PRE_RELEASE.md": """# Syntavra 0.0.1 Pre-Release

```text
product: Syntavra
version: 0.0.1
channel: pre-release
surface: setup / status / run / prove
```

No component carries an independent product version. Compatibility is represented by schema hashes, migration identifiers and capability sets.

## Evidence gates

```text
EXTERNAL_SUPERIORITY_NOT_PROVEN
MEASURED_AGENT_BENCHMARK_NOT_PROVEN
LONG_CONTEXT_QUALITY_NOT_PROVEN
LIVE_INTEGRATION_CERTIFICATION_NOT_PROVEN
DAILY_CODING_AGENT_READINESS_NOT_PROVEN
PUBLIC_PRODUCT_MATURITY_NOT_PROVEN
```

The version and channel may not change without explicit owner instruction.
""",
    "docs/ARCHITECTURE.md": """# Syntavra Architecture

```text
Context Compiler · Output Firewall · Artifact Store
Semantic Intelligence · Runtime Evidence · Session Memory
Coding Agent · Capability Security · Execution Sandbox
Provider Gateway · Adapter Platform · Headless Runtime
Interactive Console · Reliability Laboratory · Distribution
SignalBench · Receipts · Metrics · Recovery
```

All components share one artifact model, session model, semantic graph, policy engine, receipt envelope, adapter contract, configuration hierarchy, metrics schema and recovery boundary.

## Invariants

1. Raw evidence is never silently discarded.
2. Compact views retain exact artifact handles.
3. Summary loss cannot destroy exact history.
4. Unknown or unauthorized tools fail closed.
5. Provider credentials never enter agent-visible state.
6. Mutations are bounded and receipt-producing.
7. External claims remain closed until reproducible evidence passes.
""",
    "docs/UNIFIED_PLAN.md": """# Syntavra Unified Engineering Plan

One product, one architecture, one development branch, one pull request and one version identity.

Workstreams: semantic intelligence; context/output control; long-session continuity; autonomous coding; native sandbox; adapters; providers/frameworks; headless/remote execution; interactive operations; reliability; distribution; SignalBench.

The final SHA must pass unit, integration, cross-platform, package, portable, semantic, session, agent, sandbox, adapter, update, fault, manifest, CodeQL, dependency, version-lock and claim-boundary checks.
""",
    "docs/SECURITY_MODEL.md": """# Syntavra Security Model

```text
agent request → policy evaluation → signed capability
→ native sandbox → constrained execution → artifact and receipt
```

Capabilities are tool-, argument-, resource- and session-bound, expiring, single-use by default, replay-protected and revocable. Provider credentials remain transport-only. Unsupported enforcement is reported honestly and fails closed when required.
""",
    "docs/ADAPTER_PLATFORM.md": """# Syntavra Adapter Platform

CLI presence is not required. MCP, hooks, plugins, IDE extensions, SDKs, provider proxies, configuration adapters, agent protocols, desktop integrations and remote workspaces are supported surfaces.

Lifecycle: detect, install, configure, connect, intercept, authorize, observe, health, upgrade, rollback, uninstall and certify.

States: Contract, Configured, Connected, Intercepting, Enforced and Certified.
""",
    "docs/SIGNALBENCH.md": """# SignalBench

SignalBench compares Syntavra, raw-provider baselines and pinned competitors under identical repository, task, verifier, provider/model, temperature, budget, timeout and machine boundaries.

Lower token use alone is not superiority. Success and quality must be non-inferior, exact recovery must hold and wall time must not materially regress.
""",
    "docs/OPERATIONS.md": """# Syntavra Operations

Supported operator surface:

```bash
syntavra setup
syntavra status
syntavra run
syntavra prove
```

Installation and updates are checksum-verified, atomic and rollback-capable. Headless jobs emit deterministic status, artifacts and receipts.
""",
}

TEXT_SUFFIXES = {".py", ".pyi", ".md", ".txt", ".toml", ".json", ".jsonl", ".yml", ".yaml", ".mjs", ".js", ".ts", ".ini", ".cfg", ".sh", ".ps1", ".bat"}
SKIP = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__", ".pytest_cache"}


def transform(text: str) -> str:
    for source, target in REPLACEMENTS:
        text = text.replace(source, target)
    return text


def text_files() -> list[Path]:
    result = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"LICENSE", "NOTICE", "VERSION", "MANIFEST.sha256"}:
            result.append(path)
    return result


def main() -> None:
    if not LEGACY.is_dir():
        raise SystemExit("legacy package missing")
    if CANONICAL.exists():
        shutil.rmtree(CANONICAL)
    shutil.copytree(LEGACY, CANONICAL)

    for old, new in MODULE_RENAMES.items():
        source, target = CANONICAL / old, CANONICAL / new
        if source.exists():
            if target.exists():
                raise RuntimeError(f"rename collision: {target}")
            source.rename(target)

    skill_source, skill_target = ROOT / "skills" / "signal-core", ROOT / "skills" / "syntavra"
    if skill_source.exists():
        if skill_target.exists():
            shutil.rmtree(skill_target)
        skill_source.rename(skill_target)

    for old, new in PATH_RENAMES.items():
        source, target = ROOT / old, ROOT / new
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                target.unlink()
            source.rename(target)

    for path in text_files():
        if LEGACY in path.parents:
            continue
        try:
            old = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new = transform(old)
        if new != old:
            path.write_text(new, encoding="utf-8")

    for child in list(LEGACY.iterdir()):
        if child.name in {"__init__.py", "__main__.py"}:
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    (LEGACY / "__init__.py").write_text(
        '"""Compatibility namespace for installations created before the Syntavra rename."""\n'
        'from pathlib import Path as _Path\n'
        '_CANONICAL = _Path(__file__).resolve().parent.parent / "syntavra_runtime"\n'
        '__path__ = [str(_CANONICAL)]\n'
        'from syntavra_runtime import *  # noqa: F401,F403\n'
        'from syntavra_runtime import __all__, __release_channel__, __version__\n'
        'del _Path, _CANONICAL\n',
        encoding="utf-8",
    )
    (LEGACY / "__main__.py").write_text("from syntavra_runtime.unified_cli import main\n\nraise SystemExit(main())\n", encoding="utf-8")

    (ROOT / "README.md").write_text(README.rstrip() + "\n", encoding="utf-8")
    for name, content in DOCS.items():
        path = ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
    for directory in (ROOT / "docs" / "architecture", ROOT / "docs" / "benchmark", ROOT / "docs" / "operations"):
        if directory.exists():
            shutil.rmtree(directory)

    (ROOT / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["setuptools>=68", "wheel"]\nbuild-backend = "setuptools.build_meta"\n\n'
        '[project]\nname = "syntavra-runtime"\nversion = "0.0.1"\n'
        'description = "Pre-release unified AI engineering control plane and coding-agent runtime"\n'
        'readme = "README.md"\nrequires-python = ">=3.11"\ndependencies = ["cryptography>=43"]\n'
        'license = {text = "MIT"}\nauthors = [{name = "Naveax"}]\n'
        'keywords = ["ai-agent", "coding-agent", "semantic-intelligence", "context-engineering", "mcp", "sandbox", "exact-recovery"]\n'
        'classifiers = ["Development Status :: 2 - Pre-Alpha", "Programming Language :: Python :: 3", '
        '"Programming Language :: Python :: 3.11", "Programming Language :: Python :: 3.12", '
        '"Programming Language :: Python :: 3.13", "License :: OSI Approved :: MIT License", "Operating System :: OS Independent"]\n\n'
        '[project.scripts]\nsyntavra = "syntavra_runtime.unified_cli:main"\n\n'
        '[project.urls]\nRepository = "https://github.com/Naveax/Syntavra"\nIssues = "https://github.com/Naveax/Syntavra/issues"\n\n'
        '[tool.setuptools.packages.find]\ninclude = ["syntavra_runtime*", "signalcore_runtime*"]\n\n'
        '[tool.setuptools.package-data]\nsyntavra_runtime = ["bundled_skill/*.md", "bundled_skill/*.json"]\n\n'
        '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n',
        encoding="utf-8",
    )

    package = {
        "name": "@syntavra/install", "version": "0.0.1",
        "description": "One-command cross-platform installer for Syntavra 0.0.1 pre-release",
        "type": "module", "bin": {"syntavra-install": "install/index.mjs"},
        "files": ["install/index.mjs", "README.md", "LICENSE", "NOTICE", "release/pre-release.json"],
        "scripts": {"test": "node --test install/*.test.mjs", "pack:check": "npm pack --dry-run --json"},
        "engines": {"node": ">=18"},
        "publishConfig": {"access": "public", "tag": "next", "provenance": True},
        "license": "MIT", "private": False,
    }
    (ROOT / "package.json").write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")

    sdk_path = ROOT / "sdk" / "typescript" / "package.json"
    if sdk_path.exists():
        sdk = json.loads(sdk_path.read_text(encoding="utf-8"))
        sdk.update(name="@syntavra/sdk", version="0.0.1", description="TypeScript SDK for Syntavra 0.0.1 pre-release")
        sdk_path.write_text(json.dumps(sdk, indent=2) + "\n", encoding="utf-8")

    release_path = ROOT / "release" / "pre-release.json"
    release = json.loads(release_path.read_text(encoding="utf-8"))
    release.update(product="Syntavra", version="0.0.1", channel="pre-release", stable=False)
    release_path.write_text(json.dumps(release, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if WORKFLOW.exists():
        WORKFLOW.unlink()
    print("Syntavra identity migration complete")


if __name__ == "__main__":
    main()
