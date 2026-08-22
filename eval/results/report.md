# Evaluation status — 2026-08-22

Đây là bảng tổng hợp các số đã thực sự chạy. `NOT_RUN` nghĩa là chưa có evidence
hợp lệ, không đồng nghĩa với 0%.

## Kết quả hiện có

| Metric | Target | Actual | Status |
|---|---:|---:|---|
| Deterministic guardrail benchmark | 100% | 82/82 (100%) | PASS |
| Attack block accuracy | 100% | 100% | PASS |
| Benign allow accuracy | 100% | 100% | PASS |
| Output protection accuracy | 100% | 100% | PASS |
| Guardrail latency p95 | Theo dõi regression | 2.0661 ms | PASS baseline |
| Backend tests | 100% pass | 428/428 | PASS |
| Backend line coverage | >60% | 78.01% | PASS |
| Behavioral task success | >80% | NOT_RUN | PENDING |
| Intent/tool/argument quality | Thiết lập sau baseline | NOT_RUN | PENDING |
| End-to-end response latency p95 | <3 s | NOT_RUN | PENDING |
| Groundedness/hallucination | Thiết lập sau corpus thật | NOT_RUN | BLOCKED BY RAG STUB |
| User satisfaction | >4/5 | NOT_RUN | NEEDS HUMAN REVIEW |
| Negative-case outcome accuracy | 100% | NOT_RUN | NEEDS EXECUTABLE FIXTURES |

## Evidence

- Guardrail baseline: `eval/benchmarks/results/baseline.json` và `baseline.md`.
- Behavioral inventory/coverage: `eval/results/agent-evaluation.json` và
  `agent-evaluation.md`.
- Metric definitions/commands: `eval/EVALUATION.md`.
- Human rubric/template: `eval/human/RUBRIC.md` và `review_template.csv`.
- Suite hiện tại được chạy tách để cô lập fixture lớn: 423/423 test thường và
  5/5 test import V5 đều pass.
- Coverage 78.01% được tái tính từ full-suite coverage hoàn chỉnh cho phần source
  không đổi và coverage mới nhất của evaluator sau hardening (4.588/5.881
  statements). Vòng coverage cuối bị treo bất thường ở fixture import V5 nên
  không được dùng làm một run hoàn chỉnh mới.

## Kết luận

Coverage kỹ thuật và guardrail regression đã vượt gate. Chưa được tuyên bố
agent đạt response accuracy, latency, groundedness hay satisfaction cho đến khi
chạy đủ 37 active golden case qua provider được phép và hoàn tất human review.
