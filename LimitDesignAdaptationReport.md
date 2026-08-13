# Limit Design Adaptation Report

Báo cáo này đánh giá mức độ phù hợp của tài liệu thiết kế limit/budget với source code hiện tại của project, đồng thời tóm tắt các thay đổi cần thực hiện, vị trí code bị ảnh hưởng, ảnh hưởng tới nghiệp vụ/DB và rủi ro khi triển khai.

## Kết Luận Nhanh

Thiết kế trong tài liệu phù hợp với kiến trúc hiện tại của project. Project đang dùng FastAPI + LangGraph, user phần lớn anonymous, provider chính là OpenAI/OpenRouter, DB hỗ trợ PostgreSQL/SQLite và hiện chưa có Redis. Vì vậy hướng `interface-first`, không bắt Redis ngay, dùng PostgreSQL làm source of truth cho budget ledger là hợp lý.

Tuy nhiên, để adapt tốt vào source hiện tại, không nên chỉ vá từng chỗ gọi `llm.ainvoke`. Nên có một `LLMGateway`/wrapper chung làm choke point duy nhất cho mọi provider call. Đây là điểm quan trọng nhất để tránh logic budget, call count, tracing bị rải rác trong `classifier_node.py`, `booking_skill_node.py`, `advise_skill_node.py`.

Mức độ phù hợp tổng thể: cao.

- HTTP rate limit theo `anon_session_id + IP`: phù hợp ngay.
- Budget theo `global/day`, `anon_session/day`, `conversation`, `turn`: phù hợp nhưng cần bổ sung `turn_id`.
- PostgreSQL ledger: phù hợp vì project đã có DB abstraction và Docker compose có PostgreSQL.
- Redis: chưa cần bắt buộc ở phase đầu, nhưng store interface nên chừa đường thay thế.
- Atomic reserve bằng DB transaction/row locking: cần thiết nếu production có nhiều request đồng thời.

## Source Hiện Tại Liên Quan

Các điểm source hiện có hỗ trợ tốt cho thiết kế:

- Backend là FastAPI: `backend/src/main.py`, `backend/src/api/routes.py`.
- Agent dùng LangGraph: `backend/src/agents/graph.py`.
- Có `conversation_id` làm thread id: `backend/src/api/routes.py`.
- Có `trace_id`: `backend/src/api/routes.py`.
- Có tool loop limit `MAX_TOOL_CALLS = 8`: `backend/src/agents/graph.py`.
- Có tool-call-per-message limit trong guardrails: `backend/src/config.py`, `backend/src/guardrails/tool_guard.py`.
- Có provider abstraction tối thiểu cho OpenAI/OpenRouter: `backend/src/services/llm.py`.
- DB abstraction hỗ trợ SQLite/PostgreSQL: `backend/src/database`.
- Có schema tập trung: `backend/src/database/schema.py`.

Các điểm còn thiếu so với thiết kế:

- Chưa có `turn_id` semantic cho một request `/chat`.
- Chưa có `LLMGateway` là choke point duy nhất.
- Chưa có `max_llm_calls_per_turn`.
- Budget ledger hiện cần bổ sung field theo thiết kế như `turn_id`, `provider`, `reservation_microusd`, `actual_cost_microusd`.
- Chưa có atomic budget bucket/counter riêng; nếu chỉ `SUM` ledger trước mỗi call thì có rủi ro race condition.
- Chưa có pricing registry theo provider/model.
- Chưa có logic timeout `unknown`/reconcile cho provider call không rõ đã bị charge hay chưa.

## Đánh Giá Theo Từng Thành Phần Thiết Kế

### 1. HTTP Rate Limit

Mức độ phù hợp: cao.

Thiết kế đề xuất rate limit theo:

- IP burst.
- anonymous session burst.

Điều này phù hợp với project vì chưa có login/user account. `conversation_id` không nên dùng làm identity chính vì client có thể tự tạo nhiều conversation mới.

Code cần thực hiện:

- Thêm `ClientIdentityResolver` để cấp/đọc `anon_session_id`.
- Thêm middleware rate limit trong FastAPI.
- Store counter qua interface `RateLimitStore`.
- Local/test có thể memory; production nên dùng PostgreSQL trước, Redis sau nếu scale.

Phần code bị ảnh hưởng:

- `backend/src/main.py`: gắn middleware.
- `backend/src/config.py`: thêm config rate limit.
- `backend/src/security/client_identity.py`: module mới.
- `backend/src/security/rate_limit.py`: module mới.
- `.env.example`: thêm config.

Ảnh hưởng nghiệp vụ:

- Không đổi logic booking/agent.
- `/chat` hoặc `/demo/action` có thể trả `429` trước khi vào route.
- Frontend cần xử lý `429` để báo user gửi quá nhanh.

Ảnh hưởng DB:

- Nếu production dùng PostgreSQL store, cần thêm bảng counter như `rate_limit_counters`.
- Nếu phase đầu memory-only cho local, không cần DB cho local.

Rủi ro:

- Nếu IP lấy từ proxy header mà cấu hình sai, attacker có thể spoof IP để bypass.
- Nếu limit IP quá chặt, nhiều user cùng NAT/Wi-Fi có thể bị ảnh hưởng.
- Nếu dùng PostgreSQL cho rate limit traffic cao, DB có thể bị tăng write load. Redis sẽ phù hợp hơn khi scale.

### 2. Agent Execution Limit

Mức độ phù hợp: rất cao, nhưng source cần bổ sung.

Thiết kế chỉ ra điểm đúng: một HTTP request không tương đương một provider call. Một `/chat` có thể gồm classifier LLM, skill LLM, tool loop, rồi lại skill LLM.

Source hiện đã có:

- `MAX_TOOL_CALLS = 8`
- `guardrails_max_tool_calls_per_message = 3`

Nên bổ sung:

- `turn_id`.
- `max_llm_calls_per_turn`.
- `max_estimated_cost_per_turn`.

Code cần thực hiện:

- Sinh `turn_id` trong `/api/v1/chat`.
- Truyền `turn_id` vào agent state metadata.
- Mọi LLM call phải đi qua gateway để tăng/check counter theo turn.

Phần code bị ảnh hưởng:

- `backend/src/api/routes.py`
- `backend/src/agents/state.py`
- `backend/src/agents/nodes/classifier_node.py`
- `backend/src/agents/nodes/booking_skill_node.py`
- `backend/src/agents/nodes/advise_skill_node.py`
- Module mới `backend/src/services/llm_gateway.py`

Ảnh hưởng nghiệp vụ:

- Không thay đổi nghiệp vụ booking nếu limit chưa chạm.
- Khi agent loop bất thường, request kết thúc sớm bằng message an toàn thay vì tiếp tục gọi provider/tool.

Ảnh hưởng DB:

- Nếu cần audit từng call, ledger nên lưu `turn_id`.
- Nếu chỉ enforce in-process cho một turn, không bắt buộc DB, nhưng budget/cost vẫn nên ghi DB.

Rủi ro:

- Nếu `max_llm_calls_per_turn` quá thấp, các flow booking hợp lệ có thể bị cắt giữa chừng.
- Cần test các flow nhiều bước: search, hold, update draft, confirm, request/verify access.

### 3. Budget Hierarchy

Mức độ phù hợp: cao.

Thiết kế đề xuất hierarchy:

- turn.
- conversation.
- anonymous session/day.
- global/day.
- IP/day optional abuse guard.

Điểm này phù hợp hơn thiết kế chỉ có `global/session/IP` vì:

- `turn` chặn một request đơn lẻ trở nên quá đắt.
- `conversation` chặn một chat kéo dài đốt tiền.
- `anon_session/day` là quota gần với anonymous user nhất.
- `global/day` là hard cap bảo vệ toàn hệ thống.
- `IP/day` chỉ nên là secondary guard vì NAT có thể gom nhiều user.

Code cần thực hiện:

- Thêm config:
  - `LLM_TURN_MAX_COST_USD`
  - `LLM_CONVERSATION_MAX_COST_USD`
  - `LLM_SESSION_MAX_COST_USD_PER_DAY`
  - `LLM_GLOBAL_MAX_COST_USD_PER_DAY`
  - `LLM_IP_MAX_COST_USD_PER_DAY`
- Budget check phải kiểm tra tất cả bucket trước khi gọi provider.
- Không coi `conversation_id` là user identity chính.

Phần code bị ảnh hưởng:

- `backend/src/config.py`
- `backend/src/services/usage_budget.py` hoặc `backend/src/services/llm_gateway.py`
- `backend/src/database/schema.py`
- `backend/src/api/routes.py`

Ảnh hưởng nghiệp vụ:

- User có thể bị chặn nếu vượt quota dù tốc độ gửi không cao.
- Chat UI nên trả message thân thiện qua response bình thường, không nhất thiết HTTP 429.

Ảnh hưởng DB:

- Cần ledger/counter theo `turn_id`, `conversation_id`, `anon_session_id`, `client_ip`, `usage_date`.
- Nên lưu amount bằng integer `microUSD`, không dùng float.

Rủi ro:

- Estimate quá conservative sẽ deny user sớm.
- Estimate quá thấp sẽ vẫn vượt budget thực tế.
- Nếu không atomic reserve, request đồng thời có thể cùng pass budget check và vượt cap.

### 4. PostgreSQL Ledger

Mức độ phù hợp: cao.

Project đã có PostgreSQL trong Docker compose và DB abstraction. Vì vậy dùng PostgreSQL làm source of truth cho accounting là phù hợp.

Thiết kế ledger nên gồm:

- `id`
- `trace_id`
- `turn_id`
- `conversation_id`
- `anon_session_id`
- `client_ip`
- `provider`
- `model`
- `estimated_input_tokens`
- `estimated_output_tokens`
- `estimated_cost_microusd`
- `reservation_microusd`
- `actual_input_tokens`
- `actual_output_tokens`
- `actual_cost_microusd`
- `status`
- `created_at`
- `completed_at`

Status:

- `reserved`
- `completed`
- `released`
- `failed`
- `unknown`

Code cần thực hiện:

- Mở rộng `backend/src/database/schema.py`.
- Mở rộng `TABLES` để `QueryGuard` cho phép bảng/cột mới.
- Thêm migration legacy cho SQLite/PostgreSQL nếu DB đã tồn tại.

Ảnh hưởng DB:

- Có schema mới.
- Có thêm write mỗi lần LLM call.
- Có thêm query aggregate/counter trước mỗi LLM call.

Rủi ro:

- Dùng `SELECT SUM(...)` trước mỗi call có thể chậm khi ledger lớn.
- Nên có bảng counter/bucket riêng hoặc row locking để reserve atomic.
- Cần index theo `usage_date`, `anon_session_id`, `conversation_id`, `turn_id`, `status`.

### 5. LLM Gateway

Mức độ phù hợp: rất cao, nên làm trước khi mở rộng nhiều policy.

Hiện source gọi LLM trực tiếp trong các node:

- `classifier_node.py`
- `booking_skill_node.py`
- `advise_skill_node.py`

Thiết kế đề xuất `LLMGateway` làm choke point duy nhất là đúng. Gateway nên lo:

1. max LLM calls per turn.
2. estimate tokens.
3. estimate cost.
4. atomic reserve.
5. provider call.
6. extract usage metadata.
7. compute actual cost.
8. finalize/release/unknown.
9. trace ledger.

Code cần thực hiện:

- Tạo `backend/src/services/llm_gateway.py`.
- Chuyển các node từ `llm.ainvoke(...)` sang `llm_gateway.invoke(...)`.
- Giữ `backend/src/services/llm.py` chỉ làm nhiệm vụ build provider client.

Ảnh hưởng nghiệp vụ:

- Không đổi prompt/tool logic.
- Dễ kiểm soát mọi LLM call thống nhất.

Rủi ro:

- Nếu còn một node/tool gọi provider trực tiếp, budget bị bypass.
- Cần test grep/static check để đảm bảo không còn `ainvoke` provider rải rác ngoài gateway.

### 6. Cost Estimator Và Pricing Registry

Mức độ phù hợp: cao, cần vì project có cả OpenAI/OpenRouter.

Không nên hardcode model pricing rải rác. Nên có registry:

- provider.
- model.
- input price per 1M tokens.
- output price per 1M tokens.

Phase đầu có thể dùng config default:

- `LLM_ESTIMATED_INPUT_TOKEN_PRICE_PER_1M`
- `LLM_ESTIMATED_OUTPUT_TOKEN_PRICE_PER_1M`
- `LLM_ESTIMATED_OUTPUT_TOKENS_PER_CALL`

Về sau nên mở rộng thành JSON config hoặc bảng DB nếu nhiều model/provider.

Code cần thực hiện:

- `backend/src/services/llm_pricing.py` hoặc trong `llm_gateway.py`.
- Config trong `backend/src/config.py`.
- `.env.example`.

Ảnh hưởng DB:

- Không bắt buộc nếu pricing nằm trong config.

Rủi ro:

- OpenRouter model giá thay đổi theo provider/model; config sai sẽ estimate sai.
- Token estimate bằng `chars / 4` chỉ là gần đúng, đặc biệt tiếng Việt có thể lệch.

## Tóm Tắt Thay Đổi Sẽ Thực Hiện

### Backend API

Thay đổi:

- Sinh thêm `turn_id` trong `/api/v1/chat`.
- Gắn identity `anon_session_id`, `client_ip`, `conversation_id`, `turn_id`, `trace_id`.
- Rate limit request trước khi gọi agent.

File:

- `backend/src/api/routes.py`
- `backend/src/main.py`

Ảnh hưởng:

- Có thể trả `429` với spam.
- Chat response có thể chứa `action_error=LLM_BUDGET_EXCEEDED` khi hết budget.

### Security / Rate Limit

Thay đổi:

- Thêm resolver anonymous identity.
- Thêm `RateLimitStore` interface.
- Thêm middleware rate limit.

File:

- `backend/src/security/client_identity.py`
- `backend/src/security/rate_limit.py`
- `backend/src/config.py`

Ảnh hưởng:

- Không đổi nghiệp vụ booking.
- Có thêm cookie anonymous session.

### Agent / LLM

Thay đổi:

- Thêm `LLMGateway`.
- Bỏ gọi provider trực tiếp trong node.
- Thêm max LLM calls per turn.
- Thêm budget reserve/finalize.

File:

- `backend/src/services/llm_gateway.py`
- `backend/src/services/llm.py`
- `backend/src/agents/nodes/classifier_node.py`
- `backend/src/agents/nodes/booking_skill_node.py`
- `backend/src/agents/nodes/advise_skill_node.py`
- `backend/src/agents/state.py`

Ảnh hưởng:

- Không đổi LangGraph topology.
- Có thể chặn request hợp lệ nếu vượt turn/conversation/session/global budget.

### Database

Thay đổi:

- Thêm bảng rate limit counters.
- Thêm bảng LLM budget ledger.
- Có thể thêm bảng budget buckets/counters để atomic reserve nhanh hơn.

File:

- `backend/src/database/schema.py`
- `backend/src/database/sqlite.py`
- `backend/src/database/postgres.py`

Ảnh hưởng:

- Có migration schema.
- Có write DB cho mỗi LLM call và mỗi rate-limit window.
- Cần index tốt để tránh ảnh hưởng latency.

### Config

Thay đổi:

- Thêm config rate limit.
- Thêm config budget theo USD.
- Thêm config agent execution cap.
- Thêm config pricing estimate.

File:

- `backend/src/config.py`
- `.env.example`

Ảnh hưởng:

- Dễ tinh chỉnh policy không cần sửa code.
- Cần giá trị default vừa đủ rộng để không phá local demo.

## Rủi Ro Khi Implement Theo Thiết Kế

### Rủi Ro Kỹ Thuật

- Circular import nếu `LLMGateway` import `dependencies` trong lúc app import graph. Nên inject service cẩn thận hoặc lazy-load.
- DB write tăng mạnh nếu mọi rate limit và LLM call đều ghi PostgreSQL.
- Race condition budget nếu reserve không atomic.
- SQLite local có concurrency thấp hơn PostgreSQL, dễ lock nếu test spam nhiều request.
- QueryGuard cần cập nhật đầy đủ bảng/cột mới, nếu thiếu sẽ block SQL runtime.

### Rủi Ro Nghiệp Vụ

- Limit quá thấp làm user thật bị chặn khi flow booking cần nhiều turn/tool.
- IP budget có thể ảnh hưởng nhiều user dùng chung mạng.
- Conversation budget dễ bị bypass nếu dùng làm identity chính, nên chỉ là limit phụ.
- Budget theo estimate có thể deny nhầm nếu estimate output tokens quá cao.

### Rủi Ro Vận Hành

- Nếu production scale nhiều backend instance mà rate limit vẫn dùng memory thì policy sai.
- Nếu chỉ dùng PostgreSQL cho high-QPS rate limit, DB có thể thành bottleneck.
- Giá OpenAI/OpenRouter thay đổi mà config pricing không cập nhật thì budget lệch bill thật.
- Timeout provider không rõ có charge hay chưa cần trạng thái `unknown`, nếu release hết sẽ underestimate.

### Rủi Ro Observability

- Nếu không có dashboard/query báo cáo, ledger có nhưng khó dùng để vận hành.
- Cần log `reservation_id`, `turn_id`, `trace_id` để debug request bị deny.
- Không nên log raw prompt/contact/token khi ghi budget/rate-limit event.

## Khuyến Nghị Adapt Theo Phase

### Phase 1

- Thêm `turn_id`.
- Thêm `ClientIdentityResolver`.
- Thêm rate limit theo session/IP.
- Thêm `LLMGateway` làm choke point.
- Thêm max LLM calls per turn.

### Phase 2

- Thêm budget ledger PostgreSQL.
- Dùng integer `microUSD`.
- Thêm atomic reserve/finalize/release/unknown.
- Thêm budget hierarchy: turn, conversation, anon_session/day, global/day, IP/day.

### Phase 3

- Thêm pricing registry theo provider/model.
- Thêm dashboard/report chi phí.
- Tối ưu store: Redis cho rate limit nếu scale, PostgreSQL giữ ledger audit.

## Đánh Giá Cuối

Thiết kế có khả năng adapt tốt vào source code hiện tại, đặc biệt vì backend đã có FastAPI middleware point, LangGraph metadata, DB abstraction và guardrail layer sẵn. Phần cần làm cẩn thận nhất là `LLMGateway` và atomic budget reserve. Nếu làm hai phần này tốt, các node agent và nghiệp vụ booking gần như không cần thay đổi lớn, còn hệ thống sẽ có một lớp kiểm soát chi phí/burst rõ ràng, audit được và có đường scale lên Redis sau này.
