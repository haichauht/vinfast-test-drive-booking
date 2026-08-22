# Agent Evaluation Report

- Generated: **2026-08-22T10:17:20Z**
- Dataset: **vinfast_booking_agent_golden** (39 cases)
- Behavioral run: **NOT_RUN** (0 attempted; 0/37 active cases fully scored)

## Quality

| Metric | Result | Scored cases |
|---|---:|---:|
| Task success | NOT_RUN | 0 |
| Intent accuracy | NOT_RUN | 0 |
| Intent macro-F1 | NOT_RUN | 0 |
| Skill accuracy | NOT_RUN | 0 |
| Tool accuracy | NOT_RUN | 0 |
| Required argument match | NOT_RUN | 0 |
| Argument field F1 | NOT_RUN | 0 |
| Response requirements | NOT_RUN | 0 |
| Database assertions | NOT_RUN | 0 |
| Forbidden behavior rate | NOT_RUN | 0 |
| Mean groundedness | NOT_RUN | 0 |
| Hallucination rate | NOT_RUN | 0 |

## Performance and operations

| Metric | Result |
|---|---:|
| Latency p50 | NOT_RUN ms |
| Latency p95 | NOT_RUN ms |
| Latency p99 | NOT_RUN ms |
| Error rate | NOT_RUN |
| Total tokens | NOT_RUN |
| Estimated cost | NOT_RUN |
| Test line coverage | 78.0100% |

## Security and human evaluation

- Negative-case outcome accuracy: **NOT_RUN** (0/12).
- Human review: **NOT_RUN**; case coverage NOT_RUN.
- Human task success: **NOT_RUN**.
- Satisfaction: **NOT_RUN/5**; CSAT 4–5: **NOT_RUN**.

## Case status

| Case | Status | Intent | Skill | Tool |
|---|---|---:|---:|---:|
| `SEARCH-001` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `HOLD-001` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `CONFIRM-001` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `CONFLICT-001` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `HOLD_EXPIRED-001` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `OTP_BAD-001` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `OTP_EXPIRED-001` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `CANCEL-001` | known_gap | NOT_RUN | NOT_RUN | NOT_RUN |
| `RESCHEDULE-001` | known_gap | NOT_RUN | NOT_RUN | NOT_RUN |
| `INJECTION-001` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `PII-001` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `ADVISE-001` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `SEARCH-002` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `HOLD-002` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `ADVISE-002` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `SEARCH-003` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `HOLD-003` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `ADVISE-003` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `SEARCH-004` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `HOLD-004` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `ADVISE-004` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `SEARCH-005` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `HOLD-005` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `ADVISE-005` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `SEARCH-006` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `HOLD-006` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `ADVISE-006` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `SEARCH-007` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `HOLD-007` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `SEARCH-008` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `HOLD-008` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `SEARCH-009` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `HOLD-009` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `SEARCH-010` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `HOLD-010` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `MODEL-NOT-IN-SHOWROOM-001` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `MODEL-UNSUPPORTED-001` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `STAFF-CAPACITY-001` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |
| `BOOK-FOR-OTHER-001` | not_run | NOT_RUN | NOT_RUN | NOT_RUN |

## Interpretation limits

- Component scores may be available while task success remains null until every required DB/policy check is graded.
- LLM-as-judge scores and human ratings must identify their source; missing reviews are not converted to zero.
- Token totals are only complete when the runtime/provider returns usage metadata for every model call.
