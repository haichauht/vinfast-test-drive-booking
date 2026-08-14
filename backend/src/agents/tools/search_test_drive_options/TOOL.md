# Search Test Drive Options Tool

## Mô tả
Tìm mẫu xe, phiên bản, showroom và slot khả dụng. Tool không giữ slot.

## Tham số
`vehicle_model` bắt buộc; `vehicle_variant`, `showroom_id`, `showroom_query` (tên/code/địa chỉ), `preferred_date`, `preferred_time` (`HH:MM`) và tọa độ là tùy chọn.

- `showroom_limit` là số showroom tối đa trả về khi tìm theo vị trí/địa chỉ, mặc định `5`. Chỉ truyền khi người dùng yêu cầu một số lượng cụ thể hoặc workflow thật sự cần số lượng khác.
- `slot_limit` là số slot tối đa trả về cho một showroom cụ thể. Mặc định không giới hạn số dòng trong cửa sổ 30 ngày; chỉ truyền khi người dùng yêu cầu một số lượng slot cụ thể hoặc workflow cần giới hạn nhỏ hơn.
- Nếu người dùng không yêu cầu số lượng, bỏ qua hai tham số này để dùng mặc định.
- Dữ liệu slot luôn bị giới hạn trong 30 ngày tiếp theo và được xếp gần giờ mong muốn nhất khi có `preferred_time`.

## Kết quả
Trả stage `showroom_selection` hoặc `slot_selection`, xe đã resolve, showroom/slot và yêu cầu giấy phép.

## Ví dụ
```python
search_test_drive_options.invoke({"vehicle_model": "VF 7", "showroom_id": "showroom_id"})

search_test_drive_options.invoke({"vehicle_model": "VF 7", "address": "Hà Nội", "showroom_limit": 3})
```
