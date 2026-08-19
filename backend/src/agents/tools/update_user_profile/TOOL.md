# Update User Profile Tool

## Mô tả

Ghi nhận thông tin cá nhân hóa bền vững mà Post-booking Agent nhận ra từ message,
lịch sử hội thoại và profile brief. Tool enqueue Redis và trả ngay; worker merge
vào anonymous/trusted profile mà không gọi LLM khác.

Chỉ gọi khi có signal mới, cần sửa, tăng/giảm độ tin cậy hoặc rút signal cũ.
Không gọi chỉ để lấp đầy mọi section đang trống.

## Tham số

Tool nhận một tham số bắt buộc `signals`: mảng có ít nhất một
`SignalCandidate`. `profile_id`, `conversation_id` và `trace_id` được hệ
thống inject; agent không truyền các giá trị này.

| Field | Bắt buộc | Miền giá trị | Ý nghĩa |
|---|---:|---|---|
| `category` | Có | allow-list bên dưới | Nhóm thông tin |
| `key` | Có | semantic key ổn định | Ví dụ `daily_commute_distance` |
| `value` | Có | string/number/bool/list/object | Giá trị cần lưu |
| `description` | Không | chuỗi ngắn | Câu hiển thị trong profile brief |
| `certainty` | Không | `known`, `likely`, `possible` | Mặc định `possible` |
| `confidence` | Không | số `0..1` | Mặc định `0.5` |
| `source_type` | Không | `explicit_user`, `implicit_user`, `trusted_domain` | Mặc định `implicit_user` |
| `operation` | Không | `add`, `strengthen`, `weaken`, `revise`, `retract` | Mặc định `add` |

## Category allow-list

- `fact`: sự thật user nói rõ hoặc context xác nhận, như số con, xe đang dùng.
- `usage`: cách dùng xe, quãng đường, hành trình, hoàn cảnh gia đình.
- `experience`: kinh nghiệm lái xe hoặc EV có liên quan.
- `interest`: topic quan tâm như charging, ADAS, family space.
- `concern`: điều user lo ngại hoặc muốn kiểm chứng.
- `test_drive_goal`: điều muốn đánh giá trong buổi lái thử.
- `conversation_preference`: cách user muốn nhận hỗ trợ.
- `likely_intent`: mục tiêu lớn được suy ra từ nhiều signal.
- `custom_intent`: intent bền vững chưa phù hợp category trên.

## Quy tắc certainty và source

- User nói trực tiếp: `known`, `explicit_user`, confidence thường `0.85–1.0`.
- Suy luận có nhiều signal hỗ trợ: `likely`, `implicit_user`, thường `0.6–0.84`.
- Giả thuyết cần xác nhận: `possible`, `implicit_user`, thường dưới `0.6`.
- Khi user sửa thông tin dùng `revise`; phủ nhận hoàn toàn dùng `retract`.
- Không biến inference thành known fact.

## Không được lưu

OTP, access token, email/số điện thoại, credential, raw conversation hoặc trạng
thái booking tạm thời. Không lưu dữ liệu chỉ vì profile đang trống.

## Ví dụ

```json
{
  "signals": [
    {
      "category": "usage",
      "key": "daily_commute_distance",
      "value": {"distance_km": 40, "frequency": "daily"},
      "description": "Đi làm khoảng 40 km mỗi ngày.",
      "certainty": "known",
      "confidence": 0.95,
      "source_type": "explicit_user",
      "operation": "add"
    },
    {
      "category": "likely_intent",
      "key": "evaluate_charging_feasibility",
      "value": true,
      "description": "Có khả năng đang đánh giá tính khả thi của việc sạc xe điện.",
      "certainty": "likely",
      "confidence": 0.7,
      "source_type": "implicit_user",
      "operation": "add"
    }
  ]
}
```

## Kết quả

- `queued`: Redis đã nhận job.
- `unavailable`: Redis chưa nhận được job; không khẳng định đã cập nhật.
- `skipped/profile_not_resolved`: chưa resolve được profile.
