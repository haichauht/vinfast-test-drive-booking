# Guardrail Benchmark Report

- Generated: `2026-08-22T08:30:51.004415+00:00`
- Dataset SHA-256: `eb34119f3d6c7da494f5cfa3ba520c67a61cb52203330179c8d7366da0ea7a7f`
- Result: **82/82 PASS** (100.00%)
- Runtime: `157.7182 ms`
- Category coverage gate: **PASS** (30 categories)

## Quality Metrics

| Metric | Value |
|---|---:|
| Attack-block accuracy | 100.00% |
| Benign-allow accuracy | 100.00% |
| Output-protection accuracy | 100.00% |
| Median latency | 0.9396 ms |
| p95 latency | 2.0661 ms |

## Results By Category

| Category | Passed | Total | Pass rate |
|---|---:|---:|---:|
| `abuse_ban` | 2 | 2 | 100.00% |
| `abusive_language` | 3 | 3 | 100.00% |
| `action_contract` | 3 | 3 | 100.00% |
| `analysis_hiding` | 2 | 2 | 100.00% |
| `benign_allow` | 5 | 5 | 100.00% |
| `benign_output` | 2 | 2 | 100.00% |
| `context_contract` | 2 | 2 | 100.00% |
| `context_injection` | 2 | 2 | 100.00% |
| `conversation_binding` | 2 | 2 | 100.00% |
| `explicit_confirmation` | 8 | 8 | 100.00% |
| `indirect_injection` | 2 | 2 | 100.00% |
| `input_validation` | 2 | 2 | 100.00% |
| `mutation_isolation` | 2 | 2 | 100.00% |
| `nested_action_contract` | 3 | 3 | 100.00% |
| `output_limits` | 2 | 2 | 100.00% |
| `payload_limits` | 2 | 2 | 100.00% |
| `pii_redaction` | 2 | 2 | 100.00% |
| `prompt_injection` | 6 | 6 | 100.00% |
| `prompt_leakage` | 3 | 3 | 100.00% |
| `rate_limit` | 2 | 2 | 100.00% |
| `role_injection` | 4 | 4 | 100.00% |
| `secret_exfiltration` | 2 | 2 | 100.00% |
| `secret_redaction` | 2 | 2 | 100.00% |
| `structured_redaction` | 3 | 3 | 100.00% |
| `tool_allowlist` | 2 | 2 | 100.00% |
| `tool_limits` | 2 | 2 | 100.00% |
| `tool_read_only_batch` | 2 | 2 | 100.00% |
| `tool_replay` | 2 | 2 | 100.00% |
| `tool_state` | 2 | 2 | 100.00% |
| `unicode_normalization` | 4 | 4 | 100.00% |

## Failures

No failed cases.

## Interpretation

This is a deterministic, offline policy benchmark. A pass demonstrates regression stability for the curated cases; it does not prove that every prompt injection or data-leak technique is covered. Authorization, rate limiting, domain validation and live-agent behavioral evaluation remain separate gates.
