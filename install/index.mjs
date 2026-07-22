#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import process from "node:process";
import path from "node:path";
import { pathToFileURL } from "node:url";

const VERSION = "0.0.1";
const CHANNEL = "pre-release";
const PROFILES = new Set(["minimal", "balanced", "audit"]);
const REF_PATTERN = /^(?![-/])(?!.*(?:^|\/)\.\.(?:\/|$))[A-Za-z0-9._/-]+$/;

function usage() {
  return `SignalCore ${VERSION} ${CHANNEL} installer

Usage:
  npx @signalcore/install [options]
  npx github:Naveax/SignalCore [options]

Options:
  --project <path>       Project to configure (default: current directory)
  --profile <name>       minimal, balanced, or audit (default: minimal)
  --ref <git-ref>        Git ref to install from (default: main)
  --python <command>     Explicit Python executable
  --plan                 Print the exact non-shell command plan without changing the system
  --no-setup             Install the package but do not configure detected hosts
  --skip-status          Do not run the final status verification
  -h, --help             Show this help
`;
}

export function parseArgs(argv) {
  const options = {
    project: process.cwd(),
    profile: "minimal",
    ref: "main",
    python: "",
    plan: false,
    setup: true,
    status: true
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => {
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) throw new Error(`${arg} requires a value`);
      index += 1;
      return value;
    };
    if (arg === "--project") options.project = path.resolve(next());
    else if (arg === "--profile") options.profile = next();
    else if (arg === "--ref") options.ref = next();
    else if (arg === "--python") options.python = next();
    else if (arg === "--plan") options.plan = true;
    else if (arg === "--no-setup") options.setup = false;
    else if (arg === "--skip-status") options.status = false;
    else if (arg === "-h" || arg === "--help") options.help = true;
    else throw new Error(`unknown option: ${arg}`);
  }
  if (!PROFILES.has(options.profile)) throw new Error(`unsupported MCP profile: ${options.profile}`);
  if (!REF_PATTERN.test(options.ref)) throw new Error(`unsafe git ref: ${options.ref}`);
  return options;
}

function candidateCommands(explicit) {
  if (explicit) return [[explicit]];
  if (process.env.PYTHON) return [[process.env.PYTHON]];
  if (process.platform === "win32") {
    return [["py", "-3.13"], ["py", "-3.12"], ["py", "-3.11"], ["python"]];
  }
  return [["python3.13"], ["python3.12"], ["python3.11"], ["python3"], ["python"]];
}

function probe(candidate) {
  const [command, ...prefix] = candidate;
  const result = spawnSync(command, [
    ...prefix,
    "-c",
    "import sys; print('.'.join(map(str, sys.version_info[:3]))); raise SystemExit(sys.version_info < (3, 11))"
  ], { encoding: "utf8", shell: false });
  return result.status === 0
    ? { command, prefix, version: result.stdout.trim() }
    : null;
}

export function resolvePython(explicit = "") {
  for (const candidate of candidateCommands(explicit)) {
    const resolved = probe(candidate);
    if (resolved) return resolved;
  }
  throw new Error("Python 3.11 or newer is required. Install Python, then run this command again.");
}

function renderCommand(command, args) {
  return [command, ...args].map((value) => JSON.stringify(value)).join(" ");
}

function run(command, args) {
  const result = spawnSync(command, args, { stdio: "inherit", shell: false });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(`command failed with exit code ${result.status}: ${renderCommand(command, args)}`);
}

export function buildPlan(options, python) {
  const source = `git+https://github.com/Naveax/SignalCore.git@${options.ref}`;
  const installArgs = [
    ...python.prefix,
    "-m", "pip", "install",
    "--disable-pip-version-check",
    "--upgrade",
    source
  ];
  const setupArgs = [
    ...python.prefix,
    "-m", "signalcore_runtime",
    "--project", options.project,
    "setup", "--apply",
    "--mcp-profile", options.profile
  ];
  const statusArgs = [
    ...python.prefix,
    "-m", "signalcore_runtime",
    "--project", options.project,
    "status"
  ];
  return {
    installer: "@signalcore/install",
    version: VERSION,
    channel: CHANNEL,
    source,
    python: { command: python.command, prefix: python.prefix, version: python.version },
    project: options.project,
    profile: options.profile,
    commands: [
      { phase: "install", command: python.command, args: installArgs },
      ...(options.setup ? [{ phase: "setup", command: python.command, args: setupArgs }] : []),
      ...(options.status ? [{ phase: "status", command: python.command, args: statusArgs }] : [])
    ]
  };
}

export function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  if (options.help) {
    process.stdout.write(usage());
    return 0;
  }
  const python = resolvePython(options.python);
  const plan = buildPlan(options, python);
  if (options.plan) {
    process.stdout.write(`${JSON.stringify(plan, null, 2)}\n`);
    return 0;
  }
  process.stdout.write(`SignalCore ${VERSION} ${CHANNEL}: installing from ${options.ref}\n`);
  for (const item of plan.commands) {
    process.stdout.write(`\n[${item.phase}] ${renderCommand(item.command, item.args)}\n`);
    run(item.command, item.args);
  }
  process.stdout.write("\nSignalCore installation and verification completed.\n");
  return 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  try {
    process.exitCode = main();
  } catch (error) {
    process.stderr.write(`SignalCore installer failed: ${error instanceof Error ? error.message : String(error)}\n`);
    process.exitCode = 1;
  }
}
