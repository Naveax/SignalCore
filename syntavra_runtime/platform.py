from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .platform_common import CHANNEL, VERSION, canonical_json, sha256_bytes
from .artifacts import (
    ArtifactRecord, ArtifactStore, ContextCompiler, ContextIRItem,
    ContextPack, FirewallReceipt, OutputFirewall,
)
from .semantic_intelligence import IncrementalCodeIntelligenceGraph
from .session_memory import SessionMemory
from .capability_security import CapabilityDecision, CapabilitySecurity
from .secretless_gateway import SecretlessProviderGateway
from .adapter_platform import ADAPTERS, AdapterContract, CodingAgent, AdapterRegistry

class SyntavraPlatform:
    """One facade for the competitor-parity and beyond feature set."""

    def __init__(self, project: Path, state_root: Path):
        self.project = project.resolve(strict=False)
        self.state_root = state_root.resolve(strict=False)
        self.state_root.mkdir(parents=True, exist_ok=True)
        self.artifacts = ArtifactStore(self.state_root / "artifacts")
        self.firewall = OutputFirewall(self.artifacts)
        self.context = ContextCompiler(self.artifacts)
        self.graph = IncrementalCodeIntelligenceGraph(self.state_root / "semantic-graph.sqlite3")
        project_id = sha256_bytes(str(self.project).encode("utf-8"))
        self.memory = SessionMemory(self.state_root / "session-memory.sqlite3", project_id=project_id)
        self.security = CapabilitySecurity(self.state_root / "security")
        self.agent = CodingAgent(project=self.project, graph=self.graph, memory=self.memory, security=self.security)

    def status(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "channel": CHANNEL,
            "project": str(self.project),
            "artifacts": self.artifacts.stats(),
            "graph": self.graph.stats(),
            "memory": self.memory.stats(),
            "adapters": AdapterRegistry.validate(),
            "providers": sorted(SecretlessProviderGateway.PROVIDERS),
            "capabilities": {
                "context_compiler_ir": True,
                "universal_output_firewall": True,
                "content_addressed_exact_recovery": True,
                "incremental_code_graph": True,
                "multi_view_memory_dag": True,
                "signed_single_use_capabilities": True,
                "secretless_provider_gateway": True,
                "cli_and_non_cli_adapters": True,
                "reference_coding_agent": True,
            },
            "claim_boundary": "functional capabilities are internally tested; external superiority remains receipt-gated",
        }

    def doctor(self) -> dict[str, Any]:
        artifact_check = self.artifacts.verify()
        adapter_check = AdapterRegistry.validate()
        return {
            "ok": artifact_check["ok"] and adapter_check["ok"],
            "artifact_integrity": artifact_check,
            "adapters": adapter_check,
            "graph": self.graph.stats(),
            "memory": self.memory.stats(),
            "version_locked": VERSION == "0.0.1" and CHANNEL == "pre-release",
        }


def manifest() -> dict[str, Any]:
    return {
        "version": VERSION,
        "channel": CHANNEL,
        "runtime": "unified",
        "components": [
            "context-compiler", "output-firewall", "artifact-store",
            "semantic-intelligence", "session-memory", "capability-security",
            "provider-gateway", "adapter-platform", "coding-agent",
        ],
        "adapter_contract": AdapterRegistry.validate(),
        "external_claims": "NOT_PROVEN_WITHOUT_EXTERNAL_RECEIPTS",
    }

__all__ = [
    "ArtifactRecord", "ArtifactStore", "ContextCompiler", "ContextIRItem",
    "ContextPack", "FirewallReceipt", "OutputFirewall",
    "IncrementalCodeIntelligenceGraph", "SessionMemory", "ADAPTERS", "AdapterContract",
    "CapabilityDecision", "CapabilitySecurity", "CodingAgent",
    "SecretlessProviderGateway", "AdapterRegistry", "SyntavraPlatform", "manifest",
]
