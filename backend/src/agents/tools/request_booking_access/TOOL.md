# Request Booking Access Tool

## Mô tả
Tạo OTP challenge cho `lookup`, `reschedule`, `cancel`, `update_details` hoặc `update_notifications`.
OTP có hạn 5 phút, tối đa 5 lần thử và có cooldown khi gửi lại (các giá trị có thể cấu hình).

## Tham số
Mã booking, contact đối chiếu, purpose và SMS/email.

## Bảo mật
Response chỉ chứa destination đã mask. OTP thô không được lưu hoặc trả bởi tool.
