# Search Test Drive Options Tool

## Mô tả
Tìm mẫu xe, phiên bản, showroom và slot khả dụng. Tool không giữ slot.

## Tham số
`vehicle_model` bắt buộc; `vehicle_variant`, `showroom_id`, `showroom_query` (tên/code/địa chỉ), `preferred_date`, `preferred_time` (`HH:MM`), tọa độ và `limit` là tùy chọn. Kết quả slot tối đa 5 và được xếp gần giờ mong muốn nhất.

## Kết quả
Trả stage `showroom_selection` hoặc `slot_selection`, xe đã resolve, showroom/slot và yêu cầu giấy phép.

## Ví dụ
```python
search_test_drive_options.invoke({"vehicle_model": "VF 7", "showroom_id": "showroom_id"})
```
