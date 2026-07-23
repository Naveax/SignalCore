from __future__ import annotations

import os
import re
import shlex
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


_UNSAFE = re.compile(r"(?:\|\||&&|[|;`]|\$\(|\n|\r|>|<)")


@dataclass(frozen=True)
class RewriteRule:
    name: str
    executable: str
    argument_pattern: re.Pattern[str]
    append: tuple[str, ...] = ()
    replace: tuple[tuple[str, str], ...] = ()
    blocked_flags: tuple[str, ...] = ()
    reason: str = "reduce machine-irrelevant output"


@dataclass(frozen=True)
class RewriteResult:
    original: tuple[str, ...]
    rewritten: tuple[str, ...]
    changed: bool
    rule: str | None
    safe: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _rule(name: str, executable: str, pattern: str, *, append: Sequence[str] = (), replace: Sequence[tuple[str, str]] = (), blocked: Sequence[str] = (), reason: str = "reduce machine-irrelevant output") -> RewriteRule:
    return RewriteRule(name, executable, re.compile(pattern), tuple(append), tuple(replace), tuple(blocked), reason)


# 64 deterministic, fail-closed rewrite rules. Rules only add compact/non-interactive
# flags when the user did not request an incompatible human-oriented format.
RULES: tuple[RewriteRule, ...] = (
    _rule("git-status", "git", r"^status(?:\s|$)", append=("--porcelain=v2", "--branch"), blocked=("--short", "--porcelain", "-s")),
    _rule("git-log", "git", r"^log(?:\s|$)", append=("--oneline", "--decorate=no", "-n", "40"), blocked=("--format", "--pretty", "--oneline", "-p", "--patch")),
    _rule("git-diff-stat", "git", r"^diff(?:\s|$)", append=("--stat", "--compact-summary"), blocked=("--stat", "--name-only", "--name-status", "--numstat", "-p", "--patch")),
    _rule("git-show-stat", "git", r"^show(?:\s|$)", append=("--stat", "--oneline"), blocked=("--stat", "--format", "--pretty", "-p", "--patch")),
    _rule("git-branch", "git", r"^branch(?:\s|$)", append=("--format=%(refname:short) %(objectname:short) %(upstream:trackshort)" ,), blocked=("--format", "-v", "-vv")),
    _rule("git-stash", "git", r"^stash\s+list(?:\s|$)", append=("--format=%gd %h %s",), blocked=("--format",)),
    _rule("git-worktree", "git", r"^worktree\s+list(?:\s|$)", append=("--porcelain",), blocked=("--porcelain",)),
    _rule("git-fetch", "git", r"^fetch(?:\s|$)", append=("--quiet",), blocked=("--verbose", "-v", "--quiet")),
    _rule("git-remote", "git", r"^remote\s+-v(?:\s|$)", replace=(("-v", "get-url --all"),), blocked=()),
    _rule("git-tag", "git", r"^tag(?:\s|$)", append=("--sort=-creatordate",), blocked=("--sort", "--format")),
    _rule("rg", "rg", r".*", append=("--no-heading", "--line-number", "--color=never"), blocked=("--heading", "--json", "--vimgrep", "--color")),
    _rule("grep", "grep", r".*", append=("-n", "--color=never"), blocked=("-n", "--line-number", "--color")),
    _rule("fd", "fd", r".*", append=("--color=never",), blocked=("--color",)),
    _rule("find", "find", r".*", append=(), blocked=()),
    _rule("ls", "ls", r".*", append=("-1", "--color=never"), blocked=("-l", "--long", "-1", "--color")),
    _rule("tree", "tree", r".*", append=("--noreport", "-C"), blocked=("--noreport", "-C", "--dirsfirst")),
    _rule("pytest", "pytest", r".*", append=("-q", "--tb=short",), blocked=("-q", "--quiet", "-v", "--verbose", "--tb")),
    _rule("py-test", "py.test", r".*", append=("-q", "--tb=short"), blocked=("-q", "--quiet", "-v", "--verbose", "--tb")),
    _rule("cargo-test", "cargo", r"^test(?:\s|$)", append=("--quiet",), blocked=("--quiet", "-q", "--verbose", "-v")),
    _rule("cargo-check", "cargo", r"^check(?:\s|$)", append=("--quiet",), blocked=("--quiet", "-q", "--verbose", "-v")),
    _rule("go-test", "go", r"^test(?:\s|$)", append=("-json",), blocked=("-json", "-v")),
    _rule("npm-test", "npm", r"^(?:test|run\s+test)(?:\s|$)", append=("--silent",), blocked=("--silent", "--loglevel")),
    _rule("npm-list", "npm", r"^(?:list|ls)(?:\s|$)", append=("--depth=0", "--json"), blocked=("--depth", "--json", "--long")),
    _rule("pnpm-test", "pnpm", r"^(?:test|run\s+test)(?:\s|$)", append=("--silent",), blocked=("--silent", "--reporter")),
    _rule("pnpm-list", "pnpm", r"^(?:list|ls)(?:\s|$)", append=("--depth=0", "--json"), blocked=("--depth", "--json")),
    _rule("yarn-test", "yarn", r"^(?:test|run\s+test)(?:\s|$)", append=("--silent",), blocked=("--silent", "--verbose")),
    _rule("yarn-list", "yarn", r"^list(?:\s|$)", append=("--depth=0", "--json"), blocked=("--depth", "--json")),
    _rule("jest", "jest", r".*", append=("--silent", "--reporters=default"), blocked=("--silent", "--verbose", "--json", "--reporters")),
    _rule("vitest", "vitest", r".*", append=("--reporter=basic",), blocked=("--reporter", "--silent")),
    _rule("playwright", "playwright", r"^test(?:\s|$)", append=("--reporter=line",), blocked=("--reporter",)),
    _rule("ruff", "ruff", r"^(?:check|format)(?:\s|$)", append=("--output-format=concise",), blocked=("--output-format", "--verbose")),
    _rule("mypy", "mypy", r".*", append=("--no-error-summary", "--show-column-numbers"), blocked=("--pretty", "--no-error-summary")),
    _rule("eslint", "eslint", r".*", append=("--format=compact",), blocked=("--format", "-f")),
    _rule("biome", "biome", r"^(?:check|lint)(?:\s|$)", append=("--reporter=summary",), blocked=("--reporter",)),
    _rule("coverage", "coverage", r"^report(?:\s|$)", append=("--format=total",), blocked=("--format", "-m")),
    _rule("docker-build", "docker", r"^build(?:\s|$)", append=("--progress=plain",), blocked=("--progress", "--quiet", "-q")),
    _rule("docker-ps", "docker", r"^ps(?:\s|$)", append=("--format={{.ID}} {{.Image}} {{.Status}} {{.Names}}",), blocked=("--format",)),
    _rule("docker-images", "docker", r"^images(?:\s|$)", append=("--format={{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}",), blocked=("--format",)),
    _rule("docker-logs", "docker", r"^logs(?:\s|$)", append=("--tail=200",), blocked=("--tail", "-n", "--follow", "-f")),
    _rule("docker-inspect", "docker", r"^inspect(?:\s|$)", append=("--format={{json .}}",), blocked=("--format", "-f")),
    _rule("docker-stats", "docker", r"^stats(?:\s|$)", append=("--no-stream", "--format={{.Name}} {{.CPUPerc}} {{.MemUsage}}"), blocked=("--no-stream", "--format")),
    _rule("kubectl-get", "kubectl", r"^get(?:\s|$)", append=("-o", "json"), blocked=("-o", "--output", "-w", "--watch")),
    _rule("kubectl-describe", "kubectl", r"^describe(?:\s|$)", append=(), blocked=()),
    _rule("kubectl-logs", "kubectl", r"^logs(?:\s|$)", append=("--tail=200",), blocked=("--tail", "-f", "--follow")),
    _rule("kubectl-events", "kubectl", r"^events(?:\s|$)", append=("-o", "json"), blocked=("-o", "--output", "--watch")),
    _rule("gh-pr", "gh", r"^pr\s+(?:view|checks)(?:\s|$)", append=("--json", "number,title,state,statusCheckRollup"), blocked=("--json", "--web")),
    _rule("gh-issue", "gh", r"^issue\s+(?:list|view)(?:\s|$)", append=("--json", "number,title,state,labels"), blocked=("--json", "--web")),
    _rule("gh-run", "gh", r"^run\s+(?:list|view)(?:\s|$)", append=("--json", "databaseId,name,status,conclusion,headSha"), blocked=("--json", "--log")),
    _rule("pip-list", "pip", r"^list(?:\s|$)", append=("--format=json",), blocked=("--format", "--verbose")),
    _rule("pip-show", "pip", r"^show(?:\s|$)", append=(), blocked=()),
    _rule("uv-pip-list", "uv", r"^pip\s+list(?:\s|$)", append=("--format=json",), blocked=("--format",)),
    _rule("poetry-show", "poetry", r"^show(?:\s|$)", append=("--tree",), blocked=("--tree", "--latest")),
    _rule("terraform-plan", "terraform", r"^plan(?:\s|$)", append=("-no-color", "-compact-warnings"), blocked=("-json", "-no-color")),
    _rule("terraform-show", "terraform", r"^show(?:\s|$)", append=("-json",), blocked=("-json", "-no-color")),
    _rule("ansible", "ansible-playbook", r".*", append=("-v",), blocked=("-v", "-vv", "-vvv", "-vvvv")),
    _rule("aws", "aws", r".*", append=("--output", "json", "--no-cli-pager"), blocked=("--output", "--cli-auto-prompt")),
    _rule("gcloud", "gcloud", r".*", append=("--format=json", "--quiet"), blocked=("--format", "--verbosity")),
    _rule("az", "az", r".*", append=("--output", "json"), blocked=("--output", "-o")),
    _rule("systemctl", "systemctl", r"^(?:status|list-units)(?:\s|$)", append=("--no-pager", "--plain"), blocked=("--no-pager", "--output")),
    _rule("journalctl", "journalctl", r".*", append=("--no-pager", "-n", "200", "-o", "short-iso"), blocked=("--no-pager", "-n", "--lines", "-o", "--output", "-f")),
    _rule("dotnet-test", "dotnet", r"^test(?:\s|$)", append=("--verbosity", "minimal"), blocked=("--verbosity", "-v")),
    _rule("maven-test", "mvn", r".*", append=("-q",), blocked=("-q", "-X", "--debug")),
    _rule("gradle-test", "gradle", r".*", append=("--console=plain", "--warning-mode=summary"), blocked=("--console", "--info", "--debug")),
    _rule("cmake", "cmake", r".*", append=("--log-level=WARNING",), blocked=("--log-level", "--trace")),
    _rule("ctest", "ctest", r".*", append=("--output-on-failure", "--no-tests=error"), blocked=("--verbose", "-V")),
    _rule("git-grep", "git", r"^grep(?:\s|$)", append=("-n",), blocked=("-n", "--line-number", "--column")),
    _rule("git-reflog", "git", r"^reflog(?:\s|$)", append=("--oneline", "-n", "40"), blocked=("--format", "--pretty", "--oneline", "-n", "--max-count")),
    _rule("git-shortlog", "git", r"^shortlog(?:\s|$)", append=("-sne",), blocked=("-s", "-n", "-e", "--summary", "--numbered", "--email")),
    _rule("cargo-tree", "cargo", r"^tree(?:\s|$)", append=("--depth", "3"), blocked=("--depth", "--prefix", "--format")),
    _rule("cargo-metadata", "cargo", r"^metadata(?:\s|$)", append=("--format-version", "1", "--no-deps"), blocked=("--format-version", "--no-deps", "--filter-platform")),
    _rule("cargo-audit", "cargo", r"^audit(?:\s|$)", append=("--json",), blocked=("--json", "--quiet")),
    _rule("cargo-deny", "cargo", r"^deny(?:\s|$)", append=("--format", "json"), blocked=("--format",)),
    _rule("cargo-nextest", "cargo", r"^nextest\s+run(?:\s|$)", append=("--status-level", "fail", "--final-status-level", "fail"), blocked=("--status-level", "--final-status-level")),
    _rule("go-vet", "go", r"^vet(?:\s|$)", append=("-json",), blocked=("-json", "-v")),
    _rule("go-list", "go", r"^list(?:\s|$)", append=("-json",), blocked=("-json", "-f", "-template")),
    _rule("golangci-lint", "golangci-lint", r"^(?:run)?(?:\s|$)", append=("--out-format=line-number",), blocked=("--out-format", "--output")),
    _rule("govulncheck", "govulncheck", r".*", append=("-json",), blocked=("-json", "-mode")),
    _rule("bun-test", "bun", r"^(?:test|run\s+test)(?:\s|$)", append=("--reporter=dot",), blocked=("--reporter", "--verbose")),
    _rule("bun-install", "bun", r"^(?:install|add|update)(?:\s|$)", append=("--silent",), blocked=("--silent", "--verbose")),
    _rule("deno-test", "deno", r"^test(?:\s|$)", append=("--quiet",), blocked=("--quiet", "--reporter")),
    _rule("deno-lint", "deno", r"^lint(?:\s|$)", append=("--json",), blocked=("--json", "--compact")),
    _rule("mocha", "mocha", r".*", append=("--reporter", "dot"), blocked=("--reporter", "-R")),
    _rule("ava", "ava", r".*", append=("--tap",), blocked=("--tap", "--verbose")),
    _rule("tox", "tox", r".*", append=("-q",), blocked=("-q", "--quiet", "-v", "--verbose")),
    _rule("semgrep", "semgrep", r".*", append=("--json", "--quiet"), blocked=("--json", "--quiet", "--text")),
    _rule("sqlfluff", "sqlfluff", r"^(?:lint|parse)(?:\s|$)", append=("--format", "json"), blocked=("--format", "-f")),
    _rule("trivy", "trivy", r".*", append=("--format", "json", "--quiet"), blocked=("--format", "-f", "--quiet")),
    _rule("snyk", "snyk", r"^(?:test|code\s+test|container\s+test)(?:\s|$)", append=("--json",), blocked=("--json", "--sarif")),
    _rule("composer-show", "composer", r"^show(?:\s|$)", append=("--format=json",), blocked=("--format", "-f")),
    _rule("phpunit", "phpunit", r".*", append=("--colors=never",), blocked=("--colors", "--testdox")),
    _rule("rspec", "rspec", r".*", append=("--format", "progress", "--no-color"), blocked=("--format", "-f", "--color", "--no-color")),
    _rule("swift-test", "swift", r"^test(?:\s|$)", append=("--quiet",), blocked=("--quiet", "--verbose")),
    _rule("xcodebuild", "xcodebuild", r".*", append=("-quiet",), blocked=("-quiet", "-verbose")),
    _rule("jq", "jq", r".*", append=("-c",), blocked=("-c", "--compact-output", "-r", "--raw-output")),
    _rule("yq", "yq", r".*", append=("-o=json", "-I=0"), blocked=("-o", "--output-format", "-I", "--indent")),
    _rule("sqlite3", "sqlite3", r".*", append=("-json",), blocked=("-json", "-csv", "-table", "-line")),
    _rule("psql", "psql", r".*", append=("--csv", "--quiet"), blocked=("--csv", "--quiet", "-q", "--tuples-only")),
    _rule("mysql", "mysql", r".*", append=("--batch", "--skip-column-names"), blocked=("--batch", "-B", "--skip-column-names", "-N")),
    _rule("redis-cli", "redis-cli", r".*", append=("--raw",), blocked=("--raw", "--json", "--csv")),
    _rule("gh-release", "gh", r"^release\s+list(?:\s|$)", append=("--json", "tagName,name,isDraft,isPrerelease,publishedAt"), blocked=("--json", "--web")),
    _rule("gh-workflow", "gh", r"^workflow\s+list(?:\s|$)", append=("--json", "id,name,state"), blocked=("--json", "--web")),
    _rule("gh-secret", "gh", r"^secret\s+list(?:\s|$)", append=("--json", "name,updatedAt"), blocked=("--json",)),
    _rule("gh-variable", "gh", r"^variable\s+list(?:\s|$)", append=("--json", "name,value,updatedAt"), blocked=("--json",)),
    _rule("gh-codespace", "gh", r"^codespace\s+list(?:\s|$)", append=("--json", "name,state,repository"), blocked=("--json",)),
    _rule("docker-system", "docker", r"^system\s+df(?:\s|$)", append=("--format={{json .}}",), blocked=("--format", "-v", "--verbose")),
    _rule("docker-volume", "docker", r"^volume\s+ls(?:\s|$)", append=("--format={{json .}}",), blocked=("--format", "-q", "--quiet")),
    _rule("docker-network", "docker", r"^network\s+ls(?:\s|$)", append=("--format={{json .}}",), blocked=("--format", "-q", "--quiet")),
    _rule("hadolint", "hadolint", r".*", append=("--format", "json"), blocked=("--format", "-f")),
    _rule("shellcheck", "shellcheck", r".*", append=("--format", "json1"), blocked=("--format", "-f")),
    _rule("bats", "bats", r".*", append=("--formatter", "tap"), blocked=("--formatter", "-F")),
    _rule("bazel", "bazel", r"^(?:test|build)(?:\s|$)", append=("--noshow_progress", "--ui_event_filters=-info"), blocked=("--show_progress", "--noshow_progress", "--ui_event_filters")),
    _rule("buck2", "buck2", r"^(?:test|build)(?:\s|$)", append=("--console=simple",), blocked=("--console",)),
    _rule("pants", "pants", r".*", append=("--level=warn",), blocked=("--level",)),
    _rule("msbuild", "msbuild", r".*", append=("-nologo", "-verbosity:minimal"), blocked=("-nologo", "-verbosity", "/verbosity")),
    _rule("terraform-validate", "terraform", r"^validate(?:\s|$)", append=("-json",), blocked=("-json", "-no-color")),
    _rule("helm-list", "helm", r"^list(?:\s|$)", append=("-o", "json"), blocked=("-o", "--output")),
    _rule("helm-status", "helm", r"^status(?:\s|$)", append=("-o", "json"), blocked=("-o", "--output")),
    _rule("kubectl-config", "kubectl", r"^config\s+get-contexts(?:\s|$)", append=("-o", "name"), blocked=("-o", "--output")),
)


class CommandRewriteEngine:
    def __init__(self, rules: Sequence[RewriteRule] = RULES):
        self.rules = tuple(rules)

    @staticmethod
    def _parse(command: str | Iterable[str]) -> tuple[tuple[str, ...], bool]:
        if isinstance(command, str):
            unsafe = bool(_UNSAFE.search(command))
            try:
                return tuple(shlex.split(command, posix=os.name != "nt")), unsafe
            except ValueError:
                return tuple(command.split()), True
        return tuple(str(item) for item in command), False

    @staticmethod
    def _executable_index(argv: Sequence[str]) -> int | None:
        index = 0
        assignment = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*")
        while index < len(argv) and assignment.fullmatch(argv[index]):
            index += 1
        while index < len(argv):
            wrapper = Path(argv[index]).name.casefold()
            if wrapper not in {"command", "env", "sudo", "time"}:
                break
            index += 1
            if wrapper == "env":
                while index < len(argv) and assignment.fullmatch(argv[index]):
                    index += 1
            if index < len(argv) and argv[index].startswith("-"):
                return None
        return index if index < len(argv) else None

    @staticmethod
    def _arguments(argv: Sequence[str]) -> str:
        return " ".join(argv[1:]).casefold()

    @staticmethod
    def _has_blocked(argv: Sequence[str], blocked: Sequence[str]) -> bool:
        for token in argv[1:]:
            for flag in blocked:
                if token == flag or token.startswith(flag + "="):
                    return True
        return False

    def rewrite(self, command: str | Iterable[str]) -> RewriteResult:
        argv, unsafe = self._parse(command)
        if not argv:
            return RewriteResult(argv, argv, False, None, False, "empty command")
        if unsafe:
            return RewriteResult(argv, argv, False, None, False, "shell composition is not rewritten")
        executable_index = self._executable_index(argv)
        if executable_index is None:
            return RewriteResult(argv, argv, False, None, False, "wrapper options are not rewritten")
        command_argv = argv[executable_index:]
        executable = Path(command_argv[0]).name.casefold()
        args = self._arguments(command_argv)
        for rule in self.rules:
            if executable != rule.executable or not rule.argument_pattern.search(args):
                continue
            if self._has_blocked(command_argv, rule.blocked_flags):
                return RewriteResult(argv, argv, False, rule.name, True, "explicit user format preserved")
            rewritten_command = list(command_argv)
            for before, after in rule.replace:
                try:
                    index = rewritten_command.index(before)
                except ValueError:
                    continue
                rewritten_command[index:index + 1] = shlex.split(after)
            rewritten_command.extend(rule.append)
            result = tuple([*argv[:executable_index], *rewritten_command])
            return RewriteResult(argv, result, result != argv, rule.name, True, rule.reason)
        return RewriteResult(argv, argv, False, None, True, "no matching rewrite rule")

    def manifest(self) -> dict[str, object]:
        return {
            "rules": [rule.name for rule in self.rules],
            "count": len(self.rules),
            "fail_closed": True,
            "shell_composition_rewritten": False,
            "safe_wrappers": ["command", "env", "sudo", "time"],
            "target_minimum": 110,
            "coverage_gate": len(self.rules) >= 110,
        }
