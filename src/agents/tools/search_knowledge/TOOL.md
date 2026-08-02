# Search Knowledge Tool

## Mô tả (Description)
Tìm kiếm thông tin, tài liệu liên quan trong hệ thống tri thức (Knowledge Base) của dự án. 
Đây là công cụ hữu ích cho kỹ năng RAG (Retrieval-Augmented Generation) khi Agent cần thêm ngữ cảnh để trả lời các câu hỏi về tài liệu hoặc thông tin đặc thù.

## Tham số đầu vào (Arguments)
* `query` (str): Từ khóa hoặc câu hỏi cần tìm kiếm thông tin chi tiết.

## Kết quả trả về (Returns)
* `str`: Chuỗi văn bản chứa kết quả tìm kiếm tương ứng từ Knowledge Base hoặc thông báo lỗi/không tìm thấy.

## Ví dụ sử dụng (Usage Examples)
```python
from src.agents.tools import search_knowledge

result = search_knowledge.invoke({"query": "chính sách nghỉ phép của công ty"})
print(result)
# Output: "Kết quả tìm kiếm cho: chính sách nghỉ phép của công ty"
```
