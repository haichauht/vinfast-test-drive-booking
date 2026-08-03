# Update Booking Draft Tool

## Mô tả
Patch Booker, Driver, khai báo giấy phép và notification plan của booking `held`.

## Tham số
`booking_id`; các object patch tùy chọn; `expected_version` để chống ghi đè.

## Quy tắc
Không đổi slot và không xác nhận booking. Service từ chối hold hết hạn hoặc version conflict.
