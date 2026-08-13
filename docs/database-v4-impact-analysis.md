# Phân tích tác động khi áp dụng VinFast Booking Dataset V4

## 1. Phạm vi và kết luận

Báo cáo này đối chiếu ERD V4 trong ảnh được cung cấp với schema và code tại nhánh hiện tại. Hệ thống đang dùng SQL viết tay, PostgreSQL ở Docker và SQLite cho local/test; schema nguồn nằm tại [`backend/src/database/schema.py`](../backend/src/database/schema.py#L299).

**Kết luận:** không nên thay nguyên trạng schema hiện tại bằng ERD V4. Nên dùng **thiết kế đích hybrid**: nhận các phần tốt của V4 (địa giới, cờ demo theo showroom, ca làm, unavailability/transfer, tài khoản nội bộ và audit) nhưng giữ các cơ chế hiện tại về hold slot, optimistic locking, lịch sử reschedule, OTP/access session, idempotency và thông tin retry/provider của notification. Nếu áp dụng V4 nguyên trạng, các flow tìm lịch, giữ chỗ, xác nhận, OTP, tra cứu, đổi/hủy lịch, check-in và gửi thông báo đều bị gãy.

### Tóm tắt quyết định

| Nhóm | Thiết kế nên chọn |
| --- | --- |
| Địa giới, phạm vi demo | V4, có bổ sung constraint và giữ `showrooms.code/timezone/contact` |
| Xe, slot, booking, people | Hybrid, phần lớn giữ cấu trúc hiện tại |
| Ca làm, xe bận, chuyển xe | V4, nhưng phải kiểm tra theo khoảng thời gian |
| Notification, OTP/session | Hybrid; không được bỏ bảng bảo mật hiện tại |
| Portal nội bộ, RBAC, audit | V4, triển khai thành một bounded context riêng |
| Migration | Migration có version, expand/backfill/switch/contract; không sửa DDL trực tiếp rồi deploy |

## 2. Các vấn đề và tác động

### Vấn đề 1 — Địa giới hành chính và trạng thái showroom

**Đánh giá:** V4 tốt hơn khi thêm `provinces → districts → wards` và `booking_demo_enabled`; dữ liệu địa điểm có thể lọc chính xác thay vì match token trên chuỗi địa chỉ. Tuy nhiên không nên bỏ `showrooms.code`, `timezone`, `phone`, `email`, `created_at`, `updated_at`. `status` cũng cần định nghĩa rõ và không nên nhập nhằng với quyền nhận booking demo.

**Rủi ro khi đổi:** `CatalogService` đang lọc `is_active=1`, sắp theo `code`, tìm showroom bằng code/tên/address và cache token theo `updated_at` ([`catalog.py`](../backend/src/services/booking/catalog.py#L77), [`catalog.py`](../backend/src/services/booking/catalog.py#L96)). CSV import đang upsert bằng `code` ([`importer.py`](../backend/src/services/booking/importer.py#L25)). Bỏ các cột này làm gãy tìm showroom, import và cache. Frontend map/search vẫn chạy nếu DTO tương thích, nhưng showroom bị tắt demo có thể vẫn xuất hiện nếu backend chỉ kiểm tra `status`.

**Sửa đề xuất:** giữ `code UNIQUE`, `timezone`, contact và timestamps; thêm ba FK địa giới nullable ở pha đầu, backfill rồi mới `NOT NULL`. Thêm `CHECK(status IN ('active','inactive'))`, `booking_demo_enabled BOOLEAN`, index `(booking_demo_enabled,status,province_id,district_id)`. Ràng buộc district thuộc province và ward thuộc district bằng FK/composite FK hoặc trigger. Trong search bắt buộc `status='active' AND booking_demo_enabled=true`; cập nhật importer, seed, DTO và test map/tìm theo địa chỉ.

### Vấn đề 2 — Danh mục model/variant xe

**Đánh giá:** thiết kế hiện tại tốt hơn V4 cho nghiệp vụ đang chạy. V4 chỉ giữ `id/code/name/status` ở model và `id/model_id/code/name` ở variant, trong khi hệ thống cần `vehicle_type`, `required_license_class`, ghi chú GPLX, thông số variant, cờ active và timestamps.

**Rủi ro khi đổi:** flow search trả `license_requirement`; hold snapshot `required_license_class`; check-in yêu cầu xác minh GPLX. Các join này nằm trong [`catalog.py`](../backend/src/services/booking/catalog.py#L96), [`lifecycle.py`](../backend/src/services/booking/lifecycle.py#L13) và [`staff.py`](../backend/src/services/booking/staff.py#L22). Bỏ `is_active` cũng làm hỏng danh sách model/variant và cho phép đặt mẫu xe đã ngừng phục vụ. Dataset/import headers và seed sẽ không còn khớp.

**Sửa đề xuất:** giữ schema hiện tại, có thể đổi `is_active` thành `status` chỉ khi cung cấp compatibility view/cột kép trong thời gian chuyển đổi. Giữ GPLX ở model hoặc tách bảng `vehicle_model_booking_policies(model_id, required_license_class, effective_from, effective_to)` nếu cần lịch sử. Tạo unique `(model_id, code)` cho variant thay vì `code` global nếu code variant chỉ duy nhất trong một model. Không lưu `model_id` lặp lại ở `demo_vehicles`; suy ra qua `variant_id`.

### Vấn đề 3 — Xe demo: V4 làm mất định danh và điều kiện sẵn sàng

**Đánh giá:** thiết kế hiện tại tốt hơn. V4 thêm `license_plate` nhưng bỏ/đổi `asset_code`, VIN, `minimum_booking_soc`, `charging_status`, `is_active`, timestamps và đồng thời lưu cả `model_id` lẫn `variant_id`.

**Rủi ro khi đổi:** search/hold/confirm đều yêu cầu xe active, `operational_status='available'` và pin đạt `minimum_booking_soc` ([`catalog.py`](../backend/src/services/booking/catalog.py#L96), [`lifecycle.py`](../backend/src/services/booking/lifecycle.py#L13)). Xóa các cột này có thể cho đặt xe đang sạc hoặc pin thấp. `model_id` và `variant_id` có thể lệch nhau, khiến UI hiển thị một mẫu nhưng cấp xe mẫu khác. `asset_code` hiện xuất hiện trong kết quả slot và là định danh vận hành ổn định hơn biển số.

**Sửa đề xuất:** giữ `variant_id` là nguồn model duy nhất; giữ `asset_code UNIQUE`, `vin UNIQUE`, đổi `plate_number` sang `license_plate` bằng migration có alias. Giữ ngưỡng pin hoặc chuyển sang policy theo showroom/model. Chuẩn hóa status và thêm `CHECK battery_soc BETWEEN 0 AND 100`. `is_active` có thể hợp nhất vào status `inactive`, nhưng code phải chuyển đồng bộ và cần compatibility view trong rollout.

### Vấn đề 4 — Slot và cơ chế hold đồng thời

**Đánh giá:** thiết kế hiện tại tốt hơn V4 cho consistency. V4 bỏ `held_until`, `current_booking_id`, `block_reason`, timestamps khỏi `test_drive_slots`; chỉ giữ status. Trong hệ thống hiện tại, slot và booking được cập nhật cùng transaction khi hold, expire, confirm, cancel và reschedule.

**Rủi ro khi đổi:** [`hold_slot`](../backend/src/services/booking/lifecycle.py#L13) đọc/ghi `held_until/current_booking_id`; [`confirm_booking`](../backend/src/services/booking/lifecycle.py#L293) xác nhận slot đang thuộc đúng booking; [`expire_held_bookings`](../backend/src/services/booking/lifecycle.py#L403) trả slot về available. Bỏ ownership làm hai request có thể cùng xác nhận một slot, khó phân biệt hold hiện hành và hold đã hết hạn. Chỉ có `UNIQUE(demo_vehicle_id,start_at,end_at)` hiện tại cũng chưa chặn hai khoảng thời gian giao nhau.

**Sửa đề xuất:** giữ các cột ownership hoặc chuyển sang mô hình derived-state có partial unique/exclusion constraint và query khóa hàng rõ ràng. Với PostgreSQL nên dùng `tstzrange` + `EXCLUDE USING gist (demo_vehicle_id WITH =, time_range WITH &&)` cho trạng thái chiếm dụng, và `SELECT ... FOR UPDATE`/conditional update khi hold. Giữ `block_reason`, timestamps; index `(showroom_id,status,start_at)`. Nếu dùng booking làm nguồn hold, phải bảo đảm chỉ một booking `held/confirmed` hoạt động trên mỗi slot bằng partial unique index.

### Vấn đề 5 — Booking V4 làm mất lịch sử và kiểm soát ghi đè

**Đánh giá:** thiết kế hiện tại tốt hơn; chỉ `showroom_id` của V4 là hữu ích cho báo cáo nhưng là dữ liệu lặp với slot. V4 bỏ `driver_person_id`, các timestamp trạng thái, lý do hủy, chuỗi reschedule, `source_channel`, `version`, timestamps và chỉ thêm `booked_at`.

**Rủi ro khi đổi:** optimistic locking của draft/confirm dùng `version`; đổi lịch dùng `rescheduled_from_booking_id/replaced_by_booking_id`; hủy/check-in/complete dùng timestamp và reason ([`lifecycle.py`](../backend/src/services/booking/lifecycle.py#L171), [`management.py`](../backend/src/services/booking/management.py#L152), [`management.py`](../backend/src/services/booking/management.py#L229), [`staff.py`](../backend/src/services/booking/staff.py#L76)). Bỏ chúng gây lost update, mất audit nghiệp vụ và không dựng được lịch sử booking. `bookings.showroom_id` có thể khác `slot.showroom_id` sau update sai hoặc transfer xe.

**Sửa đề xuất:** giữ toàn bộ lifecycle/version hiện tại; có thể đổi `confirmed_at` thành `booked_at` nhưng cần định nghĩa và migration rõ. Không thêm `showroom_id` nếu luôn truy qua slot; nếu cần snapshot lịch sử, đặt tên `booked_showroom_id`, bất biến sau confirm và kiểm tra bằng trigger tại thời điểm đặt. Dùng enum/check tập trung, index `booking_code`, `(status,hold_expires_at)`, các FK reschedule và constraint ngăn self-reference.

### Vấn đề 6 — Quan hệ Booker/Driver và bảng `people`

**Đánh giá:** hybrid. V4 chuyển `driver_person_id` sang `booking_driver_details`, làm bảng booking gọn hơn, nhưng hệ thống hiện tại thường xuyên cần cả booker và driver. V4 cũng bỏ `preferred_channel`, `normalized_phone/email` và timestamps khỏi `people`; đây là regression.

**Rủi ro khi đổi:** draft tạo/chỉnh hai person, self-booking dùng chung person; OTP tìm chủ booking và danh sách lịch cùng số điện thoại dựa trên normalized phone ([`lifecycle.py`](../backend/src/services/booking/lifecycle.py#L171), [`access.py`](../backend/src/services/booking/access.py#L17), [`access.py`](../backend/src/services/booking/access.py#L240), [`management.py`](../backend/src/services/booking/management.py#L25)). Di chuyển FK buộc sửa mọi join/read/write, notification recipient và cleanup person. Bỏ chuẩn hóa số điện thoại gây tra cứu sai giữa `+84` và `0`, hoặc trùng customer.

**Sửa đề xuất:** giữ `booker_person_id` và `driver_person_id` ở booking; `booking_driver_details` chỉ chứa khai báo/kiểm tra GPLX. Giữ normalized fields, tạo index cho `normalized_phone` và lower email; không đặt unique tuyệt đối nếu một số liên hệ hợp lệ cho nhiều người. Cân nhắc mã hóa PII, retention/anonymization và tránh trả phone/email ở dashboard. Nếu vẫn chọn V4, tạo view compatibility để service thấy `driver_person_id` như cũ trong pha chuyển đổi.

### Vấn đề 7 — Ca làm và phân công sales

**Đánh giá:** V4 tốt hơn vì thêm `staff_shifts`; hiện tại `slot_sales_assignments` chỉ gán người vào slot và không chứng minh người đó đang làm ca. Tuy nhiên V4 bỏ contact/role/is_active/timestamps của `sales_staff` và bỏ `assignment_role/created_at` của assignment, không nên áp dụng phần lược bỏ.

**Rủi ro khi đổi:** confirm đang chọn assignment active đầu tiên, staff operation chỉ kiểm tra nhân viên active và cùng showroom, chưa kiểm tra ca hoặc assignment ([`lifecycle.py`](../backend/src/services/booking/lifecycle.py#L293), [`staff.py`](../backend/src/services/booking/staff.py#L10)). Thêm bảng mà không sửa logic sẽ không tạo giá trị; ngược lại, bắt buộc shift ngay lập tức sẽ khiến toàn bộ seed hiện tại không phân công được ai. `created_by` của shift theo ERD chưa chỉ rõ FK là user nào.

**Sửa đề xuất:** thêm shifts nullable/opt-in trước, backfill ca; khi confirm chọn staff có assignment active **và** shift phủ `slot.start_at/end_at`, không overlap, đúng showroom. Giữ role/contact/status của staff; liên kết `created_by` tới `internal_users`, thêm `created_at/updated_at`. Quy định fallback “chưa phân công” thay vì fail booking nếu chưa có staff. Staff check-in nên kiểm tra scope RBAC + assignment/manager scope, không chỉ cùng showroom.

### Vấn đề 8 — `vehicle_unavailability` và `vehicle_transfers`

**Đánh giá:** V4 tốt hơn vì biểu diễn xe bận theo khoảng thời gian và lịch sử điều chuyển; `operational_status` hiện tại chỉ là snapshot toàn cục. Đây là phần nên bổ sung, không thay thế hoàn toàn status.

**Rủi ro khi đổi:** search hiện chỉ lọc status/pin và overlap slot; hold/confirm không đọc hai bảng mới. Xe bảo trì hoặc đang chuyển showroom vẫn có thể được đặt. Nếu cập nhật ngay `demo_vehicles.showroom_id` khi transfer trong khi các slot tương lai còn ở showroom cũ, join và quyền staff sẽ mâu thuẫn. ERD có `requested_by` nhưng chưa rõ FK/internal permission, và không thấy thời điểm hiệu lực transfer.

**Sửa đề xuất:** `vehicle_unavailability(start_at,end_at,reason,created_by)` cần `CHECK end_at>start_at` và exclusion constraint chống khoảng chồng nếu nghiệp vụ yêu cầu. Search/hold/confirm phải anti-join unavailability. Transfer nên có `effective_at/completed_at`, from/to khác nhau, state machine; chỉ đổi showroom của xe khi complete và phải block/migrate/cancel các slot bị ảnh hưởng trong cùng transaction. Thêm flow manager tạo block, operations admin duyệt transfer, audit mọi thay đổi; bổ sung test search/hold race và transfer có booking tương lai.

### Vấn đề 9 — Notification plan/job của V4 chưa đủ cho worker hiện tại

**Đánh giá:** hybrid. V4 tốt hơn ở hướng một plan theo `channel/template_code/status` và job tham chiếu `plan_id`; nhưng lại bỏ recipient, loại thông báo, provider result, số lần thử tối đa, lỗi và timestamps. Thiết kế hiện tại tốt hơn cho dispatch/retry và observability.

**Rủi ro khi đổi:** confirm/reschedule/cancel tạo job theo recipient và channel; worker join `people`, claim `pending→processing`, tăng attempt, lưu provider result và retry ([`lifecycle.py`](../backend/src/services/booking/lifecycle.py#L293), [`background.py`](../backend/src/services/booking/background.py#L10)). V4 dùng `send_at/retry_count`, còn code dùng `scheduled_at/attempt_count`; đổi tên trực tiếp làm worker dừng. Không có recipient thì không biết gửi cho booker hay driver. Status V4 có `retrying/cancelled`, hiện code retry bằng cách trả lại `pending`.

**Sửa đề xuất:** chuyển plan thành các dòng `(booking_id,recipient_role,channel,template_code,schedule_rule,status)`; job giữ `recipient_person_id`, `notification_type`, `scheduled_at`, attempt/max_attempts, provider fields, error và timestamps. Unique chống tạo job trùng theo plan/recipient/schedule. Dùng claim an toàn PostgreSQL `FOR UPDATE SKIP LOCKED`; quy định `retrying` hoặc giữ `pending` nhất quán. Migration phải dual-read các tên cột trong một release.

### Vấn đề 10 — V4 thiếu `otp_challenges`, customer access session và idempotency

**Đánh giá:** thiết kế hiện tại bắt buộc phải giữ. Khối “Thông báo & OTP” trong V4 không có nơi lưu `code_hash`, expiry, attempt/lock/supersede; `internal_sessions` là session nhân viên, không thay thế `booking_access_sessions`. V4 cũng không thể hiện `idempotency_records`.

**Rủi ro khi đổi:** request/verify OTP và quyền theo purpose phụ thuộc trực tiếp vào hai bảng access ([`access.py`](../backend/src/services/booking/access.py#L17), [`access.py`](../backend/src/services/booking/access.py#L137)). Tra cứu, sửa, hủy và reschedule từ frontend dùng token này ([`frontend/src/api/booking.js`](../frontend/src/api/booking.js#L144)). Bỏ idempotency có thể tạo hai hold/confirm/cancel khi client retry. Dùng chung internal session cho customer tạo lỗ hổng scope và vòng đời token.

**Sửa đề xuất:** giữ `otp_challenges`, `booking_access_sessions`, `idempotency_records`; chỉ lưu hash OTP/token, TTL, attempt, consumed/revoked và permissions. Thêm unique/partial index cho challenge active, cleanup job và rate-limit theo destination/IP ở gateway. Tách hẳn customer access khỏi `internal_sessions`. Nếu muốn bám tên V4, đặt chúng trong schema/module `customer_access`, không nhập vào portal auth.

### Vấn đề 11 — Portal nội bộ, RBAC và audit

**Đánh giá:** V4 tốt hơn và giải quyết lỗ hổng hiện tại: `internal_users`, mapping showroom, sessions, roles, audit, Zalo links. Hiện `/admin/import/*` và `/dashboard` chưa có authentication ([`routes.py`](../backend/src/api/routes.py#L198), [`routes.py`](../backend/src/api/routes.py#L227)); Streamlit admin có thể reset/import trực tiếp ([`admin_app.py`](../backend/admin_app.py#L63)).

**Rủi ro khi thêm:** chỉ tạo bảng không tạo authorization. `internal_user_showrooms` cần semantics cho operations admin toàn hệ thống; staff phải liên kết 1–1/nullable với internal user. Audit chỉ có `resource_type/resource_id` nhưng thiếu action, outcome, request/trace ID và before/after an toàn. Token session cần hash, rotation/revocation; không được log raw token. Role string trên user khó mở rộng nhiều quyền hoặc nhiều role.

**Sửa đề xuất:** thêm auth middleware/dependency cho admin/staff API; role + scope showroom được kiểm tra tại service, không tin frontend. Dùng `internal_sessions(token_hash,user_id,expires_at,revoked_at,created_at,last_seen_at)`. Audit append-only gồm actor, action, resource, showroom scope, outcome, trace_id, metadata đã loại PII; operations admin xem toàn bộ, manager chỉ phạm vi. Bảo vệ import/reset/transfer/shift/unavailability/audit endpoints và tạo UI portal riêng; không tái sử dụng customer OTP token.

### Vấn đề 12 — Status, kiểu thời gian và constraint chưa đủ chặt

**Đánh giá:** cả hai thiết kế đều cần cải thiện. Schema hiện tại dùng `TEXT` cho timestamp/boolean ngay cả PostgreSQL; V4 chỉ liệt kê status mà không nêu enum/check, timezone, cascade hay unique. Status xe giữa hai bên khác nhau (`in_use/out_of_service` so với `maintenance/inactive`); notification cũng khác `processing` và `retrying`.

**Rủi ro khi đổi:** mapping sai status làm search coi xe không sẵn sàng là available, worker bỏ qua job, dashboard đếm sai. So sánh thời gian dạng text chỉ an toàn khi mọi giá trị đều ISO UTC đồng nhất. FK thiếu chính sách delete có thể để orphan hoặc xóa nhầm dữ liệu audit. Query hiện phụ thuộc tên literal rải trong catalog/lifecycle/management/staff/background/dashboard.

**Sửa đề xuất:** với PostgreSQL dùng `TIMESTAMPTZ`, `BOOLEAN`, enum hoặc lookup/check có migration rõ; API luôn trả ISO-8601 có offset. Lập state transition table/document dùng chung, không đổi tên status trước khi code hỗ trợ cả hai. Bổ sung unique/FK/index theo access path, `ON DELETE RESTRICT` cho dữ liệu vận hành, cascade chỉ cho detail thuộc booking khi chính sách retention cho phép. SQLite test phải mô phỏng cùng constraint quan trọng hoặc có test PostgreSQL integration.

### Vấn đề 13 — Cơ chế migration hiện tại không đủ để adapt V4

**Đánh giá:** cần thiết kế mới tốt hơn. Hiện startup chạy `CREATE TABLE IF NOT EXISTS`, sau đó chỉ `ALTER TABLE ADD COLUMN` thủ công cho PostgreSQL/SQLite ([`postgres.py`](../backend/src/database/postgres.py#L112), [`sqlite.py`](../backend/src/database/sqlite.py#L106)). Cách này không quản lý rename, backfill, drop, đổi constraint, rollback hay thứ tự release.

**Rủi ro khi đổi:** deploy DDL V4 trực tiếp làm code cũ lỗi ngay; `QueryGuard` từ chối bảng/cột chưa có trong metadata ([`guard.py`](../backend/src/database/guard.py#L86)). SQLite và PostgreSQL có thể lệch schema. `CREATE IF NOT EXISTS` không sửa bảng đã tồn tại, khiến môi trường mới chạy còn môi trường cũ lỗi âm thầm. Migration dài có thể khóa bảng booking đang hoạt động.

**Sửa đề xuất:** dùng Alembic hoặc migration runner có bảng version. Triển khai expand/contract: (1) thêm bảng/cột/index nullable; (2) cập nhật `TABLES`/QueryGuard; (3) backfill kiểm đếm; (4) code dual-write/read-new-fallback-old; (5) switch traffic và theo dõi; (6) thêm NOT NULL/FK; (7) release sau mới bỏ cột cũ. Backup/restore rehearsal, checksum/count/FK validation và rollback theo từng pha là điều kiện bắt buộc.

### Vấn đề 14 — Dataset, admin, API, frontend và test bị ảnh hưởng dây chuyền

**Đánh giá:** V4 không chỉ là thay database. Importer đang định nghĩa cứng 15 CSV và dependency ([`importer.py`](../backend/src/services/booking/importer.py#L60), [`importer.py`](../backend/src/services/booking/importer.py#L257)); seed/bootstrap, admin reset/table browser, dashboard và test fixtures đều gắn với schema hiện tại.

**Rủi ro khi đổi:** file V4 có thêm địa giới, shift, unavailability, transfer, internal tables và đổi header/cột; import sẽ reject hoặc insert sai thứ tự. Admin reset có thể vi phạm FK. Frontend map cần DTO showroom ổn định; lịch đã đặt/reschedule cần booking/slot/advisor như cũ ([`BookingPage.jsx`](../frontend/src/pages/BookingPage.jsx#L546), [`BookingPage.jsx`](../frontend/src/pages/BookingPage.jsx#L1558), [`BookingPage.jsx`](../frontend/src/pages/BookingPage.jsx#L1680)). Agent tool có thể trả lỗi nếu service SQL chưa đổi đồng bộ.

**Sửa đề xuất:** version dataset (`v3`, `v4`) và viết importer V4 riêng, không sửa in-place importer cũ. Cập nhật thứ tự FK, seed counts, bootstrap tables, admin reset/browser, dashboard queries và QueryGuard metadata. Giữ response contract qua adapter/serializer trong giai đoạn migration để frontend không phải đổi cùng lúc. Bổ sung integration test cho search→hold→confirm, OTP→lookup, update/cancel/reschedule, staff check-in, notification retry, RBAC scope, vehicle block/transfer và chạy tối thiểu một suite trên PostgreSQL.

## 3. Phạm vi code cần sửa theo flow

| Flow | Thành phần chính cần sửa |
| --- | --- |
| Khởi tạo/migration | `database/schema.py`, `database/postgres.py`, `database/sqlite.py`, `database/guard.py`, migration mới |
| Import/seed/admin | `services/booking/importer.py`, `bootstrap.py`, `scripts/seed_dev_db.py`, `admin_app.py`, `eval/data/*` |
| Tìm showroom/slot | `services/booking/catalog.py`, location DTO/API, `frontend/src/api/booking.js`, map/booking page |
| Hold/confirm/expire | `lifecycle.py`, background scheduler, idempotency và concurrency tests |
| OTP/tra cứu/sửa/hủy/đổi | `access.py`, `management.py`, booking agent tools, frontend booking management |
| Staff/check-in | `staff.py`, shift/assignment service mới, internal auth/RBAC dependency |
| Notification | `lifecycle.py`, `background.py`, provider adapters, worker deployment |
| Portal/audit/transfer | API/service mới, Streamlit hoặc portal mới, audit middleware, RBAC tests |

## 4. Thứ tự triển khai khuyến nghị

1. Chốt data dictionary V4 hybrid, status/state machine, cardinality và retention/PII policy.
2. Đưa migration có version vào hệ thống; thêm địa giới, cờ demo, shifts, unavailability, transfers và internal auth/audit theo kiểu additive.
3. Backfill dữ liệu, thêm compatibility view/DTO; chưa xóa cột hiện tại.
4. Sửa search/hold/confirm để xét showroom demo, ca làm và xe không khả dụng; thêm constraint chống overlap/race.
5. Triển khai portal auth/RBAC/audit, khóa các admin endpoint hiện đang công khai.
6. Nâng notification theo plan/job hybrid; giữ nguyên OTP/customer session/idempotency.
7. Chạy dual-write, đối soát và test PostgreSQL end-to-end; switch read path sau khi số liệu khớp.
8. Chỉ contract/drop cột cũ ở release kế tiếp sau khi có backup, rollback rehearsal và thời gian quan sát ổn định.

## 5. Điều kiện nghiệm thu trước khi cut-over

- Không có orphan FK; số lượng showroom/xe/slot/booking/person và lịch sử status khớp trước–sau.
- Không tạo được hai booking active cho cùng slot hoặc hai khoảng sử dụng chồng nhau của cùng xe.
- Hold 120 giây, expire, retry request và idempotency vẫn đúng dưới concurrent test.
- OTP không lưu plaintext; session customer và internal tách biệt, đúng TTL/revoke/scope.
- Search không trả showroom tắt demo, xe maintenance/unavailable/đang transfer hoặc staff ngoài ca.
- Reschedule/cancel/check-in/complete giữ đủ event, timestamp và audit actor.
- Notification không gửi trùng, retry đúng giới hạn và lưu provider outcome.
- Admin/import/dashboard/transfer/shift/audit đều yêu cầu đúng role và showroom scope.
