from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .competitive_common_v7 import CHANNEL, VERSION, canonical_json, sha256_bytes
from .competitive_artifacts_v7 import (
    ArtifactRecord, ContentAddressedArtifactStoreV2, ContextCompilerV2, ContextIRItem,
    ContextPackV2, FirewallReceiptV2, UniversalOutputFirewallV2,
)
from .competitive_graph_v7 import IncrementalCodeIntelligenceGraph
from .competitive_memory_v7 import SessionMemoryDAGV2
from .competitive_security_v7 import CapabilityDecisionV2, CapabilitySecurityV2
from .competitive_gateway_v7 import SecretlessProviderGatewayV2
from .competitive_adapters_v7 import ADAPTERS_V2, AdapterContractV2, ReferenceCodingAgentV2, UniversalAdapterRegistryV2

class CompetitiveRuntimeV7:
    """One facade for the competitor-parity and beyond feature set."""

    def __init__(self, project: Path, state_root: Path):
        self.project = project.resolve(strict=False)
        self.state_root = state_root.resolve(strict=False)
        self.state_root.mkdir(parents=True, exist_ok=True)
        self.artifacts = ContentAddressedArtifactStoreV2(self.state_root / "artifacts-v2")
        self.firewall = UniversalOutputFirewallV2(self.artifacts)
        self.context = ContextCompilerV2(self.artifacts)
        self.graph = IncrementalCodeIntelligenceGraph(self.state_root / "code-graph-v3.sqlite3")
        project_id = sha256_bytes(str(self.project).encode("utf-8"))
        self.memory = SessionMemoryDAGV2(self.state_root / "memory-dag-v2.sqlite3", project_id=project_id)
        self.security = CapabilitySecurityV2(self.state_root / "security-v2")
        self.agent = ReferenceCodingAgentV2(project=self.project, graph=self.graph, memory=self.memory, security=self.security)

    def status(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "channel": CHANNEL,
            "project": str(self.project),
            "artifacts": self.artifacts.stats(),
            "graph": self.graph.stats(),
            "memory": self.memory.stats(),
            "adapters": UniversalAdapterRegistryV2.validate(),
            "providers": sorted(SecretlessProviderGatewayV2.PROVIDERS),
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
        adapter_check = UniversalAdapterRegistryV2.validate()
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
        "runtime": "competitive-v7",
        "components": [
            "context-compiler-v2", "output-firewall-v2", "artifact-store-v2",
            "code-intelligence-graph-v3", "session-memory-dag-v2", "capability-security-v2",
            "secretless-provider-gateway-v2", "universal-adapter-contract-v2", "reference-agent-v2",
        ],
        "adapter_contract": UniversalAdapterRegistryV2.validate(),
        "external_claims": "NOT_PROVEN_WITHOUT_EXTERNAL_RECEIPTS",
    }

__all__ = [
    "ArtifactRecord", "ContentAddressedArtifactStoreV2", "ContextCompilerV2", "ContextIRItem",
    "ContextPackV2", "FirewallReceiptV2", "UniversalOutputFirewallV2",
    "IncrementalCodeIntelligenceGraph", "SessionMemoryDAGV2", "ADAPTERS_V2", "AdapterContractV2",
    "CapabilityDecisionV2", "CapabilitySecurityV2", "ReferenceCodingAgentV2",
    "SecretlessProviderGatewayV2", "UniversalAdapterRegistryV2", "CompetitiveRuntimeV7", "manifest",
]
