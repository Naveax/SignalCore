from __future__ import annotations

from dataclasses import replace
from typing import Any


def install() -> None:
    from . import host_adapters
    from . import product_surface

    if getattr(host_adapters, "_signalcore_v001_platform_paths", False):
        return

    # These hosts load Agent Skills natively. Their project adapters should copy
    # SignalCore's skill and must not invent unsupported MCP/settings keys.
    for host in ("pi", "omp", "openclaw"):
        current = host_adapters.KNOWN_HOSTS[host]
        host_adapters.KNOWN_HOSTS[host] = replace(current, config_path="")

    # A generic editor executable or project directory is not proof that its AI
    # extension is installed. Only integration-specific files may trigger setup.
    vscode = host_adapters.KNOWN_HOSTS["vscode-copilot"]
    host_adapters.KNOWN_HOSTS["vscode-copilot"] = replace(
        vscode,
        project_markers=(".vscode/mcp.json", ".github/copilot-instructions.md"),
        user_markers=(),
    )
    jetbrains = host_adapters.KNOWN_HOSTS["jetbrains-copilot"]
    host_adapters.KNOWN_HOSTS["jetbrains-copilot"] = replace(
        jetbrains,
        project_markers=(".idea/mcp.json", ".github/copilot-instructions.md"),
        user_markers=(),
    )

    original_find_executable = host_adapters._find_executable

    def strict_find_executable(host: str) -> str | None:
        if host in {"vscode-copilot", "jetbrains-copilot"}:
            return None
        return original_find_executable(host)

    host_adapters._find_executable = strict_find_executable

    replacements = {
        "vscode-copilot": product_surface.PlatformAdapter(
            "vscode-copilot",
            (),
            (".vscode/mcp.json", ".github/copilot-instructions.md"),
            "instructions+mcp",
            True,
            False,
            False,
            "integration-marker-contract-tested",
        ),
        "jetbrains-copilot": product_surface.PlatformAdapter(
            "jetbrains-copilot",
            (),
            (".idea/mcp.json", ".github/copilot-instructions.md"),
            "instructions+mcp",
            True,
            False,
            False,
            "integration-marker-contract-tested",
        ),
        "kiro": product_surface.PlatformAdapter(
            "kiro",
            ("kiro", "kiro-cli", "q"),
            (".kiro/settings/mcp.json", ".kiro/skills/signal-core/SKILL.md"),
            "mcp+native-skill",
            True,
            True,
            True,
            "official-path-contract-tested",
        ),
        "pi": product_surface.PlatformAdapter(
            "pi",
            ("pi",),
            (".pi/settings.json", ".pi/skills/signal-core/SKILL.md"),
            "native-skill+extension-capable",
            False,
            True,
            True,
            "official-skill-path-contract-tested",
        ),
        "omp": product_surface.PlatformAdapter(
            "omp",
            ("omp",),
            (".omp/agent/config.yml", ".omp/skills/signal-core/SKILL.md"),
            "native-skill+mcp-capable-host",
            False,
            True,
            True,
            "official-skill-path-contract-tested",
        ),
        "openclaw": product_surface.PlatformAdapter(
            "openclaw",
            ("openclaw",),
            ("skills/signal-core/SKILL.md", ".openclaw/skills/signal-core/SKILL.md"),
            "workspace-skill+plugin-compatible",
            False,
            True,
            True,
            "official-skill-path-contract-tested",
        ),
    }
    product_surface.PLATFORM_ADAPTERS = tuple(
        replacements.get(item.host, item)
        for item in product_surface.PLATFORM_ADAPTERS
    )
    host_adapters._signalcore_v001_platform_paths = True
