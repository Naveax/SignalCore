export declare const SYNTAVRA_VERSION: "0.0.1";
export declare const SYNTAVRA_CHANNEL: "pre-release";
export type SyntavraWorkload = "coding-agent" | "repository-task" | "swe-bench" | "oolong-long-context" | "session-continuity" | "tool-routing";
export type SyntavraArm = "baseline" | "plain-host" | "syntavra" | "syntavra-minimal" | "syntavra-balanced" | "caveman" | "rtk" | "token-savior" | "jcodemunch" | "full-competitor-pack" | "context-mode" | "headroom" | "volt-lcm" | "recursive";
export type TokenSource = "system" | "skill_description" | "skill_body" | "tool_schema" | "repository_context" | "tool_output" | "memory" | "conversation_history" | "user_prompt" | "assistant_output" | "reasoning" | "cached";
export type AttributionConfidence = "PROVIDER_OBSERVED" | "LOCALLY_TOKENIZED" | "ESTIMATED" | "UNKNOWN";
export interface ProviderUsageReceipt {
    receipt_id: string;
    provider: string;
    model: string;
    request_id: string;
    session_id: string;
    repository_hash: string;
    integration_id: string;
    observed_at: string;
    wall_time_ms: number;
    input_tokens: number;
    cached_input_tokens: number;
    output_tokens: number;
    cost_usd: number;
    quality_score: number;
    success: boolean;
    synthetic: boolean;
    raw_usage_hash: string;
    workload: SyntavraWorkload;
    arm: SyntavraArm;
    task_id: string;
    repetition: number;
    metadata?: Record<string, unknown>;
}
export interface TokenAttributionReceipt {
    receipt_id: string;
    task_id: string;
    arm_id: string;
    repetition: number;
    session_id: string;
    provider: string;
    model: string;
    request_id_hash: string;
    provider_receipt_hash: string;
    sources: Partial<Record<TokenSource, number>>;
    confidence: Partial<Record<TokenSource, AttributionConfidence>>;
    baseline_tokens: number | null;
    baseline_confidence: AttributionConfidence;
    created_at: number;
    receipt_hash: string;
    metadata?: Record<string, unknown>;
}
export interface ReceiptValidation {
    ok: boolean;
    reasons: string[];
    billableInputTokens: number;
    totalTokens: number;
}
export interface AttributionValidation {
    ok: boolean;
    reasons: string[];
    observedTokens: number;
    avoidedTokens: number | null;
}
export declare function validateProviderUsageReceipt(receipt: ProviderUsageReceipt): ReceiptValidation;
export declare function assertProviderUsageReceipt(receipt: ProviderUsageReceipt): ProviderUsageReceipt;
export declare function validateTokenAttributionReceipt(receipt: TokenAttributionReceipt): AttributionValidation;
export declare function assertTokenAttributionReceipt(receipt: TokenAttributionReceipt): TokenAttributionReceipt;
