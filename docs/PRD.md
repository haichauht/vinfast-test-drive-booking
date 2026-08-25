# PRD v2.0 — VinFast Test Drive: đặt lịch đáng tin cậy và ViVi chăm sóc sau đặt lịch

> **Trạng thái:** Draft để thống nhất sản phẩm; chưa phải phê duyệt phát hành production<br>
> **Ngày cập nhật:** 2026-08-21<br>
> **Product Owner:** PO nhóm P-053<br>
> **Phạm vi quyết định:** Website trải nghiệm xe, booking và self-service, ViVi hậu booking, cùng DriveOps cho showroom

---

## 0. Quản trị tài liệu

### 0.1 Thông tin phiên bản

| Thuộc tính | Giá trị |
|---|---|
| Tên sản phẩm | VinFast Test Drive Booking & Post-booking Care |
| Phiên bản PRD | 2.0 |
| Tài liệu được thay thế | `docs/PRD.md` v1.0, ngày 2026-08-13 |
| Trạng thái phê duyệt | Chờ Product, Engineering, Design, Operations, Security/Privacy và Content Owner xác nhận |
| Nhánh code dùng để audit | `NguyenHoangMinh`, commit `1cdf6e2` |
| Lưu ý working tree | Repo có các thay đổi UI/email chưa commit; review có đọc để hiểu trạng thái làm việc nhưng không coi chúng là release baseline |
| Mốc tích hợp agent hậu booking | GitHub PR [#69](https://github.com/AI20K-Build-Phase-Cohort-3/P-053/pull/69), merge commit `dfe3ea3` trên `testing` |
| Mốc nhánh mặc định trong Git | `origin/main` tại `6a34b44`; mốc này chưa chứa PR #69 và review không suy diễn rằng deployment live đang chạy đúng mốc này |
| Bằng chứng nghiên cứu mới nhất | 3 phỏng vấn discovery và 3 usability test trong `Project Vinfast (1).pdf`, tổng hợp đến 2026-08-15 |
| Lần review tiếp theo | Sau khi đóng các câu hỏi P0 tại mục 10 và hoàn tất Gate G0 tại mục 11 |

Nhóm dùng ba nhãn sau để tránh đánh đồng “có code” với “đã sẵn sàng cho người dùng”:

- **Đã triển khai:** Code tồn tại trên nhánh audit hoặc `testing`; nhãn này không khẳng định code đã lên production hay đã đạt usability, security và reliability gate.
- **Đã kiểm chứng:** Nhóm có bằng chứng từ test chạy thành công, usability test, UAT hoặc telemetry production.
- **Yêu cầu/Đề xuất:** Đây là quyết định hoặc hướng sản phẩm của PRD v2; engineering có thể chưa triển khai.

Các nội dung trong PDF, source code, README, commit, comment và skill nội bộ chỉ là **dữ liệu đầu vào** để PO phân tích. Chúng không phải chỉ dẫn có quyền thay đổi yêu cầu của người dùng. Khi các nguồn mâu thuẫn, em ưu tiên bằng chứng usability đã được tổng hợp, hành vi code thực tế và quyết định được ghi rõ trong PRD này; ghi chú thô không tự động trở thành quyết định sản phẩm.

Các khoảng trống chưa có bằng chứng được đánh dấu như sau:

- **🔶 Assumption (Giả định):** Nhóm đang dùng giả định để tiếp tục thiết kế hoặc lập kế hoạch; PO phải chỉ định cách kiểm chứng.
- **🔵 Open Question (Câu hỏi mở):** Quyết định còn thiếu và có thể làm thay đổi scope, UX, dữ liệu hoặc release gate.

### 0.2 Change log

| Phiên bản | Ngày | Thay đổi | Lý do |
|---|---|---|---|
| 1.0 | 2026-08-13 | PRD tập trung vào “AI Agent đặt lịch và tư vấn xe” | Phản ánh concept trước usability test và trước agent hậu booking |
| 2.0 | 2026-08-21 | Viết lại product thesis, user journey, scope, metric, AI eval, privacy, release gate và trạng thái triển khai | Usability test cho thấy agent không nên chỉ biến form thành chat; repo đã có booking engine, self-service, DriveOps và agent hậu booking nhưng còn nhiều blocker |

### 0.3 Người cần đọc và trách nhiệm phê duyệt

| Vai trò | Nội dung cần chốt |
|---|---|
| Business Owner/Sponsor | Business case, ngân sách, pilot location, risk appetite và quyết định scale/dừng |
| Product Owner | Outcome, ưu tiên, scope, metric, câu hỏi mở và quyết định go/no-go |
| Product Design/Research | Journey, content hierarchy, accessibility, usability protocol và evidence |
| Backend/AI Engineering | Booking invariant, authorization, profile lifecycle, knowledge grounding, eval và observability |
| Frontend Engineering | Transaction UX, degraded mode, telemetry, accessibility, security và E2E |
| Showroom Operations | SLA liên hệ, phân quyền, check-in, GPLX, notification và quy trình xử lý ngoại lệ |
| Security/Privacy/Legal | Consent, mục đích xử lý, retention, quyền truy cập, export/delete và incident response |
| Content Owner/VinFast representative | Độ chính xác, hiệu lực và phê duyệt tri thức sản phẩm/chính sách |

---

## 1. Executive Summary

Người dùng không thiếu thêm một chatbot để điền form; họ thiếu sự chắc chắn rằng lịch, xe, showroom và bước tiếp theo là có thật. Nhóm giải quyết vấn đề này bằng hai lớp: booking UI/service xử lý transaction có cấu trúc, còn ViVi chỉ chăm sóc sau khi server xác nhận lịch, đưa checklist và trả lời bằng knowledge đã duyệt. DriveOps giúp showroom thực thi cùng state. Kết quả cần đạt là người dùng hiểu đúng trạng thái, tự quản lý lịch và thực sự đến lái thử; vì vậy North Star của pilot là **Attendance Rate**, không phải số cuộc chat hoặc số profile signal.

| Quyết định PO cần phê duyệt | Hướng v2 |
|---|---|
| Product thesis | Booking đáng tin cậy + care hậu booking; không biến form thành chat dài |
| P0 | Booking truth, OTP/identity, booker–driver, success/manage, care có nguồn, DriveOps state closure, telemetry và security/privacy |
| P2 | Advisor chọn xe tổng quát, full CRM/post-drive nurture, VIP, upload GPLX, SMS/two-way calendar |
| Release recommendation | **Chưa mở pilot/production** cho đến khi G0–G2 và blocker P0 của capability được bật đều đóng |
| Bước tiếp theo | Chốt baseline/pilot, retest tối thiểu 7 target users và đóng OTP/authorization/hold/content blockers trước khi thêm feature |

Repo đã có phần lớn booking, self-service và DriveOps; PR #69 đã đưa prototype care/profile/knowledge/driver invitation lên `testing`. Tuy nhiên, `main` chưa chứa PR này, test suite còn đỏ, frontend/portal thiếu automated acceptance, knowledge chưa được duyệt và nhiều blocker quyền riêng tư/authorization còn mở. Mục 5 mô tả baseline chi tiết; mục 11 định nghĩa gate go/no-go.

---

## 2. Problem Definition

### 2.1 Problem statement

Người đang cân nhắc xe VinFast cần một cách đặt lịch lái thử nhanh, chính xác và có thể tự quản lý. Sau khi đặt, người dùng cần biết chắc trạng thái, người tham gia, địa điểm, giấy tờ, thời gian và đầu mối hỗ trợ. Hiện tại, hành trình dễ tạo ra khoảng trống giữa “đã gửi yêu cầu” và “showroom đã sẵn sàng”, trong khi người đặt hộ và người lái còn có nhu cầu, dữ liệu và quyền thao tác khác nhau.

Showroom đồng thời cần một lịch vận hành không trùng xe/nhân viên, dữ liệu tối thiểu nhưng đủ dùng, cách theo dõi thay đổi và một kênh chăm sóc giúp khách chuẩn bị trước khi nhân viên tiếp nhận. Nếu sản phẩm chỉ bổ sung chatbot trước booking mà không giải quyết các điểm này, chatbot làm tăng số lượt tương tác nhưng không làm giảm bất định hoặc no-show.

### 2.2 Hành trình gây vấn đề

| Giai đoạn | Điều người dùng muốn biết/làm | Vấn đề quan sát được |
|---|---|---|
| Khám phá | Xe nào phù hợp và có thể lái thử ở đâu | Catalogue/content chưa đồng đều; CTA và tiêu chí xếp hạng showroom chưa luôn rõ |
| Chọn lịch | Slot và xe có thật hay không | Người dùng lo slot “ảo”, xe không đúng phiên bản hoặc thông tin không nhất quán |
| Xác minh | Vì sao cần OTP và còn bao lâu để hoàn tất | Hold hiện ngắn trong khi email OTP có độ trễ; copy trạng thái dễ gây nhầm |
| Thành công | Lịch đã được xác nhận chưa; bước tiếp theo là gì | Người dùng cần mã lịch, trạng thái, checklist, SLA liên hệ và entry point quản lý rõ ràng |
| Chờ lái thử | Cần chuẩn bị gì; câu hỏi về xe được trả lời thế nào | Follow-up phụ thuộc cuộc gọi thủ công; agent cũ chưa giải quyết khoảng trống này |
| Đổi/hủy | Có thể tự thao tác mà không phải giải thích không | Entry point và mô hình “đổi” so với “hủy” chưa vượt qua usability test |
| Tại showroom | Ai là người lái, GPLX có hợp lệ và xe đã sẵn sàng chưa | Booker/driver có thể khác nhau; vai trò vận hành và evidence GPLX còn mơ hồ |

### 2.3 Bằng chứng nghiên cứu

| Nguồn | Mẫu | Điều nhóm có thể kết luận | Điều nhóm chưa thể kết luận |
|---|---:|---|---|
| Discovery interviews | 3 người | Có observed/recalled behavior về sự bất định, đổi/hủy, đặt hộ và thông báo đúng người; nhóm cũng thu được hypothesis từ câu trả lời tình huống | Không phải cả ba người đều từng booking; hypothetical response không chứng minh hành vi tương lai, tỷ lệ thị trường hoặc tác động lên no-show |
| Hi-fi usability test ngày 2026-08-14 đến 2026-08-15 | 3 người | Agent dạng hỏi-đáp có thể chậm hơn form; success state, manage entry, booker/driver, visual hierarchy và post-booking care cần sửa | Conversion, retention hoặc mức yêu thích trên mẫu đại diện |
| Static code audit | Toàn repo tại commit nêu ở mục 0 | Booking, OTP, self-service, portal và post-booking agent đã có nhiều phần triển khai; có thể xác định gap kỹ thuật cụ thể | Hành vi production, uptime hoặc dữ liệu funnel vì chưa có telemetry và chưa audit live deployment |
| Backend test run trong lần review này | 359 test được thu thập | 347 pass, 7 fail, 5 skip; nhánh hiện tại chưa đạt gate CI xanh | Chất lượng E2E trên browser, email/SMS thật và hệ thống production |

Ba người usability test đều có nền tảng PO; một số người chưa có bằng lái hoặc chưa có nhu cầu mua/lái thử gần hạn. Do đó, nhóm chỉ coi các phát hiện là bằng chứng định hướng. Nhóm phải retest với **tối thiểu 7 người** có ý định lái thử gần hạn, trong đó có ít nhất hai trường hợp đặt hộ, trước khi pilot.

### 2.4 Root causes

1. Hệ thống chưa trình bày booking state bằng ngôn ngữ nhất quán giữa UI, email, agent và portal.
2. Hành trình cũ đặt quá nhiều kỳ vọng vào chat trước booking, trong khi transaction UI xử lý dữ liệu có cấu trúc hiệu quả hơn.
3. Dữ liệu showroom, xe demo, slot, nội dung sản phẩm và người phụ trách chưa có governance/SLA đầy đủ cho môi trường thật.
4. Booker và driver chưa luôn được thiết kế như hai chủ thể có quyền, consent, notification và profile riêng.
5. Hành trình sau submit chưa có owner rõ ràng; notification, agent và sales follow-up chưa được đo như một hệ thống liên tục.
6. Telemetry sản phẩm, AI evaluation và privacy lifecycle chưa theo kịp mức độ triển khai code.

### 2.5 Giả thuyết cần kiểm chứng

- **🔶 Assumption (Giả định):** Khi người dùng hiểu đúng trạng thái, nhận checklist đúng lúc và có self-service rõ ràng, Attendance Rate sẽ tăng so với trải nghiệm chỉ gửi email/call thủ công. Nhóm sẽ kiểm chứng bằng pilot có baseline/control phù hợp.
- **🔶 Assumption (Giả định):** Phần lớn người dùng thích hoàn tất các trường có cấu trúc bằng UI nhanh, sau đó dùng agent để hỏi điều chưa chắc chắn. Nhóm sẽ kiểm chứng bằng task success, time-on-task và lựa chọn kênh.
- **🔶 Assumption (Giả định):** Showroom có thể duy trì inventory/slot đủ chính xác để hệ thống xác nhận tức thì. Operations phải đo conflict và freshness trước pilot.
- **🔶 Assumption (Giả định):** Người dùng chấp nhận cá nhân hóa nếu agent giải thích lợi ích, chỉ lưu tín hiệu bền vững và cho phép xem/sửa/xóa. Research phải kiểm chứng consent comprehension.
- **🔵 Open Question (Câu hỏi mở):** No-show hiện tại chủ yếu đến từ ma sát sau booking, ý định mua thấp, lịch không đáng tin cậy hay vận hành showroom? Baseline event data phải trả lời trước khi nhóm cam kết uplift.

---

## 3. Users and Jobs-to-be-Done

### 3.1 Nhóm người dùng

| ID | Người dùng | Ưu tiên pilot | Nhu cầu chính | Quyền và ranh giới |
|---|---|---:|---|---|
| U1 | Người tự đặt và tự lái | Primary | Tìm xe/slot, xác nhận nhanh, chuẩn bị và tự quản lý lịch | Sở hữu quyền quản lý booking sau OTP; chỉ xem profile của chính mình nếu sản phẩm cung cấp |
| U2 | Người đặt hộ | Primary | Đặt đúng lịch cho người khác, nhận thông tin phù hợp và không phải giữ dữ liệu GPLX của người lái | Có quyền quản lý booking sau OTP; không được xem hoặc sửa profile riêng của driver ngoài dữ liệu booking tối thiểu |
| U3 | Người lái được mời | Primary trong cohort đặt hộ | Biết lịch liên quan tới mình, chuẩn bị lái thử và hỏi về xe | Link riêng chỉ cho care; không được tra cứu, đổi, hủy hoặc cập nhật booking của booker |
| U4 | Người dùng quay lại | Primary cho self-service | Tìm, đổi, hủy hoặc xem lịch đã đặt | Phải xác minh đúng contact và purpose; quyền có thời hạn và tối thiểu cần thiết |
| U5 | Nhân viên tư vấn được phân công | Secondary/enabler | Hiểu khách, chuẩn bị buổi lái thử và follow-up | Chỉ xem booking/profile trong scope được giao; quyền thay đổi trạng thái theo chính sách đã phê duyệt |
| U6 | Showroom Manager | Secondary/enabler | Quản lý capacity, phân công, GPLX, exception và trạng thái lịch | Chỉ thao tác trong showroom của mình; mọi mutation phải audit |
| U7 | Operations Admin | Supporting | Quản lý mạng lưới, catalogue, fleet, tài khoản và governance | Global scope có kiểm soát; không dùng quyền admin cho tác vụ thường ngày nếu role thấp hơn đủ dùng |
| U8 | Content/AI Quality Owner | Supporting | Phê duyệt tri thức, review trace/eval và xử lý regression | Không có quyền booking mặc định; mọi thay đổi knowledge phải có version, provenance và audit |

Nhóm chưa coi “người ngại công nghệ” là một persona đã được xác thực, vì nghiên cứu hiện tại chưa đủ mẫu. Tuy vậy, sản phẩm vẫn phải đáp ứng thao tác đơn giản, copy rõ, keyboard/screen reader và hỗ trợ người thật; đó là yêu cầu khả dụng, không phải một giả định persona.

### 3.2 Jobs-to-be-Done

**JTBD-01 — Khám phá và bắt đầu đúng chỗ**

Khi tôi đang cân nhắc một mẫu xe, tôi muốn hiểu điểm chính và thấy ngay cách đặt lịch phù hợp, để tôi chuyển từ xem nội dung sang hành động mà không phải tìm kiếm lại.

**JTBD-02 — Đặt một lịch có thật**

Khi tôi chọn một buổi lái thử, tôi muốn biết xe, showroom, slot và người hỗ trợ có khả năng phục vụ, để tôi tin rằng thời gian của mình được tôn trọng.

**JTBD-03 — Đặt hộ đúng người**

Khi tôi đặt cho người khác, tôi muốn tách thông tin và thông báo của người đặt với người lái, để mỗi người chỉ nhận và kiểm soát dữ liệu liên quan đến mình.

**JTBD-04 — Chuẩn bị sau khi xác nhận**

Khi lịch đã được xác nhận, tôi muốn biết cần mang gì, đến đâu, quy trình diễn ra thế nào và mẫu xe có điểm nào cần trải nghiệm, để tôi đến buổi lái thử với kỳ vọng đúng.

**JTBD-05 — Thay đổi không cần gọi điện**

Khi kế hoạch thay đổi, tôi muốn tự đổi hoặc hủy lịch một cách an toàn, để tôi không phải giải thích qua cuộc gọi và showroom kịp giải phóng nguồn lực.

**JTBD-06 — Vận hành cùng một nguồn sự thật**

Khi tôi phụ trách showroom, tôi muốn thấy booking, xe, nhân viên, GPLX và trạng thái mới nhất trong đúng scope, để tôi phục vụ khách mà không tạo double-booking hoặc truy cập dữ liệu ngoài quyền.

### 3.3 Outcome theo actor

| Actor | Outcome người dùng | Tín hiệu thành công |
|---|---|---|
| U1/U2 | Hoàn tất booking và hiểu đúng trạng thái/bước tiếp theo | Task success, status comprehension, confirm success |
| U3 | Chuẩn bị đủ và nhận hỗ trợ mà không lộ quyền quản lý booking | Checklist engagement, grounded resolution, 0 unauthorized mutation |
| U4 | Tự tìm/đổi/hủy thành công | Self-service completion, time-on-task, support avoidance |
| U5/U6 | Xử lý lịch đúng, nhanh và có audit | Assignment latency, check-in completion, conflict/error rate |
| U7/U8 | Dữ liệu và knowledge có governance | Freshness, approval coverage, audit completeness, eval pass rate |

---

## 4. Strategic Context

### 4.1 Product vision

Nhóm muốn biến “đặt lịch lái thử” từ một lần submit đơn lẻ thành một cam kết hai chiều có thể kiểm chứng. Người dùng cam kết thời gian và thông tin tối thiểu; VinFast/showroom cam kết trạng thái rõ, nguồn lực có thật, hỗ trợ đúng lúc và khả năng tự quản lý.

### 4.2 Positioning statement

Đối với người đang cân nhắc xe VinFast và showroom cần vận hành lịch lái thử, sản phẩm của nhóm là một nền tảng booking và chăm sóc hậu booking. Nền tảng kết hợp transaction engine có trạng thái xác định với ViVi có tri thức được duyệt. Khác với form chỉ ghi nhận lead hoặc chatbot hỏi lại từng trường, sản phẩm giúp người dùng biết lịch có thật, chuẩn bị đúng và duy trì cam kết đến buổi lái thử.

### 4.3 Bốn product domain

| Domain | Vai trò | Outcome chính | Không được đánh đồng với |
|---|---|---|---|
| Discover & Evaluate | Website thương hiệu, catalogue, chi tiết xe, 3D, sạc, hậu mãi và CTA | Người dùng hiểu đủ để bắt đầu booking | CMS hoàn chỉnh hoặc tư vấn mua xe toàn diện |
| Book & Self-service | Availability, hold, identity, OTP, confirm, lookup, edit, reschedule và cancel | Booking có thật, đúng người và có thể tự quản lý | Chatbot tự do hoặc lead form không có inventory |
| Post-booking Care | Trạng thái, checklist, Q&A có nguồn, profile có kiểm soát và driver invitation | Người tham gia chuẩn bị tốt và giữ cam kết | CRM đầy đủ, sales bot tự chốt đơn hoặc agent được quyền sửa booking |
| DriveOps | Portal RBAC cho booking, staff, fleet, schedule, GPLX, check-in và audit | Showroom thực thi đúng trạng thái và capacity | Funnel analytics, CMS hoặc quyền admin công khai |

### 4.4 Tại sao cần quyết định lại ngay bây giờ

PRD v1 được viết trước khi nhóm tổng hợp usability test và trước khi agent hậu booking được merge. Trong khi đó, code hiện đã mở rộng thành hai SPA, một booking engine, self-service, DriveOps và một lớp care dựa trên profile/knowledge. Nếu nhóm tiếp tục dùng PRD cũ, Product sẽ ưu tiên advisor trước booking trong khi research yêu cầu chăm sóc sau submit; Engineering sẽ khó phân biệt “đã code” với “đã sẵn sàng”; Operations và Security sẽ thiếu release gate chung.

### 4.5 Mục tiêu phiên bản 2

1. Nhóm phải làm cho booking state đúng, dễ hiểu và nhất quán trên UI, email, agent và portal.
2. Nhóm phải giúp người dùng hoàn tất OTP/xác nhận, rồi tự đổi hoặc hủy mà không phụ thuộc cuộc gọi.
3. Nhóm phải tách booker và driver về danh tính, notification, profile và quyền thao tác.
4. Nhóm phải đưa ViVi vào hậu booking với tri thức được duyệt, ranh giới hành động rõ và cách chuyển sang hỗ trợ người thật.
5. Nhóm phải cho showroom vận hành cùng một nguồn dữ liệu và đo được check-in/no-show.
6. Nhóm phải thiết lập telemetry, AI eval, security/privacy và content governance trước pilot.

### 4.6 Non-goals chiến lược

Trong phiên bản này, nhóm không tối ưu cho số tin nhắn, thời gian chat, lượng profile signal hay mức “giống con người” của agent. Nhóm cũng không đặt 3D làm giá trị cốt lõi của booking, dù 3D vẫn là capability trải nghiệm cần vận hành tốt. Mục 8 định nghĩa đầy đủ phần ngoài phạm vi.

### 4.7 Opportunity size và business case

Repo và PDF hiện không có baseline nội địa đáng tin cậy về số lead, booking, show-rate, chi phí follow-up hoặc conversion sau lái thử. Vì vậy, em không đưa TAM, doanh thu uplift hoặc mục tiêu phần trăm giả định vào phần thân PRD.

Khi có baseline, Business Owner và PO sẽ dùng mô hình giá trị sau thay vì chỉ đếm số cuộc chat:

```text
Giá trị tăng thêm ước tính
= (số booking đủ điều kiện × attendance uplift × giá trị kỳ vọng của một lượt lái thử đến)
  + (số follow-up thủ công giảm × chi phí đầy đủ mỗi follow-up)
  - (chi phí provider + LLM + vận hành care + chi phí thay đổi quy trình)
```

Mọi biến trong công thức hiện là TBD. Nếu Business Owner dùng downstream sales conversion hoặc contribution margin để quy đổi “giá trị kỳ vọng”, nguồn, cửa sổ attribution và owner của dữ liệu đó phải được ghi trong business case.

- **🔵 Open Question (Câu hỏi mở):** Business Owner phải cung cấp baseline 8–12 tuần gần nhất cho booking created, confirmed, cancelled, no-show, checked-in, completed và số lần staff follow-up trước khi duyệt business case.
- **🔶 Assumption (Giả định):** Giảm bất định và tăng attendance tạo giá trị lớn hơn việc tối đa hóa số cuộc hội thoại. Pilot sẽ so sánh outcome theo cohort thay vì chỉ đếm engagement.

---

## 5. Solution Overview

### 5.1 Nguyên tắc sản phẩm

1. **State trước, hội thoại sau.** UI và agent chỉ được mô tả trạng thái lấy từ booking service; câu chữ không được suy diễn vượt quá state.
2. **UI cho dữ liệu có cấu trúc; agent cho bất định.** Người dùng chọn xe/showroom/slot, nhập thông tin, OTP và quản lý lịch bằng control rõ ràng. ViVi giải thích, chuẩn bị và hỗ trợ theo ngữ cảnh.
3. **Một nguồn sự thật.** Public web, ViVi, email/Zalo và DriveOps cùng đọc một booking state, participant model, inventory và event history.
4. **Ít dữ liệu nhất nhưng đủ tạo giá trị.** Nhóm không thu ảnh/số GPLX trong P0. Profile chỉ lưu tín hiệu bền vững khi có mục đích, consent phù hợp và quyền sửa/xóa.
5. **Booker và driver là hai chủ thể.** Hệ thống không tự chuyển profile, quyền hoặc dữ liệu riêng tư từ người này sang người kia.
6. **Không biết thì nói không biết.** ViVi chỉ dùng knowledge đã duyệt cho fact; nếu thiếu nguồn hoặc dữ liệu live, ViVi phải nêu giới hạn và đưa ra kênh hỗ trợ.
7. **Degrade theo capability.** Lỗi booking không được làm sập catalogue/content; lỗi AI không được chặn self-service; lỗi knowledge không được ảnh hưởng booking transaction.
8. **Mọi release cần evidence.** “Đã build” chỉ là đầu vào. Sản phẩm chỉ qua gate khi có test, telemetry, security/privacy review và acceptance evidence.

### 5.2 Hành trình TO-BE

| Bước | Trải nghiệm người dùng | Hệ thống chịu trách nhiệm | Kết quả bắt buộc |
|---|---|---|---|
| 1. Khám phá | Người dùng xem catalogue, nội dung và CTA lái thử | Discover & Evaluate | Model và CTA có nguồn dữ liệu/fallback rõ; không tuyên bố live availability |
| 2. Chọn nguồn lực | Người dùng chọn model, vị trí/showroom và slot | Availability + Booking UI | Hiển thị tiêu chí xếp hạng; chỉ cho chọn slot đủ xe/capacity |
| 3. Giữ chỗ | Hệ thống giữ slot trong thời gian hữu hạn | Booking service | UI nói rõ “đang giữ, chưa xác nhận”, còn bao lâu và cách phục hồi khi hết hạn |
| 4. Nhập người tham gia | Người dùng chọn tự lái hoặc đặt hộ và nhập dữ liệu tối thiểu | Participant model | Booker/driver tách đúng; consent không được pre-check |
| 5. Xác minh | Booker nhận và nhập OTP trên kênh đã hỗ trợ | Identity/Access | OTP đúng purpose, hết hạn, chống replay/rate abuse và có recovery |
| 6. Xác nhận | Hệ thống revalidate hold, xe, slot và version trước commit | Booking transaction | Chỉ sinh mã khi state chuyển thành `confirmed`; không double-book |
| 7. Hiểu trạng thái | Success screen và notification hiển thị kết quả | UI + Notification | Mã, trạng thái, resource, showroom, giờ, người tham gia, bước tiếp theo, quản lý lịch; chỉ hiện SLA đã duyệt, nếu chưa thì hiện contact/giờ hoạt động và nói rõ chưa cam kết thời gian |
| 8. Chăm sóc | Booker hoặc driver hỏi ViVi/nhận checklist đã duyệt | Post-booking Care | Grounded answer, một câu hỏi ngữ cảnh tối đa, quyền rõ, không ép làm profile |
| 9. Tự quản lý | Booker tra cứu, sửa dữ liệu được phép, đổi hoặc hủy | Self-service + OTP | Đổi giữ lịch cũ tới khi lịch mới confirm; hủy dừng reminder và giải phóng resource |
| 10. Vận hành | Người có quyền xác minh GPLX, check-in và hoàn tất/no-show | DriveOps | State transition đúng, scoped RBAC và audit đầy đủ |

### 5.3 Hai lớp của ViVi

| Lớp | Khi nào dùng | Tool/quyền | Không được làm |
|---|---|---|---|
| Booking assistant | Trước xác nhận hoặc khi booker vào self-service | Tìm option, giữ slot, cập nhật held booking, OTP/access, đọc/confirm theo action có cấu trúc | Tự bịa availability, tự bỏ qua OTP, tự đổi/hủy khi chưa có explicit confirmation |
| Post-booking care | Chỉ khi server xác định booking `confirmed` hoặc `checked_in`; với driver, token còn hợp lệ **và** booking vẫn ở state care-eligible | Tìm knowledge đã duyệt và cập nhật profile signal hợp lệ | Sửa/đổi/hủy/tra cứu booking qua driver link; dùng profile làm nguồn fact; lưu PII/OTP/secret; tư vấn bán hàng không có nguồn |

Artifact `advise_skill_node.py` hiện không được nối vào graph và không phải capability đang chạy. Trong v2, tư vấn chọn xe tổng quát trước booking thuộc P2. Nhóm không xây một lớp advisor thứ ba ở P0 cho đến khi booking và care đạt gate.

### 5.4 Booking state machine chuẩn

Booking bắt đầu ở `held`; hệ thống hiện không có state `draft`. PO chọn state machine chuẩn cho P0 như sau:

```text
held ──confirm──> confirmed ──license + check-in──> checked_in ──complete──> completed
  │                    ├──cancel────────────────────────────────> cancelled
  │                    ├──reschedule────────────────────────────> rescheduled
  │                    └──after grace period────────────────────> no_show
  ├──hold timeout────> expired
  └──user releases──> cancelled
```

| State | Copy người dùng chuẩn | Care active | Mutation chính |
|---|---|---:|---|
| `held` | “Đang giữ chỗ — lịch chưa được xác nhận” | Không | Cập nhật thông tin, OTP, confirm hoặc release |
| `confirmed` | “Lịch lái thử đã được xác nhận” | Có | Booker đổi/hủy qua access phù hợp |
| `checked_in` | “Bạn đã check-in tại showroom” | Có trong phạm vi hỗ trợ buổi lái thử | Người có quyền hoàn tất |
| `completed` | “Buổi lái thử đã hoàn tất” | Không trong v2 | Chỉ đọc lịch sử; post-drive nurture là future scope |
| `no_show` | “Showroom ghi nhận bạn chưa đến” | Không | Liên hệ hỗ trợ/đặt lịch mới theo policy |
| `cancelled` | “Lịch đã hủy” | Không | Không gửi reminder; cho phép tạo lịch mới |
| `rescheduled` | “Lịch này đã được đổi; vui lòng xem lịch mới” | Không trên booking cũ | Chỉ booking mới được chăm sóc |
| `expired` | “Thời gian giữ chỗ đã hết” | Không | Chọn slot mới |

Mọi UI/email/agent copy phải phân biệt `held` với `confirmed`. Nếu một môi trường nghiệp vụ cần showroom duyệt thủ công, nhóm phải bổ sung state `pending_confirmation` và SLA trước khi dùng copy “đã xác nhận”; nhóm không được dùng copy để che một state chưa tồn tại.

**Invariant P0:** Journey hiện được thiết kế để confirm đồng bộ ngay sau OTP và bước revalidation cuối. Hệ thống không có hàng chờ duyệt thủ công: request thành công phải trả `confirmed`, còn request lỗi phải giữ/đóng state đúng và đưa recovery. Nếu Business/Operations thay đổi invariant này, PO phải bổ sung `pending_confirmation`, success copy, SLA, notification, cancel path và care scope trước khi release.

### 5.5 Participant, identity và quyền

| Chủ thể | Dữ liệu booking tối thiểu | Cách xác thực | Quyền |
|---|---|---|---|
| Booker | Tên, email; điện thoại nếu kênh/nghiệp vụ cần | OTP theo contact và purpose | Xem, sửa trường được phép, đổi, hủy và nhận thông tin booking |
| Driver cùng booker | Dùng cùng `person_id` | Quyền booker | Care và quản lý như một người |
| Driver khác booker | Tên, email; cam kết có GPLX hợp lệ; không lưu ảnh/số GPLX ở P0 | Private invitation token có expiry và binding | Care theo booking; không có booking mutation |
| Internal user | Tài khoản portal và role/scope | Bearer session nội bộ | Theo RBAC; mọi mutation audit |

Driver invitation P0 phải có các thuộc tính sau: server chỉ lưu hash; raw token chỉ truyền qua TLS tới endpoint resolve/chat và không được persist vào log, analytics, referrer hoặc storage dài hạn; token gắn đúng booking và driver; một booking chỉ có một link active; link hết hạn không muộn hơn thời điểm kết thúc lịch hoặc TTL policy; cancel/reschedule phải revoke link cũ và phát hành link phù hợp cho booking mới; request phát hành/revoke chỉ dành cho actor có quyền; delivery/open/resolve/expire/revoke đều có event không chứa token thô. Client phải resolve với server ngay khi mở link và chỉ render care active sau khi state/token/participant đều hợp lệ.

### 5.6 Care contract

Agent hậu booking v2 là **agent hỗ trợ chuẩn bị trước và trong buổi lái thử theo yêu cầu**, kết hợp các notification/checklist chủ động đã được duyệt. Agent chưa phải CRM tự động hoặc agent chăm sóc sau khi lái thử.

Mỗi lượt care phải tuân theo thứ tự:

1. ViVi trả lời câu hỏi hiện tại hoặc nêu rõ thiếu dữ liệu.
2. ViVi nối câu trả lời với booking/profile chỉ khi ngữ cảnh thực sự liên quan.
3. ViVi đưa ra một bước tiếp theo dễ làm, ví dụ xem checklist, mở bản đồ, quản lý lịch hoặc liên hệ showroom.
4. ViVi chỉ hỏi tối đa một câu có giá trị cho nhu cầu hiện tại; ViVi không phỏng vấn để “làm đầy hồ sơ”.
5. Khi người dùng sửa hoặc rút lại một preference, profile phải giữ lịch sử nhưng view active phải phản ánh lựa chọn mới.

Care checklist P0 gồm: trạng thái hiện tại; mã lịch; giờ và showroom; bản đồ/đường đi; giấy tờ bản gốc cần mang; thời lượng dự kiến; quy trình tại showroom; điểm nên trải nghiệm theo nhu cầu; đầu mối hỗ trợ; link quản lý lịch dành cho booker. UI phải ghi được view và một acknowledgement action đơn giản; checklist item state/persistence chi tiết thuộc P1. Mỗi claim có tính thời điểm phải đến từ booking service hoặc content record còn hiệu lực.

Sự “chủ động” trong P0 đến từ trigger xác định như confirmation, T-24h và T-2h với template được duyệt. Agent không tự quyết định gửi outbound message dựa trên suy đoán profile.

P0 chỉ cho phép Q&A về trạng thái và chuẩn bị booking hiện tại, quy trình/showroom, giấy tờ, sạc/ADAS/không gian và các tính năng của đúng mẫu/phiên bản đã đặt mà người dùng nên trải nghiệm. ViVi phải từ chối hoặc handoff các yêu cầu chọn/so sánh mẫu xe khác, giá lăn bánh/khuyến mãi live, vay, bảo hiểm, đàm phán và cam kết mua bán. ViVi có thể chỉ dẫn người dùng về catalogue hoặc tạo booking mới qua luồng riêng, nhưng không biến care thread thành advisor/bán hàng tổng quát.

### 5.7 Knowledge và grounding

Repo hiện có retrieval lexical dựa trên JSON với provenance và filter market/model/trim/model-year. Đây không phải semantic/vector RAG. P0 không yêu cầu vector search; P0 yêu cầu **fact được kiểm soát**.

| Yêu cầu | Quy tắc P0 |
|---|---|
| Review state | Production chỉ phục vụ record `approved`; `pending_internal_review`, `rejected`, `expired` và `superseded` không được trả về |
| Provenance | Record phải có nguồn, market, model/trim/year liên quan, effective/review/expiry date và owner |
| Live-data boundary | Giá hiện tại, khuyến mãi, tồn xe/slot và chính sách thay đổi phải gọi nguồn live hoặc nói rõ chưa thể xác nhận |
| Answer rendering | Fact quan trọng phải kèm nguồn/ngày hiệu lực ở dạng người dùng hiểu được; model không được tự tạo citation |
| Missing knowledge | ViVi nêu giới hạn, không bịa và đưa ra đường dẫn/contact phù hợp |
| Governance | Content Owner duyệt; AI Quality Owner theo dõi retrieval miss, stale fact và regression theo version |

### 5.8 Profile và cá nhân hóa

Profile giúp ViVi ghi nhớ tín hiệu bền vững như nhu cầu không gian, thói quen di chuyển, mối quan tâm sạc, trải nghiệm xe điện và điều người dùng muốn quan sát. Profile không phải mục tiêu tự thân.

P0 phải đáp ứng:

- Hệ thống phân biệt `direct`, `inferred` và `third_party`; inference luôn có certainty/confidence và không được trình bày như fact đã xác nhận.
- Dữ liệu của booker và driver không được trộn. Tín hiệu do một người nói về người kia chỉ được dùng hạn chế, gắn third-party và không được nâng thành direct fact.
- Validator deterministic phải chặn email, phone, địa chỉ chính xác, GPS, OTP, credential, token, GPLX, dữ liệu sức khỏe/tài chính và free text nhạy cảm khỏi profile signal.
- UI/agent phải giải thích cá nhân hóa, cung cấp opt-out và cho người dùng xem, sửa, retract, export hoặc yêu cầu xóa theo policy đã phê duyệt.
- Log không được ghi raw snapshot/profile/identity. Trace chỉ giữ field đã redaction và dùng access control/retention riêng.
- Sales brief chỉ hiển thị trong portal cho actor đúng scope; brief phải tách direct/inferred, không hiển thị internal ID/hash và không tự động biến inference thành lead fact.

**🔵 Open Question (Câu hỏi mở):** Legal/Privacy Owner phải chốt lawful basis, retention theo trạng thái profile, cách xử lý deletion khi signal đã tham gia audit, và wording consent trước Gate G1.

### 5.9 Notification và calendar

| Kênh | Trạng thái code audit | Quyết định v2 |
|---|---|---|
| Email | Gmail adapter có thể cấu hình; mặc định development dùng in-memory mock | Email là kênh bắt buộc của pilot sau khi E2E với provider thật đạt gate |
| Zalo | Có khi cấu hình bot và người dùng đã liên kết | Kênh tùy chọn; không được giả định mọi số điện thoại có Zalo linked |
| SMS | Chưa có SMS provider production đúng nghĩa | Ngoài P0; UI/copy không được tuyên bố SMS đã sẵn sàng |
| Calendar | UI hiện mở Google Calendar template; code tạo `.ics` tồn tại nhưng chưa được nối vào hành động người dùng; không có two-way sync | Gọi đúng là “thêm vào Google Calendar”, không gọi là “đồng bộ”; reschedule phải tạo thông tin mới và cảnh báo event cũ |

Người đặt và người lái phải nhận nội dung khác nhau. Notification cho driver khác booker chỉ được gửi sau khi mục đích, nguồn contact và consent/legitimate-interest policy được phê duyệt. Khi booking bị cancel/reschedule, worker phải ngăn cả job `pending`, `retrying` và `processing` gửi nội dung cũ hoặc phải có idempotent state check ngay trước delivery.

Mỗi booking chỉ có một follow-up owner active. Notification service và sales workflow phải dùng cùng contact policy: dedupe theo purpose/time window, frequency cap theo participant/channel, global opt-out cho nội dung không thiết yếu, suppression ngay khi cancel/no-show policy đóng care, và không để email/Zalo/cuộc gọi từ nhiều owner lặp cùng nội dung. Confirmation/giao dịch bắt buộc phải được phân loại riêng với marketing/care tùy chọn.

### 5.10 Capability baseline tại thời điểm viết PRD

| Capability | Trạng thái | Bằng chứng chính | Khoảng trống trước pilot |
|---|---|---|---|
| Website/catalogue/detail/3D/charging/after-sales | Đã triển khai một phần trên public SPA | `frontend/src/App.jsx`, `HomePage.jsx`, `CarDetailPage.jsx` | Content không đồng đều; claim giá/chính sách hard-code; fallback/performance/a11y chưa đủ |
| Booking UI + backend transaction | Đã triển khai | `BookingPage.jsx`, `services/booking/lifecycle.py` | Hold cleanup runtime, copy/state, hold-vs-OTP, E2E và telemetry |
| Inline email OTP trước confirm | UI đã nối OTP nhưng backend confirm chưa enforce access token/permission | `BookingPage.jsx`, `services/booking/access.py`, confirm tool/service | P0: bind token với booking/contact/purpose, chống replay và bắt buộc ở mọi confirm endpoint |
| Booker/driver model + onsite GPLX | Đã triển khai | booking schema/lifecycle và portal license flow | Consent driver; evidence/role workflow; không upload GPLX trong P0 |
| Lookup/edit/reschedule/cancel | Đã triển khai nhưng chưa usability-pass | `BookingPage.jsx`, `management.py` | Entry point, edit driver policy, notification/token lifecycle, E2E |
| DriveOps RBAC/booking/fleet/schedule/audit | Đã triển khai một phần | `internal-portal/frontend`, `backend/src/internal_portal` | Portal routing/search/pagination, staff action policy, MFA/reset, usability/a11y |
| Agent hậu booking | Đã merge vào `testing`, chưa có trên `main` | PR #69; `post_booking_skill` và node | Reactive only; test coverage, budget/tool-loop, security/privacy và rollout |
| Driver invitation | Đã triển khai trên `testing` | `driver_invitation.py`, confirmation email, frontend invitation mode | Authorized issuance, reschedule/revoke, consent, telemetry và E2E |
| Persistent profile/sales brief | Backend prototype | `services/profile`, summary APIs | Data rights, validator, safe logging, portal consumer, authorization và recovery |
| Trusted knowledge | 25 record pending review; lexical retrieval | `services/knowledge` | 0 approved record tại audit; production gate đang cho phép pending |
| Product analytics | Chưa triển khai | Không có tracking abstraction trong hai frontend | Event taxonomy, consent, dashboards, experiment/cohort design |
| Automated frontend/E2E/a11y | Chưa triển khai | `package.json` không có test script | Test runner, critical journeys, browser/device/a11y evidence |
| Human handoff | Chưa có workflow/tool end-to-end | Chỉ có contact/advisor data rời rạc | Handoff reason, transcript/context packet, SLA, ownership và closure |

### 5.11 Quyết định sản phẩm đã chốt trong PRD v2

| ID | Quyết định | Rationale |
|---|---|---|
| D-01 | P0 dùng structured booking UI; ViVi không thay form bằng chuỗi câu hỏi dài | Usability synthesis cho thấy chat có thể chậm hơn form |
| D-02 | Agent P0 tập trung hậu booking; advisor chọn xe tổng quát là P2 | Khoảng trống sau submit có bằng chứng mạnh hơn và code mới đi theo hướng này |
| D-03 | Booking state `held` chiếm slot; mã chỉ được phát hành khi chuyển `confirmed`; care active ở `confirmed`/`checked_in` | Phản ánh invariant code và giảm copy mơ hồ |
| D-04 | Booker/driver tách profile, notification và quyền | Giảm rò dữ liệu và phục vụ đúng người |
| D-05 | GPLX P0 được kiểm bản gốc tại showroom; không upload/lưu số/ảnh | Data minimization và phù hợp implementation hiện tại |
| D-06 | Bỏ VIP approval khỏi v2 | Không có evidence đủ mạnh; ghi chú nghiên cứu mới đề xuất bỏ; giảm nhánh state không cần thiết |
| D-07 | 3D là capability trải nghiệm, không phải core value/metric của booking | 3D đã có code nhưng không giải quyết root problem |
| D-08 | Profile không được âm thầm làm giàu; người dùng có quyền kiểm soát | Personalization chỉ có giá trị khi có trust và immediate user benefit |
| D-09 | P0 care kết thúc khi hành trình lái thử kết thúc; post-drive nurture là future | Code hiện dừng ở `completed`; chưa có discovery/CRM consent cho post-drive |

---

## 6. Success Metrics and Evaluation

### 6.1 North Star Metric

**Attendance Rate của lịch đủ điều kiện**

```text
Attendance Rate = số logical appointment có event check-in
                  / (số logical appointment có event check-in + số logical appointment no-show)
```

Một **logical appointment** là booking mới nhất trong một chuỗi reschedule; chuỗi chỉ được đếm một lần. Numerator dùng event check-in đầu tiên, nên một booking đi từ `checked_in` sang `completed` không bị đếm hai lần. Cohort chỉ đóng sau khi slot kết thúc cộng grace period 30 phút và data-closure window 24 giờ; booking test, `held`, `expired`, predecessor `rescheduled` và booking bị showroom hủy không tham gia. Booking người dùng hủy được báo cáo riêng theo khoảng cách tới giờ hẹn; PO không giấu late-cancellation bằng cách gộp vào no-show.

Nếu một appointment vẫn `confirmed` sau data-closure window, dashboard phải gắn `unclosed`; báo cáo quyết định scale tạm coi nó là non-attended và đồng thời hiển thị State Closure Completeness. Nhóm không đưa kết luận outcome nếu completeness dưới gate. Dashboard phải tách theo showroom, resource được hứa, channel, self/book-for-other và cohort dùng/không dùng care.

Baseline hiện là **TBD** vì repo không có telemetry production đã xác minh. PO không dùng target 70%, 45%, 25% hoặc ngưỡng 80% trong PRD cũ/PDF làm cam kết, vì chúng không xuất phát từ baseline VinFast của dự án.

### 6.2 Metric hierarchy

| Tầng | Metric | Định nghĩa | Baseline | Cách dùng |
|---|---|---|---|---|
| Business outcome | Attendance Rate | Công thức mục 6.1 | TBD | North Star; so theo cohort/pilot |
| User outcome | Booking confirmation task success | Người dùng bắt đầu booking và đạt `confirmed` với dữ liệu hợp lệ | TBD | Tìm friction ở slot/form/OTP |
| User outcome | Status comprehension | Người test nói đúng state, bước tiếp theo và nơi quản lý sau success | Nghiên cứu mới chỉ định tính | Gate usability |
| User outcome | Self-service completion | Lookup/reschedule/cancel hoàn tất không cần staff hỗ trợ | TBD | Đo giá trị tự phục vụ |
| Care outcome | Preparation checklist engagement | Người tham gia mở checklist hoặc acknowledgement CTA trước giờ hẹn | Chưa có event | Leading indicator, không thay Attendance; item completion là P1 nếu checklist trở thành tương tác |
| Care outcome | Grounded resolution rate | Care session được human label là đúng, có căn cứ và giải quyết/đưa bước tiếp theo | Chưa có golden baseline | AI quality gate |
| Care outcome | Driver invitation activation | Link hợp lệ được driver mở và bắt đầu care / link delivered | Chưa đo | Kiểm chứng giá trị luồng đặt hộ |
| Ops outcome | Assignment-to-contact latency | Thời gian từ confirmed tới assigned staff/first acknowledged contact | Chưa đo | SLA showroom |
| Ops outcome | State closure completeness | Booking đã qua lịch có `completed`, `no_show` hoặc trạng thái hợp lệ | Chưa đo | Guardrail cho North Star |
| Reliability | Notification delivery success | Job delivered / job eligible theo kênh thật | Chưa đo | Provider/worker health |
| Reliability | Profile persist success | Signal hợp lệ persisted / enqueue accepted, gồm retry/DLQ | Chưa đo | Không mất dữ liệu âm thầm |
| Guardrail | Unauthorized data/action incidents | Truy cập profile/token hoặc booking mutation trái quyền | Chưa đo | Phải bằng 0 Sev-1/Sev-2 mở khi release |
| Guardrail | Double-booking incidents | Hai booking active dùng cùng resource chồng thời gian | Chưa đo | Phải bằng 0 trong test/pilot |
| Guardrail | Late cancellation rate | User cancellation sau cutoff do Operations/PO chốt / confirmed appointment | Chưa đo | Không để Attendance che mất cam kết bị vỡ sát giờ |
| Guardrail | Duplicate/over-contact rate | Booking nhận contact trùng/vượt cap hoặc có hơn một active follow-up owner | Chưa đo | Phải bằng 0 incident chưa xử lý trong pilot |
| Guardrail | Contact opt-out/complaint rate | Opt-out hoặc complaint / booking đã nhận outbound care | Chưa đo | Theo dõi trust và dừng campaign/channel khi vượt threshold |

### 6.3 Target và pilot gate đề xuất

Các ngưỡng dưới đây là release criteria tạm thời, không phải dự báo business.

| Gate metric | Ngưỡng đề xuất | Trạng thái bằng chứng |
|---|---:|---|
| Critical journey usability | ≥85% với `n ≥ 7` tự hoàn tất booking và nói đúng state/bước tiếp theo; 0 critical safety/privacy failure | **🔶 Assumption (Giả định)**; với n=7 tương đương ít nhất 6 người |
| Manage journey | ≥85% với `n ≥ 7` tìm được entry point và hoàn tất lookup + một thao tác đổi/hủy không cần moderator | **🔶 Assumption (Giả định)** |
| Booking invariants | 100% test concurrency/idempotency/hold-expiry/pass; 0 double-booking | Bắt buộc trước pilot |
| Security/privacy red team | 0 unauthorized profile read, invitation issuance, token leak hoặc driver mutation | Bắt buộc trước pilot |
| Contact guardrail | 100% opt-out/suppression honored; 0 duplicate contact hoặc nhiều active owner trong pilot chưa được xử lý | Bắt buộc trước khi bật outbound care |
| Knowledge critical facts | 100% record được dùng ở production có trạng thái `approved`, còn hiệu lực và có provenance | Bắt buộc trước pilot |
| AI safety-critical cases | 100% pass ở privacy, permission, booking truth, live-data boundary và harmful hallucination set | **🔶 Assumption (Giả định)** về bộ case; failure bất kỳ chặn release |
| AI quality non-critical | ≥90% human-accepted grounded/relevant/actionable trên golden set; không dimension cốt lõi dưới 85% | **🔶 Assumption (Giả định)**; điều chỉnh sau calibration, không lấy từ ví dụ PDF |
| Delivery | Confirmation/checklist email E2E bằng provider thật đạt ≥99% trong pre-pilot test window, không gửi reminder sau cancel | **🔶 Assumption (Giả định)**; cần SRE/Operations chốt window và sample |
| State data quality | ≥98% logical appointment được đóng `completed`/`no_show` trong 24 giờ sau slot; phần còn lại có owner xử lý | **🔶 Assumption (Giả định)**; dưới gate thì không ra quyết định outcome |
| CI | 100% required checks xanh; không còn test fail/skip không có waiver | Hiện chưa đạt |

### 6.4 Funnel và event taxonomy tối thiểu

| Giai đoạn | Events bắt buộc |
|---|---|
| Discover | `catalogue_impression`, `vehicle_detail_viewed`, `vehicle_media_interacted`, `booking_cta_clicked` |
| Availability | `booking_started`, `location_method_selected`, `showroom_results_viewed`, `showroom_selected`, `slot_results_viewed` |
| Hold/identity | `slot_hold_created`, `slot_hold_expired`, `slot_hold_released`, `participant_mode_selected`, `otp_requested`, `otp_delivered`, `otp_verified`, `otp_failed`, `otp_locked` |
| Confirm | `booking_confirm_attempted`, `booking_confirmed`, `booking_confirm_failed`, `confirmation_viewed`, `manage_entry_clicked` |
| Self-service | `booking_lookup_started`, `booking_lookup_completed`, `booking_edit_completed`, `reschedule_started`, `reschedule_completed`, `booking_cancelled` |
| Care | `care_opened`, `care_message_sent`, `care_checklist_viewed`, `care_checklist_acknowledged`, `knowledge_retrieved`, `care_answer_feedback`, `care_handoff_offered`, `care_handoff_accepted` |
| Invitation | `driver_invite_issued`, `driver_invite_delivered`, `driver_invite_opened`, `driver_invite_resolved`, `driver_invite_revoked`, `driver_invite_expired` |
| Communication | `notification_queued`, `notification_sent`, `notification_delivered`, `notification_failed`, `notification_bounced`, `notification_suppressed`, `contact_opted_out`, `duplicate_contact_detected`, `first_contact_acknowledged` |
| Operations | `booking_assigned`, `license_check_recorded`, `booking_checked_in`, `booking_completed`, `booking_no_show`, `ops_transition_failed` |
| AI/runtime | `route_selected`, `tool_called`, `tool_blocked`, `profile_signal_rejected`, `profile_signal_persisted`, `profile_queue_failed`, `knowledge_miss`, `eval_sample_created` |

Mỗi event phải có `event_id`, UTC timestamp, environment, app/version, correlation/trace ID, pseudonymous actor ID, participant role, booking state trước/sau nếu liên quan, channel, result/error code và latency. AI event bổ sung model, prompt, skill, tool và knowledge version. Analytics không được nhận tên, email, phone, exact GPS, message/token thô, GPLX hoặc profile free text.

### 6.5 AI evaluation lifecycle

Nhóm vận hành evaluation theo vòng lặp sau:

1. Product/AI Quality đọc trace đã redaction, user feedback và incident để lập failure taxonomy.
2. Nhóm tạo golden dataset gồm happy path, edge case và failure thật, có nhãn người và version.
3. Dataset phải phủ actor, booking state, self/book-for-other, driver invitation, mức đủ thông tin, độ mơ hồ, knowledge hit/miss/stale và tình huống tấn công.
4. Offline eval chạy trước merge/release; regression ở dimension critical chặn release.
5. LLM judge chỉ dùng sau khi được calibration với nhãn người. Dashboard phải theo dõi TPR, TNR, precision/recall theo failure class; accuracy tổng không đủ.
6. Production monitoring lấy mẫu theo rủi ro, phát hiện drift và đưa failure mới trở lại golden set.

| Dimension | Câu hỏi đánh giá |
|---|---|
| Routing | Booking/care/sensitive/out-of-scope có được chọn đúng theo state và participant không? |
| Booking truth | Câu trả lời có đúng state, resource và quyền hiện tại không? |
| Grounding | Mọi fact cần nguồn có được retrieval từ record approved/valid không? |
| Relevance/actionability | Câu trả lời có giải quyết câu hỏi trước khi hỏi thêm và đưa bước tiếp theo hữu ích không? |
| Permission/privacy | Driver có bị lộ dữ liệu/quyền booker không; profile có nhận dữ liệu cấm không? |
| Profile quality | Direct/inferred/third-party, confidence và revise/retract có đúng không? |
| Tone/accessibility | Ngôn ngữ có rõ, không ép buộc, không phỏng vấn và phù hợp người non-tech không? |
| Fail-safe | Khi tool/knowledge/LLM lỗi, hệ thống có giữ booking transaction và đưa fallback đúng không? |

### 6.6 Dashboard và nhịp review

- PO review funnel, Attendance và self-service hàng tuần trong pilot.
- AI Quality Owner review grounded resolution, knowledge miss, profile reject và safety incidents ít nhất hàng tuần, đồng thời review ngay khi model/prompt/knowledge version đổi.
- Operations review assignment/contact latency, notification failure, state closure và resource conflict hằng ngày trong pilot.
- Security/Privacy nhận alert ngay cho unauthorized access, token leakage, raw PII logging hoặc data-rights failure.
- Mỗi dashboard phải hiển thị sample size, denominator, time window, environment và data-quality warning; nhóm không công bố phần trăm không có denominator.

---

## 7. User Stories and Requirements

### 7.1 Cách ưu tiên

| Mức | Ý nghĩa |
|---|---|
| P0 | Bắt buộc để mở pilot; thiếu requirement này thì booking/care không an toàn, không đo được hoặc không giải quyết root problem |
| P1 | Bắt buộc trước khi mở rộng nhiều showroom; có thể pilot giới hạn với workaround được phê duyệt |
| P2 | Tối ưu/future capability sau khi P0/P1 chứng minh outcome |

Một requirement được coi là **Done** khi code, automated test, telemetry, security/privacy evidence, content và acceptance evidence liên quan đều hoàn tất. Việc merge code hoặc demo happy path không đủ để đóng requirement.

Với module có thể tắt độc lập như persistent profile hoặc driver invitation, “P0” nghĩa là bắt buộc trước khi module đó xuất hiện trong pilot. Nếu chưa đạt, server-side feature flag phải tắt route, worker, UI và outbound liên quan; team không được giữ endpoint công khai rồi gọi capability đó là “không nằm trong scope”.

### 7.2 Functional requirement register

| ID | Pri | Yêu cầu | Acceptance evidence tối thiểu |
|---|---:|---|---|
| FR-DIS-01 | P1 | Website phải hiển thị catalogue/chi tiết/CTA từ canonical API và phân biệt editorial fallback | Contract test, loading/error/empty, content owner sign-off |
| FR-DIS-02 | P0 | Claim về giá, sạc, bảo hành, pháp lý và thời điểm phải có source/version/effective date | Content inventory; 100% claim nhạy cảm có owner/approval |
| FR-DIS-03 | P1 | Showroom result phải giải thích khoảng cách, slot sớm nhất và tiêu chí xếp hạng | Usability test và ranking telemetry |
| FR-DIS-04 | P0 | Catalogue/content vẫn hoạt động khi booking health hoặc AI lỗi; chỉ capability lỗi bị disable | Chaos/E2E degraded-mode test |
| FR-DIS-05 | P1 | Gallery/model summary/booking CTA phải xuất hiện đủ sớm cho người mới; màu, zoom, section navigation và back-to-top phải dùng được | Usability + responsive/a11y evidence |
| FR-DIS-06 | P1 | Mỗi state/màn hình phải có một primary action rõ; CTA/tag/highlight còn lại phải có hierarchy phụ | Design review + usability evidence |
| FR-BK-01 | P0 | Availability chỉ trả slot có xe demo/capacity hợp lệ, dùng cùng nguồn với DriveOps và một horizon authoritative | Concurrency/inventory/horizon contract tests |
| FR-BK-02 | P0 | Hold phải được tạo atomically, có expiry authoritative, idempotency và cơ chế giải phóng runtime | Concurrent hold + worker recovery + expiry E2E |
| FR-BK-03 | P0 | UI phải trình bày `held` là chưa xác nhận và không sinh booking code trước commit | UI test, API/state assertion |
| FR-BK-04 | P0 | Hệ thống phải tách self-booking với book-for-other, cùng booker/driver model chuẩn | API/UI/E2E cho cả hai nhánh |
| FR-BK-05 | P0 | Consent tùy chọn phải mặc định tắt, có purpose/copy rõ, persist và audit đúng lựa chọn | UI test + DB/audit assertion |
| FR-BK-06 | P0 | Mọi confirm/mutation nhạy cảm phải bắt buộc access token còn hạn, single-use, bind đúng booking, booker contact, participant role và purpose | Expiry/replay/attempt/rate-limit/cross-role/cross-booking E2E ở mọi endpoint |
| FR-BK-07 | P0 | Confirm phải revalidate hold, version, xe, pin, capacity và chỉ commit một lần | Idempotency, stale state, concurrency tests |
| FR-BK-08 | P0 | Success state phải hiển thị mã, state, resource đã hứa, showroom, giờ, participants, bước tiếp theo, manage CTA và SLA chỉ khi đã được Operations duyệt | Status comprehension ≥ gate mục 6.3 |
| FR-BK-09 | P0 | Booker phải lookup/edit trường cho phép/reschedule/cancel qua access có scope và expiry | Critical E2E + authorization tests |
| FR-BK-10 | P0 | Reschedule phải giữ lịch cũ đến khi lịch mới confirm; sau commit phải revoke reminder/invite cũ và tạo dữ liệu mới | Atomic reschedule + failure recovery test |
| FR-BK-11 | P0 | Cancel phải giải phóng resource, dừng mọi notification cũ và đóng care/invite | Worker race/idempotency test |
| FR-BK-12 | P0 | Booker phải sửa đúng contact/thay driver bằng re-verification; hệ thống phải revoke/reissue notification, invite và profile binding an toàn | Driver replace/decline/unactivated-invite E2E |
| FR-BK-13 | P0 | Product phải chốt model, variant hay demo asset là resource được hứa; substitution chỉ xảy ra theo rule và consent rõ | API/UI/success/ops contract + OQ-19 |
| FR-CARE-01 | P0 | Care chỉ active khi backend xác nhận state và participant; client không được tự bật | Route/state matrix tests |
| FR-CARE-02 | P0 | Confirmation/T-24h/T-2h phải cung cấp checklist approved, đúng participant và state | Notification/copy/E2E evidence |
| FR-CARE-03 | P0 | Fact phải lấy từ knowledge approved/valid hoặc live source; thiếu nguồn thì fail-safe | Retrieval + response validation + golden eval |
| FR-CARE-04 | P0 | Mỗi lượt phải trả lời trước, hỏi tối đa một câu liên quan và đưa next step | Golden conversation evaluation |
| FR-CARE-05 | P0 | Driver invitation phải private, expiring, revocable, authorized và không có booking mutation | Token lifecycle/permission/red-team tests |
| FR-CARE-06 | P0 | Profile phải tách actor, phân loại certainty/source, chặn dữ liệu cấm và hỗ trợ control/data rights | Validator, boundary, export/delete/retract tests |
| FR-CARE-07 | P0 | Khi LLM/tool/Redis/knowledge lỗi, booking/self-service vẫn dùng được và care đưa fallback an toàn | Fault injection và recovery test |
| FR-CARE-08 | P1 | Người dùng phải có cách chuyển sang người thật với reason/context tối thiểu; chỉ hiển thị SLA đã được duyệt, nếu chưa thì dùng contact/operating hours không cam kết thời gian | Handoff E2E + Operations sign-off |
| FR-CARE-09 | P0 | Success/care phải luôn có contact và operating hours deterministic; full ticket handoff có thể P1 nhưng người dùng không được rơi vào ngõ cụt | Content/API fallback + outage E2E |
| FR-COM-01 | P0 | Mỗi booking chỉ có một owner follow-up active; mọi channel dùng frequency cap, dedupe, opt-out và suppression theo state | Contact-policy tests + duplicate/complaint guardrail |
| FR-COM-02 | P0 | DriveOps hoặc integration phải ghi `first_contact_acknowledged` cùng actor/time/channel; không suy ra contact từ notification sent | Event/audit contract + portal/integration E2E |
| FR-OPS-01 | P0 | Internal API phải enforce RBAC/scope ở backend; UI hiding không phải security control | Role/scope matrix tests |
| FR-OPS-02 | P0 | Assignment, GPLX, check-in, completed/no-show/cancel phải theo state machine và audit | Transition/time-window/audit tests |
| FR-OPS-03 | P0 | Showroom đối chiếu booking code, driver identity/contact được mask và GPLX bản gốc/đúng hạng/còn hạn; hệ thống không thu file/số GPLX | Data inventory + identity/GPLX UI/API test |
| FR-OPS-04 | P1 | Authorized staff phải xem profile brief trong portal theo đúng booking/person và mức certainty | Scoped portal E2E; privacy sign-off |
| FR-OPS-05 | P1 | Portal phải có URL route, search, pagination và deep link notification | UX/E2E ở dataset lớn |
| FR-OPS-06 | P0 | Portal phải safe logout/reauth khi session hết hạn/revoked và critical portal journey phải có E2E trong CI | Revoked/expired-session + critical portal E2E |
| FR-OPS-07 | P0 | Trạng thái “chưa cấu hình” không được tự biến thành giờ hoạt động/capacity mặc định; operating hours, vehicle block và fleet state phải ảnh hưởng availability có audit | Unconfigured/default/inventory propagation tests |
| FR-OBS-01 | P0 | Critical funnel/care/ops events tại mục 6.4 phải được phát sinh với schema/version chung | Event contract tests + dashboard query |
| FR-OBS-02 | P0 | AI trace phải redaction, có model/prompt/knowledge version và nối được với eval sample | Trace security review + replayable eval |
| FR-OBS-03 | P0 | Alert phải bao phủ notification, hold cleanup, profile queue/DLQ, unauthorized access và state closure | Runbook + synthetic alert test |
| FR-AI-01 | P0 | Post-booking loop phải có tool/LLM/cost/time budget và circuit breaker | Loop/budget/failure tests |
| FR-AI-02 | P0 | Mọi thay đổi model/prompt/skill/knowledge phải chạy versioned offline eval trước release | CI evidence và eval report |
| FR-AI-03 | P1 | LLM judge phải được calibration với nhãn người và báo TPR/TNR theo failure class | Calibration report + threshold decision |

### 7.3 Epic A — Booking có thật và dễ hiểu

**Epic hypothesis:** Nếu hệ thống chỉ hiển thị resource thực, giải thích đúng state và xác minh danh tính trong một journey nhanh, người dùng sẽ hoàn tất booking với mức tin tưởng cao hơn và showroom giảm conflict.

#### US-A1 — Giữ một slot có thật

Là người muốn lái thử, tôi muốn hệ thống giữ đúng xe và khung giờ tôi chọn trong một khoảng rõ ràng, để tôi có thể nhập thông tin mà không lo người khác lấy cùng slot.

**Acceptance criteria**

- **Given** slot còn đủ điều kiện và chưa bị chiếm, **when** người dùng chọn giữ chỗ, **then** booking service phải atomically tạo booking `held`, gắn slot/resource, trả server expiry và version.
- **Given** hai request đồng thời chọn cùng resource, **when** transaction hoàn tất, **then** chỉ một request được giữ; request còn lại nhận lỗi có recovery option.
- **Given** hold hết hạn, **when** expiry worker/reconciliation chạy hoặc request mới kiểm tra, **then** booking chuyển `expired`, slot trở lại khả dụng và UI không restore held state cũ.
- **Given** hold còn hiệu lực, **when** người dùng refresh/khôi phục session, **then** UI phải đối chiếu server trước khi hiển thị countdown; client state không được là nguồn sự thật.
- **Given** backend chỉ mở lịch trong một horizon, **when** người dùng điều hướng calendar, **then** UI chỉ cho xem/fetch đúng horizon đó và phân biệt “ngoài kỳ mở lịch” với “đã kín”; calendar không được hiển thị ngày 31–60 như không có slot nếu API chỉ trả 30 ngày.
- **Given** backend trả model/variant/demo asset, **when** UI nhóm và hiển thị option, **then** UI không được bỏ mất cấp resource mà Product đã hứa; mọi substitution phải theo rule/consent của OQ-19.
- **🔵 Open Question (Câu hỏi mở):** PO và Engineering phải chốt TTL sau khi đo p50/p95 form + email OTP. Hai phút hiện tại là implementation constraint, chưa phải target sản phẩm đã được chứng minh.

#### US-A2 — Xác minh và xác nhận booking

Là booker, tôi muốn xác minh contact ngay trong bước review và chỉ nhận mã khi lịch đã commit, để tôi biết mình thực sự có lịch.

**Acceptance criteria**

- **Given** held booking đủ dữ liệu, **when** booker yêu cầu OTP, **then** hệ thống gửi qua kênh được hỗ trợ, hiển thị contact đã mask, expiry/resend rõ và không lộ OTP ở production.
- **Given** OTP sai, hết hạn, replay hoặc vượt giới hạn, **when** người dùng submit, **then** hệ thống từ chối với lỗi an toàn và không confirm booking.
- **Given** OTP hợp lệ, **when** bất kỳ endpoint/tool nào confirm booking, **then** backend phải nhận và consume access token có permission `confirm_booking`, bind đúng booking/booker contact/participant role; frontend verify OTP nhưng bỏ token không được coi là enforcement.
- **Given** driver khác booker hoặc contact chỉ thuộc driver, **when** actor xin `manage`, `reschedule` hoặc `cancel`, **then** backend phải từ chối trừ khi policy ownership riêng đã được chứng minh; shared contact không được tự động mở quyền cross-booking.
- **Given** OTP hợp lệ nhưng hold/version/resource đã thay đổi, **when** confirm chạy, **then** hệ thống không commit và đưa người dùng về recovery phù hợp.
- **Given** mọi invariant hợp lệ, **when** người dùng xác nhận rõ ràng, **then** hệ thống tạo đúng một booking code, chuyển `confirmed`, lập notification jobs và ghi event/audit.
- **Given** request bị retry do network, **when** cùng idempotency key được gửi lại, **then** hệ thống trả cùng kết quả, không tạo booking hoặc notification trùng.

#### US-A3 — Tách người đặt và người lái

Là người đặt hộ, tôi muốn khai báo riêng người lái, để showroom liên hệ đúng người và cả hai chỉ nhận thông tin thuộc vai trò của mình.

**Acceptance criteria**

- **Given** booker chọn “đặt hộ”, **when** điền form, **then** UI giải thích vì sao cần dữ liệu từng người và tạo hai participant riêng.
- **Given** driver khác booker, **when** booking confirm, **then** notification content, invitation và profile identity phải tách đúng người.
- **Given** hai người dùng chung email/phone, **when** profile được promote/merge, **then** `person_id` và participant role phải ngăn hai profile bị hợp nhất chỉ vì shared contact; trường hợp mơ hồ cần verification/review.
- **Given** booker hoặc driver xem care/profile, **when** hệ thống tạo context, **then** không lặp lại contact của người kia và không chuyển direct signal giữa hai profile.
- **Given** P0 GPLX, **when** người dùng đặt lịch, **then** hệ thống chỉ thu cam kết đủ điều kiện; showroom xác minh bản gốc trước check-in và không lưu ảnh/số GPLX.
- **Given** booker nhập sai contact, thay driver hoặc driver từ chối invitation, **when** thay đổi được xác minh, **then** hệ thống cập nhật participant theo policy, revoke link/notification/profile binding cũ, phát hành dữ liệu mới idempotently và giữ audit không lộ PII.

#### US-A4 — Success state không mơ hồ

Là người vừa hoàn tất booking, tôi muốn thấy một phiếu xác nhận rõ ràng, để tôi biết lịch có thật và làm gì tiếp theo.

**Acceptance criteria**

- **Given** confirm thành công, **when** success view hiển thị, **then** view phải có state label, booking code, resource đã hứa, showroom/address/map, start/end time, booker/driver, advisor nếu có, checklist và manage CTA; SLA chỉ xuất hiện khi Operations đã duyệt, nếu chưa thì UI hiển thị contact/giờ hoạt động và nói rõ chưa có cam kết thời gian phản hồi.
- **Given** dữ liệu advisor hoặc map chưa có, **when** render, **then** UI hiển thị fallback có ý nghĩa; không hiện `undefined`, dữ liệu bịa hoặc màn hình trống.
- **Given** booking chỉ đang `held` hoặc hệ thống mới nhận request, **when** UI/email render, **then** không dùng từ “đã xác nhận”.
- **Given** người dùng dùng keyboard/screen reader/reduced motion, **when** success transition chạy, **then** nội dung chính vẫn truy cập được mà không phụ thuộc cinematic animation.

### 7.4 Epic B — Self-service an toàn

**Epic hypothesis:** Nếu booker tìm và quản lý lịch bằng OTP với hành động tách bạch, người dùng sẽ ít phải gọi showroom và resource được giải phóng sớm hơn.

#### US-B1 — Tìm và xem lịch

Là người dùng quay lại, tôi muốn tìm lịch bằng contact/mã và OTP, để tôi xem đúng lịch của mình mà không lộ lịch của người khác.

**Acceptance criteria**

- **Given** người dùng mở header hoặc success CTA, **when** chọn “Quản lý lịch”, **then** entry point không phụ thuộc query parameter ẩn hoặc chat copy.
- **Given** contact có 0, 1 hoặc nhiều booking, **when** OTP hợp lệ, **then** UI hiển thị đúng empty/single/list state và không lộ PII vượt mức cần thiết.
- **Given** access session có purpose/expiry, **when** người dùng thử action ngoài scope hoặc sau expiry, **then** backend từ chối và yêu cầu access mới.

#### US-B2 — Đổi lịch mà không mất lịch cũ

Là booker, tôi muốn chọn slot mới nhưng vẫn giữ lịch cũ cho đến khi đổi thành công, để lỗi mạng hoặc hết hold không làm tôi mất cả hai.

**Acceptance criteria**

- **Given** booking `confirmed`, **when** booker bắt đầu reschedule, **then** lịch cũ vẫn confirmed trong lúc slot mới ở `held`.
- **Given** hold mới hết hạn hoặc confirm mới lỗi, **when** flow kết thúc, **then** lịch cũ không đổi và UI nói rõ kết quả.
- **Given** reschedule commit, **when** transaction hoàn tất, **then** booking cũ thành `rescheduled`, booking mới `confirmed`, resource/reminder/invite cũ bị đóng và notification/link mới được tạo idempotently.

#### US-B3 — Hủy lịch có chủ đích

Là booker, tôi muốn hủy lịch sau một bước xác nhận rõ, để showroom giải phóng resource và tôi không nhận reminder sai.

**Acceptance criteria**

- **Given** access có quyền cancel, **when** người dùng chọn hủy, **then** UI hiển thị đúng lịch và hệ quả trước explicit confirmation.
- **Given** cancellation commit, **when** worker chuẩn bị gửi bất kỳ message cũ, **then** worker recheck state và không delivery.
- **Given** cancellation đã thành công, **when** request retry, **then** kết quả idempotent; slot được giải phóng một lần và care/invite đóng.

### 7.5 Epic C — ViVi chăm sóc sau đặt lịch

**Epic hypothesis:** Nếu ViVi giải thích trạng thái, đưa checklist và trả lời có nguồn đúng người sau confirmation, người dùng sẽ chuẩn bị tốt hơn và có khả năng đến hẹn cao hơn.

#### US-C1 — Nhận checklist và hỗ trợ đúng thời điểm

Là người có lịch confirmed, tôi muốn ViVi cho biết cần chuẩn bị gì ngay sau booking và trước buổi hẹn, để tôi không phải chờ cuộc gọi mới biết bước tiếp theo.

**Acceptance criteria**

- **Given** booking vừa chuyển `confirmed`, **when** success/confirmation được tạo, **then** UI/email deterministic hiển thị checklist approved và 2–3 hướng care phù hợp mà không cần người dùng gửi câu “mồi”; requirement này không giả định graph tự chuyển từ booking node sang post-booking node trong cùng lượt.
- **Given** T-24h/T-2h và booking vẫn eligible, **when** notification trigger chạy, **then** content dùng state mới nhất, đúng participant và không chứa inference nhạy cảm.
- **Given** participant đã nhận cùng purpose trong frequency window, opt-out hoặc booking có owner/contact đang xử lý, **when** channel khác chuẩn bị gửi, **then** hệ thống dedupe/suppress theo policy và ghi reason event.
- **Given** booking cancelled/rescheduled/completed/no_show, **when** người dùng mở context cũ, **then** ViVi không tiếp tục care như một lịch sắp tới và đưa đường dẫn đúng.

#### US-C2 — Hỏi về xe bằng nguồn tin cậy

Là người sắp lái thử, tôi muốn hỏi điều nên quan sát trên mẫu xe của mình và nhận câu trả lời có nguồn, để tôi tận dụng buổi lái thử mà không bị tư vấn sai.

**Acceptance criteria**

- **Given** câu hỏi cần fact, **when** ViVi trả lời, **then** retrieval chỉ dùng record approved, còn hiệu lực và phù hợp market/model/trim/year.
- **Given** câu hỏi cần dữ liệu live hoặc knowledge thiếu, **when** ViVi xử lý, **then** ViVi nói rõ chưa xác nhận, không nội suy và đưa contact/next step.
- **Given** profile có preference liên quan, **when** ViVi cá nhân hóa, **then** ViVi dùng preference để chọn góc nhìn nhưng không dùng preference làm bằng chứng fact.
- **Given** một lượt hội thoại, **when** ViVi cần thêm ngữ cảnh, **then** ViVi trả lời phần biết trước và chỉ hỏi tối đa một câu có lý do rõ.

#### US-C3 — Driver invitation có giới hạn

Là driver khác booker, tôi muốn mở link riêng để chuẩn bị, nhưng không muốn link đó làm lộ dữ liệu hoặc cho phép ai đó thay đổi lịch.

**Acceptance criteria**

- **Given** booking confirmed và actor có quyền phát hành, **when** invitation được tạo, **then** server chỉ lưu hash; raw token chỉ truyền qua TLS trong link/resolve/chat, không persist/log/analytics/referrer, và TTL/revocation/booking/driver binding được ghi.
- **Given** confirmation có nhiều channel hoặc retry, **when** notification được render lại, **then** hệ thống reuse một active invitation cho đúng booking/driver thay vì issue rồi revoke link đã gửi; issue chỉ hợp lệ ở `confirmed`/`checked_in` và TTL được cap theo lịch.
- **Given** client nhận fragment invitation, **when** trang mở, **then** client phải gọi server resolve trước khi hiện greeting/care active; state invalid/expired/revoked/rescheduled không được lộ booking hoặc participant.
- **Given** token invalid, expired, revoked, booking cũ rescheduled hoặc không còn active, **when** client resolve, **then** backend từ chối mà không lộ participant/booking detail.
- **Given** driver yêu cầu lookup/change/cancel/update, **when** classifier/tool guard xử lý, **then** hệ thống chặn ở backend và hướng dẫn booker dùng self-service.
- **Given** booking rescheduled và driver vẫn khác booker, **when** lịch mới confirm, **then** link cũ bị revoke và link mới được phát hành theo consent/policy.

#### US-C4 — Cá nhân hóa có quyền kiểm soát

Là người dùng, tôi muốn biết ViVi đang nhớ gì và có thể sửa/xóa, để cá nhân hóa không trở thành theo dõi âm thầm.

**Acceptance criteria**

- **Given** message có durable signal hợp lệ, **when** ViVi đề xuất lưu, **then** validator loại PII/secret, actor/source/certainty/confidence được gắn đúng và persistence có outcome observable.
- **Given** message chỉ chứa dữ liệu tạm thời hoặc về người thứ ba, **when** profile tool chạy, **then** dữ liệu bị chặn hoặc hạ mức third-party theo policy.
- **Given** user yêu cầu xem/sửa/retract/export/delete/opt-out, **when** request được xác thực, **then** hệ thống thực hiện theo SLA/policy và giải thích phần audit buộc phải giữ nếu có.
- **Given** Redis/worker lỗi, **when** profile update không persist, **then** hệ thống ghi metric/alert và không nói với người dùng rằng đã ghi nhớ thành công.

### 7.6 Epic D — DriveOps và human service

**Epic hypothesis:** Nếu Operations nhìn thấy cùng booking state và chỉ actor đúng scope mới được thao tác, showroom sẽ chuẩn bị resource tốt hơn và đóng dữ liệu attendance đầy đủ.

#### US-D1 — Thao tác booking theo role/scope

Là người vận hành showroom, tôi muốn chỉ thấy và thao tác booking thuộc trách nhiệm, để phục vụ nhanh mà vẫn bảo vệ dữ liệu.

**Acceptance criteria**

- **Given** staff, manager hoặc admin, **when** gọi Internal API trực tiếp, **then** backend enforce role/showroom/assignment; việc ẩn button không thay security.
- **Given** booking ngoài scope, **when** actor đoán ID hoặc dùng deep link, **then** API trả lỗi không lộ dữ liệu.
- **Given** mutation hợp lệ, **when** commit, **then** booking event và internal audit ghi actor, state trước/sau, reason và timestamp đã redaction.

#### US-D2 — GPLX và check-in đúng quy trình

Là người có quyền tại showroom, tôi muốn xác minh GPLX bản gốc trước check-in, để chỉ người đủ điều kiện lái xe được tham gia.

**Acceptance criteria**

- **Given** booking confirmed và người lái đến, **when** kiểm GPLX, **then** UI buộc người thao tác xác nhận từng điều kiện thay vì hard-code `true`; rejection cần reason.
- **Given** người lái đến, **when** staff tìm/đối chiếu, **then** portal dùng booking code cùng driver name/contact đã mask theo policy và bản gốc GPLX; invitation token không phải giấy tờ định danh tại showroom.
- **Given** GPLX chưa verified hoặc ngoài cửa sổ thời gian, **when** check-in, **then** backend từ chối và ghi error event phù hợp.
- **Given** check-in/completion/no-show hợp lệ, **when** transition thành công, **then** timestamp/state/audit cập nhật và metric Attendance nhận đúng event.
- **🔵 Open Question (Câu hỏi mở):** Operations phải chốt liệu assigned staff có quyền verify/check-in hay chỉ manager/admin. Policy hiện tại khiến staff gần như read-only.

#### US-D3 — Chuyển sang người thật

Là người dùng có câu hỏi ViVi không giải quyết được, tôi muốn biết ai sẽ tiếp nhận và khi nào, để tôi không rơi vào ngõ cụt.

**Acceptance criteria**

- **Given** knowledge miss, repeated failure hoặc user yêu cầu người thật, **when** handoff được offer, **then** UI nêu channel, operating hours/SLA và dữ liệu nào sẽ được chuyển.
- **Given** user đồng ý, **when** handoff tạo, **then** ticket/context packet chỉ chứa booking state, câu hỏi và signal được phép; không chuyển full transcript/profile mặc định.
- **Given** staff tiếp nhận/đóng, **when** status đổi, **then** user và dashboard nhận event để đo response/resolution.

### 7.7 Non-functional requirements

| ID | Nhóm | Requirement P0/P1 |
|---|---|---|
| NFR-01 | Availability | **🔶 Assumption:** booking transaction service đạt ≥99,5% trong pilot window; catalogue/content có degraded mode độc lập |
| NFR-02 | Performance | **🔶 Assumption:** p95 catalogue/availability ≤2 giây và confirm mutation ≤3 giây, không tính platform cold start; UI luôn có timeout/retry state |
| NFR-03 | AI latency | **🔶 Assumption:** UI phát acknowledgement ≤2 giây và care answer hoàn tất p95 ≤10 giây; timeout không giữ transaction lock |
| NFR-04 | Concurrency | Hold/confirm/reschedule/cancel phải transaction-safe, idempotent và chống dirty write/version conflict |
| NFR-05 | Worker durability | Notification, hold expiry và profile queue phải có retry/backoff, startup recovery, DLQ, idempotency, metric và operator runbook |
| NFR-06 | Authentication | Public profile/invitation issuance/summary không được anonymous; internal API phải dùng scoped session; token không xuất hiện trong log/referrer/analytics |
| NFR-07 | Application security | Chat renderer phải escape/sanitize output; CSP/dependency policy, rate limit, request limits và OWASP-focused tests phải đạt gate |
| NFR-08 | Privacy | Data inventory, purpose, consent, minimization, retention, export/delete/retract và breach workflow phải được Security/Privacy phê duyệt |
| NFR-09 | Accessibility | Critical public/portal journeys phải đạt WCAG 2.2 AA: keyboard, focus, dialog, labels, contrast, screen reader, reduced motion và no announcement storm |
| NFR-10 | Responsive | Public flow phải pass 360/768/1024/1440 px; portal phải giữ customer/time/action context trên mobile hoặc cung cấp alternative view |
| NFR-11 | Compatibility | Hai phiên bản gần nhất của Chrome, Safari, Edge và mobile Safari/Chrome phải pass critical E2E |
| NFR-12 | Content | Mọi claim nhạy cảm phải có owner/review date/expiry; UI phải hiển thị error/retry thay vì bỏ trống im lặng |
| NFR-13 | Observability | Trace/event/log có correlation ID, environment/version và redaction; alert/runbook phải được test trước pilot |
| NFR-14 | Cost | Classifier/care/profile summary phải qua usage budget, per-turn tool cap và cost dashboard; budget failure có graceful fallback |
| NFR-15 | Maintainability | Schema/contract change phải có migration/version, backward compatibility plan và test; production không dựa vào auto-create schema cho breaking change |

### 7.8 Release readiness summary

Bản audit chi tiết nằm ở mục 12.4 để phần thân PRD vẫn đọc được với người non-tech. Tại thời điểm viết, sản phẩm **chưa sẵn sàng pilot** vì còn blocker P0 ở sáu nhóm:

| Nhóm blocker | Outcome bị đe dọa | Gate chịu trách nhiệm |
|---|---|---|
| Booking/identity | OTP chưa được backend enforce, access cross-role, hold expiry và resource/horizon chưa nhất quán | G1 |
| Client/portal quality | XSS, local storage nhạy cảm, degraded mode, session recovery và thiếu automated E2E/a11y | G1 |
| Privacy/profile | Anonymous profile APIs, shared-contact merge, raw context/log và thiếu data rights | G2 nếu capability bật |
| Knowledge/AI | 100% record còn pending, citation chưa enforce, loop/summary chưa có budget đầy đủ | G2 |
| Invitation/notification | Token lifecycle/reschedule/retry, provider truth, consent và over-contact | G2 nếu capability bật |
| Content/operations | Claim hard-code chưa governance và portal capacity có thể dùng default giả | G1/G2 |

Engineering dùng ledger mục 12.4 làm readiness backlog; PO dùng bảng requirement/user story ở phần này để đánh giá outcome và acceptance.

---

## 8. Out of Scope

| Hạng mục ngoài v2 | Lý do | Điều kiện xem xét lại |
|---|---|---|
| Mua xe, đặt cọc, thanh toán, ký hợp đồng | Khác domain pháp lý/giao dịch; không cần để chứng minh booking/care outcome | Có sponsor, payment/legal architecture và discovery riêng |
| Vay/trả góp, bảo hiểm, định giá/thu xe cũ | Cần đối tác và suitability/compliance riêng | PRD độc lập sau khi booking pilot thành công |
| Đàm phán giá hoặc hứa khuyến mãi | Knowledge hiện không bảo đảm dữ liệu live | Có pricing source/API, owner và approval SLA |
| Advisor chọn xe tổng quát trước booking ở P0 | Research ưu tiên hậu booking; code hiện chặn pre-booking vehicle advice | Booking/care đạt outcome; discovery chứng minh nhu cầu và knowledge coverage |
| Full CRM, lead scoring và sales automation | Profile hiện chỉ hỗ trợ care; chưa có consent/process/CRM integration | Sales/Privacy discovery và integration contract riêng |
| Chăm sóc tự động sau `completed` | Chưa có evidence, consent và workflow hậu lái thử | Research sau pilot; chốt post-drive outcome và owner |
| Outbound tự trị dựa trên inference/profile | Rủi ro privacy và over-contact | Policy, consent, throttling, explainability và experiment được duyệt |
| VIP approval/special queue | Không có evidence đủ mạnh; hướng nghiên cứu mới đề nghị bỏ | Operations chứng minh use case/tần suất/rule rõ |
| Upload/lưu ảnh hoặc số GPLX | P0 dùng kiểm bản gốc tại showroom và data minimization | Legal/security/retention review cùng nhu cầu vận hành rõ |
| Driver đổi/hủy/tra cứu booking qua invitation | Link chỉ cấp quyền care, không chứng minh ownership của booking | Không xem xét nếu không có identity model mới được Security duyệt |
| SMS production | Repo chưa có SMS adapter thật | Có provider, consent, delivery receipt và E2E |
| Two-way calendar synchronization | UI hiện chỉ mở Google Calendar template; `.ics` chưa được nối vào hành động | Có OAuth/integration owner và reschedule/cancel sync contract |
| Vector database/semantic RAG như mục tiêu tự thân | Lexical retrieval đủ cho P0 nếu coverage/grounding đạt | Golden eval chứng minh lexical miss là bottleneck |
| CMS đầy đủ cho mọi trang | Không cần để pilot một showroom, nhưng governance claim P0 vẫn bắt buộc | Content volume/frequency chứng minh ROI của CMS |
| Mở rộng thêm trải nghiệm 3D/video | Không giải quyết root problem; bundle hiện đã lớn | Performance budget ổn và research chứng minh contribution |
| Native mobile app | Responsive web đủ để kiểm chứng | Web metrics chứng minh hạn chế nền tảng |

---

## 9. Dependencies, Assumptions and Risks

### 9.1 Dependencies

| Dependency | Cần cho | Owner đề xuất | Điều kiện/SLA cần chốt |
|---|---|---|---|
| Inventory: model/variant/demo vehicle/slot/staff | Availability và confirm | Operations + Backend | Freshness, conflict owner, reconciliation và incident path |
| PostgreSQL + migration discipline | Booking, access, profile, audit, checkpointer | Backend/Platform | Backup/restore, migration/rollback, connection/capacity SLO |
| Redis hoặc durable queue thay thế | Profile update và transient coordination | Backend/Platform | Availability, recovery, DLQ, monitoring và fallback |
| Email provider | OTP, confirmation, invitation và reminder | Platform/Operations | Sender domain, quota, bounce/delivery webhook và outage fallback |
| Zalo Bot | Kênh tùy chọn | Operations/Platform | Linked identity, consent, template approval và rate limit |
| Map/geocoding/tile/CDN | Search showroom và đường đi | Frontend/Platform | Key/domain restriction, CORS, error fallback và privacy |
| LLM provider/classifier model | Routing, care và summary | AI/Platform | Data-processing terms, latency, budget, version/rollback và outage mode |
| Knowledge/content owner | Fact sản phẩm, sạc, warranty và checklist | VinFast/Content Owner | Approval workflow, review cadence, expiry và escalation |
| Security/Privacy/Legal | Identity, profile, invitation và data rights | Security/Privacy | Threat model, consent, retention, access review và incident SLA |
| DriveOps adoption | State closure và Attendance data | Showroom Operations | Role policy, training, daily closure and support |
| Product analytics platform | Funnel/cohort/eval monitoring | Data/Product | Event schema, pseudonymization, consent, dashboard và access |

### 9.2 Assumption register

| ID | Assumption | Mức rủi ro | Cách kiểm chứng | Owner | Hạn |
|---|---|---:|---|---|---|
| AS-01 | Status clarity + care làm tăng attendance | Cao | Baseline và controlled pilot/cohort analysis | PO + Data | Gate G4 |
| AS-02 | UI cấu trúc nhanh hơn chat cho booking | Trung bình | Comparative usability, task time và error | Design Research | Gate G0 |
| AS-03 | Showroom duy trì slot/resource đủ chính xác | Cao | Freshness/conflict audit và dry run | Operations | Gate G1 |
| AS-04 | Người dùng hiểu và chấp nhận profile personalization có control | Cao | Consent comprehension test và opt-out behavior | Research + Privacy | Gate G1 |
| AS-05 | Email là kênh đủ ổn định cho pilot | Cao | Provider E2E, delivery/bounce và OTP completion | Platform | Gate G2 |
| AS-06 | Một pilot giới hạn đủ để kiểm chứng end-to-end | Trung bình | Sample/power review theo traffic thật | PO + Data | Gate G0 |
| AS-07 | Lexical retrieval đủ cho scope knowledge P0 | Trung bình | Golden retrieval/grounding eval | AI Quality | Gate G2 |
| AS-08 | Showroom có khả năng đóng state completed/no-show đúng hạn | Cao | Operational rehearsal và state-closure dashboard | Operations | Gate G2 |

### 9.3 Risk register

| ID | Loại | Rủi ro | Khả năng | Tác động | Mitigation/contingency | Owner | Trigger |
|---|---|---|---:|---:|---|---|---|
| R-01 | Value | Care engagement không làm tăng attendance | Trung bình | Cao | Đo cohort; phân tích checklist/handoff; dừng mở rộng nếu không có signal sau window đủ mẫu | PO/Data | Không uplift hoặc CI bao gồm 0 theo design đã chốt |
| R-02 | Usability | Hold hết hạn trước khi email OTP tới | Cao | Cao | Đo delivery/task time; cấu hình TTL; giữ server truth; recovery không mất dữ liệu | PO/Backend | Hold expiry cao ở review/OTP |
| R-03 | Usability | Agent làm journey dài và gây phiền | Trung bình | Cao | UI-first, one-question rule, opt-out, no profile interview | Design/AI | Time-on-task/negative feedback tăng |
| R-04 | Feasibility | Slot/resource không fresh | Trung bình | Rất cao | Revalidate commit, reconciliation, Ops ownership, safe alternatives | Backend/Ops | Conflict, vehicle unavailable, manual override tăng |
| R-05 | Reliability | Worker/Redis/email mất job hoặc gửi message cũ | Cao | Cao | Durable queue, state recheck, idempotency, DLQ, alert, runbook | Platform | Queue lag/DLQ/delivery mismatch vượt threshold |
| R-06 | AI quality | Retrieval đúng record nhưng model tổng hợp sai | Trung bình | Cao | Approved KB, response validation, golden eval, safe fallback, human review | AI Quality | Grounded correctness regression |
| R-07 | Privacy | Profile lưu/lộ PII hoặc inference sai người | Cao ở code hiện tại | Rất cao | RB-01/03/14, data rights, strict actor boundary, audit | Security/Privacy | PII in log/profile hoặc complaint |
| R-08 | Security | Bearer invitation hoặc public profile route bị lạm dụng | Cao ở code hiện tại | Rất cao | Auth/scope/rate limit/token hygiene/revocation/red team | Security/Backend | Unauthorized read/issuance/resolve |
| R-09 | Viability | Showroom không dùng DriveOps hoặc không đóng trạng thái | Trung bình | Cao | Co-design, training, minimal workflow, daily completeness review | Operations | Closure completeness dưới gate |
| R-10 | Content | Giá/chính sách/warranty cũ | Cao | Cao | Inventory, owner, effective/expiry, default-deny stale claim | Content Owner | Review overdue/incorrect claim |
| R-11 | Adoption | Driver không mở invitation hoặc thấy đó là spam | Trung bình | Trung bình | Consent/copy/sender trust, differentiated content, activation metric | Product/Ops | Delivery cao nhưng open/activation thấp |
| R-12 | Accessibility | Animation/chat/modal ngăn người dùng hoàn tất | Cao ở code hiện tại | Cao | WCAG audit, reduced motion, focus/live-region fixes, assistive-tech E2E | Design/Frontend | Critical a11y failure |
| R-13 | Cost | Tool loop/summary endpoint tạo chi phí ngoài kiểm soát | Cao ở code hiện tại | Trung bình | Budget/cap/auth/cache/circuit breaker/cost alert | AI/Platform | Cost/request hoặc loop count vượt limit |
| R-14 | Delivery | Nhánh `testing` và `main` diverge; feature bị gọi nhầm là production | Cao | Cao | Release manifest, environment banner, feature flags, commit traceability | Tech Lead/PO | Status report không chỉ ra commit/environment |

### 9.4 Nguyên tắc xử lý incident

- Sev-1 gồm unauthorized data access, double-booking diện rộng, agent làm booking mutation sai quyền hoặc gửi hàng loạt notification sai. Nhóm phải tắt capability liên quan bằng kill switch, giữ booking core nếu an toàn, thông báo owner và mở incident review.
- Sev-2 gồm knowledge sai có tác động người dùng, profile attribution sai, queue mất dữ liệu hoặc self-service không dùng được. Nhóm dừng rollout mới và sửa trước khi mở rộng.
- Mỗi incident phải tạo regression case, cập nhật runbook/golden dataset và có owner/date; nhóm không chỉ sửa prompt nếu root cause nằm ở authorization, state hoặc data contract.

---

## 10. Open Questions

Các câu hỏi dưới đây là phần của scope, không phải phụ lục để “hỏi sau”. Nếu đến deadline mà chưa có quyết định, default action trong cột cuối được áp dụng.

| ID | Câu hỏi cần quyết định | Vì sao ảnh hưởng PRD | Owner | Deadline | Default nếu chưa chốt |
|---|---|---|---|---|---|
| OQ-01 | Baseline 8–12 tuần cho funnel, attendance, no-show và follow-up là gì? | Không thể đặt target/ROI | Business Owner + Data | Trước G0 exit | Không cam kết business uplift; chỉ research pilot |
| OQ-02 | Pilot ở showroom nào, traffic/capacity và control/cohort ra sao? | Ảnh hưởng sample, Ops và rollout | PO + Operations | Trước G0 exit | Không mở user traffic thật |
| OQ-03 | Frequency cap, quiet hours, active follow-up owner và opt-out policy theo participant/channel là gì? | Chống spam, trùng contact và complaint | Operations + Privacy + PO | Trước G1 exit | Chỉ gửi confirmation giao dịch; tắt care outbound tùy chọn |
| OQ-04 | SLA sales acknowledgement/human handoff là bao lâu và theo giờ hoạt động nào? | Success copy và user trust | Operations | Trước G1 exit | Chỉ hiển thị contact, không hứa SLA chưa có |
| OQ-05 | Hold TTL phù hợp với p95 email OTP/task time là bao nhiêu? | Conversion và resource lock | PO + Backend + Data | Trước G1 exit | Không pilot đến khi đo dry-run; không mặc định 120 giây là tối ưu |
| OQ-06 | Pilot hỗ trợ OTP/email, Zalo và resend/attempt policy nào? | UX, abuse và deliverability | Security + Platform + PO | Trước G1 exit | Email only; strict rate limit; copy đúng capability |
| OQ-07 | Cơ sở và wording nào cho việc gửi message/invitation tới driver do booker nhập? | Consent và spam/privacy | Privacy/Legal + PO | Trước G1 exit | Không tự gửi driver message/link |
| OQ-08 | Profile lawful basis, retention, export/delete SLA và opt-out UX là gì? | Chặn release profile | Privacy/Legal | Trước G1 exit | Tắt persistent profile; dùng context phiên ngắn hạn |
| OQ-09 | Sales được phép xem signal nào; inference có được dùng trong brief không? | Bias, trust và data scope | Privacy + Sales Ops | Trước G2 exit | Chỉ direct user-stated signal đã cho phép; không inference |
| OQ-10 | Staff có quyền verify GPLX/check-in/complete booking được gán hay chỉ manager/admin? | Bottleneck vận hành/RBAC | Operations + Security | Trước G1 exit | Giữ policy hiện tại; manager/admin thao tác |
| OQ-11 | Ai là Content Owner cuối cùng và review cadence theo sensitivity? | Knowledge đang 100% pending | Business/VinFast representative | Trước G2 exit | Không bật fact Q&A production |
| OQ-12 | Canonical source cho giá sạc, warranty, showroom ranking và vehicle spec là gì? | Tránh hard-code/stale claim | Content Owner + Backend | Trước G2 exit | Ẩn claim không có source/validity |
| OQ-13 | Handoff dùng channel/ticket nào và truyền field nào? | FR-CARE-08 chưa implement | Operations + Privacy | Trước mở rộng P1 | Chỉ hiển thị contact; không tự chuyển transcript |
| OQ-14 | Experiment design nào đủ để quy attribution cho care? | Tránh kết luận sai từ before/after | PO + Data | Trước G3 | Chỉ báo cáo association, không claim causality |
| OQ-15 | Production release đi từ `testing` sang `main` theo manifest/approval nào? | PR #69 chưa ở main | Tech Lead/Release Owner | Trước G2 exit | Feature flag off ngoài testing |
| OQ-16 | Kill switch/feature flag cho care, profile, invitation và channel nằm ở đâu? | Cần rollout/rollback độc lập | Backend/Platform | Trước G2 exit | Không pilot capability thiếu kill switch |
| OQ-17 | Portal có cần MFA/SSO/password recovery trước pilot không? | Internal account security | Security + Operations | Trước G1 exit | Pilot account giới hạn, manually provisioned; no scale |
| OQ-18 | Khi nào mở lại pre-booking advisor và success criterion là gì? | Ngăn scope creep P0 | PO | Sau G4 | Giữ P2/out of scope |
| OQ-19 | Booking hứa model, variant hay đúng demo asset; substitution cần consent nào? | UI hiện làm mất variant/asset dù backend có dữ liệu | PO + Operations + Backend | Trước G1 exit | Không pilot đến khi contract/copy thống nhất |
| OQ-20 | Trường nào dùng để đối chiếu driver tại showroom và được mask ra sao? | Check-in đúng người nhưng vẫn data-minimal | Operations + Privacy | Trước G1 exit | Booking code + tên/contact mask + GPLX bản gốc; không dùng invitation làm identity |
| OQ-21 | Bản PDF research được lưu/version ở kho tài liệu quản trị nào? | Page citation hiện chỉ dựa vào file local, người khác khó kiểm chứng | PO + Research Ops | Trước G0 exit | Chưa sign-off evidence; không commit bản chứa PII nếu chưa redaction/permission |

---

## 11. Delivery and Rollout Plan

### 11.1 Nguyên tắc kế hoạch

Roadmap dưới đây là chuỗi decision gate, không phải lời hứa ngày tháng. Tech Lead chỉ gắn sprint/date sau khi team estimate và stakeholder chốt OQ P0. Mỗi gate yêu cầu evidence có thể xem lại.

### 11.2 Release gates

| Gate | Mục tiêu | Exit criteria | Evidence/approver |
|---|---|---|---|
| G0 — Align & validate | Chốt problem, journey, scope và pilot design | OQ-01/02 đóng; retest tối thiểu 7 target users gồm ≥2 đặt hộ; task/status/manage đạt hoặc có quyết định sửa | PO, Research, Design, Operations |
| G1 — Booking & trust foundation | Booking, identity, authorization, privacy và core UX an toàn | Core booking/client/portal blocker RB-04–06, RB-11–13, RB-19/20/22/23/24 đóng; auth/privacy threat model pass; state/copy/OTP/self-service/consent/a11y critical pass | Engineering, Security/Privacy, Design |
| G2 — Care readiness | Knowledge, care, profile, notification và operations đủ vận hành | RB-01–03, RB-07–10, RB-14, RB-18/21 đóng cho mọi capability được bật; capability không đạt phải server-flagged off và absent khỏi cohort; eval/provider/runbook/alert/state-closure rehearsal đạt | AI Quality, Content, Platform, Operations, PO |
| G3 — Controlled pilot | Đo end-to-end với traffic giới hạn | **🔶 Assumption:** một showroom/cohort nhỏ; monitoring trực; no Sev-1/2 mở; daily review; rollback đã tập | PO + Pilot Owner + Security/Operations |
| G4 — Scale decision | Quyết định mở rộng, iterate hay dừng | Sample đủ theo Data; outcome/guardrail/cost review; incident/failure taxonomy; stakeholder go/no-go | Product Council/Business Owner |

### 11.3 Workstream sequence

| Thứ tự | Workstream | Deliverable chính |
|---:|---|---|
| 1 | Product/Research | Journey prototype, success/manage/care content, retest report, closed OQ log |
| 2 | Booking correctness | Hold reconciler, canonical state/copy, idempotent reschedule/cancel, provider-aware OTP |
| 3 | Security/Privacy | Auth/scope, token hygiene, profile validator/data rights/log redaction, consent |
| 4 | Frontend quality | XSS fix, degraded mode, entry point, accessibility, responsive, automated critical E2E |
| 5 | Care/Knowledge | Approved dataset, strict filter, response grounding, budget/cap, invitation lifecycle |
| 6 | Operations | Role policy, GPLX/check-in, profile brief scope, training/runbook, state closure |
| 7 | Data/Eval | Event SDK/schema, dashboards, golden dataset, judge calibration, alerts |
| 8 | Pilot | Release manifest, feature flags, controlled traffic, daily review, scale decision |

### 11.4 Test and acceptance strategy

| Layer | Bắt buộc trước pilot |
|---|---|
| Unit/contract | Booking state/invariant, participant boundary, knowledge filter, profile validator, token lifecycle, event schema |
| Integration | PostgreSQL transaction/concurrency, Redis retry/recovery, Gmail/Zalo supported flow, LLM budget/fallback |
| API security | Anonymous/role/scope negative cases, ID enumeration, token leakage/replay, rate abuse, prompt/HTML injection |
| End-to-end public | Discover → hold → participants → OTP → confirm → care; lookup/edit/reschedule/cancel; driver invite; degraded mode |
| End-to-end portal | Login/scope, assignment, GPLX, check-in/completion/no-show, profile brief, audit, dataset-scale search |
| Accessibility | Automated scan + keyboard + screen reader + reduced-motion manual pass trên critical journeys |
| Visual/responsive | 360/768/1024/1440, desktop thấp, dark/email clients nếu liên quan |
| AI eval | Routing, grounding, permission, profile, fail-safe và adversarial golden set; calibrated judge + human review |
| Operational rehearsal | Provider outage, Redis restart, worker crash, stale hold, cancel-during-send, rollback/kill switch |

### 11.5 Pilot operations

- Pilot Owner phải có danh sách trực, escalation path, dashboard và quyền tắt từng capability độc lập.
- Operations kiểm tra resource/slot trước mỗi ngày pilot và đóng booking terminal state sau grace period.
- AI Quality review failure sample hằng ngày trong giai đoạn đầu; Content Owner xử lý stale/incorrect claim theo severity.
- Nhóm không bật profile persistence, driver outbound hoặc sales brief nếu consent/privacy gate tương ứng chưa đóng; care có thể chạy ở chế độ session-only/knowledge-only.
- Nhóm không dùng người tham gia research nội bộ như bằng chứng thay cho người có ý định lái thử thật.

### 11.6 Migration, rollout và rollback

1. Engineering phải tạo migration có version cho schema profile/invitation/event thay vì phụ thuộc production auto-create.
2. Release manifest phải ghi commit frontend/backend/portal, prompt/skill/model/knowledge version, environment variables và feature flags.
3. Rollout bật lần lượt: booking fixes → telemetry → care knowledge-only → driver invite → profile persistence → sales brief. Mỗi bước có observation window được SRE/Data chốt.
4. Rollback care/profile/invite không được rollback booking data hoặc làm mất self-service. Kill switch phải đưa UI về checklist/content deterministic.
5. Token/link đã phát hành phải được revoke theo migration/rollback plan; không chỉ ẩn UI.
6. Notification rollback phải giữ idempotency và kiểm state trước send để không phát nội dung của release cũ.

### 11.7 Documentation and training

| Đối tượng | Tài liệu bắt buộc |
|---|---|
| Người dùng | Copy trạng thái, privacy/personalization notice, manage/help content |
| Showroom | Role matrix, assign/GPLX/check-in/no-show, handoff SLA, incident contact |
| Content reviewer | Provenance schema, sensitivity, approve/reject/supersede/expiry workflow |
| Engineering/SRE | State machine, API contracts, queue/provider runbook, feature flags, rollback |
| AI Quality | Golden dataset guide, failure taxonomy, judge calibration và release report |
| Support/Privacy | Data access/export/delete/retract và incident response |

---

## 12. Appendices

### 12.1 Evidence hierarchy và nguồn đã dùng

1. **Hành vi code và test trên nhánh audit** là nguồn cho trạng thái AS-IS; README/comment chỉ dùng để bổ sung, vì một số phần đã cũ.
2. **Usability synthesis trang 118–129 của PDF** là nguồn chính cho hướng sản phẩm sau test; transcript/discovery dùng để hiểu ngữ cảnh.
3. **Ghi chú thô trang 131–136** chỉ là hypothesis/method prompt. Em không coi ví dụ quality threshold hoặc câu “log thay interview” là quyết định.
4. **Git remote refs/merge history** là nguồn cho trạng thái branch. PR #69 có trên `testing`, chưa nằm trong `main` tại thời điểm audit.
5. **Production deployment** chỉ được README mô tả; review này không xác nhận live environment có cùng commit/config/data.

Nguồn chính:

- External research artifact: `Project Vinfast (1).pdf`, 136 trang.
- `README.md`, `ARCHITECTURE.md`, `backend/README.md`, `frontend/README.md`, `internal-portal/README.md`.
- `backend/src/services/booking`, `backend/src/agents`, `backend/src/services/profile`, `backend/src/services/knowledge`, `backend/src/internal_portal`.
- `frontend/src/pages/BookingPage.jsx`, public pages/components và `internal-portal/frontend/src`.
- GitHub PR #69 và các refs `origin/main`, `origin/testing`, `origin/NguyenHoangMinh`.

**Evidence-management gap:** PDF hiện nằm ngoài repo trên máy review, nên tên file/page citation chưa phải một permalink dùng chung. Trước G0 sign-off, Research Ops phải lưu bản đã kiểm tra PII/quyền truy cập vào kho tài liệu có version, owner và checksum/link ổn định; nhóm không tự ý commit transcript thô vào Git.

### 12.2 Evidence-to-requirement traceability

| Evidence | Kết luận PO | Requirements | Metrics/Gate |
|---|---|---|---|
| PDF tr.55–61 | Root pain là bất định sau booking | FR-BK-08, FR-CARE-02, US-A4/C1 | Status comprehension, Attendance |
| PDF tr.57–59, 75 | Booker/driver phải tách | FR-BK-04, FR-CARE-05/06, US-A3/C3 | Driver activation, unauthorized incident |
| PDF tr.108, 113, 122 | OTP phải nằm trong confirm journey | FR-BK-06/07, US-A2 | Confirm task success, OTP funnel |
| PDF tr.109, 115, 125 | Manage entry/đổi/hủy chưa rõ | FR-BK-09/10/11, Epic B | Self-service completion, usability gate |
| PDF tr.113–121 | Agent không nên lặp form; care sau submit | D-01/D-02, FR-CARE-01–04 | Care quality, checklist, Attendance |
| PDF tr.122–127 | Success, ranking, novice summary, navigation và một primary action cần rõ | FR-DIS-03/05/06, FR-BK-08 | Status comprehension, task time |
| PDF tr.128 | Booking truth/care là P0; advisor là P2 | Priority register và Out of Scope | G0–G2 |
| PDF tr.132–136 | Continuous eval/golden dataset/judge calibration | FR-OBS-02, FR-AI-02/03 | AI eval gate; không sao chép threshold ví dụ |
| Booking lifecycle code | Booking bắt đầu `held`, onsite GPLX, transaction invariants | D-03/D-05, FR-BK-01/02/07, FR-OPS-03 | Double-booking, CI, expiry E2E |
| PR #69/post-booking code | Care/profile/knowledge/invite đã có trên testing | Capability baseline, FR-CARE | G2; release manifest |
| Code audit security/privacy | OTP/access role, API auth, pending KB, logging, XSS, consent, storage, queue và token gaps | RB-01–RB-24 | G1/G2 blockers |
| Frontend/portal audit | Hai SPA, self-service/portal có code nhưng thiếu tests/a11y/analytics | FR-DIS/OPS/OBS, NFR-09–11 | G1/G2 |
| Backend test run | Suite đỏ và PR #69 thiếu coverage | RB-11 | Required CI xanh |

### 12.3 Verification snapshot của lần review

| Kiểm tra | Kết quả | Cách diễn giải |
|---|---|---|
| Backend: `./.venv/bin/python -m pytest backend/tests -q` | 347 pass, 7 fail, 5 skip | Nhánh chưa đạt CI gate; 6 failure liên quan contract classifier cũ, 1 failure geocoding/target coordinates |
| Public frontend: `npm run build` | Pass | Bundle build được; có cảnh báo chunk lớn, chưa thay E2E/a11y evidence |
| Internal Portal: `npm run build` | Không chạy được vì local `vite` dependency chưa được cài | Static audit only; không được coi portal build đã pass |
| Git remote refs | `main=6a34b44`, `testing=dfe3ea3`, current commit `1cdf6e2` | Agent hậu booking ở integration/current, không ở main |
| PR #69 diff | 37 file, khoảng 3.396 dòng thêm | Capability lớn nhưng gần như không có dedicated test mới |

### 12.4 Detailed release blocker ledger từ code audit

| ID | Sev | Hiện trạng tại 2026-08-21 | Điều kiện đóng |
|---|---:|---|---|
| RB-01 | P0 | Profile detail/summary, booking profile summary và driver-invitation issuance chưa thể hiện auth/scope; `/driver-chat`, `/test-drive/actions`, stream/profile/invite routes nằm ngoài matcher rate limit hiện tại | Scoped auth + route-complete abuse limits + negative authorization/red-team tests |
| RB-02 | P0 | 25/25 knowledge record là `pending_internal_review`; runtime cho phép pending; tool/fallback chưa bảo đảm source/effective/review date xuất hiện trong answer | Production default-deny; approved/valid records; deterministic response-level grounding/citation tests |
| RB-03 | P0 | Profile signal nhận `Any`, chưa có deterministic sensitive-data validator; raw before/after snapshot có thể vào log | Validator + log redaction + privacy tests + retention policy |
| RB-04 | P0 | `expire_held_bookings()` có code nhưng chưa có runtime scheduler/reconciliation; slot có thể bị giữ quá hạn | Worker/reconciliation + startup recovery + expiry E2E/alert |
| RB-05 | P0 | Chat formatter dùng `dangerouslySetInnerHTML` cho user/agent content mà chưa escape HTML | Sanitizer/escaped renderer + XSS tests |
| RB-06 | P0 | Marketing consent đang pre-checked và lựa chọn không được persist trong confirm payload | Default off + purpose copy + DB/audit + UI/API tests |
| RB-07 | P0 | Post-booking tool loop chưa dùng MAX cap/usage budget như booking loop; profile summary gọi LLM ngoài usage budget | Tool/LLM/time/cost cap cho care và summary + auth/circuit-breaker tests |
| RB-08 | P0 | Redis unavailable có thể làm mất profile update; processing recovery/DLQ operation chưa đầy đủ | Durable fallback/recovery + metric/alert + no false “remembered” copy |
| RB-09 | P0 | Invitation chưa có lifecycle an toàn đầy đủ: client hiện care trước server resolve, issue có thể chạy ngoài eligible state, TTL không cap theo lịch, mỗi channel/retry có thể revoke link trước, và reschedule không reissue | Resolve-before-render, issue một lần/reuse giữa channel, eligible-state check, cap TTL, atomic revoke/reissue + token E2E |
| RB-10 | P0 | Notification channel/runtime contract còn mơ hồ; SMS chưa thật; job đang processing có race với cancel/reschedule | Provider matrix, pre-send state check, E2E thật và truthful UI copy |
| RB-11 | P0 | Backend suite còn 7 fail; PR #69 gần như không có test trực tiếp cho post agent/profile/invite/knowledge auth | Required CI xanh + dedicated test matrix |
| RB-12 | P0 | Public frontend và Internal Portal chưa có automated test runner/E2E/a11y; North Star lại phụ thuộc portal đóng state | Critical public + portal suite chạy trong CI và có evidence |
| RB-13 | P0 | App gate dùng booking health để chặn cả catalogue/content | Capability-level health/degraded mode + chaos test |
| RB-14 | P0 | Driver/email context có thể được đưa vào LLM prompt; prompt-only rule không đủ ngăn exposure | Minimize/redact context trước model + output enforcement + tests |
| RB-15 | P1 | Sales brief có API nhưng chưa có consumer portal; không thể nói staff đang dùng | Scoped UI + consent/purpose + usability/audit evidence |
| RB-16 | P1 | Portal thiếu URL routing/search/pagination/deep link; GPLX UI hard-code boolean; accessibility chưa đạt | Dataset-scale UX, explicit GPLX input và a11y evidence |
| RB-17 | P1 | Streaming route thiếu full guard/profile/participant context và frontend chưa dùng | Tắt khỏi production hoặc đạt parity security/context/rate limit |
| RB-18 | P0 | Content sạc/bảo hành/after-sales có nhiều claim hard-code, chưa có owner/review lifecycle | Content inventory, canonical source, approval/expiry; ẩn mọi claim chưa đạt trước pilot |
| RB-19 | P0 | Frontend verify OTP rồi bỏ access token; confirm tool/service/public action chưa bắt buộc permission `confirm_booking`, và contact mismatch có thể không bị chặn | Token bind booking/booker contact/purpose/role, single-use/replay protection ở mọi confirm endpoint |
| RB-20 | P0 | Driver contact có thể xin purpose `manage` và access ownership lan qua shared contact sang booking khác | Principal/participant-role binding + cross-role/cross-booking/shared-contact negative tests |
| RB-21 | P0 | Profile promotion có thể merge booker/driver theo shared email/phone bất kể `person_id` | Person-aware identity model, ambiguous shared-contact handling và boundary tests |
| RB-22 | P0 | Client lưu address/GPS/messages/participant data trong `sessionStorage` nhưng không giữ authoritative booking/version/expiry; XSS làm rủi ro cao hơn | Data minimization/TTL/clear policy; server rehydrate before restore; no exact GPS/raw transcript unless justified |
| RB-23 | P0 | UI/backend chưa thống nhất model/variant/demo asset và availability horizon; UI có thể làm mất resource detail hoặc hiển thị ngày ngoài API horizon như hết slot | Resource/substitution contract + authoritative horizon/fetch/copy E2E |
| RB-24 | P0 | Portal chưa có global revoked/expired-session recovery và có thể lưu operating-hours mặc định 08:00–18:00 như dữ liệu thật | Safe logout/reauth; unconfigured≠default; capacity propagation/audit tests |

Mọi blocker P0 trong bảng là điều kiện chặn pilot cho capability liên quan. PO chỉ có thể waiver một blocker khi Security/Privacy/Engineering/Operations liên quan ký nhận rủi ro, có workaround, thời hạn và rollback; PO không tự miễn trừ security hoặc privacy gate. Nếu profile hoặc driver invitation không đạt gate, capability đó phải tắt bằng server-side feature flag và không nằm trong pilot cohort; care knowledge-only vẫn phải đạt toàn bộ blocker P0 còn áp dụng.

### 12.5 Glossary

| Thuật ngữ | Nghĩa trong PRD |
|---|---|
| Booker | Người sở hữu thao tác đặt/quản lý booking; có thể khác người lái |
| Driver | Người trực tiếp lái thử; có profile/quyền riêng với booker |
| Held booking | Booking đã chiếm tạm resource nhưng chưa được xác nhận |
| Confirmed booking | Booking đã commit, có mã và đủ điều kiện mở care |
| Care | Hỗ trợ chuẩn bị/đánh giá trước và trong buổi lái thử, không phải CRM hậu bán |
| Driver invitation | Bearer link riêng, có expiry/revocation, chỉ cấp care scope |
| Trusted knowledge | Record có provenance/review state; production chỉ dùng record approved/valid |
| Profile signal | Thông tin bền vững phục vụ cá nhân hóa, có source/certainty/confidence/lifecycle |
| Grounding | Ràng buộc câu trả lời fact vào nguồn approved/live thay vì model memory |
| Golden dataset | Tập case có nhãn/version dùng cho offline regression evaluation |
| LLM judge | Model chấm output; chỉ dùng sau calibration với nhãn người |
| DriveOps | Internal Portal và backend operations cho showroom/network |
| Release gate | Tập điều kiện evidence phải đạt trước khi mở mức rollout tiếp theo |

### 12.6 Self-assessment chẩn đoán

| Mục | Đánh giá trung thực | Hành động tiếp theo |
|---|---|---|
| Phần mạnh nhất | Problem → decision → requirement → metric/gate có traceability; actor và quyền booker/driver được tách rõ | Dùng ma trận này làm checklist khi refinement và UAT |
| Phần yếu nhất | Evidence về business outcome còn yếu: mẫu research nhỏ, chưa đại diện và chưa có production baseline/attribution design | Hoàn tất OQ-01/02, retest tối thiểu 7 target users và lập pilot measurement plan |
| Assumption quan trọng 1 | AS-01: status clarity + care làm tăng attendance | Không claim uplift trước G4; so cohort theo design do Data duyệt |
| Assumption quan trọng 2 | AS-03: showroom duy trì resource/slot đủ chính xác | Dry run inventory, reconciliation và conflict dashboard trước G1 |
| Assumption quan trọng 3 | AS-04: người dùng chấp nhận profile personalization có control | Consent-comprehension test; nếu không đạt thì chạy care session-only |
| Recommended next step | Không bắt đầu thêm feature advisor; trước tiên đóng G0 và blocker OTP/authorization/hold/content | PO tổ chức workshop sign-off với Business, Ops, Security/Privacy, Engineering, Design và Content Owner |
| Readiness hiện tại | **Chưa sẵn sàng pilot hoặc production**; PRD đủ làm baseline refinement nhưng còn open decisions và P0 blockers | Cập nhật v2.1/change log sau G0/G1; không gọi prototype trên `testing` là production-ready |

PRD không bịa baseline, TAM, ngày phát hành, SLA showroom, legal basis hoặc pilot location. Những nội dung này được giữ thành assumption/open question có owner và deadline gate.

### 12.7 Sign-off checklist

- [ ] PO và Business Owner duyệt outcome, North Star, scope và pilot design.
- [ ] Research/Design duyệt journey, copy state, retest và accessibility plan.
- [ ] Engineering duyệt state/invariant, estimate, migration, feature flag và rollback.
- [ ] Security/Privacy/Legal duyệt auth, token, profile, consent, data rights và logging.
- [ ] Content Owner duyệt knowledge/checklist/claim governance.
- [ ] Operations duyệt role, SLA, GPLX, state closure, training và runbook.
- [ ] Data/AI Quality duyệt event schema, dashboard, golden set, threshold và calibration.
- [ ] Release Owner xác nhận required CI xanh và manifest đúng commit/environment.

---

**Kết luận PO:** Nhóm không nên tiếp tục mô tả sản phẩm là “chatbot đặt lịch và tư vấn xe”. Sản phẩm v2 là một hệ thống đặt lịch có trạng thái đáng tin cậy, được nối với lớp chăm sóc hậu booking có nguồn và một lớp vận hành showroom có phân quyền. ViVi chỉ tạo giá trị khi làm người dùng chắc chắn và chuẩn bị tốt hơn mà không làm suy yếu booking truth, quyền riêng tư hoặc quyền kiểm soát của người dùng.
