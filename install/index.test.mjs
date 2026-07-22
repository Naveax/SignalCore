import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { buildPlan, parseArgs } from "./index.mjs";

test("parses the one-command defaults without changing the version", () => {
  const parsed = parseArgs(["--plan"]);
  assert.equal(parsed.profile, "minimal");
  assert.equal(parsed.ref, "main");
  const plan = buildPlan(parsed, { command: "python3", prefix: [], version: "3.13.0" });
  assert.equal(plan.version, "0.0.1");
  assert.equal(plan.channel, "pre-release");
  assert.equal(plan.commands[0].phase, "install");
  assert.match(plan.source, /SignalCore\.git@main$/);
});

test("rejects unsafe refs and unknown profiles", () => {
  assert.throws(() => parseArgs(["--ref", "../main"]), /unsafe git ref/);
  assert.throws(() => parseArgs(["--profile", "everything"]), /unsupported MCP profile/);
});

test("help is executable without probing Python", () => {
  const result = spawnSync(process.execPath, ["install/index.mjs", "--help"], {
    cwd: new URL("..", import.meta.url),
    encoding: "utf8"
  });
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /npx @signalcore\/install/);
  assert.match(result.stdout, /0\.0\.1 pre-release/);
});
