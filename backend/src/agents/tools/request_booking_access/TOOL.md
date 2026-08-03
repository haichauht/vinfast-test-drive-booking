# Request Booking Access Tool

## Mô tả
Tạo OTP challenge cho `lookup`, `reschedule`, `cancel`, `update_details` hoặc `update_notifications`.

## Tham số
Mã booking, contact đối chiếu, purpose và SMS/email.

## Bảo mật
Response chỉ chứa destination đã mask. OTP thô không được lưu hoặc trả bởi tool.
