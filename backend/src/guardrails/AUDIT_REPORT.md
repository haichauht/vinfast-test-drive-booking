# Guardrails Security Audit Report

## 1. Thông tin audit

| Thuộc tính | Giá trị |
|---|---|
| Phạm vi | Public chat input, structured actions, tool pre-execution, public output và application trace logging |
| Phương pháp | Manual code review, abuse-case modeling, unit/integration regression và deterministic benchmark |
| Thành phần | `src/guardrails`, `src/api/routes.py`, `src/agents/graph.py`, `src/agents/trace.py`, booking tool boundary |
| Ngoài phạm vi | Hạ tầng gateway/WAF, cloud IAM, secret store, provider security và pentest production |
| Benchmark | 52 curated cases: input, output và tool |
| Kết luận | Các finding trực tiếp trong phạm vi đã được remediation và có regression gate; residual risk được liệt kê riêng |

Audit này đánh giá defense-in-depth ở biên AI/tool. Nó không thay thế
authentication, authorization trong domain service, rate limiting, database
constraints, dependency scanning hoặc kiểm thử xâm nhập.

## 2. Data flow và trust boundaries

```text
Untrusted client
  │ ChatRequest / DemoActionRequest
  ▼
Pydantic schema
  │
  ├── InputGuard: normalize, payload budget, injection, action contracts
  │      └── block: safe response, no agent invocation
  ▼
Classifier / active skill
  │
  ▼
GuardedToolNode: skill allowlist, call budget, replay, mutation isolation,
  │              explicit confirmation
  ├── block: ToolMessage(error), no tool execution
  ▼
Domain service: validation, authorization, idempotency, transaction
  │
  ▼
OutputGuard: hide analysis, redact secret/PII, prompt-leak fallback, truncate
  │
  ▼
Public ChatResponse
```

Logging là một boundary song song: request, LLM message, tool args/result và
response đi qua `trace.redact()` trước khi ghi structured event.

## 3. Risk rating

- **Critical**: có thể gây mutation trái phép hoặc lộ credential có tác động
  trực tiếp trên production.
- **High**: có đường bypass/leak thực tế nhưng cần điều kiện hoặc phạm vi hẹp.
- **Medium**: defense-in-depth thiếu, denial-of-service nhỏ hoặc false-positive
  đáng kể.
- **Low**: maintainability/observability có thể làm policy drift trong tương lai.

## 4. Findings và remediation

### GR-001 — Negated confirmation được hiểu là đồng ý

| Thuộc tính | Giá trị |
|---|---|
| Mức độ | High |
| Trạng thái | Fixed |
| Vấn đề | Regex cũ tìm keyword `confirm/xác nhận/chốt` nên “Tôi không xác nhận” vẫn có thể cho phép tool chốt booking. |
| Remediation | Thêm normalized negative-confirmation policy chạy trước positive match; structured UI action vẫn là explicit authorization path. |
| Unit test | `test_blocks_confirmation_when_user_phrase_is_explicitly_negated` |
| Benchmark | `TOOL-CONFIRM-003`, `TOOL-CONFIRM-004` |

### GR-002 — Unicode compatibility và bidi controls có thể né input pattern

| Thuộc tính | Giá trị |
|---|---|
| Mức độ | High |
| Trạng thái | Fixed |
| Vấn đề | NFC không fold full-width ASCII và danh sách ký tự loại bỏ không bao phủ toàn bộ Unicode format controls. |
| Remediation | Chuyển sang NFKC; loại category `Cf` và control character không phải tab/newline. |
| Unit test | `test_blocks_injection_obfuscated_with_unicode_compatibility_or_bidi_controls` |
| Benchmark | `INPUT-ATTACK-008` đến `INPUT-ATTACK-010` |

### GR-003 — Structured action chỉ allowlist top-level

| Thuộc tính | Giá trị |
|---|---|
| Mức độ | High |
| Trạng thái | Fixed |
| Vấn đề | `booker_patch`, `driver_patch`, license/notification patch có thể chứa field không bao giờ hợp lệ; một object không đúng type có thể rơi xuống service. |
| Remediation | Thêm nested contract riêng cho chat và demo actions; block unknown field và non-object trước tool/service. |
| Unit test | `test_blocks_unknown_nested_structured_action_fields`, `test_blocks_non_object_nested_structured_action_field` |
| Benchmark | `INPUT-CONTRACT-003` đến `INPUT-CONTRACT-005` |

### GR-004 — Output redaction bỏ sót key naming variants và backend token

| Thuộc tính | Giá trị |
|---|---|
| Mức độ | High |
| Trạng thái | Fixed |
| Vấn đề | Exact snake-case comparison không bắt camel/kebab/space variants; `access_token` không nằm trong denylist của `action_data`. |
| Remediation | Canonicalize sensitive keys; mở rộng secret policy; redact backend access/refresh/session token, key/hash/private credential nhưng vẫn giữ hai workflow capability cần thiết. |
| Unit test | `test_redacts_sensitive_key_naming_variants_and_backend_tokens_from_action_data` |
| Benchmark | `OUTPUT-REDACTION-005`, `OUTPUT-REDACTION-006`, `OUTPUT-REDACTION-007` |

### GR-005 — Direct credential assignment và prompt marker coverage hẹp

| Thuộc tính | Giá trị |
|---|---|
| Mức độ | High |
| Trạng thái | Fixed |
| Vấn đề | Text-only secret như `openrouter_api_key=...`, `authorization: Bearer ...` hoặc một số developer/system markers có thể không có structured metadata để literal-redact. |
| Remediation | Mở rộng assignment regex và system/developer leak patterns; safe fallback thay toàn bộ response khi phát hiện prompt marker. |
| Unit test | `test_redacts_direct_credential_assignments_without_structured_secret_metadata`, `test_replaces_additional_system_prompt_leak_markers` |
| Benchmark | `OUTPUT-REDACTION-003`, `OUTPUT-LEAK-001` đến `OUTPUT-LEAK-003` |

### GR-006 — Trace logging policy drift so với public output

| Thuộc tính | Giá trị |
|---|---|
| Mức độ | High |
| Trạng thái | Fixed |
| Vấn đề | Logger có danh sách secret riêng, thiếu một số key và không redact direct credential assignment trong free text. |
| Remediation | Trace dùng sensitive-key policy tập trung, cùng canonicalization và assignment redaction; bổ sung regression test trên structured log record. |
| Unit test | `test_trace_redaction.py` |
| Benchmark | Output redaction cases kiểm chứng policy tương ứng; trace có unit gate riêng để tránh ghi report chứa log secret. |

### GR-007 — Production có thể cấu hình tắt deterministic guardrails

| Thuộc tính | Giá trị |
|---|---|
| Mức độ | Medium |
| Trạng thái | Fixed |
| Vấn đề | `GUARDRAILS_ENABLED=false` từng hợp lệ ở mọi environment. |
| Remediation | Settings fail startup nếu production tắt guardrails; debug bypass chỉ còn ở development/test. |
| Unit test | `test_production_cannot_disable_guardrails` |
| Benchmark | Không áp dụng; đây là configuration invariant. |

## 5. Control matrix

| Threat | Prevent | Detect/test | Residual control |
|---|---|---|---|
| Prompt/role injection | NFKC + high-confidence patterns + context scan | Input unit/API/benchmark | Skill allowlist và domain authorization vẫn là primary containment |
| Tool privilege escalation | Per-skill allowlist | Tool unit/benchmark | Tool schema và service permission checks |
| Duplicate/batched mutation | Fingerprint + mutation isolation | Tool unit/benchmark | Idempotency key và DB transaction |
| Accidental confirmation | Explicit/negation-aware confirmation | Unit/benchmark | UI structured confirmation and optimistic version |
| Payload abuse | Byte/depth/node/string/call budget | Unit/API/benchmark | Gateway body/rate limits |
| Secret/PII leak | Key/text redaction + prompt fallback | Output/trace/API/benchmark | Minimize data before LLM, HTTPS, proxy log policy |
| Cross-booking access | Access-session scope in service | Service negative tests | OTP limits, token TTL/revocation, database constraints |

## 6. Residual risks và open actions

### RR-001 — Regex không bao phủ mọi prompt injection

- Mức độ: Medium.
- Chấp nhận tạm thời: Có.
- Lý do: homoglyph đa script, encoding nhiều lớp và semantic jailbreak không thể
  được giải quyết đầy đủ bằng regex.
- Containment: tool allowlist, action contract, authorization, output redaction.
- Điều kiện đóng/giảm: bổ sung adversarial corpus từ incident/red-team; cân nhắc
  classifier riêng nhưng không thay deterministic boundaries.

### RR-002 — Workflow capability vẫn xuất hiện trong `action_data`

- Mức độ: Medium.
- `challenge_id` và `access_session_token` được giữ có chủ ý để frontend hoàn
  tất OTP flow; chúng không được phép xuất hiện trong natural-language response,
  log hoặc diagnostic `tool_input`.
- Yêu cầu vận hành: HTTPS, CORS allowlist, không log response body ở proxy/APM,
  không persist token dài hạn trong browser, TTL/revocation bắt buộc.

### RR-003 — Draft booking ID là capability trước khi xác thực OTP

- Mức độ: Medium.
- `get/update/confirm` held draft dùng opaque booking ID và optimistic version
  trong luồng tạo booking. Đây là domain design, không chỉ guardrail.
- Open action: threat-model entropy, lifetime, conversation binding và replay;
  cân nhắc draft capability token riêng nếu public exposure mở rộng.

### RR-004 — Rate limiting/gateway controls nằm ngoài module

- Mức độ: High nếu endpoint public Internet không có gateway protection.
- Cần kiểm chứng deployment: per-IP/session limit cho chat, hold, confirm và OTP;
  request body limit; alert burst/anomaly. Guardrails payload budget không thay
  rate limiting.

### RR-005 — Live LLM behavior chưa được chứng minh bởi offline benchmark

- Mức độ: Medium.
- `eval/golden` hiện có behavioral specification nhưng schema validation không
  phải behavioral pass.
- Open action: chạy live evaluation trên DB cô lập, pin model/prompt/config,
  chấm tool/arguments/response/DB assertion và báo riêng known gaps.

## 7. Release checklist

- [ ] `APP_ENV=production` không thể khởi động khi guardrails tắt.
- [ ] Targeted guardrail/API tests pass.
- [ ] 52/52 deterministic benchmark cases pass.
- [ ] Full backend regression và Ruff pass.
- [ ] Không có raw secret/PII trong stdout, logs hoặc generated report.
- [ ] Action/tool mới đã cập nhật top-level và nested contract.
- [ ] Mutating tool mới đã được phân loại và có confirmation/idempotency policy.
- [ ] Gateway rate limit, HTTPS, CORS và proxy logging được kiểm chứng ở deployment.
- [ ] Residual risk/open action mới có owner và điều kiện đóng.

## 8. Cách cập nhật audit

Mỗi policy change phải cập nhật đồng thời code, test, benchmark dataset và phần
finding/control liên quan. Không chuyển finding sang `Fixed` nếu mới chỉ có tài
liệu hoặc unit test nhưng enforcement path chưa được nối vào API/graph thực tế.
