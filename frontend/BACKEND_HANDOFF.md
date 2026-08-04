# VinFast frontend — Backend handoff

Tài liệu này là điểm bắt đầu cho đội backend khi nối dữ liệu thật vào UI/UX và animation hiện có. Các vị trí cần thay fixture trong source đều được đánh dấu bằng `TODO [BACKEND/*]` và trỏ về tài liệu này.

## 1. Hiện trạng

Frontend là React SPA chạy bằng Vite. Giao diện, responsive, accessibility cơ bản và state machine đặt lịch đã hoàn chỉnh ở mức prototype; chưa có request mạng thật.

Những phần đang là dữ liệu giả hoặc xử lý cục bộ:

- Catalogue, thông số, màu và media xe: `src/data/cars.js`.
- Media trang chủ/ViVi: `src/data/media.js`.
- Nội dung hậu mãi, pin/trạm sạc, thời hạn và media chính sách: `src/data/ownership.js`.
- Showroom và nhân viên sale: `showroomDirectory` trong `src/pages/BookingPage.jsx`.
- Nhận diện tỉnh, phường/xã và intent của chat: parser cục bộ trong `BookingPage.jsx`.
- Lịch trống: `createSlots()` sinh theo công thức, không phải tồn xe thật.
- Bản đồ: SVG mô phỏng; tọa độ `x/y` chỉ phục vụ layout.
- Giữ lịch và tạo booking: `setTimeout`; mã lịch sinh từ `Date.now()`.
- Tra cứu, bổ sung, đổi lịch và huỷ lịch: mới có UX hội thoại, chưa có dữ liệu thật.
- `sessionStorage` chỉ giữ mẫu xe gần nhất và một số UI flag; chưa khôi phục được toàn bộ tiến trình.

Không thay cấu trúc JSX/CSS khi nối API nếu không có thay đổi UX đã được duyệt. Ưu tiên thay nguồn dữ liệu và action tại đúng marker.

## 2. Cấu hình môi trường và deploy

Các biến frontend đề xuất:

```text
VITE_API_BASE_URL=https://api.example.vn
VITE_MAPS_PROVIDER=google
VITE_MAPS_PROVIDER_KEY=<public-domain-restricted-key>
VITE_ANALYTICS_ENABLED=true
```

- Không đặt private key hoặc service credential trong biến `VITE_*`; mọi biến này đều có thể đọc được trong browser.
- Nginx phải dùng `try_files $uri /index.html` cho `/cars/:id`, `/booking`, `/after-sales`, `/charging` và các route SPA khác.
- `/api` không được rơi vào SPA fallback. Nếu reverse proxy, đặt timeout riêng cho agent streaming.
- Không cache response booking/lookup. Asset có hash trong `dist/assets` có thể cache immutable.
- API dùng TLS, CORS allowlist và cookie `Secure; HttpOnly; SameSite=Lax` nếu chọn cookie session.

## 3. State machine đặt lịch

Backend agent/draft phải trả đúng `nextStage` trong tập giá trị bên dưới. Không để LLM tự phát minh stage hoặc action UI.

| Stage | Mục đích UX | Workspace | Hành động server chính |
|---|---|---|---|
| `idle` | Chờ chọn người lái | agent-only | Tạo/khôi phục draft |
| `need_car` | Chưa có xe gần nhất | agent-only | Lấy xe đủ điều kiện lái thử |
| `need_address` | Hỏi địa chỉ chi tiết | car | Geocode input |
| `need_ward` | Đã có tỉnh nhưng thiếu phường/xã | car | Trả clarification |
| `choose_showroom` | Chọn 3–4 showroom có đúng xe | map | Query inventory + distance |
| `choose_slot` | Chọn ngày/giờ có đúng xe | schedule | Query live slots |
| `collect_info` | Nhập thông tin trong panel agent | schedule | Tạo/kiểm tra hold, validate form |
| `review` | Kiểm tra phiếu trước khi đặt | ticket | Validate hold còn hiệu lực |
| `success` | Xe + phiếu + ViVi thành công | success layout | Booking đã commit |
| `lookup` | Tra cứu lịch đã đặt | agent | Xác minh khách hàng, trả allowed actions |

Quy tắc chuyển stage:

1. Nếu URL có `?car=<vehicleId>` hoặc draft có `selectedVehicleId`, sau modal người lái chuyển thẳng `need_address`.
2. Nếu chỉ nhận diện được tỉnh/thành, giữ màn hình xe và trả `need_ward`; không tải toàn bộ showroom của tỉnh.
3. Chỉ chuyển `choose_showroom` sau khi có địa chỉ chuẩn hoá tới phường/xã hoặc lat/lng đủ tin cậy.
4. Showroom phải có đúng `vehicleId` trước, khoảng cách chỉ là tiêu chí xếp hạng thứ hai.
5. Chỉ chuyển `collect_info` sau khi server tạo hold thành công.
6. Chỉ chuyển `success` sau khi booking được commit idempotently.
7. Khi 409/410 ở hold hoặc create booking, quay lại `choose_slot`; giữ nguyên địa chỉ, showroom và form khách hàng.

## 4. API map đề xuất

Tên endpoint có thể đổi theo chuẩn nội bộ, nhưng payload và lifecycle cần giữ tương đương.

| Method | Endpoint | Nơi dùng | Ghi chú |
|---|---|---|---|
| `GET` | `/api/v1/vehicles` | Home, menu, switcher | Có `sortOrder`, category và test-drive eligibility |
| `GET` | `/api/v1/vehicles/{id}` | Trang chi tiết, panel xe | Trả specs, colors, presentation và brochure revision |
| `GET` | `/api/v1/vehicles/{id}/media` | Detail gallery/chapters | Media có type, tone, focal point, sort order |
| `GET` | `/api/v1/content/home?locale=vi-VN` | Home | Hero, video, editorial panels, testimonial đã publish |
| `GET` | `/api/v1/content/ownership?locale=vi-VN` | Hậu mãi, pin & trạm sạc | Policy blocks có revision, effectiveAt, source document và sortOrder |
| `POST` | `/api/v1/test-drive/drafts` | Bắt đầu flow | Trả `draftId`, `stage`, `expiresAt` |
| `GET` | `/api/v1/test-drive/drafts/{id}` | Reload/khôi phục | Không trả PII nếu draft chưa được xác minh |
| `PATCH` | `/api/v1/test-drive/drafts/{id}` | Mỗi lựa chọn | Patch recipient, vehicle, address, showroom, stage |
| `POST` | `/api/v1/locations/geocode` | Nhập địa chỉ | Trả province/ward ids, lat/lng, formattedAddress, confidence |
| `GET` | `/api/v1/test-drive/showrooms` | Map/cards | Query `vehicleId`, `lat`, `lng`; có inventory + distance |
| `GET` | `/api/v1/test-drive/vehicles?showroomId=` | Đổi xe | Chỉ xe lái thử thực sự khả dụng ở showroom |
| `GET` | `/api/v1/test-drive/slots` | Schedule/cards | Query `showroomId`, `vehicleId`, date range |
| `POST` | `/api/v1/test-drive/holds` | Xác nhận slot | Atomic hold; trả `holdId`, `holdExpiresAt` |
| `DELETE` | `/api/v1/test-drive/holds/{id}` | Đổi xe/slot, thoát flow | Idempotent release |
| `POST` | `/api/v1/test-drive/bookings` | Xác nhận cuối | Bắt buộc `Idempotency-Key` |
| `POST` | `/api/v1/test-drive/bookings/lookup` | Tra cứu | Tên + điện thoại; có challenge/OTP nếu cần |
| `PATCH` | `/api/v1/test-drive/bookings/{id}/reschedule` | Bổ sung/đổi lịch | Dùng hold mới, idempotent |
| `POST` | `/api/v1/test-drive/bookings/{id}/cancel` | Huỷ lịch | Trả trạng thái và thời điểm huỷ |
| `POST` | `/api/v1/booking-agent/sessions` | Khởi tạo ViVi | Gắn với draft, không nhúng PII vào prompt log |
| `POST` | `/api/v1/booking-agent/messages` | Prompt ViVi | Stream text + structured UI actions |

## 5. Contract xe và media

Ví dụ tối thiểu:

```json
{
  "id": "vf6",
  "name": "VF 6",
  "navName": "VF 6",
  "category": "personal",
  "body": "SUV hạng B",
  "seatCount": 5,
  "price": {
    "amount": 689000000,
    "currency": "VND",
    "label": "Giá niêm yết"
  },
  "tagline": "Mạnh mẽ và tinh tế.",
  "description": "...",
  "testDriveEligible": true,
  "sortOrder": 30,
  "brochure": {
    "label": "VF 6 Brochure",
    "url": "https://cdn.example.vn/...pdf",
    "revision": "2026-01-29"
  },
  "presentation": {
    "heroImageUrl": "https://cdn.example.vn/...webp",
    "studioImageUrl": "https://cdn.example.vn/...png",
    "studioImageMode": "cutout",
    "motionImageUrl": "https://cdn.example.vn/...png",
    "motionPreset": "drive-ltr",
    "focalPoint": { "x": 0.5, "y": 0.5 },
    "aspectRatio": 2.27,
    "alt": "VinFast VF 6 màu trắng, góc đầu xe 3/4",
    "film": {
      "url": "https://cdn.example.vn/vehicles/vf6/presentation.mp4",
      "posterUrl": "https://cdn.example.vn/vehicles/vf6/presentation-poster.webp",
      "mimeType": "video/mp4",
      "width": 1920,
      "height": 1080,
      "duration": 30.14,
      "eyebrow": "VF 6 trong chuyển động",
      "title": "...",
      "description": "...",
      "captionUrl": null,
      "revision": "2026-08-04"
    }
  },
  "specifications": [
    { "key": "range_nedc", "value": 460, "unit": "km", "label": "Quãng đường NEDC", "sortOrder": 10 }
  ],
  "colors": [
    { "id": "infinity-blanc", "name": "Trắng Infinity Blanc", "hex": "#ECECE8", "imageUrl": "https://cdn.example.vn/...webp", "sortOrder": 10 }
  ]
}
```

### Quy tắc media phục vụ animation

- `studioImageMode` chỉ nhận `cutout`, `plate`, `photo`.
- `motionPreset` chỉ nhận preset frontend đã hỗ trợ, ban đầu gồm `drive-ltr`, `float`, `static`. Backend không trả JavaScript, selector GSAP, duration hoặc easing.
- Ảnh `cutout` phải có alpha thật, không nền trắng, không bệ/khung chữ nhật, không watermark và có khoảng trong an toàn quanh xe.
- Với `drive-ltr`, đầu xe hướng sang phải hoặc góc đầu 3/4; không dùng góc đuôi xe. CDN không được flatten alpha khi tối ưu.
- Trả `width`, `height`, `aspectRatio`, `focalPoint`, `alt`, `revision` để tránh layout shift và cache sai.
- Chapter media cần `mediaType`: `exterior`, `profile`, `rear`, `cockpit`, `cabin`, `rearSeats`, `technology`, `drive`, `charging`, `cargo`.
- `tone` chỉ là `light` hoặc `dark` để frontend chọn frame tương phản đúng.
- Video cần `posterUrl`, `mimeType`, `duration`, `width`, `height`, captions/transcript nếu có lời nói. Autoplay chỉ áp dụng video muted.
- `presentation.film` là optional. Khi không có hoặc tải lỗi, frontend dùng `posterUrl`/`heroImageUrl` làm fallback và tiếp tục render gallery; không để lỗi video chặn trang chi tiết.
- Mỗi vehicle/revision chỉ được trả **một** object `presentation.film`, không trả mảng và không nhân bản cùng URL ở nhiều record. Nếu CMS có bản ghi trùng, backend chọn bản `publishedAt` mới nhất trước khi serialize; frontend chỉ mount một player cho route đang xem.
- `motionImageUrl` dùng trong hero phải là cutout alpha thật, canvas đã crop sát `safeBounds` và không chứa nền trắng/ô màu. Với VF 9, preset hiện tại tham chiếu asset đã crop `vf9-studio`; backend cần cung cấp bản CDN tương đương để không lộ khung trên nền trang.
- VF 8 và VF 8 Thế hệ mới hiện có hai file local giống hệt byte nhưng vẫn là hai record media độc lập. Backend/CMS không gộp quan hệ theo checksum vì nội dung biên tập, revision và ngày publish của hai mẫu có thể tách riêng sau này.
- Frontend luôn tôn trọng `prefers-reduced-motion`; backend phải có ảnh fallback cho mọi video/motion asset.
- Khi dữ liệu/media async render xong, frontend integration gọi `ScrollTrigger.refresh()`; không khởi tạo lại toàn bộ GSAP timeline trên từng chunk stream.

### Contract media trang chủ và quy tắc lớp ảnh

- `factoryFilm` và `factoryAerial` là hai content block độc lập, có `sortOrder` riêng. Không composite ảnh toàn cảnh nhà máy vào video dây chuyền và không trả HTML/CSS positioning từ CMS.
- CTA cuối trang `homeAction` chỉ nhận tối đa một `vehicleRender`. Nền phía sau là gradient do frontend quản lý; không trả thêm ảnh xe nền thứ hai.
- Các panel VF 8/VF 9 tại `flagship-passage` bắt buộc dùng `studioImageUrl` với `studioImageMode: "cutout"`. Nếu chưa có alpha thật, backend trả `plate` để frontend đóng khung có chủ đích, không gắn nhãn sai là `cutout`.
- Mọi block media cần stable `id`, `sortOrder`, `alt`, `focalPoint`, `width`, `height` và `revision`. API không trả selector, z-index, vị trí tuyệt đối hay timeline GSAP.

### Contract nội dung hậu mãi, pin và trạm sạc

Hai route `/after-sales` và `/charging` đang đọc fixture có nguồn từ brochure trong `src/data/ownership.js`. Khi nối CMS/API, không trả một khối HTML tự do. Backend nên trả các block có cấu trúc, ví dụ:

```json
{
  "slug": "charging",
  "locale": "vi-VN",
  "revision": "2026-08-04",
  "effectiveAt": "2024-03-19T00:00:00+07:00",
  "sourceDocument": {
    "title": "Dịch vụ pin ô tô điện VinFast",
    "url": "https://cdn.example.vn/policies/charging.pdf",
    "checksum": "sha256:..."
  },
  "network": {
    "provinceCount": 63,
    "portCount": 150000,
    "portCountQualifier": "more_than"
  },
  "tariff": {
    "amountPerKwh": 3858,
    "currency": "VND",
    "vatIncluded": true,
    "effectiveAt": "2024-03-19"
  },
  "blocks": [
    { "id": "charging-notice", "type": "notice_timeline", "sortOrder": 10, "items": [] },
    { "id": "charging-units", "type": "charger_catalogue", "sortOrder": 20, "items": [] }
  ]
}
```

Quy tắc bắt buộc:

- Mọi con số pháp lý/chính sách cần `effectiveAt`, `revision` và `sourceDocument`; không cache vô thời hạn.
- Chính sách thuê pin phải có trạng thái `legacy_existing_customers_only` để UI không hiển thị như dịch vụ mở mới.
- Thời hạn bảo hành pin trả theo `vehicleIds`, `durationMonths`, `distanceKm` và `whicheverComesFirst`; frontend chịu trách nhiệm format, không parse chuỗi pháp lý.
- Danh mục trụ sạc trả `powerKw`, số cổng, điện áp vào/ra, chuẩn bảo vệ, nhiệt độ vận hành và media có `alt`, `width`, `height`, `revision`.
- Không cho CMS gửi selector GSAP hoặc JavaScript. CMS chỉ chọn animation preset allowlist: `hero-scale`, `stagger-cards`, `pinned-chapter`, `static`.
- Khi policy hết hiệu lực hoặc chưa publish, API phải trả trạng thái rõ ràng; frontend giữ bản bundled fallback kèm cảnh báo nguồn, không tự ghép dữ liệu cũ và mới.

## 6. Contract showroom, slot, hold và booking

Showroom:

```json
{
  "id": "hcm-nguyen-thi-thap",
  "name": "VinFast Nguyễn Thị Thập",
  "formattedAddress": "...",
  "provinceId": "79",
  "wardId": "...",
  "location": { "lat": 10.739, "lng": 106.701 },
  "distanceMeters": 3800,
  "travelDurationSeconds": 900,
  "openingStatus": "open",
  "availableVehicleIds": ["vf6", "vf-mpv-7"],
  "accessibility": { "wheelchairAccessible": true }
}
```

Slot:

```json
{
  "inventorySlotId": "slot_01J...",
  "vehicleId": "vf6",
  "showroomId": "hcm-nguyen-thi-thap",
  "startAt": "2026-08-06T09:45:00+07:00",
  "endAt": "2026-08-06T10:30:00+07:00",
  "timezone": "Asia/Ho_Chi_Minh",
  "status": "available"
}
```

Booking create request:

```json
{
  "draftId": "draft_01J...",
  "holdId": "hold_01J...",
  "recipientType": "other",
  "vehicleId": "vf6",
  "showroomId": "hcm-nguyen-thi-thap",
  "customer": { "fullName": "...", "phone": "...", "email": "..." },
  "driver": { "fullName": "..." },
  "licenceConsent": { "confirmed": true, "version": "2026-08-01" },
  "privacyConsent": { "version": "2026-08-01" }
}
```

Booking response phải có:

- `id`, `bookingCode`, `status`, `vehicle`, `showroom`, `slot`.
- `customer` và `driver` ở dạng phù hợp với quyền xem hiện tại.
- `assignedSalesRepresentative`: `name`, `phone`, `avatarUrl` nếu đã phân công.
- `allowedActions`: `lookup`, `reschedule`, `cancel` theo trạng thái.
- `createdAt`, `updatedAt`, `notificationStatus` cho SMS/email.

### Vòng đời hold

1. User chọn slot chỉ mở popup; chưa cần giữ inventory.
2. User bấm “Xác nhận khung giờ” thì tạo hold atomic.
3. UI nhận `holdId` và `holdExpiresAt`, sau đó mới chuyển sang form.
4. Đổi xe, showroom hoặc slot phải release hold cũ trước/đồng thời với việc tạo hold mới.
5. Booking create tiêu thụ hold. Retry cùng `Idempotency-Key` phải trả cùng booking, không tạo bản ghi thứ hai.
6. Hold hết hạn trả `410`; slot vừa bị người khác lấy trả `409`. Cả hai trường hợp quay về lịch trống và giữ dữ liệu form trong memory.

## 7. Agent response contract

Agent trả text để hội thoại tự nhiên, đồng thời phải trả action có cấu trúc để UI render an toàn:

```json
{
  "messageId": "msg_01J...",
  "conversationId": "conv_01J...",
  "text": "Tôi tìm thấy 4 showroom có VF 6 gần bạn.",
  "nextStage": "choose_showroom",
  "entities": {
    "vehicleId": "vf6",
    "provinceId": "79",
    "wardId": "..."
  },
  "actions": [
    { "type": "select_showroom", "showroomId": "hcm-nguyen-thi-thap" }
  ],
  "ui": { "activeView": "map" }
}
```

- Backend/LLM chỉ được trả action type trong allowlist.
- Frontend đối chiếu id với dữ liệu API trước khi thực thi action.
- Không render HTML do agent trả về.
- Free text chứa tên, điện thoại, email phải được redact trước observability/prompt logs.
- Nếu agent timeout/429, các card xe, showroom và slot vẫn phải thao tác được; flow không phụ thuộc hoàn toàn vào text generation.

## 8. Persistence và privacy

- Ưu tiên draft server-side; browser chỉ giữ opaque `draftId` hoặc secure session cookie.
- Không lưu họ tên, điện thoại, email, thông tin GPLX hoặc nội dung prompt vào `localStorage/sessionStorage`.
- Draft chưa có PII có thể tự hết hạn sau thời gian ngắn. Draft có PII phải theo retention policy đã duyệt.
- Lookup/cancel/reschedule nên có OTP hoặc challenge phù hợp, rate limit và audit trail.
- Mã lịch không được suy ra từ timestamp tuần tự.
- Log backend phải redact PII; analytics tuyệt đối không nhận raw chat text.

## 9. Error và loading contract

| Tình huống | HTTP | UX bắt buộc |
|---|---:|---|
| Địa chỉ mơ hồ/chỉ có tỉnh | `422` | Giữ input, chuyển `need_ward`, hỏi phường/xã |
| Xe/showroom không tồn tại | `404` | Bỏ id lỗi, mở lại chọn xe/showroom |
| Slot vừa được người khác giữ | `409` | Đóng modal, refresh lịch, gợi ý slot gần nhất |
| Hold hết hạn | `410` | Về `choose_slot`, giữ form trong memory |
| Form sai | `422` | Map lỗi theo field, focus field đầu tiên |
| Submit trùng | cùng idempotency result | Hiện một booking duy nhất |
| Agent rate limit | `429` | Hiện retry; card/action thủ công vẫn hoạt động |
| API lỗi/offline | `5xx`/network | Không xoá draft UI; retry có kiểm soát |

Mọi request làm thay đổi stage cần loading state, disable action gây duplicate và hỗ trợ huỷ request cũ khi user đổi xe/showroom.

## 10. Analytics events

Đề xuất event allowlist:

- `vehicle_list_view`, `vehicle_view`, `vehicle_color_select`, `vehicle_media_view`.
- `test_drive_nudge_impression`, `test_drive_nudge_dismiss`, `booking_cta_click`.
- `booking_recipient_select`, `booking_vehicle_select`, `booking_address_submit`.
- `showrooms_loaded`, `booking_showroom_select`, `slots_loaded`, `booking_slot_select`.
- `booking_hold_created`, `booking_hold_conflict`, `booking_form_error`.
- `booking_created`, `booking_lookup`, `booking_reschedule`, `booking_cancel`.
- `vivi_message_sent`, `vivi_action_selected`, `media_load_error`.
- `ownership_page_view`, `ownership_section_view`, `policy_source_open`, `charging_hotline_click`.

Thuộc tính chung chỉ gồm `eventId`, `anonymousSessionId`, `draftId`, `vehicleId`, `showroomId`, `stage`, `placement`, timestamp và trạng thái. Không gửi name, phone, email, địa chỉ chi tiết hoặc raw prompt.

## 11. Thứ tự tích hợp khuyến nghị

### P0 — để flow đúng sự thật

1. API base URL, SPA fallback và error client dùng chung.
2. Catalogue/media thật với presentation contract.
3. Draft/session restore; chỉ khi đó dòng “Tiến trình được giữ trên thiết bị” mới hoàn toàn chính xác.
4. Geocoding + showroom có đúng xe + live slots.
5. Hold lifecycle và create booking idempotent.
6. Success ticket dùng booking response và sale được phân công thật.

### P1 — hoàn chỉnh nghiệp vụ

1. Lookup + verification.
2. Reschedule/cancel với allowed actions.
3. SMS/email notification status.
4. Map SDK và routing distance.
5. Analytics không PII.

### P2 — ViVi và CMS

1. Agent session/message streaming với structured actions.
2. CMS trang chủ, testimonial và video.
3. CDN transformations, poster và responsive media.

## 12. Checklist nghiệm thu backend ↔ frontend

- [ ] Direct load `/cars/vf6` và `/booking` không 404.
- [ ] Direct load `/after-sales` và `/charging` không 404; anchor sub-navigation nằm dưới header sticky.
- [ ] Reload booking khôi phục đúng stage nhưng không để lộ PII trong browser storage.
- [ ] Showroom được lọc theo đúng xe trước rồi mới theo khoảng cách.
- [ ] Mọi slot có `inventorySlotId`; browser không tự sinh lịch.
- [ ] 409/410 không làm mất địa chỉ/showroom/form.
- [ ] Double click/retry chỉ tạo một booking.
- [ ] Ticket thành công dùng booking/sale response thật.
- [ ] Lookup, reschedule và cancel chỉ mở sau verification.
- [ ] Ảnh `drive-ltr` có alpha và đúng hướng đầu xe; không lộ khung khi chạy.
- [ ] `prefers-reduced-motion` vẫn hiển thị đủ nội dung.
- [ ] Media lỗi có fallback; dữ liệu ảnh async không làm sai ScrollTrigger.
- [ ] Giá sạc, phí lưu trụ, số cổng sạc và thời hạn bảo hành hiển thị đúng `revision/effectiveAt`; thuê pin luôn gắn nhãn khách hàng hiện hữu.
- [ ] Analytics và log không chứa PII/raw prompt.
- [ ] Mobile, keyboard, screen reader và timezone `Asia/Ho_Chi_Minh` được kiểm tra.
