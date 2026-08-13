# DEBUG PLAN

Phạm vi: đọc tĩnh source hiện tại, chưa sửa lỗi. Các vị trí dòng bên dưới theo phiên bản source tại thời điểm lập báo cáo.

## 1. Lỗi/trace nội bộ hiển thị trực tiếp trên giao diện khi chọn slot đã qua

**Kết luận:** Lỗi có thật. Backend đã chặn slot quá khứ đúng nghiệp vụ, nhưng chuỗi lỗi từ tool đang được đưa gần như nguyên văn tới UI. Slot vừa tải có thể trở thành quá khứ do màn hình để lâu; dữ liệu cũ khôi phục từ `sessionStorage` cũng có thể giữ slot không còn hợp lệ.

**Nguyên nhân:** `hold_slot()` phát sinh `BookingError("SLOT_NO_LONGER_AVAILABLE", ...)` khi `start_at <= now`. `ToolNode(handle_tool_errors=True)` biến exception thành nội dung `ToolMessage`; sau đó `booking_skill_node` gán `action_error = str(decoded)`. `OutputGuard` chỉ lọc secret/PII và cắt độ dài, không chuyển exception/trace thành lỗi công khai chuẩn. Frontend `agentAction()` dùng toàn bộ `action_error` làm `ApiError.message`, rồi `confirmSlot()` hiển thị lại cả trong tin nhắn chat lẫn vùng `booking-api-error`. Vì vậy nội dung kỹ thuật có thể xuất hiện trực tiếp và còn bị lặp.

**Vị trí:**

- `backend/src/services/booking/lifecycle.py:13-43` — kiểm tra và phát sinh lỗi slot quá khứ.
- `backend/src/guardrails/tool_guard.py:111-126` — `ToolNode` tự bắt exception.
- `backend/src/agents/nodes/booking_skill_node.py:118-148` — đưa nguyên kết quả lỗi vào `action_error`.
- `backend/src/guardrails/output_guard.py:36-68` — chưa có allow-list/mapping lỗi công khai.
- `frontend/src/api/booking.js:51-58` và `frontend/src/pages/BookingPage.jsx:1302-1330,1888-1889` — chuyển và render nguyên `error.message`.

**Cách sửa đề xuất:** Chuẩn hóa lỗi tool tại backend thành contract chỉ gồm `code`, thông báo thân thiện và `retryable`; không đưa `repr(exception)`, traceback hay nội dung `ToolMessage` ra `ChatResponse`. Mapping theo allow-list, ví dụ `SLOT_NO_LONGER_AVAILABLE` → “Khung giờ này đã qua hoặc không còn khả dụng, vui lòng chọn giờ khác”. `action_error` nên là mã ổn định hoặc object lỗi công khai, không phải chuỗi exception. Frontend map theo `code`, chỉ hiển thị một thông báo, đóng modal, bỏ slot cũ và tải lại danh sách. Có thể lọc lại `start_at > Date.now()` trước khi render/confirm, nhưng backend vẫn phải là lớp kiểm tra cuối.

**Ảnh hưởng luồng khác:** Mapping tập trung sẽ tác động mọi structured action (`search_options`, `update_draft`, `confirm_booking`, OTP), theo hướng không còn lộ chi tiết kỹ thuật. Cần giữ `code/retryable` để các luồng hết hạn hold, trùng slot, xe không sẵn sàng vẫn điều hướng đúng. Refresh danh sách có thêm một request và có thể thay đổi slot đang thấy, nhưng không làm thay đổi dữ liệu booking đã xác nhận.

## 2. Tin nhắn chứa “gần nhất” bị rule frontend chặn, không gửi Agent

**Kết luận:** Lỗi có thật và nằm ở frontend. Khi đã có GPS và danh sách showroom, regex khớp “gần nhất/gan nhat/nearest” sẽ tự chọn phần tử đầu tiên; `sendBookingMessage()` không được gọi. Câu “VinFast ... đã được chọn...” đến từ `chooseShowroom()`, không phải phản hồi của Agent.

**Nguyên nhân:** `handlePrompt()` xử lý ba nhánh cứng trước nhánh gửi chat: chọn showroom gần nhất, tìm showroom có chữ `vinfast`, và coi toàn bộ tin nhắn ở bước chờ địa chỉ là địa chỉ. Nhánh “gần nhất” gọi thẳng `chooseShowroom(nearbyShowrooms[0], true)`. Ngoài ra các regex hủy/đổi lịch sau response vẫn tự đổi state UI, có thể xung đột với intent/tool result của Agent.

**Vị trí:** `frontend/src/pages/BookingPage.jsx:1334-1413`, trọng tâm `1350-1384`; câu mặc định được tạo tại `1273-1289`.

**Cách sửa đề xuất:** Mọi tin nhắn người dùng nhập trong composer luôn gọi `sendBookingMessage(value, context)` để Agent xử lý và quyết định tool call. Truyền đủ GPS, danh sách/ID showroom, stage và lựa chọn hiện tại trong context; áp dụng tool result bằng `applyAgentToolResult()`. Gỡ các regex intent khỏi `handlePrompt()` hoặc chỉ dùng chúng cho gợi ý hiển thị, tuyệt đối không short-circuit request và không tự đổi state nghiệp vụ. Các nút chọn nhanh showroom/slot vẫn được giữ và tiếp tục gọi structured action trực tiếp, vì đây là hành động UI đã xác định rõ, không cần qua LLM và giúp tối ưu token/độ trễ. Bổ sung test: câu bất kỳ nhập trong chat có “gần nhất” phải gọi `/chat` đúng một lần; click nút chọn nhanh phải gọi đúng structured action và không gọi LLM.

**Ảnh hưởng luồng khác:** Tin nhắn tự do về địa chỉ/showroom sẽ phụ thuộc Agent và LLM nên có thể tăng độ trễ, chi phí và độ biến thiên; cần bảo đảm prompt/tool schema xử lý tốt địa chỉ, showroom và GPS. Nút chọn nhanh không bị ảnh hưởng và vẫn là đường đi tiết kiệm token. Luồng hủy/đổi lịch phải chuyển điều hướng state sang dựa trên tool/action trả về để tránh mất hành vi hiện tại.

## 3. Người dùng vẫn gửi thêm tin nhắn khi Agent đang trả lời

**Kết luận:** Lỗi có thật. `agentTyping` chỉ điều khiển animation; form, textarea và nút gửi không bị khóa, còn `handlePrompt()` không có guard chống submit đồng thời.

**Nguyên nhân:** Trong lúc request đang `await`, người dùng có thể submit lại. Nhiều request dùng cùng `conversation_id` có thể hoàn thành lệch thứ tự, làm message/UI stage bị đảo hoặc ghi checkpoint hội thoại cạnh tranh. Chỉ gọi `setAgentTyping(true)` không chặn được lần submit tiếp theo; hai lần Enter rất nhanh còn có thể xảy ra trước khi React render state mới.

**Vị trí:** `frontend/src/pages/BookingPage.jsx:762`, `1334-1413`, và composer tại `1985-1995`. Hạ tầng request đã nhận `signal` ở `frontend/src/api/client.js:52-60`, nhưng `sendBookingMessage/agentRequest` chưa truyền signal từ UI (`frontend/src/api/booking.js:39-62`).

**Cách sửa đề xuất:** Tạo trạng thái `isSending` riêng cho request chat và một `useRef` lock; kiểm tra lock ngay đầu `handlePrompt()`, khóa trước khi gọi API và mở trong `finally`. Đặt `disabled` cho textarea/nút gửi, chặn Enter, thêm `aria-busy` và placeholder phù hợp. `useRef` là cần thiết để chặn hai lần submit rất nhanh trước khi React kịp render state mới. Nên khóa cả các choice có thể làm thay đổi cùng booking state trong thời gian request. Không triển khai nút Dừng hoặc cơ chế hủy request trong phạm vi sửa lỗi này.

**Ảnh hưởng luồng khác:** Khóa gửi sẽ tuần tự hóa hội thoại và tránh race, nhưng người dùng phải chờ request thành công, lỗi hoặc timeout mới gửi lại; vì vậy cần bảo đảm `finally` luôn mở khóa và API có timeout/retry phù hợp. Không nên dùng chung `agentTyping` làm lock vì state này còn được dùng cho delay giả và các thao tác GPS/showroom.

## 4. Chưa giới hạn độ dài tin nhắn gửi cho ViVi

**Kết luận:** Lỗi chỉ đúng ở tầng UI. Backend đã giới hạn `message` từ 1 đến 5.000 ký tự và có test nhận đúng 5.000/từ chối 5.001. Tuy nhiên textarea không có `maxLength`, không có đếm ký tự hay validation trước khi gửi, nên người dùng vẫn có thể nhập và bấm gửi chuỗi dài rồi mới bị server từ chối.

**Nguyên nhân:** `ChatRequest.message` có `max_length=5000`, nhưng composer chỉ bind `value/onChange`. Khi FastAPI trả lỗi Pydantic 422, `apiPost()` giả định `body.detail` là object có `.message`; thực tế validation detail thường là array, nên UI có khả năng chỉ nhận thông báo chung “Yêu cầu không thành công” thay vì biết vượt giới hạn.

**Vị trí:**

- `backend/src/models/schemas.py:6-23` — giới hạn server đã tồn tại.
- `backend/tests/test_api/test_routes_extended.py:5-24` — test biên 1/5.000/5.001 ký tự.
- `frontend/src/pages/BookingPage.jsx:1985-1996` — chưa giới hạn/đếm ký tự.
- `frontend/src/api/client.js:65-72` — chưa parse chuẩn lỗi validation dạng array.

**Cách sửa đề xuất:** Thêm `maxLength`, bộ đếm và kiểm tra trước submit ở frontend với cùng giới hạn 5.000 ký tự của backend. Không hard-code hai giá trị độc lập: coi OpenAPI/schema backend là nguồn contract, sinh hoặc đồng bộ hằng `CHAT_MESSAGE_MAX_LENGTH` cho frontend từ `maxLength` của `ChatRequest.message`; thêm contract test/CI để fail nếu giới hạn FE khác BE. Nếu dự án chưa có bước generate contract, tạm đặt giá trị trong một file contract dùng chung và bắt buộc test hai phía đọc/đối chiếu file đó. Chuẩn hóa handler lỗi 422 để lấy mã/thông báo an toàn, không render raw validation payload.

**Ảnh hưởng luồng khác:** Không ảnh hưởng tool call có message ngắn do hệ thống tạo. Khi thay đổi giới hạn trong tương lai, quy trình generate/contract test sẽ buộc FE và BE cập nhật cùng nhau, tránh conflict hoặc hành vi mỗi tầng một khác. Nếu hạ giới hạn, các yêu cầu tư vấn dài có thể bị chặn; `maxLength` bảo vệ UX ở browser, còn validation server vẫn cần cho client khác hoặc request tự tạo.

## Ghi chú xác minh

- Source và test hiện có xác nhận truy vấn slot chỉ trả `start_at > now` (`backend/src/services/booking/catalog.py:195-211`) và `hold_slot` kiểm tra lại thời gian; vì vậy lỗi số 1 là lỗi công khai hóa lỗi/stale UI, không phải thiếu validation nghiệp vụ phía backend.
- Chưa thay đổi source. Không chạy được pytest trong môi trường hiện tại vì `python.exe` trỏ tới WindowsApps và không khởi động được; các kết luận test ở trên dựa trên việc đọc test/source.
