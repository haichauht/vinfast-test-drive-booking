# Kiến trúc hệ thống VinFast Test Drive + ViVi

> Tài liệu phản ánh implementation hiện có trong source, rà soát ngày 23-08-2026. Khi khác biệt, source code là nguồn sự thật.

## 1. Tổng quan hệ thống

```mermaid
flowchart LR
    Customer[Khách hàng] --> Website[Public FE<br/>React 18 + Vite<br/>React Router · GSAP · Three.js · Mapbox GL]
    Staff[Nhân viên vận hành] --> PortalUI[Internal Portal FE<br/>React 18 + Vite]
    Driver[Người lái được mời] --> DriverLink[Driver invitation link]
    Website --> PublicNginx[Nginx public FE]
    DriverLink --> PublicNginx
    PortalUI --> PortalNginx[Nginx portal FE]
    PublicNginx --> API[FastAPI API<br/>Python + Uvicorn + Pydantic]
    PortalNginx --> API
    API --> Core[Booking + Portal + Site catalogue]
    API --> AI[ViVi AI<br/>LangGraph + LangChain + guardrails]
    Core --> PG[(PostgreSQL)]
    AI --> PG
    AI --> LLM[OpenRouter / OpenAI<br/>ChatOpenAI]
    AI --> Knowledge[Trusted knowledge JSON]
    Core --> Integrations[Gmail / Zalo]
    AI --> Redis[(Redis<br/>profile queue, optional)]
```

Sơ đồ này chỉ gom các khối backend chính; sơ đồ phía trên giữ chi tiết route, profile, media và từng service.

Các frontend đều gọi backend qua Nginx khi chạy Docker. `docker-compose.yml` có đủ Postgres, Redis, backend, public frontend và internal portal. `docker-compose.prod.yml` hiện chỉ khai báo Postgres, Redis, backend và public frontend; portal chưa nằm trong stack production.

## 2. Tech stack

```mermaid
flowchart TB
    subgraph Frontend[Frontend]
        React[React 18]
        Vite[Vite]
        UI[React Router · GSAP · Three.js<br/>Mapbox GL · model-viewer]
        React --> Vite
        React --> UI
    end
    subgraph Edge[Edge & runtime]
        Nginx[Nginx]
        Docker[Docker Compose]
        Nginx --> Docker
    end
    subgraph Backend[Backend]
        Python[Python]
        FastAPI[FastAPI + Uvicorn]
        Pydantic[Pydantic Settings]
        Python --> FastAPI
        FastAPI --> Pydantic
    end
    subgraph AI[AI]
        LangGraph[LangGraph]
        LangChain[LangChain + langchain-openai]
        Provider[OpenRouter / OpenAI]
        LangGraph --> LangChain --> Provider
    end
    subgraph Data[Data & integrations]
        PG[(PostgreSQL 16)]
        Redis[(Redis 7, optional)]
        Gmail[Gmail OAuth]
        Zalo[Zalo Bot]
        Media[Local MEDIA_ROOT / CDN]
    end
    Frontend --> Nginx --> FastAPI
    FastAPI --> LangGraph
    FastAPI --> PG & Redis & Gmail & Zalo & Media
```

## 3. Backend: lớp và trách nhiệm

```mermaid
flowchart TB
    subgraph Boundary[FastAPI boundary]
        Middleware[CORS<br/>RateLimitMiddleware<br/>HTTP request logging]
        PublicRoutes[Public routes<br/>chat, stream, actions, profile, import]
        SiteRoutes[Site routes<br/>vehicles, content]
        InternalRoutes[Internal routes<br/>/internal/*]
        MediaRoute["/media static mount"]
    end
    subgraph Domain[Application services]
        Site[SiteCatalogService]
        Booking[BookingService mixins<br/>catalog, lifecycle, access, management,<br/>staff, notifications, import, dashboard, location]
        Portal[InternalPortalService mixins<br/>auth, resources, operations, notifications]
        Profiles[ProfileService + DriverInvitationService]
        Budget[UsageBudgetService]
    end
    subgraph AI[ViVi AI]
        Graph[LangGraph StateGraph]
        Guardrails[InputGuard · ToolGuard · OutputGuard]
        LLM[ChatOpenAI provider]
        Knowledge[KnowledgeService]
    end
    subgraph Infra[Persistence and integrations]
        PG[(PostgreSQL)]
        Redis[(Redis, optional)]
        Mail[Gmail OAuth]
        Zalo[Zalo Bot / OTP]
    end
    Middleware --> PublicRoutes & SiteRoutes & InternalRoutes & MediaRoute
    PublicRoutes --> Graph & Booking & Profiles & Budget
    SiteRoutes --> Site
    InternalRoutes --> Portal
    Graph --> Guardrails & LLM & Knowledge & Booking & Profiles & Budget
    Booking --> PG & Redis & Mail & Zalo
    Portal --> PG
    Profiles --> PG & Redis
    Budget --> PG
    Site --> CatalogData[In-module catalogue/content<br/>or SITE_CATALOG_PATH JSON snapshot]
```

`SiteCatalogService` không đọc catalogue từ PostgreSQL: nó dùng dữ liệu mặc định trong module hoặc snapshot JSON tại `SITE_CATALOG_PATH`, và trả ETag/Cache-Control. PostgreSQL là nguồn dữ liệu nghiệp vụ: showroom, xe demo, slot, booking, người dùng/phiên portal, OTP/access session, audit/idempotency, notification, profile và LangGraph checkpoint.

### Bề mặt API

| Nhóm | Endpoint chính | Xử lý |
| --- | --- | --- |
| Health | `GET /health`, `/api/v1/booking/health`, `/api/v1/status` | Liveness, trạng thái DB/agent. |
| Site | `GET /api/v1/vehicles`, `/vehicles/{id}`, `/content/{page}` | Catalogue/content read-only, ETag. |
| ViVi | `POST /api/v1/chat`, `/chat/stream` (alias `/booking-agent/stream`) | Chat/structured action; stream SSE. |
| Driver | `GET /driver-chat/{token}/context`, `POST /driver-chat/{token}/chat` | Chat theo link mời có thời hạn, cô lập conversation namespace. |
| Booking deterministic | `POST /api/v1/test-drive/actions` (alias `/demo/action`) | Search, hold/draft/confirm, OTP access, quản lý booking; không qua LLM. |
| Profile | `GET /user-profiles/{id}/…`, booking profile summary, driver invitation | Đọc summary/profile và tạo email link cho driver. |
| Internal | `/api/v1/internal/*` | Opaque bearer session, RBAC, dashboard, fleet, schedule, booking operations, audit. |
| Admin import | `/api/v1/admin/import/*` | Chỉ `operations_admin`; cấm import state bảo mật. |

## 4. Vòng đời ứng dụng và worker

```mermaid
sequenceDiagram
    participant U as Uvicorn
    participant F as FastAPI lifespan
    participant DB as PostgreSQL
    participant G as LangGraph
    participant N as Notification dispatcher
    participant Z as Zalo polling
    U->>F: startup
    F->>DB: initialize_database / bootstrap theo cấu hình
    F->>G: initialize_persistent_agent(DATABASE_URL)
    alt DATABASE_URL là PostgreSQL
        G->>DB: AsyncPostgresSaver.setup()
    else SQLite/local test
        G->>G: MemorySaver
    end
    F->>N: tạo task dispatch_due_notifications()
    opt Zalo enabled và polling enabled
        F->>Z: tạo polling task
    end
    loop notification_poll_interval_seconds
        N->>DB: claim và gửi notification đến hạn
    end
    F-->>U: sẵn sàng phục vụ
    U->>F: shutdown
    F->>N: cancel task
    F->>Z: cancel polling (nếu có)
    F->>G: close persistent checkpointer
```

Ở production, khởi tạo PostgreSQL checkpointer thất bại sẽ làm startup thất bại. Redis không bắt buộc cho backend: các chức năng Redis phụ thuộc như queue cập nhật profile sẽ báo unavailable nếu Redis không sẵn sàng.

## 5. ViVi: đồ thị AI thực tế

```mermaid
flowchart TD
    Start([ChatRequest]) --> Context[Resolve client identity<br/>profile + booking + participant context]
    Context --> InGuard[InputGuard<br/>validate, sanitize, payload limits]
    InGuard -->|blocked| Blocked[Safe ChatResponse]
    InGuard -->|allowed| Classifier[classifier_node]
    Classifier -->|sensitive / out_of_scope| Policy[sensitive_policy_node]
    Classifier -->|booking skill| Skill[booking_skill_node<br/>hoặc post_booking_skill_node]
    Classifier -->|confirmed booking + advisory/vehicle info| Skill
    Skill --> HasTools{AIMessage has tool calls?}
    HasTools -->|yes| Tools[Guarded ToolNode<br/>allowlist theo active skill]
    Tools --> Skill
    HasTools -->|no| OutputGuard[OutputGuard<br/>redact + response limit]
    Policy --> OutputGuard
    OutputGuard --> End([ChatResponse])
```

Classifier dùng keyword fast-path cho một số intent/safety cases, còn lại gọi LLM với structured `RouteSchema`; khi LLM không khả dụng/lỗi, code fallback về keyword/domain route. Structured booking actions bypass classifier LLM và map thẳng tới booking skill, vì vậy các button booking vẫn dùng được không cần API key LLM.

| Skill | Tool allowlist đang được nối vào graph | Ghi chú |
| --- | --- | --- |
| `booking` | `search_test_drive_options`, `hold_test_drive_slot`, `get_booking_draft`, `update_booking_draft`, `request_booking_access`, `request_user_location`, `verify_booking_access`, `get_booking_details`, `confirm_test_drive_booking` | Tool chỉ gọi `BookingService`; không có SQL trực tiếp từ model. |
| `post_booking` | `search_knowledge`, `update_user_profile` | Chỉ route khi booking đã active/confirmed; dùng knowledge JSON đã có provenance và profile context. |

`calculator` và `advise_skill_node` có trong source nhưng không được gắn vào graph công khai hiện tại. Không có vector-store/Chroma được dùng trong luồng `KnowledgeService` hiện hành; knowledge được tìm kiếm trên file JSON trusted.

### Luồng chat và tool

```mermaid
sequenceDiagram
    participant C as Customer/Driver
    participant API as POST /chat hoặc driver-chat
    participant P as ProfileService
    participant G as LangGraph
    participant L as ChatOpenAI
    participant TG as Guarded ToolNode
    participant S as Booking/Profile/Knowledge service
    participant DB as PostgreSQL / Redis
    C->>API: message, context, conversation_id
    API->>P: resolve anonymous/trusted profile + booking context
    API->>G: ainvoke(thread_id=conversation_id)
    G->>G: input guard + classifier
    alt booking hoặc post-booking cần LLM
        G->>L: prompt, history, context và tool allowlist
        L-->>G: text hoặc tool call
        opt tool call
            G->>TG: validate allowlist, limits, confirmation
            TG->>S: invoke tool
            S->>DB: transaction / retrieval / queue
            DB-->>S: result
            S-->>TG: tool result
            TG-->>G: ToolMessage
        end
    else structured booking action
        G->>TG: generated deterministic tool call
        TG->>S: BookingService command
    end
    G-->>API: response + action metadata
    API->>G: OutputGuard protection
    API-->>C: ChatResponse hoặc SSE done event
```

Provider LLM ưu tiên OpenRouter, sau đó OpenAI. `UsageBudgetService` ghi/kiểm soát ngân sách theo ngày và session trong PostgreSQL; giới hạn tool gồm tối đa 8 vòng ở graph và tối đa `guardrails_max_tool_calls_per_message` (mặc định 3) ở một message tool.

## 6. Booking và thông báo

```mermaid
flowchart LR
    UI[Booking UI hoặc deterministic action API] --> B[BookingService]
    B --> Catalog[catalog: showroom, vehicle, slot search]
    B --> Life[lifecycle: hold, draft, confirm, expire]
    B --> Access[access: OTP, access session]
    B --> Manage[management: update, reschedule, cancel]
    B --> Staff[staff: assignment, licence, check-in, complete, no-show]
    B --> Ops[import, dashboard, location]
    B --> TX[base: transaction, audit, idempotency]
    Catalog --> PG[(PostgreSQL)]
    Life --> PG
    Access --> PG
    Manage --> PG
    Staff --> PG
    Ops --> PG
    TX --> PG
    Life --> Redis[(Redis slot hold, optional)]
    B --> Jobs[notification jobs]
    Jobs --> Dispatcher[background dispatcher]
    Dispatcher --> Channel{routing provider}
    Channel --> Gmail[Gmail OAuth]
    Channel --> Zalo[Zalo]
    Channel --> Memory[In-memory fallback]
```

Mutations dùng `ui_action_id` để idempotency và `expected_version` cho optimistic concurrency. OTP/access session bảo vệ tra cứu và chỉnh sửa booking. Driver invitation được tạo từ booking, gửi qua messaging provider; token chỉ dùng cho chat/context của driver và classifier chặn các thao tác booking management trên luồng này.

## 7. Post-booking profile và personalisation

```mermaid
sequenceDiagram
    participant U as Booker hoặc driver
    participant V as post_booking_skill
    participant K as search_knowledge
    participant T as update_user_profile
    participant Q as Redis ProfileUpdateQueue
    participant W as queue worker
    participant P as ProfileService
    participant DB as PostgreSQL
    U->>V: hỏi chuẩn bị/đánh giá lái thử hoặc cung cấp sở thích
    V->>K: tra trusted knowledge theo query/model (khi cần)
    K-->>V: facts + provenance/scope
    opt thông tin durable để cá nhân hoá
        V->>T: SignalCandidate(s)
        T->>Q: enqueue reliable, dedupe ngắn hạn
        Q-->>T: queued/unavailable
        W->>Q: reserve job
        W->>P: apply signal với provenance
        P->>DB: user_profiles + user_profile_signals
        W->>Q: ack hoặc retry/dead-letter
    end
    V-->>U: tư vấn grounded và phản hồi chat
```

Profile khởi đầu anonymous theo conversation/cookie. Khi booking được confirm hoặc OTP access được xác thực, backend có thể promote/merge profile theo person và hash email/phone; plaintext liên hệ không được đưa vào profile tool. Profile queue hiện cần Redis, và worker được start/stop ở event của public router.

## 8. An toàn, quan sát và dữ liệu

- `RateLimitMiddleware` tạo cookie identity phía server và IP fallback; counters nằm ở PostgreSQL. Quota được tách cho chat, deterministic action và OTP.
- Guardrails kiểm tra input/action contract, giới hạn payload, allowlist tool, explicit confirmation trước confirmation tool, giới hạn mutation batch và redact output.
- Portal dùng opaque bearer token chỉ lưu hash trong DB, có revoke và RBAC/scope showroom; frontend portal lưu token trong `sessionStorage`.
- Trace agent và HTTP logs thực hiện redaction. `client-log` cũng redact message/context trước khi log.
- `/media` là `MEDIA_ROOT` local mount; DTO có thể phát URL CDN bằng `MEDIA_BASE_URL`.
- Không đưa `.env`, Gmail refresh token, Zalo token, OTP secret hoặc driver invitation token vào source/log/documentation.

## 9. Quy ước mở rộng

1. Tool mới phải được thêm đồng thời vào tool module, allowlist của graph, guardrail policy/contract và test; export tool đơn lẻ chưa làm tool đó có thể gọi.
2. Skill mới cần node, routing classifier, ToolNode allowlist riêng và test permission boundary.
3. Thêm booking action cần đi xuyên DTO/guardrail → frontend API → action map/tool hoặc service → test/UI directive.
4. Production cần PostgreSQL cho conversation checkpoint bền vững; Redis nên được bật nếu sử dụng cập nhật profile bất đồng bộ.
