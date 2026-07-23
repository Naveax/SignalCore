import assert from "node:assert/strict";
import test from "node:test";
import {
  SYNTAVRA_CHANNEL,
  SYNTAVRA_VERSION,
  assertProviderUsageReceipt,
  assertTokenAttributionReceipt,
  validateProviderUsageReceipt,
  validateTokenAttributionReceipt
} from "../dist/receipts.js";

function receipt(overrides = {}) {
  return {
    receipt_id: "receipt-1", provider: "openai", model: "test-model", request_id: "request-1",
    session_id: "session-1", repository_hash: "a".repeat(64), integration_id: "codex",
    observed_at: "2026-07-22T00:00:00Z", wall_time_ms: 1250, input_tokens: 1000,
    cached_input_tokens: 200, output_tokens: 300, cost_usd: 0.01, quality_score: 1,
    success: true, synthetic: false, raw_usage_hash: "b".repeat(64), workload: "coding-agent",
    arm: "syntavra", task_id: "task-1", repetition: 1, ...overrides
  };
}

function attribution(overrides = {}) {
  return {
    receipt_id: "attr-1", task_id: "task-1", arm_id: "syntavra-minimal", repetition: 1,
    session_id: "session-1", provider: "openai", model: "test-model",
    request_id_hash: "c".repeat(64), provider_receipt_hash: "d".repeat(64),
    sources: {tool_schema: 100, repository_context: 200, tool_output: 50},
    confidence: {tool_schema: "LOCALLY_TOKENIZED", repository_context: "LOCALLY_TOKENIZED", tool_output: "PROVIDER_OBSERVED"},
    baseline_tokens: 1000, baseline_confidence: "LOCALLY_TOKENIZED", created_at: 1_800_000_000,
    receipt_hash: "e".repeat(64), ...overrides
  };
}

test("keeps the package identity locked", () => {
  assert.equal(SYNTAVRA_VERSION, "0.0.1");
  assert.equal(SYNTAVRA_CHANNEL, "pre-release");
});

test("calculates billable and total token use", () => {
  const result = validateProviderUsageReceipt(receipt());
  assert.equal(result.ok, true); assert.equal(result.billableInputTokens, 800); assert.equal(result.totalTokens, 1100);
});

test("accepts the current external competitor arm vocabulary", () => {
  assert.equal(validateProviderUsageReceipt(receipt({arm: "caveman"})).ok, true);
  assert.equal(validateProviderUsageReceipt(receipt({arm: "syntavra-balanced"})).ok, true);
});

test("fails closed on invalid provider receipt data", () => {
  const invalid = receipt({observed_at: "not-a-date", cached_input_tokens: 1001, raw_usage_hash: "short", quality_score: 2});
  const result = validateProviderUsageReceipt(invalid);
  assert.equal(result.ok, false);
  for (const reason of ["invalid-observed-at", "cached-input-exceeds-input", "weak-raw-usage-hash", "invalid-quality-score"]) assert.ok(result.reasons.includes(reason));
  assert.throws(() => assertProviderUsageReceipt(invalid), /invalid Syntavra receipt/);
});

test("validates source attribution and avoided tokens", () => {
  const result = validateTokenAttributionReceipt(attribution());
  assert.equal(result.ok, true); assert.equal(result.observedTokens, 350); assert.equal(result.avoidedTokens, 650);
  assert.equal(assertTokenAttributionReceipt(attribution()).arm_id, "syntavra-minimal");
});

test("fails closed on unknown attribution sources and weak linkage", () => {
  const invalid = attribution({request_id_hash: "short", sources: {made_up: 5}, baseline_tokens: 1});
  const result = validateTokenAttributionReceipt(invalid);
  assert.equal(result.ok, false);
  assert.ok(result.reasons.includes("invalid-request-id-hash"));
  assert.ok(result.reasons.includes("unknown-source:made_up"));
  assert.throws(() => assertTokenAttributionReceipt(invalid), /invalid Syntavra attribution receipt/);
});
