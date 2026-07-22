from .competitive_common_v7 import *
from .competitive_graph_v7 import IncrementalCodeIntelligenceGraph
from .competitive_memory_v7 import SessionMemoryDAGV2
from .competitive_security_v7 import CapabilitySecurityV2

@dataclass(frozen=True)
class AdapterContractV2:
    adapter_id: str
    product: str
    surface: str
    level: str
    integration_modes: tuple[str, ...]
    detection_commands: tuple[str, ...]
    config_paths: tuple[str, ...]
    capabilities: dict[str, bool]
    maturity: str = "contract-tested"


ADAPTERS_V2: tuple[AdapterContractV2, ...] = (
    AdapterContractV2("codex-cli", "Codex CLI", "cli", "A", ("mcp", "skill", "provider-proxy", "session"), ("codex",), ("~/.codex/config.toml", "AGENTS.md"), {"tool_interception": True, "mcp": True, "session_events": True, "provider_proxy": True, "native_approval": True, "stream_interception": True}),
    AdapterContractV2("claude-code", "Claude Code", "cli", "A", ("plugin", "hooks", "mcp", "provider-proxy"), ("claude",), ("~/.claude/settings.json", ".claude/settings.json"), {"tool_interception": True, "mcp": True, "session_events": True, "provider_proxy": True, "native_approval": True, "stream_interception": True}),
    AdapterContractV2("gemini-cli", "Gemini CLI", "cli", "A", ("extension", "mcp", "provider-proxy"), ("gemini",), ("~/.gemini/settings.json", "GEMINI.md"), {"tool_interception": True, "mcp": True, "session_events": True, "provider_proxy": True, "native_approval": False, "stream_interception": True}),
    AdapterContractV2("github-copilot-vscode", "GitHub Copilot for VS Code", "ide", "B", ("mcp", "instructions", "extension"), ("code",), (".vscode/mcp.json", ".github/copilot-instructions.md"), {"tool_interception": True, "mcp": True, "session_events": True, "provider_proxy": False, "native_approval": True, "stream_interception": True}),
    AdapterContractV2("github-copilot-jetbrains", "GitHub Copilot for JetBrains", "ide", "C", ("mcp", "instructions", "plugin"), (), (".idea", ".github/copilot-instructions.md"), {"tool_interception": False, "mcp": True, "session_events": False, "provider_proxy": False, "native_approval": True, "stream_interception": False}),
    AdapterContractV2("cursor", "Cursor", "ide", "B", ("mcp", "rules", "provider-proxy"), ("cursor",), (".cursor/mcp.json", ".cursor/rules"), {"tool_interception": True, "mcp": True, "session_events": True, "provider_proxy": True, "native_approval": True, "stream_interception": True}),
    AdapterContractV2("windsurf", "Windsurf", "ide", "B", ("mcp", "rules", "provider-proxy"), ("windsurf",), (".codeium/windsurf/mcp_config.json", ".windsurfrules"), {"tool_interception": True, "mcp": True, "session_events": True, "provider_proxy": True, "native_approval": True, "stream_interception": True}),
    AdapterContractV2("kiro", "Kiro", "ide", "B", ("mcp", "steering", "hooks"), (), (".kiro/settings/mcp.json", ".kiro/steering"), {"tool_interception": True, "mcp": True, "session_events": True, "provider_proxy": False, "native_approval": True, "stream_interception": True}),
    AdapterContractV2("zed", "Zed", "ide", "C", ("mcp", "settings"), ("zed",), (".zed/settings.json", "~/.config/zed/settings.json"), {"tool_interception": False, "mcp": True, "session_events": False, "provider_proxy": False, "native_approval": False, "stream_interception": False}),
    AdapterContractV2("cline", "Cline", "ide-extension", "B", ("mcp", "rules", "hooks"), (), (".clinerules", ".vscode/mcp.json"), {"tool_interception": True, "mcp": True, "session_events": True, "provider_proxy": False, "native_approval": True, "stream_interception": True}),
    AdapterContractV2("roo-code", "Roo Code", "ide-extension", "B", ("mcp", "rules", "hooks"), (), (".roo/rules", ".vscode/mcp.json"), {"tool_interception": True, "mcp": True, "session_events": True, "provider_proxy": False, "native_approval": True, "stream_interception": True}),
    AdapterContractV2("continue", "Continue", "ide-extension", "C", ("mcp", "config"), (), (".continue/config.yaml", "~/.continue/config.yaml"), {"tool_interception": False, "mcp": True, "session_events": True, "provider_proxy": True, "native_approval": False, "stream_interception": False}),
    AdapterContractV2("opencode", "OpenCode", "cli", "A", ("mcp", "hooks", "provider-proxy", "session"), ("opencode",), ("opencode.json", "~/.config/opencode/opencode.json"), {"tool_interception": True, "mcp": True, "session_events": True, "provider_proxy": True, "native_approval": True, "stream_interception": True}),
    AdapterContractV2("aider", "Aider", "cli", "D", ("wrapper", "provider-proxy", "session"), ("aider",), (".aider.conf.yml", "~/.aider.conf.yml"), {"tool_interception": False, "mcp": False, "session_events": True, "provider_proxy": True, "native_approval": False, "stream_interception": False}),
    AdapterContractV2("openhands", "OpenHands", "platform", "B", ("sdk", "mcp", "provider-proxy", "sandbox"), (), ("openhands.toml", ".openhands"), {"tool_interception": True, "mcp": True, "session_events": True, "provider_proxy": True, "native_approval": True, "stream_interception": True}),
    AdapterContractV2("openclaw", "OpenClaw", "platform", "B", ("plugin", "mcp", "session"), ("openclaw",), ("~/.openclaw/config.json",), {"tool_interception": True, "mcp": True, "session_events": True, "provider_proxy": True, "native_approval": True, "stream_interception": True}),
    AdapterContractV2("pi", "Pi", "cli", "B", ("extension", "hooks", "session"), ("pi",), ("~/.pi/agent/settings.json",), {"tool_interception": True, "mcp": False, "session_events": True, "provider_proxy": True, "native_approval": True, "stream_interception": True}),
    AdapterContractV2("oh-my-pi", "Oh My Pi", "cli", "B", ("plugin", "hooks", "session"), ("omp",), ("~/.config/omp/config.json",), {"tool_interception": True, "mcp": False, "session_events": True, "provider_proxy": True, "native_approval": True, "stream_interception": True}),
    AdapterContractV2("qwen-code", "Qwen Code", "cli", "C", ("mcp", "instructions", "provider-proxy"), ("qwen", "qwen-code"), ("QWEN.md", "~/.qwen/settings.json"), {"tool_interception": False, "mcp": True, "session_events": True, "provider_proxy": True, "native_approval": False, "stream_interception": False}),
    AdapterContractV2("antigravity", "Antigravity", "ide", "C", ("mcp", "rules"), (), (".antigravity",), {"tool_interception": False, "mcp": True, "session_events": False, "provider_proxy": False, "native_approval": False, "stream_interception": False}),
)


class UniversalAdapterRegistryV2:
    @staticmethod
    def records() -> list[dict[str, Any]]:
        return [asdict(item) for item in ADAPTERS_V2]

    @staticmethod
    def detect(*, home: Path | None = None, project: Path | None = None) -> list[dict[str, Any]]:
        import shutil
        home = home or Path.home()
        project = project or Path.cwd()
        rows: list[dict[str, Any]] = []
        for adapter in ADAPTERS_V2:
            commands = [command for command in adapter.detection_commands if shutil.which(command)]
            configs: list[str] = []
            for candidate in adapter.config_paths:
                expanded = Path(os.path.expanduser(candidate))
                if not expanded.is_absolute():
                    expanded = project / expanded
                if expanded.exists():
                    configs.append(str(expanded))
            rows.append(asdict(adapter) | {"detected": bool(commands or configs), "detected_commands": commands, "existing_configs": configs})
        return rows

    @staticmethod
    def validate() -> dict[str, Any]:
        ids = [item.adapter_id for item in ADAPTERS_V2]
        levels = Counter(item.level for item in ADAPTERS_V2)
        surfaces = Counter(item.surface for item in ADAPTERS_V2)
        required_capabilities = {"tool_interception", "mcp", "session_events", "provider_proxy", "native_approval", "stream_interception"}
        invalid = [item.adapter_id for item in ADAPTERS_V2 if set(item.capabilities) != required_capabilities]
        return {
            "ok": len(ids) == len(set(ids)) and not invalid and len(ids) >= 20,
            "adapters": len(ids),
            "levels": dict(levels),
            "surfaces": dict(surfaces),
            "non_cli_adapters": sum(item.surface != "cli" for item in ADAPTERS_V2),
            "invalid": invalid,
            "live_boundary": "live certification requires external execution receipts",
        }


class ReferenceCodingAgentV2:
    """Small provider-neutral planner using graph, memory, firewall, and capabilities."""

    def __init__(
        self,
        *,
        project: Path,
        graph: IncrementalCodeIntelligenceGraph,
        memory: SessionMemoryDAGV2,
        security: CapabilitySecurityV2,
    ):
        self.project = project
        self.graph = graph
        self.memory = memory
        self.security = security

    def plan(self, task: str, *, session_id: str | None = None, max_symbols: int = 12) -> dict[str, Any]:
        session = self.memory.open(session_id, metadata={"goal": task, "agent": "reference-v2"})
        session_id = session["session_id"]
        self.memory.append(session_id, "task", {"goal": task})
        symbols = self.graph.query(task, limit=max_symbols)
        candidate_paths = list(dict.fromkeys(item["path"] for item in symbols))
        steps = [
            {"id": "understand", "tool": "repo.search", "arguments": {"query": task}, "resource": "workspace:/", "requires": []},
            {"id": "inspect", "tool": "repo.read", "arguments": {"paths": candidate_paths[:8]}, "resource": "workspace:/", "requires": ["understand"]},
            {"id": "patch", "tool": "repo.patch", "arguments": {"paths": candidate_paths[:8]}, "resource": "workspace:/", "requires": ["inspect", "explicit-user-authorization"]},
            {"id": "test", "tool": "test.run", "arguments": {"strategy": "affected-tests"}, "resource": "workspace:/", "requires": ["patch", "sandbox", "explicit-user-authorization"]},
            {"id": "finish", "tool": "task.finish", "arguments": {"receipt": True}, "resource": "workspace:/", "requires": ["test"]},
        ]
        decisions = []
        for step in steps:
            decision = self.security.decide(
                step["tool"], step["arguments"], resource=step["resource"],
                sandboxed=True,
                user_authorized=step["tool"] not in {"repo.patch", "test.run"},
            )
            decisions.append(asdict(decision))
        plan = {
            "version": VERSION,
            "channel": CHANNEL,
            "session_id": session_id,
            "task": task,
            "candidate_symbols": symbols,
            "candidate_paths": candidate_paths,
            "steps": steps,
            "preflight_decisions": decisions,
            "execution_mode": "plan-only-until-authorized",
            "worktree": {"required": True, "isolation": "git-worktree", "rollback": "discard-worktree"},
        }
        plan["plan_hash"] = sha256_bytes(canonical_json(plan))
        self.memory.append(session_id, "plan", {"plan_hash": plan["plan_hash"], "paths": candidate_paths, "steps": [step["id"] for step in steps]})
        return plan

