export const SYNTAVRA_VERSION = "0.0.1";
export const SYNTAVRA_CHANNEL = "pre-release";
const WORKLOADS = new Set([
    "coding-agent", "repository-task", "swe-bench", "oolong-long-context",
    "session-continuity", "tool-routing"
]);
const ARMS = new Set([
    "baseline", "plain-host", "syntavra", "syntavra-minimal", "syntavra-balanced",
    "caveman", "rtk", "token-savior", "jcodemunch", "full-competitor-pack",
    "context-mode", "headroom", "volt-lcm", "recursive"
]);
const TOKEN_SOURCES = new Set([
    "system", "skill_description", "skill_body", "tool_schema", "repository_context",
    "tool_output", "memory", "conversation_history", "user_prompt", "assistant_output",
    "reasoning", "cached"
]);
const CONFIDENCE = new Set([
    "PROVIDER_OBSERVED", "LOCALLY_TOKENIZED", "ESTIMATED", "UNKNOWN"
]);
const SHA256 = /^[0-9a-f]{64}$/;
export function validateProviderUsageReceipt(receipt) {
    const reasons = [];
    const required = [
        ["receipt_id", receipt.receipt_id], ["provider", receipt.provider], ["model", receipt.model],
        ["request_id", receipt.request_id], ["session_id", receipt.session_id],
        ["repository_hash", receipt.repository_hash], ["integration_id", receipt.integration_id],
        ["observed_at", receipt.observed_at], ["raw_usage_hash", receipt.raw_usage_hash],
        ["task_id", receipt.task_id]
    ];
    for (const [name, value] of required)
        if (!value)
            reasons.push(`missing-${name.replaceAll("_", "-")}`);
    if (!Number.isFinite(Date.parse(receipt.observed_at)))
        reasons.push("invalid-observed-at");
    if (!Number.isFinite(receipt.wall_time_ms) || receipt.wall_time_ms < 0)
        reasons.push("invalid-wall-time");
    for (const [name, value] of [["input-tokens", receipt.input_tokens], ["cached-input-tokens", receipt.cached_input_tokens], ["output-tokens", receipt.output_tokens]]) {
        if (!Number.isInteger(value) || value < 0)
            reasons.push(`invalid-${name}`);
    }
    if (receipt.cached_input_tokens > receipt.input_tokens)
        reasons.push("cached-input-exceeds-input");
    if (!Number.isFinite(receipt.cost_usd) || receipt.cost_usd < 0)
        reasons.push("invalid-cost");
    if (!Number.isFinite(receipt.quality_score) || receipt.quality_score < 0 || receipt.quality_score > 1)
        reasons.push("invalid-quality-score");
    if (!WORKLOADS.has(receipt.workload))
        reasons.push("unsupported-workload");
    if (!ARMS.has(receipt.arm))
        reasons.push("unsupported-arm");
    if (!Number.isInteger(receipt.repetition) || receipt.repetition < 1)
        reasons.push("invalid-repetition");
    if (receipt.raw_usage_hash.length < 32)
        reasons.push("weak-raw-usage-hash");
    const billableInputTokens = Math.max(0, receipt.input_tokens - receipt.cached_input_tokens);
    return { ok: reasons.length === 0, reasons: [...new Set(reasons)], billableInputTokens, totalTokens: billableInputTokens + receipt.output_tokens };
}
export function assertProviderUsageReceipt(receipt) {
    const validation = validateProviderUsageReceipt(receipt);
    if (!validation.ok)
        throw new Error(`invalid Syntavra receipt: ${validation.reasons.join(", ")}`);
    return receipt;
}
export function validateTokenAttributionReceipt(receipt) {
    const reasons = [];
    for (const [name, value] of [["receipt-id", receipt.receipt_id], ["task-id", receipt.task_id], ["arm-id", receipt.arm_id], ["session-id", receipt.session_id], ["provider", receipt.provider], ["model", receipt.model]]) {
        if (!value)
            reasons.push(`missing-${name}`);
    }
    if (!Number.isInteger(receipt.repetition) || receipt.repetition < 1)
        reasons.push("invalid-repetition");
    if (!SHA256.test(receipt.request_id_hash))
        reasons.push("invalid-request-id-hash");
    if (!SHA256.test(receipt.provider_receipt_hash))
        reasons.push("invalid-provider-receipt-hash");
    if (!SHA256.test(receipt.receipt_hash))
        reasons.push("invalid-receipt-hash");
    if (!Number.isFinite(receipt.created_at) || receipt.created_at <= 0)
        reasons.push("invalid-created-at");
    if (!CONFIDENCE.has(receipt.baseline_confidence))
        reasons.push("invalid-baseline-confidence");
    let observedTokens = 0;
    for (const [source, count] of Object.entries(receipt.sources)) {
        if (!TOKEN_SOURCES.has(source)) {
            reasons.push(`unknown-source:${source}`);
            continue;
        }
        if (!Number.isInteger(count) || count < 0) {
            reasons.push(`invalid-source-count:${source}`);
            continue;
        }
        observedTokens += count;
        const confidence = receipt.confidence[source] ?? "UNKNOWN";
        if (!CONFIDENCE.has(confidence))
            reasons.push(`invalid-confidence:${source}`);
    }
    if (observedTokens <= 0)
        reasons.push("no-positive-token-counts");
    if (receipt.baseline_tokens !== null && (!Number.isInteger(receipt.baseline_tokens) || receipt.baseline_tokens < observedTokens))
        reasons.push("invalid-baseline-tokens");
    const avoidedTokens = receipt.baseline_tokens === null ? null : Math.max(0, receipt.baseline_tokens - observedTokens);
    return { ok: reasons.length === 0, reasons: [...new Set(reasons)], observedTokens, avoidedTokens };
}
export function assertTokenAttributionReceipt(receipt) {
    const validation = validateTokenAttributionReceipt(receipt);
    if (!validation.ok)
        throw new Error(`invalid Syntavra attribution receipt: ${validation.reasons.join(", ")}`);
    return receipt;
}
