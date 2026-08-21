# Guardrail Benchmark Report

- Generated: `2026-08-21T12:55:33.618389+00:00`
- Dataset SHA-256: `504ffc0be9291e301116035a0ae39d1d942073ecade540c6dd16a30c465b6faf`
- Result: **70/70 PASS** (100.00%)
- Runtime: `133.3651 ms`

## Quality Metrics

| Metric | Value |
|---|---:|
| Attack-block accuracy | 100.00% |
| Benign-allow accuracy | 100.00% |
| Output-protection accuracy | 100.00% |
| Median latency | 1.0463 ms |
| p95 latency | 2.2342 ms |

## Results By Category

| Category | Passed | Total | Pass rate |
|---|---:|---:|---:|
| `abuse_ban` | 1 | 1 | 100.00% |
| `abusive_language` | 3 | 3 | 100.00% |
| `action_contract` | 3 | 3 | 100.00% |
| `analysis_hiding` | 1 | 1 | 100.00% |
| `benign_allow` | 5 | 5 | 100.00% |
| `benign_output` | 1 | 1 | 100.00% |
| `context_contract` | 2 | 2 | 100.00% |
| `context_injection` | 1 | 1 | 100.00% |
| `conversation_binding` | 2 | 2 | 100.00% |
| `explicit_confirmation` | 8 | 8 | 100.00% |
| `input_validation` | 2 | 2 | 100.00% |
| `mutation_isolation` | 2 | 2 | 100.00% |
| `nested_action_contract` | 3 | 3 | 100.00% |
| `output_limits` | 1 | 1 | 100.00% |
| `payload_limits` | 1 | 1 | 100.00% |
| `pii_redaction` | 2 | 2 | 100.00% |
| `prompt_injection` | 6 | 6 | 100.00% |
| `prompt_leakage` | 3 | 3 | 100.00% |
| `rate_limit` | 1 | 1 | 100.00% |
| `role_injection` | 4 | 4 | 100.00% |
| `secret_exfiltration` | 2 | 2 | 100.00% |
| `secret_redaction` | 2 | 2 | 100.00% |
| `structured_redaction` | 3 | 3 | 100.00% |
| `tool_allowlist` | 2 | 2 | 100.00% |
| `tool_limits` | 2 | 2 | 100.00% |
| `tool_read_only_batch` | 1 | 1 | 100.00% |
| `tool_replay` | 1 | 1 | 100.00% |
| `tool_state` | 1 | 1 | 100.00% |
| `unicode_normalization` | 4 | 4 | 100.00% |

## Failures

No failed cases.

## Interpretation

This is a deterministic, offline policy benchmark. A pass demonstrates regression stability for the curated cases; it does not prove that every prompt injection or data-leak technique is covered. Authorization, rate limiting, domain validation and live-agent behavioral evaluation remain separate gates.
