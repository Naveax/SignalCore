from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from signalcore_runtime.host_adapters import detect_hosts, host_spec
from signalcore_runtime.product_surface import PlatformAdapterRegistry
from signalcore_runtime.zero_friction import ZeroFrictionManager


class OfficialPlatformAdaptersV001Tests(unittest.TestCase):
    def test_official_adapter_paths_are_exposed_without_invented_config_mutation(self) -> None:
        kiro = host_spec("kiro")
        self.assertEqual(kiro.config_path, ".kiro/settings/mcp.json")
        self.assertEqual(kiro.skill_path, ".kiro/skills/signal-core")
        self.assertTrue(kiro.supports_mcp)

        for host, skill_path in (
            ("pi", ".pi/skills/signal-core"),
            ("omp", ".omp/skills/signal-core"),
            ("openclaw", "skills/signal-core"),
        ):
            spec = host_spec(host)
            self.assertEqual(spec.config_path, "", host)
            self.assertEqual(spec.skill_path, skill_path, host)
            self.assertTrue(spec.supports_native_skill, host)

        records = {row["host"]: row for row in PlatformAdapterRegistry.records()}
        self.assertEqual(records["kiro"]["config_candidates"][0], ".kiro/settings/mcp.json")
        self.assertIn(".pi/skills/signal-core/SKILL.md", records["pi"]["config_candidates"])
        self.assertIn(".omp/skills/signal-core/SKILL.md", records["omp"]["config_candidates"])
        self.assertIn("skills/signal-core/SKILL.md", records["openclaw"]["config_candidates"])

    def test_skill_only_hosts_install_without_writing_unverified_config(self) -> None:
        cases = (
            ("pi", ".pi", ".pi/skills/signal-core/SKILL.md", ".pi/settings.json"),
            ("omp", ".omp", ".omp/skills/signal-core/SKILL.md", ".omp/agent/config.yml"),
            ("openclaw", ".openclaw", "skills/signal-core/SKILL.md", "openclaw.json"),
        )
        for host, marker, skill, config in cases:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as directory:
                project = Path(directory)
                (project / marker).mkdir(parents=True)
                state = project / ".signalcore" / "pre-release"
                manager = ZeroFrictionManager(project, state)
                self.assertIn(host, manager.detected_hosts())
                result = manager.install(dry_run=False)
                self.assertTrue(result["ok"], result)
                matching = [row for row in result["host_results"] if row["host"] == host]
                self.assertEqual(len(matching), 1, result)
                self.assertTrue(matching[0]["verification"]["ok"])
                self.assertTrue((project / skill).is_file())
                self.assertFalse((project / config).exists())
                self.assertTrue(manager.doctor()["ok"])

    def test_kiro_installs_real_mcp_config_and_native_skill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".kiro").mkdir()
            manager = ZeroFrictionManager(project, project / ".signalcore" / "pre-release")
            result = manager.install(dry_run=False)
            self.assertTrue(result["ok"], result)
            self.assertTrue((project / ".kiro/settings/mcp.json").is_file())
            self.assertTrue((project / ".kiro/skills/signal-core/SKILL.md").is_file())
            self.assertTrue(manager.doctor()["ok"])

    def test_generic_repository_markers_do_not_false_detect_coding_agents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".github").mkdir()
            (project / ".vscode").mkdir()
            (project / "AGENTS.md").write_text("# Generic agents file\n", encoding="utf-8")
            with patch("shutil.which", return_value=None):
                detected = {row["host"] for row in detect_hosts(project, home=project / "empty-home")}
            self.assertNotIn("jetbrains-copilot", detected)
            self.assertNotIn("qwen-code", detected)
            self.assertNotIn("aider", detected)
            self.assertNotIn("sourcegraph-cody", detected)
            # VS Code remains a legitimate project marker, but GitHub alone no longer triggers it.
            self.assertIn("vscode-copilot", detected)

    def test_github_cli_alone_does_not_false_detect_copilot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)

            def which(name: str) -> str | None:
                return "/usr/bin/gh" if name == "gh" else None

            with patch("shutil.which", side_effect=which):
                detected = {row["host"] for row in detect_hosts(project, home=project / "home")}
            self.assertNotIn("vscode-copilot", detected)


if __name__ == "__main__":
    unittest.main()
