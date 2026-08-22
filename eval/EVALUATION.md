# Evaluation pipeline

Hệ thống có hai benchmark tách biệt:

- `eval/benchmarks`: guardrail regression deterministic, chạy offline trong CI.
- `eval/golden`: behavioral golden set cho agent; có thể chấm prediction đã ghi
  hoặc gọi live agent khi được phép gửi prompt tới model provider.

## Metric được tính

| Nhóm | Metric | Nguồn |
|---|---|---|
| Chất lượng tác vụ | task success, intent accuracy/macro-F1, skill accuracy, tool accuracy | Golden expectation + agent trace |
| Tool | exact match, required-field match, field precision/recall/F1 | Tool-call arguments |
| Kết quả | response requirements, DB assertions, negative-case outcome accuracy | Response, DB trước/sau, negative predictions |
| An toàn/chất lượng sinh | forbidden-behavior rate, groundedness, hallucination rate | Deterministic check, LLM judge hoặc human review |
| Hiệu năng | latency p50/p95/p99, turn count, error rate | Runtime trace |
| Vận hành | input/output/total tokens, estimated cost/case/success | Provider usage + rate truyền qua CLI |
| Con người | task success, correctness, relevance, groundedness, safety, satisfaction, CSAT, agreement | CSV human review |
| Kỹ thuật | line coverage | `coverage.py` JSON |

Metric chưa có dữ liệu luôn là `null` trong JSON và `NOT_RUN` trong Markdown.
Không chuyển metric chưa chấm thành `0`, vì `0` có nghĩa là đã chấm và thất bại.

`task_success_rate` chỉ nhận `true/false` sau khi toàn bộ DB/policy check bắt buộc
của case đã được chấm. Các component metric vẫn có thể có số trong lúc task
success còn `null`; report luôn ghi denominator riêng cho forbidden behavior và
groundedness.

## Lệnh chạy

Tạo inventory report, không gọi model:

```powershell
.\.venv\Scripts\python.exe backend\scripts\run_agent_evaluation.py
```

Chấm lại prediction đã ghi và nhập coverage/human review:

```powershell
.\.venv\Scripts\python.exe backend\scripts\run_agent_evaluation.py `
  --predictions artifacts\agent-predictions.json `
  --coverage-json artifacts\coverage.json `
  --human-ratings eval\human\review_template.csv
```

Live run dùng model và một bản sao SQLite tạm thời, không ghi vào DB ứng dụng:

```powershell
.\.venv\Scripts\python.exe backend\scripts\run_agent_evaluation.py --live
```

Có thể smoke test bằng `--case SEARCH-001` hoặc giới hạn bằng `--max-cases 5`.
`--include-known-gaps` mới đưa `CANCEL-001` và `RESCHEDULE-001` vào live run.
Thêm `--llm-judge` nếu đã được phép gửi cả response và tool evidence đã redact
tới provider để chấm groundedness, hallucination và các forbidden behavior chưa
thể xác định deterministic. Report ghi rõ model judge; kết quả này vẫn cần đối
chiếu human review.

Chi phí không hard-code vì giá phụ thuộc provider/model và thay đổi theo thời
gian. Khi đã xác minh giá hiện hành, truyền:

```powershell
--input-cost-per-million <rate> --output-cost-per-million <rate>
```

Quality gate tùy chọn:

```powershell
--fail-under-task-success 0.80
```

## Prediction contract

Tối thiểu:

```json
{
  "cases": [
    {
      "case_id": "SEARCH-001",
      "intent": "search_options",
      "skill": "booking",
      "tool_calls": [
        {
          "name": "search_test_drive_options",
          "arguments": {"vehicle_model": "VF 3", "showroom_id": "117"}
        }
      ],
      "response": "...",
      "latency_ms": 1250,
      "token_usage": {"input_tokens": 500, "output_tokens": 80, "total_tokens": 580}
    }
  ],
  "negative_cases": [
    {"case_id": "NEG-001", "outcome": "DENY"}
  ]
}
```

Các field grader tùy chọn gồm `database_assertions`,
`forbidden_behavior_checks`, `groundedness_score` và
`hallucination_detected`. Scorer chỉ tính denominator khi check thực sự có dữ
liệu.

## Những giới hạn cần công bố

- 39 case agent hiện là synthetic và chưa human-review; 37 active, 2 known gap.
- Các case hold/confirm/OTP hiện chỉ có một lượt dù nghiệp vụ cần state từ lượt
  trước. Kết quả live phải được đọc cùng hạn chế này.
- `search_knowledge` đang là stub, nên chưa có corpus thật để tuyên bố RAG
  groundedness/faithfulness đạt chuẩn.
- Human satisfaction và CSAT chỉ hợp lệ sau khi có người dùng/reviewer thực.
- LLM-as-judge cần ghi rõ model/judge source; không thay thế hoàn toàn human
  review.
