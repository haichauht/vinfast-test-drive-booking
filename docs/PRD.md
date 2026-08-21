# PRD: AI Agent đặt lịch lái thử & tư vấn xe VinFast

Tài liệu yêu cầu sản phẩm cho dự án P-053. Đọc cùng: [Discovery, User Empathy và Concept Spec](docs/User%20Empathy,%20Spec%20and%20PRD.pdf), [sơ đồ kiến trúc](architecture_diagram.md), [tài liệu bàn giao frontend sang backend](../frontend/BACKEND_HANDOFF.md).

---

## 0. Thông tin quản trị tài liệu

| Trường | Nội dung |
|---|---|
| Tên tính năng | AI Agent đặt lịch lái thử & tư vấn xe VinFast (ViVi) |
| Mã dự án | P-053 |
| Mã Epic (Jira) | `P053-EPIC-01` |
| Phiên bản | 1.0 |
| Ngày cập nhật | 13/08/2026 |
| Tác giả | Nguyễn Hoàng Minh, Product Owner nhóm P-053 |
| Trạng thái | Draft, chờ review với mentor và đội kỹ thuật |
| Người phê duyệt | Mentor chương trình AI Thực chiến K3–K4 (VinUni × Vingroup); đại diện nghiệp vụ showroom (chưa chỉ định) |
| Ngôn ngữ sản phẩm | Tiếng Việt (vi-VN) |

### 0.1 Change log

| Ver | Ngày | Người sửa | Nội dung thay đổi |
|---|---|---|---|
| 0.1 | 28/07/2026 | @hoangminh | Tài liệu Discovery v1 viết trước phỏng vấn: giả thuyết bài toán, chân dung phác thảo, luồng nghiệp vụ v1 |
| 0.2 | 01/08/2026 | @hoangminh | Hồ sơ Thấu hiểu người dùng dựng từ 3 cuộc phỏng vấn, kèm Product Concept Spec theo framework 4 lớp |
| 0.3 | 09/08/2026 | Nhóm P-053 | Dựng MVP chạy được: backend FastAPI với LangGraph, frontend React, luồng đặt lịch đầu cuối |
| 0.4 | 11/08/2026 | Nhóm P-053 | Hoàn thiện giao diện: media theo mã xe, 3D viewer, bản đồ showroom, hiệu ứng xác nhận |
| 1.0 | 13/08/2026 | @hoangminh | PRD hoàn chỉnh, hợp nhất Discovery, Empathy, Spec và hiện trạng mã nguồn. Bổ sung F10 Tư vấn chọn xe |

### 0.2 Các bên liên quan

Đây là bài toán B2B2C, nên trước khi bàn bất cứ điều gì khác cần tách rõ ba nhóm người, vì họ không cùng vai trò và không cùng mong muốn.

Người trả tiền là hãng xe hoặc chủ chuỗi showroom VinFast. Họ là Customer nhưng không dùng sản phẩm hằng ngày, nên nhu cầu của họ được phục vụ qua dashboard chứ không qua luồng hội thoại. Người dùng bên ngoài là khách tiềm năng đi lái thử, đây là user chính, phục vụ qua web và Zalo. Người dùng nội bộ là tư vấn viên và quản lý showroom, họ gắn với cơ chế duyệt tay và bàn làm việc HITL.

Điểm cần nhớ: bỏ quên nhân viên showroom thì họ sẽ tự né hệ thống, và mọi công sức thành vô nghĩa. Sản phẩm phải thắng cả ba tầng chứ không riêng chiều khách.

### 0.3 Tài liệu liên quan

Tài liệu Discovery, User Empathy và Concept Spec nằm trong file [`docs/docs/User Empathy, Spec and PRD.pdf`](docs/User%20Empathy,%20Spec%20and%20PRD.pdf) dài 87 trang, trong đó ba bản chép phỏng vấn đầy đủ ở mục "ITVer 1/2/3". Wireframe lo-fi ở [`docs/docs/Wireframe-Lo-fi-P053.html`](docs/Wireframe-Lo-fi-P053.html). Kiến trúc hệ thống ở [`docs/architecture_diagram.md`](architecture_diagram.md). Hướng dẫn chạy local ở [`frontend/RUN_LOCAL.md`](../frontend/RUN_LOCAL.md), còn danh sách việc backend cần nối ở [`frontend/BACKEND_HANDOFF.md`](../frontend/BACKEND_HANDOFF.md).

Hai tài liệu còn thiếu: bản thiết kế hi-fi trên Figma (hiện thiết kế đi thẳng từ wireframe lo-fi sang code) và Technical Design Doc (kiến trúc đang mô tả rải rác trong `ARCHITECTURE.md` và README backend).

---

## 1. Bối cảnh và vấn đề

### 1.1 Background

Ở Việt Nam, mua ô tô là quyết định cân nhắc dài. Từ lúc bắt đầu tìm hiểu đến lúc chốt thường mất hai đến ba tháng, cộng thêm vài tuần chờ giao xe. Trong quãng đó người mua tra cứu chủ yếu qua các sàn xe và Google, giữ liên lạc gần như hoàn toàn qua điện thoại mà phổ biến nhất là Zalo. Buổi lái thử là nơi rất nhiều người mới thực sự ra quyết định.

Quy trình đặt lịch lái thử hiện tại rời rạc và lệ thuộc vào người trực máy. Khách bấm nút "đăng ký lái thử" trên web hoặc nhắn Zalo rồi ngồi chờ nhân viên xác nhận. Họ không nhìn thấy khung giờ nào còn trống, cũng không biết xe demo đúng phiên bản mình muốn có sẵn hay không. Kết quả là trùng lịch, hụt nguồn lực đúng khung giờ, và một phần không nhỏ khách đã hẹn nhưng không xuất hiện.

Về thời điểm, chương trình AI Thực chiến K3–K4 đặt bài toán thay quy trình thủ công bằng một AI Agent hội thoại. Về mặt công nghệ, LangGraph kết hợp LLM đã đủ chín để điều phối một luồng nghiệp vụ nhiều bước có ràng buộc chặt, thay vì chỉ làm chatbot trả lời câu hỏi.

### 1.2 Problem statement

> Những người có nhu cầu mua xe và muốn lái thử VinFast, dù tự đi hay đặt hộ người thân, đang phải đánh đổi thời gian và sự chắc chắn để đặt được một buổi hẹn. Họ không thấy được giờ trống và chiếc xe có thật hay không, phải chờ nhân viên xác nhận trong vô định, và khi tới nơi vẫn có thể hụt xe hoặc bị coi như không có lịch. Hệ quả là ý định mua giảm dần theo từng bước trải nghiệm tồi, tỷ lệ no-show cao, và một phần khách rời sang đối thủ.

Ba câu hỏi "How Might We" định hướng toàn bộ sản phẩm. Làm sao để người dùng thấy ngay giờ và xe có thật, được xác nhận chắc chắn thay vì "đã tiếp nhận"? Làm sao để đổi hoặc hủy dễ như một cú chạm, không phải giải thích với con người? Làm sao để khi đặt hộ, đúng người lái được nhắc và giấy tờ của họ được bảo vệ?

Câu định vị sản phẩm: *biến đặt lái thử từ chờ đợi vô định thành chốt chắc trong vài phút.*

### 1.3 Evidence

Bằng chứng đến từ hai nguồn. Tài liệu này tách bạch rõ hai loại để không trưng số nước ngoài ra như thể đó là sự thật của thị trường trong nước.

#### A. Nghiên cứu định tính: 3 phỏng vấn người dùng Việt

Ba cuộc phỏng vấn 1:1 thực hiện ngày 01/08/2026, mỗi cuộc 22 đến 29 phút, theo lối phỏng vấn hành trình. Nhóm mời người dùng kể lại lần đặt lịch gần nhất theo từng bước kèm suy nghĩ ngay tại thời điểm đó, tránh hỏi giả định, chỉ hỏi chuyện đã thật sự xảy ra.

| Người được phỏng vấn | Tuổi, nghề | Đại diện tình huống | Giai đoạn mua |
|---|---|---|---|
| Lê Bình Nguyên | 22, mới đi làm | Mua xe lần đầu, chưa từng booking bao giờ | Mới xem |
| Nguyễn Anh Duy | 29, account quảng cáo | Người tự đặt, đã no-show thật | Mới xem sang cân nhắc |
| Trần Thảo Vy (chồng là anh Nam lái) | 35, nhân sự | Người đặt hộ, quyết định gia đình | Đang cân nhắc |

Dưới đây là các phát hiện có sức nặng nhất, kèm nguyên văn lời người dùng.

| Mã | Phát hiện | Bằng chứng nguyên văn |
|---|---|---|
| E1 | Bất định là nỗi đau gốc. Giao diện nói một kiểu, hệ thống trả lời một kiểu, nhân viên xác nhận một kiểu nữa | *"Khó chịu nhất là mình không biết cái gì đã chắc."* (anh Duy) |
| E2 | Chọn được giờ cụ thể nhưng chỉ nhận lại "đã tiếp nhận yêu cầu" | *"Nếu chỉ là gửi nhu cầu thì mình thấy không cần hiện chi tiết tới 10 giờ, 10 giờ 30. Còn nếu đã chọn được thì mình mong nó nói luôn là đặt lịch thành công."* (anh Duy) |
| E3 | Ma sát xã hội khi hủy dẫn tới no-show trong im lặng. Đây là phát hiện quan trọng nhất | *"Cái ma sát để im lặng thấp hơn cái ma sát phải giải thích với một người."* (anh Duy) |
| E4 | Ý định rơi dần qua từng bước trải nghiệm tồi, chứ không mất đột ngột | Anh Duy: lúc bấm đặt 70%, tối hôm trước 60%, sáng hôm đó còn 20% rồi bỏ. *"Không phải quên. Mình nhớ rất rõ."* |
| E5 | Người đặt khác người lái nhưng hệ thống không thừa nhận | *"Ảnh đưa tên Lê Quốc Nam thì lễ tân tìm không thấy… Cảm giác đầu tiên của ảnh là mình tới đúng chỗ mà giống như không có lịch."* (chị Vy) |
| E6 | Người đặt bị kẹt làm trung gian bất đắc dĩ | *"Từ đầu tới cuối điện thoại của chị nhận hết, trong khi chị không phải người lái và không có mặt để xử lý."* (chị Vy) |
| E7 | Giấy phép lái xe đi qua kênh cá nhân | *"Chuyển qua một tài khoản Zalo cá nhân thì chị không biết sau đó hình được lưu ở đâu."* (chị Vy) |
| E8 | Nhiều nguồn thông tin lệch giờ nhau | Hệ thống nhắn SMS giờ cũ là 14:00 trong khi nhân viên đã chốt 15:00 qua Zalo. Chồng chị Vy đi theo mốc 14:00 nên tới nơi lệch giờ |
| E9 | Chờ đợi tại showroom | Anh Duy chờ gần 40 phút mà xe chưa về, cuối cùng không được lái. Anh Nam chờ khoảng 50 phút, chỉ được lái chừng 10 phút với xe pin yếu |
| E10 | Bị truy theo sau khi không đến | Anh Duy nhận 4 cuộc gọi và 3 tin nhắn trong một tuần, từ nhiều nhân viên khác nhau, kết quả là *"mình né luôn"* |
| E11 | Bị đẩy chốt khi mới đang tìm hiểu | Ngay trong buổi lái thử, khách liên tục bị hỏi khi nào chốt, có cọc trong tháng không |
| E12 | Nhắc lịch quyết định việc có đi hay không | Anh Nguyên cho biết nếu không ai nhắc, mức chắc chắn đi tụt từ 100% xuống khoảng 60%. *"Nếu có người gọi thì mình cảm giác hôm đó người ta đặt một suất riêng cho mình."* |
| E13 | Zalo là kênh ưu tiên tuyệt đối, cả ba người đều chọn | *"Zalo vừa miễn phí vừa tiện"* (anh Nguyên). Anh Duy nói một tin sau khi đặt, một tin trước 24 giờ và một tin trước 2 giờ là đủ |
| E14 | Khách rời sang đối thủ, đây là hệ quả kinh doanh nặng nhất | Anh Duy hoãn kế hoạch và nghiêng sang Hyundai Creta. Gia đình chị Vy đi thử Mazda CX-5: *"bên đó gọi xác nhận một lần, tới nơi có xe sẵn nên chồng chị có thiện cảm hơn"* |
| E15 | Giá trị cốt lõi là sự chắc chắn và giải đáp, không phải đồ hoạ 3D | Anh Nguyên nói ngoại hình đã xem đủ qua review online rồi, thứ cần tới tận nơi là cảm nhận nội thất và cảm giác ngồi trong xe |
| E16 | Nhu cầu tư vấn được nêu rõ ràng, đây là cơ sở cho F10 | *"Mình nghĩ mình cần một người tư vấn về flow trong đó: cần những thông tin gì, cần những bước gì để có thể booking được một chiếc xe để lái thử."* (anh Nguyên) |
| E17 | Chính khách vạch ra ranh giới của AI | Anh Duy: *"Đặt giờ, chọn xe, nhắc lịch, đổi hủy thì mình dùng trợ lý. Hỏi sâu về pin, vay, bảo hiểm, đổi xe cũ thì mình cần người thật."* Chị Vy nói gần như y hệt |
| E18 | Điều kiện để khách tin là dữ liệu phải thật | *"Nếu trợ lý nói có xe mà tới nơi lại không có thì còn tệ hơn gọi sales, vì lúc đó không biết trách ai."* (anh Duy) |

Về độ tin cậy, đây là mẫu nhỏ với n bằng 3, đủ để phát hiện quy luật định tính nhưng chưa đủ để suy ra con số cho toàn thị trường. Những số như "70% xuống 20%" hay "chờ gần 2 giờ" là do chính người dùng kể lại. Chúng dùng để hiểu cơ chế vì sao họ hành động như vậy, không dùng làm thống kê.

#### B. Nghiên cứu thứ cấp, chỉ dùng để định hướng

| Mã | Phát hiện | Nguồn | Hàm ý |
|---|---|---|---|
| R1 | Khách đến thật cho lịch lái thử đặt online chỉ khoảng 40 đến 50%, nhóm dẫn đầu đạt 70 đến 80% | Demand Local 2026 | Dư địa cải thiện rất lớn |
| R2 | Xác nhận hai chiều tự động kéo bỏ hẹn từ 20–30% xuống còn 3–7% | Demand Local, AutoAlert | Cơ chế nhắc và xác nhận là trụ cột giá trị, không phải tính năng phụ |
| R3 | 55% khách phải chờ khi tới lái thử, tăng từ 41% năm 2024 | CDK Friction 2025 | Khớp trực tiếp với E9 |
| R4 | 40% khách coi khung trống thời gian thực và xác nhận tức thì là cải thiện quan trọng nhất | CDK, AutoAlert | Khớp trực tiếp với E1 và E2 |
| R6 | 78% khách nói chính buổi lái thử mới là thứ chốt họ mua xe | CDK Test Drive Value | Mỗi lịch mất đi là một cơ hội bán lớn trôi đi |
| R8 | Nhắc bởi người thật cho bỏ hẹn 13,6%, nhắc tự động 17,3%, không nhắc 23,1%; chuỗi ba tin tốt hơn một tin | Koalendar | Nhịp ba tin của F4 có cơ sở |
| R9 | Hành trình mua xe ở Việt Nam kéo dài 2 đến 3 tháng, Zalo phổ biến | VietnamNet, Q&Me, Mordor | Khớp E13 |
| R10 | Khách lớn tuổi hoặc ngại công nghệ vẫn thích gọi hotline | Q&Me và suy luận | Đừng thiết kế loại trừ nhóm này |

Cần lưu ý R1 đến R8 là bằng chứng quốc tế, chủ yếu ở thị trường Mỹ. Chúng chỉ dùng để định hướng và ước lượng độ lớn tương đối, không phải số liệu Việt Nam.

### 1.4 Opportunity size

Nhóm chưa có dữ liệu vận hành thật của showroom VinFast nên chưa tính được quy mô chính xác. Dưới đây là khung tính để điền khi có số thật, không phải con số cam kết.

```
Giá trị thu hồi mỗi tháng trên mỗi showroom
  = (Số lịch lái thử mỗi tháng)
  × (Tỷ lệ no-show hiện tại trừ tỷ lệ no-show mục tiêu)
  × (Tỷ lệ chốt mua sau khi lái thử)
  × (Biên lợi nhuận trung bình mỗi xe)
```

Có ba nguồn giá trị, xếp theo mức tin cậy giảm dần. Thứ nhất là giảm no-show, đây là nguồn có bằng chứng mạnh nhất vì cơ chế nhắc kèm xác nhận hai chiều đã chứng minh hiệu quả ở nhiều thị trường (R2, R8). Thứ hai là giảm rời bỏ sang đối thủ; hai trong ba người được phỏng vấn đã thực sự chuyển hướng sang Creta và CX-5 sau trải nghiệm tồi (E14), đây là tổn thất lớn nhất nhưng cũng khó đo nhất. Thứ ba là tiết kiệm thời gian tư vấn viên, vì mỗi lịch hiện tiêu tốn nhiều lượt gọi và nhắn qua lại mà việc tự phục vụ có thể giải phóng.

Việc cần làm là xin quyền truy cập dữ liệu vận hành thật của tối thiểu một showroom để thay khung tính này bằng con số. Đây là một trong hai câu hỏi mở lớn nhất với mentor, ghi ở mục 9.3.

---

## 2. Mục tiêu và chỉ số thành công

### 2.1 Business objectives

Sản phẩm phục vụ năm mục tiêu kinh doanh. Giảm tỷ lệ no-show của lịch lái thử, vì mỗi lịch rơi rụng là một cơ hội bán hàng trôi đi (R6). Loại bỏ hoàn toàn trùng lịch và tình trạng hụt xe demo, đây vừa là ràng buộc cứng của đề bài vừa là thứ khách cảm nhận trực tiếp khi tới nơi. Tăng tỷ lệ hoàn tất đặt lịch ngay tại điểm chạm mà khách đang có ý định cao, bởi một nút đặt lịch không nối vào hệ thống thật sẽ làm rơi đúng nhóm khách này. Giữ khách không rời sang đối thủ trong suốt giai đoạn cân nhắc hai đến ba tháng, đây là tổn thất nặng nhất đã quan sát được. Cuối cùng là giải phóng thời gian tư vấn viên khỏi việc điều phối lịch thủ công, vì sales là user nội bộ và nếu hệ thống không có lợi cho họ thì họ sẽ né.

### 2.2 User goals

Với khách tự đặt, mục tiêu là thấy giờ và xe có thật, chốt chắc trong vài phút mà không phải gọi ai. Với khách đặt hộ, mục tiêu là khai đúng người lái và không phải làm trung gian chuyển tiếp thông tin. Với người lái được đặt hộ, mục tiêu là được nhắc trực tiếp, tự xác nhận và tự lo giấy tờ qua kênh chính thống. Mọi khách đều cần đổi hoặc hủy chỉ bằng một chạm, không phải giải thích với ai và không bị truy theo sau đó. Riêng nhóm đang tìm hiểu cần được giải đáp thắc mắc về xe ngay trong hội thoại mà không bị đẩy chốt.

Phía nội bộ, tư vấn viên cần chỉ nhận những lịch khách đã xác nhận lại để không tốn giờ trống vì khách bỏ hẹn. Quản lý showroom cần kiểm soát được nguồn lực xe demo và nhân sự, và không bao giờ bị trùng lịch.

### 2.3 Non-goals

Phần này là công cụ chống scope creep. Mọi thứ dưới đây đã được cân nhắc và cố ý loại khỏi phạm vi.

| Mã | Không làm | Lý do |
|---|---|---|
| N1 | Quy trình mua, ký hợp đồng, đặt cọc mua xe | Ngoài phạm vi bài toán lái thử |
| N2 | Tính toán trả góp, hồ sơ vay ngân hàng | Cần người thật (E17), ViVi chỉ chuyển tiếp |
| N3 | Định giá và thu mua xe cũ | Như trên |
| N4 | CRM bán hàng đầy đủ | Chỉ đồng bộ lead một nguồn, không thay CRM |
| N5 | Trải nghiệm 3D "xem xe trước khi tới" như một tính năng bán hàng | E15 cho thấy khách đã xem đủ ngoại hình qua review online. 3D viewer hiện có là yếu tố thương hiệu của trang web, không tính là giá trị cốt lõi và không ưu tiên nguồn lực |
| N6 | Đa ngôn ngữ | Người dùng mục tiêu là khách Việt |
| N7 | App mobile riêng | Web responsive kết hợp Zalo là đủ (E13) |
| N8 | Lái thử hai mẫu xe trong cùng một booking | Giữ mô hình một booking chiếm một suất và một xe để không phá ràng buộc chống trùng |
| N9 | ViVi tự thương lượng giá, cam kết ưu đãi hoặc thúc chốt cọc | E11 cho thấy chính hành vi này đẩy khách đi |

### 2.4 Success metrics

Trước khi đọc bảng chỉ số, cần biết một điều quan trọng: hiện chưa có analytics nào được cài đặt trong sản phẩm. Điều này đã được xác nhận trong `BACKEND_HANDOFF.md` mục 1.2 ("Chưa có gì, không sự kiện nào được gửi") và kiểm chứng lại bằng cách rà source. Nhóm cũng chưa có quyền truy cập dữ liệu vận hành thật của showroom. Vì vậy mọi ô baseline dưới đây đều chưa đo được, và việc đầu tiên sau khi phát hành là cài tracking plan ở mục 2.5, chạy hai đến bốn tuần để có baseline thật rồi mới chốt target.

Chỉ số chính:

| Mã | Chỉ số | Định nghĩa | Baseline | Target | Nguồn |
|---|---|---|---|---|---|
| M1 | Tỷ lệ đến (show-rate), đây là North Star | Lịch `checked_in` chia lịch `confirmed` đến hạn | Chưa đo | Từ 70% trở lên sau 3 tháng | `booking_events` |
| M2 | Tỷ lệ hoàn tất đặt lịch | Booking `confirmed` chia số phiên bắt đầu luồng đặt | Chưa đo | Từ 45% trở lên | Analytics và DB |
| M3 | Thời gian từ mở luồng đến khi có mã lịch | Trung vị p50 và p90 | Chưa đo | p50 không quá 3 phút, p90 không quá 6 phút | Analytics |
| M4 | Tỷ lệ trùng lịch | Số ca hai booking cùng một suất | Chưa đo | Bằng 0, đây là ràng buộc cứng | Kiểm tra DB định kỳ |
| M5 | Tỷ lệ tự đổi hoặc hủy | Đổi/hủy qua sản phẩm chia tổng số đổi/hủy | Chưa đo | Từ 60% trở lên | `booking_events` |
| M6 | Tỷ lệ khách biến mất | `no_show` chia tổng của `no_show`, `cancelled` và `checked_in` | Chưa đo | Giảm ít nhất 30% tương đối | `booking_events` |
| M7 | Tỷ lệ đúng xe khi tới | Check-in với đúng mẫu và đúng phiên bản đã giữ | Chưa đo | Từ 95% trở lên | Check-in log |
| M8 | Tỷ lệ hội thoại tư vấn dẫn tới đặt lịch, phục vụ F10 | Phiên có ít nhất một lượt tư vấn rồi tạo booking | Chưa đo | Từ 25% trở lên | Analytics và DB |

Guardrail metrics là các chỉ số bảo vệ, ngăn việc tối ưu một số làm hỏng số khác. Nếu bất kỳ guardrail nào vượt ngưỡng đỏ, phải dừng và xem lại kể cả khi chỉ số chính đang đẹp.

| Mã | Guardrail | Bảo vệ điều gì | Ngưỡng đỏ |
|---|---|---|---|
| G1 | Số tin nhắc trung bình trên mỗi booking | Chống việc kéo M1 lên bằng cách spam khách | Trên 4 tin |
| G2 | Tỷ lệ khách tắt nhận thông báo | Đo mức phiền thật sự | Trên 5% |
| G3 | Tỷ lệ liên hệ trùng lặp, tức nhiều nhân viên cùng gọi một booking | Hành vi đã đẩy khách đi ở E10 | Bất kỳ ca nào cũng không chấp nhận |
| G4 | Chi phí nhắc trên mỗi booking | Ràng buộc chi phí nêu thẳng trong đề bài | Vượt ngân sách chốt với vận hành |
| G5 | Tỷ lệ hủy trong vòng 2 giờ trước hẹn | Kiểm tra xem "hủy một chạm" có làm hỏng lịch sales không | Trên 15% |
| G6 | Tỷ lệ trả lời sai hoặc bịa của ViVi, phục vụ F10 | Chống ảo giác LLM về thông số, giá, chính sách | Trên 2% trên bộ eval |
| G7 | p95 thời gian phản hồi API đặt lịch | Trải nghiệm "tức thì" là lời hứa lõi | Trên 1,5 giây |
| G8 | Tỷ lệ rò rỉ PII hoặc GPLX vào log và prompt | Ràng buộc bảo mật | Bất kỳ ca nào cũng không chấp nhận |

### 2.5 Tracking plan

Đây là danh sách sự kiện tối thiểu cần log để đo được các chỉ số trên. Hiện chưa cài sự kiện nào, nên đây là yêu cầu P0 của giai đoạn sau phát hành.

| Sự kiện | Khi nào bắn | Thuộc tính bắt buộc | Phục vụ chỉ số |
|---|---|---|---|
| `booking_flow_started` | Mở luồng đặt lịch | `entry_point` (home, car_detail, zalo, advisory), `vehicle_id` nếu có | M2, M3 |
| `recipient_selected` | Chọn tự lái hoặc đặt hộ | `recipient_type` | Tần suất đặt hộ |
| `vehicle_selected` | Chốt mẫu xe | `vehicle_id`, `variant_id`, `source` (tự chọn hoặc do tư vấn) | M8 |
| `address_submitted` | Nhập địa chỉ | `resolved`, `confidence` | Chất lượng geocoding |
| `showroom_selected` | Chọn showroom | `showroom_id`, `distance_km`, `rank` | |
| `slots_viewed` | Hiện lịch trống | `available_count`, `is_empty` | M2 |
| `alternatives_shown` | Hết chỗ nên hiện phương án | `alternative_count`, `reason` | Hiệu quả F6 |
| `hold_created`, `hold_failed` | Giữ chỗ | `slot_id`, `error_code` nếu có | M2, M4 |
| `hold_expired` | Hết hạn giữ | `remaining_stage` | Kiểm tra hold TTL có hợp lý không |
| `booking_confirmed` | Sinh mã lịch | `booking_code`, `duration_ms` tính từ `booking_flow_started` | M1, M2, M3 |
| `reminder_sent` | Mỗi lần gửi tin nhắc | `type` (confirm, 24h, 2h), `channel`, `recipient_role` | G1, G4 |
| `reminder_action_clicked` | Bấm nút trong tin nhắc | `action` (confirm, reschedule, cancel) | M5, hiệu quả F4 |
| `booking_rescheduled`, `booking_cancelled` | Đổi hoặc hủy | `initiator`, `hours_before` | M5, G5 |
| `checked_in` | Nhân viên check-in | `matched_by` (code, driver, booker), `vehicle_matched` | M1, M7 |
| `no_show_marked` | Đánh dấu vắng | | M6 |
| `advisory_turn` | Mỗi lượt ViVi tư vấn | `intent`, `has_citation`, `kb_hit` | M8, G6 |
| `advisory_handoff` | Chuyển người thật | `reason` (loan, insurance, tradein, unknown, user_request) | F10, tải HITL |
| `notification_opt_out` | Khách tắt nhận tin | `channel` | G2 |

Nguyên tắc log: tuyệt đối không đưa số điện thoại, email, số giấy phép lái xe hoặc ảnh giấy tờ vào sự kiện analytics hay prompt log. Backend đã có sẵn cơ chế thay bằng `[redacted]` cho PII trong `ai_agent.log`, và tracking plan phải theo cùng chuẩn đó (xem G8).

---

## 3. Người dùng và tình huống sử dụng

### 3.1 Personas

**P1, khách tự đặt.** Đây là chân dung lõi, đại diện là anh Duy 29 tuổi và anh Nguyên 22 tuổi. Họ tự tìm hiểu, tự đặt và tự lái, làm mọi thứ trên điện thoại, bận rộn và đặc biệt ghét cảnh đặt xong phải ngồi chờ xác nhận. Họ đang ở giai đoạn mới xem hoặc đang cân nhắc, nên mức chắc chắn sẽ đi thường chỉ khoảng 60 đến 70% và con số đó rơi dần theo từng bước trải nghiệm tồi. Điều họ cần là thấy slot và xe có thật, được xác nhận tức thì, tự đổi hoặc hủy mà không phải giải thích. Thứ họ sợ nhất là tới nơi mà không có lịch hoặc không đúng xe. Họ bỏ đi khi hệ thống xác nhận sai xe sai giờ, khi nhiều nhân viên cùng gọi, hoặc khi đã bấm hủy rồi mà vẫn bị gọi liên tục.

**P2, người đặt hộ.** Đại diện là chị Vy 35 tuổi, đặt cho chồng là anh Nam, người thực sự cầm lái. Nhóm này đặt lịch cho chồng, bố mẹ hoặc sếp, nghĩa là người đặt và người lái là hai người khác nhau. Đây chính là chân dung mà một hệ thống chỉ có một ô "thông tin khách hàng" không bao giờ phục vụ nổi. Họ cần khai riêng người lái, cần người lái được nhắc trực tiếp và tự lo giấy tờ, còn mình chỉ nhận bản sao để theo dõi. Nỗi đau đặc thù của họ là bị kẹt làm trung gian chuyển tiếp mọi câu hỏi, và ngại phải khai giấy tờ hộ người khác. Chính chị Vy nêu rủi ro riêng của nhóm này: tách vai trò mà bảo mật không tốt thì lại thành rủi ro lớn hơn.

**P3, người ngại công nghệ.** Đại diện là bác Hùng 58 tuổi. Đây là chân dung suy luận, chưa phỏng vấn. Nhóm này quen gọi hotline hoặc nhờ con cái, nên cần một lối thoát về người thật và không được ép hoàn toàn vào chatbot. Cần nói rõ: mọi yêu cầu phục vụ P3 trong PRD này đứng trên suy luận chứ không phải bằng chứng, và đã được ghi thành giả định A4 ở mục 9.1.

**P4, tư vấn viên.** Đại diện là "Linh", cũng chưa phỏng vấn. Điều họ sợ nhất là khách hẹn rồi không đến, vì việc đó lấy mất thời gian và hoa hồng. Họ muốn nhận khách chất lượng, lịch không vỡ, và rất cảnh giác nếu AI nhồi cho mình những lịch ảo.

**P5, quản lý showroom.** Đại diện là "Tuấn", chưa phỏng vấn. Họ lo tối ưu xe demo và nhân sự, muốn tự tay duyệt các khung VIP hoặc đặc biệt (đây chính là điểm HITL), và sợ trùng lịch hơn cả sợ trống lịch.

**P6, giám đốc kinh doanh của hãng.** Đây là Customer chứ không phải User. Họ nhìn vào tỷ lệ đặt, đến, chốt và chi phí vận hành nhưng không đụng tới ứng dụng mỗi ngày, nên nhu cầu của họ được phục vụ qua dashboard chứ không qua luồng hội thoại.

### 3.2 Jobs-to-be-Done

| Mã | JTBD | Persona |
|---|---|---|
| J1 | Khi đang cân nhắc mua xe, tôi muốn ngồi thử và lái thật chiếc xe mình nhắm để biết nó có hợp không, mà không mất cả buổi | P1, P2 |
| J2 | Khi tìm được xe ưng, tôi muốn chốt một buổi hẹn chắc chắn ngay lúc đang có hứng, để không phải quay lại việc này lần nữa | P1 |
| J3 | Khi lịch cá nhân thay đổi, tôi muốn đổi hoặc rút lui mà không phải mặt đối mặt với ai | P1, P2 |
| J4 | Khi đặt hộ người thân, tôi muốn giao lại trách nhiệm đúng cho người đi, để mình không phải theo dõi hộ | P2 |
| J5 | Khi chưa biết chọn xe nào, tôi muốn được tư vấn đúng nhu cầu mà không bị bán hàng | P1, P2 |
| J6 | Là tư vấn viên, tôi muốn thời gian của mình chỉ dành cho khách thật sự sẽ đến | P4 |
| J7 | Là quản lý, tôi muốn xe demo và nhân sự không bao giờ bị đặt chồng | P5 |

### 3.3 User journey

**Hành trình hiện tại (AS-IS).** Điều đáng chú ý nhất là đường cảm xúc: nó khởi đầu tích cực rồi tụt dần và chạm đáy ở hai khoảnh khắc sự thật.

| Giai đoạn | Khách làm gì | Cảm xúc | Điểm đau |
|---|---|---|---|
| Tìm hiểu | Xem review online, sàn xe, Google | Hào hứng | |
| Đặt lịch trên web | Chọn showroom, ngày, giờ, mẫu xe | Chuyển từ trung tính sang lo | Khoảnh khắc sự thật thứ nhất: chọn được 10 giờ rõ ràng mà sao lại báo "đã tiếp nhận"? |
| Chờ xác nhận | Chờ 45 phút rồi gần 2 tiếng | Bất an | Không biết chờ bao lâu, trong lúc chờ thì đi xem xe hãng khác |
| Sales gọi lại | Bị hỏi lại những thứ đã điền, bị đổi giờ, bị đẩy chốt cọc | Khó chịu | Xe chỉ được "ưu tiên" chứ không chắc chắn |
| Trước ngày hẹn | Nhận tin nhắc lệch giờ giữa các kênh | Rối | Hai vợ chồng hiểu hai giờ khác nhau |
| Tới showroom | Lễ tân tra tên người lái không thấy, chờ 25 đến 50 phút | Chạm đáy | Khoảnh khắc sự thật thứ hai: tới đúng chỗ mà giống như không có lịch |
| Lái thử | Khoảng 10 phút, sai phiên bản, pin yếu | Thất vọng | Không kiểm tra được thứ mình cần |
| Sau đó | Bị gọi truy theo 4 lần trong tuần | Né tránh | Chuyển sang Creta hoặc CX-5 |

Có một nhánh khác là nhánh no-show, đúng như ca của anh Duy. Ý định tụt từ 70% xuống 60% rồi còn 20%, email xác nhận không có nút hủy, và anh ngại nhắn cho sales, nên anh im lặng biến mất.

**Hành trình mong muốn (TO-BE).**

| Giai đoạn | Khách làm gì | Sản phẩm làm gì | Gỡ điểm đau nào |
|---|---|---|---|
| Tìm hiểu | Xem xe trên web, hỏi ViVi về thông số và tầm hoạt động | F10 trả lời có dẫn nguồn, gợi ý mẫu hợp nhu cầu | E16, J5 |
| Bắt đầu đặt | Bấm "Đặt lịch lái thử" ngay tại trang xe | F1 hỏi ngay "đặt cho mình hay người khác lái?" | E5 |
| Chọn nơi và giờ | Nhập địa chỉ, chọn showroom, chọn khung giờ | F2 chỉ hiện slot gắn xe thật đúng phiên bản; F6 báo hết chỗ ngay kèm 2 đến 3 phương án | E1, E2, E18 |
| Giữ chỗ | Điền thông tin trong lúc chỗ đang được giữ | F2 dùng khóa giao dịch chống trùng, hiện đếm ngược thời hạn giữ | Trùng lịch |
| Xác nhận | Nhận mã lịch và thẻ xác nhận | F4 nói "đã xác nhận" chứ không phải "đã tiếp nhận" | E2 |
| Người lái | Nếu là đặt hộ, người lái nhận link riêng để tự xác nhận và nhập giấy tờ | F3 | E5, E6, E7 |
| Trước hẹn | Nhận nhắc qua Zalo với đúng giờ, đúng xe, kèm ba nút | F4 lấy từ một nguồn sự thật, nhịp ba tin | E8, E12, R2, R8 |
| Đổi ý | Bấm Hủy là xong | F5 giải phóng chỗ và dừng mọi follow | E3, E10 |
| Tới nơi | Đọc mã lịch hoặc tên người lái là ra ngay | F7 tra được bằng cả hai danh tính | E5 |
| Lái thử | Đúng xe, đúng phiên bản, pin đủ | F2 ràng buộc theo pin và tồn kho | E9 |
| Hỏi sâu | Vay, bảo hiểm, xe cũ thì chuyển tư vấn viên giữ nguyên ngữ cảnh | F8 | E17 |

---

## 4. Phạm vi và yêu cầu chức năng

### 4.1 Bản đồ tính năng và trạng thái hiện tại

| Mã | Tính năng chính | Ưu tiên | Trạng thái | Giải nỗi đau |
|---|---|---|---|---|
| F1 | Trợ lý hội thoại đặt lịch (ViVi) | P0 | Đã build | Không biết quy trình, ngại nhắn hoặc gọi sales |
| F2 | Đặt theo suất và xe có thật, chống trùng | P0 | Đã build | E1, E2, E18, trùng lịch |
| F3 | Tách vai người đặt với người lái, kèm GPLX | P0 | Một phần | E5, E6, E7 |
| F4 | Xác nhận tức thì và nhắc đồng bộ | P0 | Một phần | E2, E8, E12 |
| F5 | Tự đổi hoặc hủy một chạm | P0 | Đã build | E3, E10 |
| F6 | Gợi ý khung thay thế khi hết chỗ | P0 | Đã build | Chờ vô định, dời tuần sau làm tụt ý định |
| F7 | Check-in tại showroom | P1 | Một phần | E5, E9 |
| F8 | Chuyển người thật (HITL) và duyệt khung VIP | P1 | Chưa build | E17, kiểm soát nguồn lực |
| F9 | Dashboard vận hành và bảo mật nền | P1 | Một phần | Không đo lường được |
| F10 | Tư vấn chọn xe và giải đáp, tính năng mới | P0 | Chưa build | E15, E16, E17, J5 |

Về những gì đã có thật trong mã nguồn: cơ chế giữ chỗ nguyên tử với khóa giao dịch chống trùng đã chạy trong `lifecycle.py`; hệ thống kiểm tra pin xe demo và kiểm tra chồng lịch trước khi cho giữ chỗ; vòng đời booking đầy đủ từ `held` sang `confirmed`, `checked_in`, `completed` cùng các nhánh `expired`, `cancelled`, `rescheduled`, `no_show`; bảng `booking_driver_details` tách hồ sơ người lái kèm trạng thái kiểm tra giấy phép; cơ chế OTP truy cập lịch qua Zalo Bot với thời hạn 60 giây, tối đa 2 lần thử và chờ 60 giây giữa hai lần gửi; lịch nhắc gồm ba tin là xác nhận sau khi đặt, nhắc trước 24 giờ và nhắc trước 2 giờ, gửi được qua Zalo, SMS và email; đổi lịch và hủy lịch idempotent; dashboard đọc dữ liệu vận hành; guardrails chặn PII vào log và chặn chủ đề nhạy cảm.

Về những gì còn thiếu: cơ chế duyệt khung VIP và hàng chờ HITL hoàn toàn không tồn tại trong code; chưa có bàn làm việc cho tư vấn viên; knowledge base cho tư vấn chưa có, vì hàm `search_knowledge` hiện chỉ trả về chuỗi cố định chứ không truy vấn gì; chưa có link riêng để người lái tự xác nhận và tự nhập giấy tờ; chưa có analytics nên không sự kiện nào được gửi; draft đặt lịch mới chỉ lưu trong `sessionStorage` nên đổi máy là mất; tám nghiệp vụ production vẫn đang đi nhờ endpoint tên `/api/v1/demo/action`; và chưa có dịch vụ geocoding để chuẩn hoá địa chỉ.

### 4.2 Business rules

Mã quy tắc giữ nguyên từ Concept Spec để truy vết được. QA dùng danh sách này làm danh mục kiểm thử.

**Vòng đời booking:**

| Mã | Quy tắc | Trạng thái |
|---|---|---|
| R-B1 | Booking vừa tạo ở trạng thái Nháp, chưa chiếm chỗ nào | Đã có |
| R-B2 | Không hai booking cùng giữ một suất tại một thời điểm | Đã có |
| R-B3 | Trạng thái "Đã giữ chỗ" có thời hạn, hết hạn thì tự giải phóng | Đã có, hiện cố định 120 giây, xem OQ-2 |
| R-B4 | Chỉ booking đã xác nhận mới có mã lịch và được nhắc | Đã có |
| R-B5 | Hủy, hết hạn giữ và no-show đều giải phóng suất | Đã có |
| R-B6 | Mọi thay đổi giờ hoặc xe phải phản chiếu về một nguồn sự thật duy nhất, mọi kênh nhắc đọc cùng nguồn | Đã có |

**Người đặt, người lái và giấy phép lái xe:**

| Mã | Quy tắc | Trạng thái |
|---|---|---|
| R-K1 | Mỗi booking có đúng một người đặt | Đã có |
| R-K2 | Nếu đặt hộ, người đặt không mặc nhiên là người lái | Đã có |
| R-K3 | Người đặt không xem được GPLX của người lái | Một phần, cần kiểm thử |
| R-K4 | Người đặt được quyền đổi hoặc hủy booking mình tạo | Đã có |
| R-D1 | Mỗi booking có đúng một người lái, nếu trùng người đặt thì dùng chung hồ sơ | Đã có |
| R-D2 | Nếu khác người đặt thì gửi link riêng để người lái tự xác nhận và tự nhập giấy tờ | Chưa có |
| R-D3 | Chỉ nhắc người lái sau khi họ đồng ý nhận tin, không spam người chưa đồng ý | Một phần |
| R-D4 | Check-in phải tra được booking bằng chính danh tính người lái, không chỉ bằng người đặt | Một phần |
| R-G1 | Không thu GPLX ở bước gửi yêu cầu, chỉ thu sau khi booking đã xác nhận | Đã có theo thiết kế |
| R-G2 | GPLX chỉ đi qua kênh chính thống, hiển thị rõ mục đích và thời hạn xóa, không qua tài khoản cá nhân của sales | Một phần |
| R-G3 | Người đặt không xem được GPLX của người lái | Một phần |
| R-G4 | Luôn có lựa chọn mang bản gốc tới đối chiếu thay cho upload | Chưa có |

**Suất và xe:**

| Mã | Quy tắc | Trạng thái |
|---|---|---|
| R-S1 | Một suất chỉ phục vụ một booking, khóa giao dịch quyết định ai giữ trước khi có tranh chấp | Đã có |
| R-S2 | Trạng thái giữ có thời hạn, hết hạn thì tự về trống | Đã có |
| R-S3 | Suất phải gắn xe đúng phiên bản khách chọn. Còn chỗ với sales mà không có xe đúng bản thì không phải là suất hợp lệ | Đã có |
| R-S4 | Khi hết suất cho khung mong muốn thì kích hoạt phương án thay thế | Đã có |
| R-X1 | Chỉ xe ở trạng thái sẵn sàng mới được gắn vào suất mở bán | Đã có |
| R-X2 | Một xe không phục vụ hai booking chồng giờ | Đã có |
| R-X3 | Pin dưới ngưỡng thì không mở suất mới cho xe đó, tránh cảnh chạy một vòng ngắn vì pin yếu | Đã có |

**Nhắc lịch, phương án thay thế và HITL:**

| Mã | Quy tắc | Trạng thái |
|---|---|---|
| R-N1 | Nội dung nhắc phải cụ thể: giờ, địa điểm, đúng mẫu xe, câu "đã giữ chỗ", kèm nút Xác nhận, Đổi, Hủy. Không nhắc chung chung | Một phần |
| R-N2 | Nhịp mặc định gồm một tin sau khi đặt, một tin trước 24 giờ và một tin trước 2 giờ. Gọi điện chỉ khi khách chọn cần tư vấn hoặc khi có thay đổi quan trọng | Đã có |
| R-N3 | Không để nhiều sales cùng nhắn hoặc gọi một booking | Chưa có |
| R-N4 | Khi booking bị hủy thì dừng mọi nhắc và mọi follow, không truy theo | Một phần |
| R-A1 | Chỉ đề xuất phương án có suất và xe thật, không đề xuất chỗ trống ảo | Đã có |
| R-A2 | Báo hết chỗ ngay tại bước chọn, không cho chọn rồi hôm sau mới báo | Đã có |
| R-A3 | Khách tự chọn trên màn hình, không bắt chờ sales gọi hỏi qua lại | Đã có |
| R-H1 | Khi chuyển người thật, AI giữ nguyên booking và hồ sơ, không bắt khai lại | Chưa có |
| R-H2 | Booking khung VIP phải qua duyệt trước khi sang trạng thái đã xác nhận | Chưa có |
| R-H3 | Từ chối duyệt thì booking về trạng thái đã hủy kèm lý do, và suất được giải phóng | Chưa có |
| R-H4 | Chỉ quản lý mới được duyệt khung VIP | Chưa có |
| R-O2 | Lead đồng bộ một nguồn, không chia số cho nhiều sales | Chưa có |

### 4.3 User stories và acceptance criteria

Định dạng: là [vai trò], tôi muốn [hành động], để [giá trị]. Acceptance criteria viết theo Given/When/Then để QA chuyển thẳng thành test case.

---

#### US-01. Slot và xe có thật, xác nhận ngay (P0, đã build)

Là người muốn lái thử, tôi muốn thấy giờ và xe còn thật và được xác nhận ngay, để chắc chắn buổi hẹn sẽ diễn ra.

Bằng chứng E1, E2, E18. Quy tắc R-S1, R-S3, R-B4.

**AC-01.1.** Given còn suất VF 6 Plus lúc 10:00 thứ Bảy tại showroom X, When tôi chọn khung đó, Then hệ thống giữ chỗ và hiển thị "Đã xác nhận, 10:00 T7, VF 6 Plus, showroom X" kèm mã lịch.

**AC-01.2.** Given khung tôi muốn đã hết chỗ, When tôi chọn, Then hệ thống hiện ngay 2 đến 3 phương án thay thế gắn xe thật, không bắt chờ sales gọi lại.

**AC-01.3.** Given một suất có xe demo với pin dưới ngưỡng phục vụ, When hệ thống dựng danh sách khung giờ, Then suất đó không được hiển thị là khả dụng.

**AC-01.4.** Given tôi đã chọn phiên bản Plus, When hệ thống hiện khung giờ, Then mọi khung hiện ra đều gắn xe đúng phiên bản Plus, không hiện khung chỉ còn chỗ với sales.

**AC-01.5.** Given màn hình cho tôi chọn giờ cụ thể, When tôi bấm xác nhận, Then hệ thống tuyệt đối không được trả về thông điệp dạng "đã tiếp nhận yêu cầu, sẽ có nhân viên liên hệ".

---

#### US-02. Không double-booking (P0, đã build)

Là hệ thống, khi hai khách tranh một suất, chỉ một người được giữ.

Quy tắc R-B2, R-S1. Phục vụ M4.

**AC-02.1.** Given suất S đang trống, When hai khách bấm giữ gần như đồng thời, Then đúng một người giữ được nhờ khóa giao dịch, còn người kia lập tức thấy phương án thay thế chứ không thấy lỗi kỹ thuật.

**AC-02.2.** Given một xe demo đã có booking từ 10:00 đến 10:30, When hệ thống xét suất 10:15 đến 10:45 của cùng xe đó, Then suất này bị từ chối vì chồng giờ.

**AC-02.3.** Given khách bấm nút Xác nhận hai lần liên tiếp do double-click hoặc mạng chập chờn, When cả hai request tới server với cùng `ui_action_id`, Then chỉ tạo một booking và request thứ hai trả về đúng kết quả của request đầu.

---

#### US-03. Đổi hoặc hủy không phải giải thích (P0, đã build)

Là người muốn lái thử, tôi muốn tự đổi hoặc hủy chỉ bằng một chạm, để không phải nhắn giải thích với ai khi kế hoạch đổi.

Bằng chứng E3, E10. Quy tắc R-N4.

**AC-03.1.** Given tôi có một lịch đã xác nhận, When tôi bấm Hủy, Then lịch được hủy tức thì, chỗ được giải phóng, và không có cuộc gọi truy theo nào sau đó.

**AC-03.2.** Given tôi vừa hủy lịch, When hệ thống xét hàng đợi thông báo, Then mọi tin nhắc đang chờ của booking đó bị hủy và không tin nào được gửi thêm.

**AC-03.3.** Given tôi muốn đổi sang khung khác, When tôi chọn khung mới, Then hệ thống giữ chỗ mới trước rồi mới giải phóng chỗ cũ, để tôi không mất cả hai.

**AC-03.4.** Given tôi từng no-show và nay quay lại đặt, When tôi bắt đầu luồng đặt, Then tôi được đặt bình thường, không bị chặn và không bị nhắc dồn về lần vắng trước.

---

#### US-04. Đặt hộ, đúng người lái được nhắc (P0, build một phần)

Là người đặt hộ, tôi muốn khai người lái là người khác, để đúng người đó được nhắc và tự lo giấy tờ, còn tôi không phải làm trung gian.

Bằng chứng E5, E6. Quy tắc R-K2, R-D2, R-D4.

**AC-04.1** (đã có). Given tôi bắt đầu đặt lịch, When hệ thống mở hội thoại, Then câu hỏi đầu tiên là "đặt cho mình hay người khác lái?", trước khi hỏi bất cứ thông tin nào khác.

**AC-04.2** (đã có). Given tôi chọn đặt cho người khác, When tôi nhập thông tin người lái, Then hệ thống tạo hồ sơ người lái riêng, tách khỏi hồ sơ người đặt.

**AC-04.3** (chưa có). Given tôi đã khai người lái là anh Nam, When booking được xác nhận, Then hệ thống gửi cho anh Nam một link riêng để anh tự xác nhận và tự nhập giấy phép lái xe.

**AC-04.4** (một phần). Given anh Nam tới showroom, When lễ tân tra bằng tên hoặc số điện thoại của anh Nam, Then hệ thống tìm ra đúng booking chứ không chỉ tra được bằng tên chị Vy.

**AC-04.5** (chưa có). Given booking đã xác nhận có người đặt khác người lái, When hệ thống gửi thông báo, Then người lái nhận bản chính có nút hành động, còn người đặt nhận bản sao chỉ để theo dõi, và nội dung hai bản khác nhau.

**AC-04.6** (một phần). Given tôi là người đặt, When tôi xem chi tiết booking, Then tôi không nhìn thấy giấy phép lái xe của người lái.

---

#### US-05. Giấy phép lái xe đúng lúc, đúng kênh (P1, build một phần)

Là người lái, tôi muốn chỉ cung cấp giấy phép khi thật cần và qua kênh chính thống, để giấy tờ của tôi không trôi nổi.

Bằng chứng E7. Quy tắc R-G1 đến R-G4.

**AC-05.1.** Given tôi mới ở bước gửi yêu cầu và lịch chưa chắc chắn, When hệ thống thu thập thông tin, Then hệ thống không được hỏi giấy phép lái xe ở bước này.

**AC-05.2.** Given lịch và xe đã được xác nhận, When hệ thống cần giấy phép, Then tôi nhập qua kênh chính thống, có thông báo rõ mục đích sử dụng và thời hạn xóa.

**AC-05.3.** Given quy trình cần đối chiếu giấy phép, When nhân viên xử lý, Then nhân viên không được yêu cầu gửi ảnh qua tài khoản Zalo hoặc Facebook cá nhân.

**AC-05.4** (chưa có). Given tôi không muốn upload trước, When hệ thống hỏi giấy phép, Then luôn có lựa chọn mang bản gốc tới đối chiếu tại showroom.

---

#### US-06. Nhắc cụ thể để tăng cam kết (P0, build một phần)

Là người dùng, tôi muốn được nhắc cụ thể rằng xe đã sẵn sàng và đã giữ chỗ cho tôi, đúng lúc, để tôi có lý do chắc chắn để đi.

Bằng chứng E12 (không nhắc thì mức chắc chắn tụt từ 100% còn 60%), E13, R2, R8. Quy tắc R-N1 đến R-N4.

**AC-06.1** (đã có). Given booking đã xác nhận lúc 10:00 thứ Bảy, When hệ thống lập lịch nhắc, Then tạo đúng ba tin: ngay sau khi đặt, trước 24 giờ và trước 2 giờ.

**AC-06.2** (một phần). Given còn 2 giờ tới hẹn, When hệ thống nhắc qua Zalo, Then tin ngắn ghi rõ giờ, địa điểm, đúng mẫu và phiên bản xe, câu "đã giữ chỗ cho bạn", kèm ba nút Xác nhận, Đổi, Hủy.

**AC-06.3.** Given khách đã nhận tin nhắc tự động, When nhân viên xét việc liên hệ, Then không có nhiều nhân viên cùng nhắn hoặc gọi cho một booking.

**AC-06.4.** Given giờ hẹn được đổi từ 14:00 sang 15:00, When bất kỳ kênh nào gửi tin, Then mọi kênh đều đọc từ một nguồn sự thật và hiển thị 15:00. Đây chính là ca lỗi thật của chị Vy ở E8.

---

#### US-07. Gợi ý khung thay thế khi hết chỗ (P0, đã build)

Là khách đang muốn đặt, tôi muốn khi khung mình chọn hết chỗ thì được đề xuất lựa chọn khác ngay, để tôi không bỏ ngang.

Bằng chứng: anh Duy nói "nói ngay là hết, đừng cho mình chọn rồi hôm sau mới báo". Quy tắc R-A1 đến R-A3.

**AC-07.1.** Given khung 10:00 thứ Bảy đã hết, When tôi chọn khung đó, Then hệ thống báo hết ngay tại bước chọn, kèm 2 đến 3 phương án theo thứ tự: lệch 30 đến 60 phút cùng showroom, rồi cùng giờ ở showroom gần nhất, rồi cùng khung vào ngày khác.

**AC-07.2.** Given hệ thống đề xuất phương án thay thế, When tôi xem danh sách, Then mọi phương án đều có suất và xe thật, không có chỗ trống ảo.

**AC-07.3.** Given cả tuần ở showroom này đã hết suất, When tôi xem lịch, Then hệ thống nói thẳng là hết và đề xuất showroom gần hoặc tuần kế, tuyệt đối không hiển thị lịch trống giả.

---

#### US-08. Check-in tại showroom (P1, build một phần)

Là người lái, tôi muốn tới nơi là có lịch ngay và đúng xe, để không phải chứng minh mình có hẹn.

Bằng chứng E5, E9. Quy tắc R-D4, R-X1, R-X3.

**AC-08.1.** Given tôi có booking đã xác nhận, When nhân viên tra bằng mã lịch, hoặc tên và số điện thoại người lái, hoặc tên và số điện thoại người đặt, Then cả ba cách đều ra đúng booking.

**AC-08.2.** Given tôi check-in thành công, When màn hình nhân viên hiển thị, Then hiện đúng xe và đúng phiên bản đã giữ, kèm vị trí xe.

**AC-08.3.** Given pin xe demo tụt dưới ngưỡng sau khi booking đã xác nhận, When hệ thống phát hiện, Then thông báo sớm cho khách và đề xuất đổi xe hoặc đổi giờ, thay vì để khách tới rồi mới biết.

---

#### US-09. Quản lý duyệt khung VIP (P1, chưa build)

Là quản lý showroom, tôi muốn duyệt các khung VIP hoặc đặc biệt trước khi hệ thống giữ chỗ, để kiểm soát nguồn lực.

Quy tắc R-H2, R-H3, R-H4.

**AC-09.1.** Given một yêu cầu rơi vào khung VIP, When khách chọn, Then booking chuyển sang trạng thái chờ quản lý duyệt, và khách được báo rõ đang chờ duyệt kèm thời gian dự kiến.

**AC-09.2.** Given booking đang chờ duyệt, When tôi duyệt, Then booking sang trạng thái đã xác nhận và khách nhận thông báo. Khi tôi từ chối, booking sang trạng thái đã hủy kèm lý do và chỗ được giải phóng.

**AC-09.3.** Given tôi là tư vấn viên chứ không phải quản lý, When tôi mở hàng chờ duyệt VIP, Then tôi không có quyền duyệt.

---

#### US-10. Chuyển người thật giữ nguyên ngữ cảnh (P1, chưa build)

Là khách có câu hỏi sâu, tôi muốn được nối với tư vấn viên mà không phải khai lại từ đầu, để không mất công.

Bằng chứng E17. Quy tắc R-H1.

**AC-10.1.** Given tôi đang hỏi ViVi về phương án vay, When ViVi chuyển tôi cho tư vấn viên, Then tư vấn viên nhìn thấy nguyên ngữ cảnh gồm xe đang quan tâm, showroom, lịch đang giữ nếu có, và lịch sử hội thoại, còn tôi không phải khai lại gì.

**AC-10.2.** Given đang ngoài giờ làm việc của showroom, When tôi yêu cầu gặp người thật, Then hệ thống nói rõ khung giờ sẽ được liên hệ lại, không để tôi chờ vô định. Chờ vô định chính là nỗi đau gốc, không được tái tạo nó ở đây.

---

#### US-11. Dashboard vận hành (P1, build một phần)

Là quản lý showroom, tôi muốn thấy phễu đặt, đến, chốt, để biết hiệu quả thật.

**AC-11.1.** Given có booking trong hệ thống, When tôi mở dashboard, Then thấy phễu đặt, đến, chốt, kèm tỷ lệ no-show, số hold đang hoạt động và số tin nhắc đang chờ.

**AC-11.2.** Given dashboard hiển thị danh sách lead, When dữ liệu được trả về, Then dữ liệu không chứa mã OTP và không chứa giấy phép lái xe thô.

**AC-11.3** (chưa có). Given một lead vào hệ thống, When lead được phân công, Then chỉ một nhân viên phụ trách, không chia một lead cho nhiều người.

---

### 4.4 F10, tư vấn chọn xe và giải đáp

Đây là phần bổ sung chính của PRD v1.0 so với Concept Spec v0.2.

#### 4.4.1 Vì sao thêm tính năng này

Có ba luận cứ, và cả ba đều đến từ bằng chứng phỏng vấn chứ không phải suy đoán.

Thứ nhất, khách nói thẳng là họ cần tư vấn. Anh Nguyên, người chưa từng booking bao giờ, nói rằng mình cần một người tư vấn về flow, cần biết những thông tin gì và những bước gì để booking được một chiếc xe để lái thử (E16). Khi được hỏi điều gì làm anh bỏ website, câu trả lời đầu tiên của anh là nó không đáp ứng được hết những thông tin anh muốn.

Thứ hai, chính tài liệu Empathy đã chỉ đích danh đây là giá trị cốt lõi. Nguyên văn: giá trị cốt lõi nằm ở việc đặt lịch chắc chắn và giải đáp thắc mắc, không phải ở đồ hoạ 3D (E15). Anh Nguyên cũng xác nhận rằng vấn đề của anh chỉ là giải đáp thắc mắc và đặt lịch.

Thứ ba, tư vấn là cửa vào tự nhiên của luồng đặt lịch. Người ở giai đoạn mới xem, chiếm hai trong ba người phỏng vấn, chưa sẵn sàng chọn ngày giờ vì họ còn đang phân vân giữa VF 6 và Creta, giữa VF 7 và CX-5. Nếu ViVi chỉ biết đặt lịch, ta bỏ lỡ toàn bộ nhóm này. F10 biến hội thoại từ câu hỏi "chọn ngày nào" thành câu hỏi "anh chị cần xe cho việc gì", rồi mới dẫn sang đặt lịch.

Về hiện trạng kỹ thuật, khung sườn đã có sẵn: node `advise_skill_node` và bộ phân loại ý định định tuyến giữa nhánh booking và nhánh advise đều đã chạy. Nhưng công cụ tra cứu tri thức lại là hàm giả. Hàm `search_knowledge` trả về đúng chuỗi `f"Kết quả tìm kiếm cho: {query}"` và không truy vấn gì cả. Nghĩa là ViVi hiện đang trả lời câu hỏi về xe hoàn toàn bằng trí nhớ của LLM. Đây là rủi ro bịa đặt nghiêm trọng, và cũng là lý do F10 được xếp mức P0.

#### 4.4.2 Phạm vi F10

| Mã | Tính năng phụ | Ưu tiên |
|---|---|---|
| F10.1 | Hỏi đáp thông số, giá, chính sách dựa trên knowledge base chính thống, có dẫn nguồn | P0 |
| F10.2 | Tư vấn chọn xe theo nhu cầu: hỏi ngược vài câu rồi gợi ý một đến hai mẫu kèm lý do | P0 |
| F10.3 | So sánh hai mẫu xe theo tiêu chí khách quan tâm | P1 |
| F10.4 | Cầu nối sang đặt lịch, giữ nguyên ngữ cảnh xe vừa tư vấn | P0 |
| F10.5 | Ranh giới và chuyển người thật cho chủ đề ngoài năng lực | P0 |
| F10.6 | Chống bịa: không biết thì nói không biết | P0 |

#### 4.4.3 Business rules của F10

| Mã | Quy tắc |
|---|---|
| R-T1 | ViVi chỉ trả lời về thông số, giá, tầm hoạt động, tính năng, chính sách bảo hành và sạc dựa trên knowledge base. Nếu không có trong knowledge base thì nói thẳng là chưa có thông tin và đề nghị nối tư vấn viên |
| R-T2 | Mọi câu trả lời chứa con số, gồm giá, tầm hoạt động, dung lượng pin, công suất, thời gian sạc, bắt buộc kèm nguồn là tên tài liệu và ngày hiệu lực |
| R-T3 | ViVi không được thúc chốt, không gợi ý đặt cọc, không tạo cảm giác khan hiếm giả, và không hỏi ngân sách hay thời điểm mua khi khách chưa nêu. Chính hành vi này ở E11 đã đẩy anh Duy và anh Nam đi |
| R-T4 | Các chủ đề bắt buộc chuyển người thật, ViVi không tự trả lời, gồm: vay và trả góp, bảo hiểm, định giá và thu mua xe cũ, khiếu nại và sự cố, đàm phán giá cùng ưu đãi cá nhân hoá. Đây là ranh giới do chính khách vạch ra ở E17 |
| R-T5 | Khi tư vấn xong và khách quan tâm một mẫu, ViVi đề nghị đặt lịch một lần duy nhất, không lặp lại nếu khách chưa muốn |
| R-T6 | Chuyển từ tư vấn sang đặt lịch phải giữ nguyên mẫu và phiên bản đang bàn, khách không phải chọn lại xe |
| R-T7 | ViVi không bao giờ hứa có xe hoặc có khung giờ trong lúc tư vấn. Mọi khẳng định về tình trạng sẵn có chỉ được nói sau khi truy vấn dữ liệu thật qua luồng đặt lịch (E18) |
| R-T8 | Câu hỏi ngoài phạm vi như chính trị, chủ quyền, lập trình, toán học đi theo chính sách guardrail hiện có, không trả lời tự do |
| R-T9 | ViVi không so sánh trực tiếp bất lợi với xe hãng khác. Được nêu thông số VinFast, không được hạ thấp đối thủ |

#### 4.4.4 User stories của F10

---

##### US-12. Hỏi đáp có nguồn về xe (P0, chưa build)

Là người đang tìm hiểu xe, tôi muốn hỏi ViVi về thông số và chính sách rồi nhận câu trả lời chính xác có dẫn nguồn, để tôi tin được thông tin đó.

**AC-12.1.** Given tôi hỏi VF 6 Plus đi được bao nhiêu km một lần sạc, When ViVi trả lời, Then câu trả lời lấy số từ knowledge base, ghi rõ đang nói về phiên bản nào, kèm nguồn và ngày hiệu lực.

**AC-12.2.** Given tôi hỏi một thông tin không có trong knowledge base, When ViVi xử lý, Then ViVi nói rõ là chưa có thông tin đó và đề nghị nối tư vấn viên, tuyệt đối không suy đoán hay bịa số.

**AC-12.3.** Given knowledge base có hai phiên bản tài liệu khác ngày, When ViVi trích dẫn, Then dùng bản mới nhất còn hiệu lực.

**AC-12.4.** Given tôi hỏi xe còn không, mai đặt được không, trong lúc đang tư vấn, When ViVi trả lời, Then ViVi không khẳng định còn hay hết, mà chuyển sang luồng đặt lịch để tra dữ liệu thật.

---

##### US-13. Tư vấn chọn xe theo nhu cầu (P0, chưa build)

Là người chưa biết chọn mẫu nào, tôi muốn kể nhu cầu rồi được gợi ý xe phù hợp, để thu hẹp lựa chọn trước khi đi lái thử.

Bằng chứng: hai trong ba người phỏng vấn đang ở giai đoạn mới xem; chị Vy và chồng mỗi người thích một mẫu khác nhau và cần lái thử để loại bớt.

**AC-13.1.** Given tôi nói nhà bốn người, hay về quê cuối tuần, chung cư có chỗ sạc, When ViVi tư vấn, Then ViVi hỏi tối đa ba câu làm rõ về số chỗ cần, ngân sách khoảng bao nhiêu, ưu tiên điều gì, rồi gợi ý một đến hai mẫu kèm lý do gắn với chính điều tôi vừa kể.

**AC-13.2.** Given tôi chỉ nói một câu mơ hồ là tôi muốn mua xe điện, When ViVi phản hồi, Then ViVi hỏi làm rõ trước chứ không đổ ngay danh sách toàn bộ mẫu xe.

**AC-13.3.** Given tôi chưa nêu ngân sách, When ViVi tư vấn, Then ViVi không hỏi tôi dự tính mua khi nào hay trả trước bao nhiêu. Đây là câu hỏi làm khách khó chịu nhất trong phỏng vấn (E11).

**AC-13.4.** Given tôi hỏi về mẫu xe trưng bày chưa mở lái thử là Lạc Hồng 900 LX hoặc 900S, When ViVi trả lời, Then ViVi nói rõ mẫu này chưa mở lái thử và không đề nghị đặt lịch cho nó.

---

##### US-14. So sánh hai mẫu xe (P1, chưa build)

Là người đang phân vân giữa hai mẫu, tôi muốn thấy bảng so sánh theo tiêu chí mình quan tâm, để quyết định thử mẫu nào.

**AC-14.1.** Given tôi hỏi VF 6 với VF 7 khác gì nhau, When ViVi trả lời, Then hiện bảng so sánh tối đa sáu tiêu chí gồm kích thước, số chỗ, tầm hoạt động, công suất, giá và tính năng nổi bật, mỗi số đều có nguồn.

**AC-14.2.** Given tôi nêu tiêu chí riêng như quan tâm hàng ghế sau và an toàn cho trẻ con, When ViVi so sánh, Then ViVi ưu tiên đúng tiêu chí tôi nêu lên đầu bảng.

**AC-14.3.** Given tôi hỏi VF 6 so với Hyundai Creta thì sao, When ViVi trả lời, Then ViVi nêu thông số VF 6 và không hạ thấp Creta, đồng thời đề nghị lái thử để tôi tự cảm nhận.

---

##### US-15. Từ tư vấn sang đặt lịch, không mất ngữ cảnh (P0, chưa build)

Là người vừa được tư vấn xong, tôi muốn đặt lịch ngay mà không phải chọn lại xe, để không mất công làm lại.

**AC-15.1.** Given ViVi vừa tư vấn tôi nên thử VF 6 Plus, When tôi nói vậy đặt lịch cho tôi, Then luồng đặt lịch mở với VF 6 Plus đã được chọn sẵn, và bước tiếp theo là hỏi đặt cho mình hay người khác lái.

**AC-15.2.** Given tôi đang ở giữa luồng đặt lịch, When tôi hỏi một câu tư vấn như xe này sạc đầy mất bao lâu, Then ViVi trả lời rồi quay lại đúng bước tôi đang dở, không làm mất tiến trình đặt lịch.

**AC-15.3.** Given tôi được tư vấn nhưng chưa muốn đặt, When tôi nói để tôi suy nghĩ thêm, Then ViVi không nhắc lại lời mời đặt lịch trong phần còn lại của phiên.

---

##### US-16. Ranh giới rõ ràng, chuyển người thật đúng lúc (P0, chưa build)

Là người có câu hỏi tài chính hoặc phức tạp, tôi muốn được nối với người thật thay vì nhận câu trả lời chung chung, để tôi có thông tin dùng được.

Bằng chứng E17: anh Duy và chị Vy độc lập nêu gần như cùng một danh sách.

**AC-16.1.** Given tôi hỏi về trả góp, lãi suất, bảo hiểm hoặc thu xe cũ, When ViVi nhận diện chủ đề, Then ViVi không tự trả lời mà nói rõ sẽ nối tôi với tư vấn viên, và chuyển kèm nguyên ngữ cảnh.

**AC-16.2.** Given tôi hỏi cùng một câu ba lần mà ViVi vẫn không trả lời được, When lượt thứ ba kết thúc, Then ViVi chủ động đề nghị chuyển người thật thay vì tiếp tục xin lỗi.

**AC-16.3.** Given tôi nói thẳng là cho tôi gặp người thật, When ViVi nhận yêu cầu, Then chuyển ngay, không cố giữ tôi lại và không hỏi thêm lý do. Nhóm ngại công nghệ ở R10 cần đúng lối thoát này.

---

#### 4.4.5 Nguồn tri thức cho F10

| Nguồn | Nội dung | Trạng thái |
|---|---|---|
| Catalogue xe trong database | Tên, phiên bản, giá niêm yết, số chỗ, kiểu dáng, thông số tóm tắt | Đã có, ở `vehicle_models` và `vehicle_variants` |
| Nội dung trang marketing | Trang chủ, trạm sạc, hậu mãi | Đã có, qua `/api/v1/content/{page}` |
| Brochure PDF chính thức | Thông số chi tiết từng mẫu | File có trong bundle frontend nhưng chưa được index |
| Chính sách bảo hành, sạc, hậu mãi | Điều kiện, thời hạn | Chưa có, cần thu thập từ VinFast |
| Danh mục showroom | Địa chỉ, giờ mở cửa, liên hệ | Đã có |
| Câu hỏi thường gặp | Quy trình lái thử, giấy tờ cần mang | Chưa có, cần soạn |

Về ràng buộc nội dung, knowledge base chỉ được nạp từ tài liệu chính thống của VinFast và mỗi tài liệu phải gắn ngày hiệu lực. Không scrape web, không lấy từ diễn đàn hay bài review. Sai thông số giá hoặc sai chính sách là rủi ro pháp lý chứ không chỉ là lỗi trải nghiệm.

### 4.5 Edge cases và error states

| Mã | Tình huống | Xử lý mong muốn | Trạng thái |
|---|---|---|---|
| EC-01 | Đua giữ chỗ, hai khách cùng bấm một suất trong tích tắc | Khóa giao dịch quyết định, người thua lập tức thấy phương án thay thế chứ không thấy lỗi kỹ thuật | Đã có |
| EC-02 | Hold hết hạn ngay khi bấm xác nhận | Nếu suất vẫn còn thì ưu tiên hoàn tất; nếu vừa bị người khác giữ thì chuyển sang phương án thay thế, không báo lỗi cụt | Đã có |
| EC-03 | Người lái không bao giờ tự xác nhận hoặc không nạp giấy phép | Booking vẫn giữ cho người đặt, nhắc riêng người lái, cho check-in bằng bản gốc | Chưa có, xem OQ-5 |
| EC-04 | Đổi lịch nhưng suất mới cũng hết giữa chừng | Quay lại bước chọn suất kèm phương án thay thế, giữ nguyên hồ sơ và không bắt khai lại | Đã có |
| EC-05 | Pin xe tụt dưới ngưỡng sau khi đã xác nhận | Thông báo sớm và đề xuất đổi xe hoặc giờ, thay vì để khách tới rồi mới biết | Một phần |
| EC-06 | No-show rồi khách quay lại đặt | Cho đặt lại bình thường, không truy theo và không nhắc dồn | Đã có |
| EC-07 | Một người đặt nhiều booking cho nhiều người lái | Mỗi booking có người lái riêng, việc nhắc và giấy tờ tách theo từng người | Đã có |
| EC-08 | Showroom hết suất cả tuần | Nói thẳng, đề xuất showroom gần hoặc tuần kế, không hiển thị lịch trống giả | Đã có |
| EC-09 | Địa chỉ mơ hồ, chỉ nhận diện được tỉnh hoặc thành phố | Giữ màn hình xe, hỏi lại phường xã, không tải toàn bộ showroom của tỉnh | Một phần, chưa có geocoding |
| EC-10 | Không có showroom nào gần | Gợi ý showroom kế tiếp kèm khoảng cách rõ ràng | Đã có |
| EC-11 | Mất mạng giữa luồng đặt | Giữ tiến trình, báo rõ hold còn hay hết, cho thử lại | Một phần, mới có `sessionStorage` |
| EC-12 | Backend không khả dụng | Báo rõ ràng, không để trang trắng, polling health mỗi 30 giây | Đã có |
| EC-13 | LLM không phản hồi hoặc hết quota | Luồng đặt lịch bằng nút vẫn chạy bình thường vì không phụ thuộc LLM, chỉ chat tự do báo lỗi | Đã có theo thiết kế |
| EC-14 | Khách nhập số điện thoại hoặc email sai định dạng | Báo lỗi tại chỗ, không mất dữ liệu đã nhập | Đã có |
| EC-15 | OTP sai quá số lần cho phép | Khóa thử lại, hướng dẫn xin mã mới sau thời gian chờ | Đã có, hiện 2 lần và chờ 60 giây |
| EC-16 | Số điện thoại chưa liên kết Zalo Bot | Báo rõ "chưa liên kết", khác hẳn với "kênh chưa cấu hình", kèm hướng dẫn cách liên kết | Đã có |
| EC-17 | Khách hỏi câu ngoài phạm vi như chính trị, code, toán | Theo chính sách guardrail hiện có, từ chối lịch sự và kéo về chủ đề xe | Đã có |
| EC-18 | Knowledge base trả về kết quả mâu thuẫn | Ưu tiên tài liệu mới nhất còn hiệu lực; nếu vẫn mâu thuẫn thì không trả lời số mà chuyển người thật | Chưa có |
| EC-19 | Khách hỏi về xe không có trong catalogue | Nói rõ chưa có thông tin, không suy đoán | Chưa có |
| EC-20 | Ngoài giờ làm việc showroom mà cần chuyển người thật | Nói rõ khung giờ sẽ được liên hệ lại, không để khách chờ vô định | Chưa có |

---

## 5. Yêu cầu phi chức năng

### 5.1 Hiệu năng

API tra khung giờ trống phải trả về trong 800ms ở mức p95, còn API giữ chỗ và xác nhận trong 1,5 giây ở mức p95, đúng theo guardrail G7. Phản hồi đầu tiên của ViVi khi tư vấn không quá 3 giây, và nếu có streaming thì tính từ token đầu tiên. Hệ thống phải chịu được ít nhất 200 phiên đặt lịch đồng thời trên mỗi showroom mà không suy giảm. Thời gian dựng trang lần đầu (LCP) trên mạng 4G không quá 2,5 giây.

Có một yêu cầu bắt buộc cần nhấn mạnh: luồng đặt lịch bằng nút không được phụ thuộc vào LLM. LLM chết thì việc đặt lịch vẫn phải chạy.

### 5.2 Bảo mật và phân quyền

Hệ thống không được ghi số điện thoại, email, số giấy phép lái xe hoặc ảnh giấy tờ vào log ứng dụng hay prompt log. Backend đã có cơ chế thay bằng `[redacted]`, và cơ chế này phải phủ 100% đường ghi log. Giấy phép lái xe chỉ truyền qua kênh chính thống có TLS, cấm đi qua tài khoản cá nhân của nhân viên.

Việc truy cập lịch đã đặt phải qua xác thực OTP, và phiên truy cập có thời hạn. Phân quyền theo vai: khách chỉ thấy lịch của mình, tư vấn viên thấy lịch được phân công, và chỉ quản lý mới được duyệt khung VIP. Người đặt không xem được giấy phép lái xe của người lái. Dashboard và API vận hành không bao giờ trả về mã OTP hoặc dữ liệu giấy phép thô.

Guardrails đầu vào và đầu ra phải chặn chủ đề nhạy cảm, chặn rò rỉ prompt và chặn lộ dữ liệu nội bộ qua hội thoại. Mọi thao tác thay đổi trạng thái booking đều có idempotency key để chống lặp.

### 5.3 Quyền riêng tư và tuân thủ dữ liệu

Nguyên tắc là thu thập tối thiểu, chỉ lấy dữ liệu cần cho buổi hẹn, và không thu giấy phép lái xe trước khi lịch được xác nhận theo R-G1. Ngay tại điểm thu thập giấy phép phải thông báo rõ mục đích sử dụng và thời hạn lưu. Giấy phép được xóa tự động sau thời hạn đã công bố, con số cụ thể chờ chốt ở OQ-4. Người dùng có quyền yêu cầu xóa dữ liệu của mình. Sản phẩm tuân thủ Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân, và có cơ chế tắt nhận thông báo được tôn trọng ngay lập tức, gắn với guardrail G2.

### 5.4 Khả năng tiếp cận

Các luồng chính gồm đặt lịch, tra cứu, đổi và hủy phải đạt WCAG 2.1 mức AA. Tương phản màu cho chữ thường tối thiểu 4.5:1. Người dùng phải điều hướng được hoàn toàn bằng bàn phím, và có link bỏ qua để nhảy tới nội dung chính. Mọi ảnh có thuộc tính `alt` mô tả, mọi trường nhập có nhãn liên kết đúng. Giao diện phải tôn trọng `prefers-reduced-motion`, nghĩa là hiệu ứng chuyển cảnh tắt được.

Có một yêu cầu riêng phục vụ persona P3: lối thoát về người thật phải hiện rõ trên mọi màn hình.

### 5.5 Đa ngôn ngữ và thiết bị

Tiếng Việt là ngôn ngữ duy nhất ở bản này, đúng theo non-goal N6. Dấu tiếng Việt phải hiển thị đúng trên mọi kênh, kể cả tin nhắn Zalo và SMS. Thiết kế theo hướng mobile-first vì hai trong ba người phỏng vấn đặt lịch trên điện thoại. Hỗ trợ Chrome, Safari và Edge ở hai phiên bản gần nhất, riêng Safari iOS từ bản 15 trở lên, và hoạt động được ở màn hình rộng 360px.

### 5.6 Khả năng mở rộng và vận hành

Kiến trúc phải chịu được mở rộng lên ít nhất 50 showroom mà không cần đổi thiết kế. Các tham số như giờ mở cửa, thời hạn giữ chỗ và ngưỡng pin phải cấu hình được theo từng showroom. Cần health check cho từng thành phần gồm database, LLM và kênh thông báo. Mỗi lượt hội thoại phải truy vết được để phục vụ debug, nhưng trace không được chứa PII. Chi phí LLM và chi phí tin nhắn phải theo dõi được theo từng booking, gắn với guardrail G4.

---

## 6. Trải nghiệm và thiết kế

### 6.1 Tài liệu thiết kế

Wireframe lo-fi đã có tại [`docs/docs/Wireframe-Lo-fi-P053.html`](docs/Wireframe-Lo-fi-P053.html). Bản thiết kế hi-fi trên Figma thì chưa có, vì thiết kế hiện đi thẳng từ lo-fi sang code; rủi ro này đã ghi ở R-05. Giao diện đang chạy là một React SPA gồm năm trang: trang chủ, chi tiết xe, đặt lịch, hậu mãi và trạm sạc.

### 6.2 Bản đồ màn hình

| Mã | Màn hình | Mục đích | Trạng thái |
|---|---|---|---|
| M1 | Điểm vào, gồm nút "Đặt lái thử" trên web và Zalo OA | Mở luồng, tạo booking nháp, báo rõ đây là kênh chính thống để tạo niềm tin (E18) | Web đã có, Zalo OA chưa có |
| M2 | Hội thoại chọn xe và showroom | Chọn mẫu, phiên bản và showroom gần | Đã có |
| M3 | Chọn suất theo lịch thời gian thực, kèm phương án thay thế | Cho khách thấy giờ có thật theo xe và giữ chỗ | Đã có |
| M4 | Khai "đặt cho ai" | Tách vai ngay tại điểm đặt | Đã có |
| M5 | Xác nhận kèm mã lịch | Biến "đã tiếp nhận" thành "đã xác nhận" | Đã có |
| M6 | Link riêng cho người lái để tự xác nhận và nhập giấy phép | Đúng người lái đồng ý và nạp giấy tờ an toàn | Chưa có |
| M7 | Trang "Lịch của tôi" để đổi hoặc hủy một chạm | Tự phục vụ, gỡ ma sát xã hội khi hủy | Đã có |
| M8 | Mẫu tin nhắc qua Zalo và email | Giữ cam kết bằng nội dung cụ thể | Một phần |
| M9 | Check-in tại showroom | Đảm bảo tới nơi là có lịch và đúng xe | Một phần |
| M10 | Bàn làm việc HITL, gồm hàng chờ handoff và hàng chờ duyệt VIP | Đưa người thật vào đúng lúc, giữ ngữ cảnh | Chưa có |
| M11 | Dashboard vận hành | Cho showroom đo phễu đặt, đến, chốt | Một phần |
| M12 | Hội thoại tư vấn phục vụ F10 | Hỏi đáp có nguồn, gợi ý xe, so sánh | Chưa có, màn hình mới |

### 6.3 Trạng thái màn hình bắt buộc

Mỗi màn hình phải thiết kế đủ năm trạng thái, và đây là nơi trải nghiệm hay dở lộ ra rõ nhất.

Trạng thái mặc định là lúc mọi thứ bình thường. Trạng thái đang tải phải có phản hồi thị giác trong vòng 300ms, và riêng thao tác giữ chỗ với xác nhận thì phải khóa nút để chống bấm hai lần. Trạng thái rỗng, chẳng hạn khi hết suất, phải nói thẳng kèm đề xuất phương án thật, tuyệt đối không bao giờ hiện lịch trống giả theo R-A1. Trạng thái lỗi phải nói được hai điều: chuyện gì đã xảy ra và người dùng nên làm gì tiếp theo, đồng thời giữ nguyên dữ liệu họ đã nhập. Trạng thái thành công phải xác nhận rõ ràng kèm mã lịch, và phải phân biệt rạch ròi giữa "đã giữ chỗ, chờ xác nhận" với "đã xác nhận".

### 6.4 UX copy

Nguyên tắc xuyên suốt là nói cho khách biết cái gì đã chắc (E1). Cột bên phải trong bảng dưới là những cách viết tuyệt đối phải tránh, lấy thẳng từ nỗi đau đã ghi nhận trong phỏng vấn.

| Tình huống | Nên viết | Không được viết |
|---|---|---|
| Đặt lịch thành công | "Đã xác nhận. 10:00 T7 07/09, VF 6 Plus, VinFast Gò Vấp. Mã lịch VF260907A1B2" | "Yêu cầu của bạn đã được tiếp nhận, nhân viên sẽ liên hệ." Chính câu này gây bất định ở E2 |
| Đang giữ chỗ | "Đang giữ chỗ cho bạn, còn 1:47 để hoàn tất" | "Đang xử lý…" |
| Hết chỗ | "Khung 10:00 vừa có người đặt. Còn 3 lựa chọn có sẵn xe VF 6 Plus: …" | "Khung giờ không khả dụng." |
| Tin nhắc trước 24 giờ | "Nhắc lịch: 10:00 mai, VF 6 Plus đã được giữ cho anh Nam, VinFast Gò Vấp. [Xác nhận] [Đổi giờ] [Hủy]" | "Đừng quên lịch hẹn của bạn!" Nhắc chung chung là vô ích theo E12 |
| Hủy thành công | "Đã hủy lịch. Chỗ đã được giải phóng. Không có ai liên hệ lại về lịch này." | "Rất tiếc bạn hủy lịch. Nhân viên sẽ gọi lại để tư vấn thêm." Truy theo đẩy khách đi theo E10 |
| Đặt hộ | "Đã gửi link xác nhận riêng cho anh Nam qua Zalo. Chị nhận bản sao để theo dõi." | "Chúng tôi sẽ liên hệ với bạn." Người đặt bị kẹt làm trung gian theo E6 |
| Thu giấy phép lái xe | "Cần bằng lái của người lái để chuẩn bị hồ sơ. Dữ liệu dùng cho buổi lái thử này và xóa sau [X] ngày. Hoặc bạn có thể mang bản gốc tới đối chiếu." | "Vui lòng gửi ảnh 2 mặt bằng lái." (E7) |
| Backend lỗi | "Hiện chưa kết nối được hệ thống đặt lịch. Bạn thử lại sau ít phút, hoặc gọi hotline [số]." | Trang trắng, hoặc dòng "Error 500" |
| F10 không biết | "Thông tin này em chưa có trong tài liệu chính thức. Em nối anh chị với tư vấn viên nhé?" | Bịa một con số nghe hợp lý, đây là rủi ro nặng nhất của F10 theo G6 |
| F10 chuyển người thật | "Phần trả góp cần tư vấn viên tính theo hồ sơ cụ thể. Em chuyển anh chị nhé, anh chị không phải khai lại gì." | "Bạn có thể tham khảo lãi suất khoảng 8 đến 10% một năm." (R-T4) |

### 6.5 Nguyên tắc thiết kế rút từ phỏng vấn

Nói cái gì đã chắc, ở mọi bước; trạng thái đang giữ và trạng thái đã xác nhận phải trông khác nhau rõ rệt. Không bao giờ hiện lựa chọn không có thật, vì thà nói hết còn hơn cho chọn rồi rút lại (E18). Nút hủy phải dễ tìm ngang nút đặt, bởi giấu nút hủy không giữ được khách mà chỉ tạo ra no-show im lặng (E3). Không đẩy chốt: không đếm ngược giả, không câu "chỉ còn 2 suất", không hỏi ngân sách khi khách chưa mời (E11). Và luôn có lối thoát về người thật, hiện rõ trên mọi màn hình (R10).

---

## 7. Phụ thuộc và ràng buộc

### 7.1 Phụ thuộc kỹ thuật

| Mã | Phụ thuộc | Trạng thái | Rủi ro nếu thiếu |
|---|---|---|---|
| DEP-1 | Dữ liệu tồn kho xe demo thời gian thực từ showroom | Chưa có nguồn thật | Chí mạng. Không có dữ liệu thật thì toàn bộ lời hứa "slot có thật" sụp đổ (E18) |
| DEP-2 | Lịch làm việc tư vấn viên | Chưa có nguồn thật | Không xác định được suất khả dụng chính xác |
| DEP-3 | Zalo Bot API để gửi tin và nhận webhook | Đã tích hợp, cần token production | Mất kênh liên lạc ưu tiên số một (E13) |
| DEP-4 | Nhà cung cấp LLM (OpenAI hoặc OpenRouter) | Đã tích hợp | Chat tự do và F10 ngừng hoạt động, nhưng đặt lịch bằng nút vẫn chạy |
| DEP-5 | Nhà cung cấp bản đồ kèm API key giới hạn domain | Đang dùng Leaflet tải từ CDN và tile Google không key, không dùng được cho production | Bản đồ chọn showroom không hiển thị |
| DEP-6 | Dịch vụ geocoding chuẩn hoá địa chỉ | Chưa có | Không phân biệt được địa chỉ mơ hồ với trường hợp không có showroom |
| DEP-7 | Nền tảng analytics | Chưa chọn | Không đo được bất kỳ chỉ số nào ở mục 2.4 |
| DEP-8 | Knowledge base chính thống cho F10 | Cần thu thập từ VinFast | F10 không thể triển khai an toàn |
| DEP-9 | Nhà cung cấp SMS và email dự phòng | Có khung, chưa có nhà cung cấp thật | Không có kênh dự phòng khi khách chưa dùng Zalo |
| DEP-10 | Hạ tầng triển khai | Một phần | Không phát hành được |

### 7.2 Phụ thuộc tổ chức

Cần xin quyền truy cập dữ liệu và khách thật của một showroom để kiểm chứng, việc này do PO cùng mentor phụ trách và hiện là câu hỏi mở lớn nhất (DEP-11). Cần phỏng vấn tư vấn viên và quản lý showroom vì hai persona P4 và P5 chưa có tiếng nói nào trong nghiên cứu (DEP-12). Cần VinFast cung cấp nội dung chính thống gồm brochure và chính sách bảo hành, sạc, hậu mãi (DEP-13). Cần đào tạo nhân viên showroom dùng màn hình check-in và bàn làm việc HITL (DEP-14). Cuối cùng cần pháp chế phê duyệt chính sách lưu và xóa giấy phép lái xe (DEP-15).

### 7.3 Ràng buộc

Về kỹ thuật, backend chạy Python 3.11 trở lên với FastAPI, LangGraph điều phối agent, cơ sở dữ liệu là SQLite ở môi trường dev và PostgreSQL ở production với khóa giao dịch; frontend dùng React và Vite. Việc chống trùng lịch là ràng buộc cứng của đề bài và không được đánh đổi vì bất kỳ lý do gì.

Về chi phí, chi phí nhắc lịch và chi phí LLM được nêu thẳng là ràng buộc trong đề bài, nên được theo dõi qua guardrail G4.

Về pháp lý, sản phẩm chịu Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân, và giấy phép lái xe là dữ liệu nhạy cảm.

Về nghiệp vụ, hai mẫu Lạc Hồng 900 LX và 900S là xe trưng bày, chưa mở bán và chưa cho lái thử, nên cố ý không nằm trong catalogue đặt lịch. Chỉ bật lên khi VinFast thực sự mở lái thử.

Về nguồn lực, nhóm dự án làm trong khuôn khổ chương trình đào tạo với thời lượng giới hạn.

---

## 8. Kế hoạch phát hành

### 8.1 Phân kỳ

**MVP v1.0 đã dựng xong và đang ở trạng thái demo nội bộ.** Luồng đặt lịch đầu cuối chạy được với dữ liệu thật trong database. Cụ thể đã có F1 trợ lý hội thoại, F2 slot và xe có thật kèm chống trùng, F5 đổi hủy một chạm, F6 phương án thay thế; đã tách hồ sơ người đặt với người lái ở mức dữ liệu; đã có OTP truy cập lịch qua Zalo, lịch nhắc trước 24 giờ và 2 giờ, dashboard đọc dữ liệu; và website đã đủ trang chủ, chi tiết xe, trạm sạc, hậu mãi, bản đồ showroom cùng 3D viewer. Điều kiện để gọi là sẵn sàng thí điểm là hoàn tất phần P0 còn thiếu ở v1.1.

**Bản v1.1 nhắm tới trạng thái sẵn sàng thí điểm**, gồm các việc P0 còn thiếu: xây F10 tư vấn với knowledge base thật và RAG để thay hàm `search_knowledge` giả (US-12 đến US-16); làm link riêng cho người lái tự xác nhận và nạp giấy phép (AC-04.3); viết lại nội dung tin nhắc cho cụ thể kèm ba nút hành động (AC-06.2); cài analytics theo tracking plan ở mục 2.5; dựng endpoint production thật để bỏ `/api/v1/demo/action`; lưu draft đặt lịch phía server; và khóa bản đồ production cùng geocoding (DEP-5, DEP-6).

**Phase 2 tập trung vào vận hành showroom**, gồm F8 với bàn làm việc tư vấn viên và duyệt khung VIP (US-09, US-10); hoàn chỉnh F7 check-in với màn hình nhân viên và mã QR (US-08); đồng bộ lead một nguồn để chống chia số cho nhiều sales (R-N3, R-O2); dashboard phễu đặt, đến, chốt đầy đủ (US-11); và kết nối tồn kho xe demo thời gian thực (DEP-1).

**Phase 3 là mở rộng**, gồm kênh Zalo OA cho phép đặt lịch trực tiếp trong Zalo vì người dùng nghiêng về kênh này (OQ-6), so sánh xe nâng cao mở rộng từ F10.3, streaming câu trả lời của ViVi, gợi ý khung giờ tối ưu theo tải showroom, và thử nghiệm cơ chế tăng cam kết như giữ chỗ có điều kiện. Riêng việc cuối chỉ làm sau khi có dữ liệu trả lời OQ-1.

### 8.2 Chiến lược rollout

| Giai đoạn | Phạm vi | Điều kiện chuyển tiếp |
|---|---|---|
| 1. Nội bộ | Nhóm dự án và mentor, dùng dữ liệu giả | Chạy hết bộ kiểm thử, không còn lỗi P0 |
| 2. Thí điểm một showroom | Một showroom, sau feature flag, khách thật | Ít nhất 2 tuần, M4 bằng 0, G3 bằng 0, có baseline cho M1 và M2 |
| 3. Mở dần theo phần trăm | 10%, rồi 30%, 60% và 100% lưu lượng của showroom thí điểm | Mỗi bậc giữ ít nhất 3 ngày, không guardrail nào chạm ngưỡng đỏ |
| 4. Nhân rộng | Thêm showroom theo cụm | Vận hành ổn định 4 tuần |

Cần bốn feature flag bắt buộc: `booking_agent_enabled` để bật tắt toàn bộ luồng agent và trả về form cũ, `advisory_enabled` riêng cho F10, `zalo_reminders_enabled`, và `vip_approval_enabled`.

Về A/B test, chỉ chạy khi đã có đủ lưu lượng. Thử nghiệm thứ nhất so nhịp nhắc hai tin với ba tin, giả thuyết là ba tin tăng show-rate mà không tăng tỷ lệ tắt nhận tin, quyết định dựa trên M1 tăng trong khi G1 và G2 không vượt ngưỡng. Thử nghiệm thứ hai so có với không có F10 ở điểm vào, giả thuyết là tư vấn trước làm tăng tỷ lệ hoàn tất đặt lịch, đo bằng M2 và M8. Thử nghiệm thứ ba so thời hạn giữ chỗ 2 phút với 5 phút, giả thuyết là thời hạn dài giảm tỷ lệ rớt ở bước điền thông tin mà chưa làm giảm suất khả dụng, đo bằng M2 tăng và tỷ lệ `hold_expired` giảm; việc này gắn với OQ-2.

### 8.3 Migration dữ liệu

Đây là sản phẩm mới nên không có dữ liệu lịch sử cần migrate. Nhưng cần chuẩn bị bốn nhóm dữ liệu nền trước khi thí điểm: danh mục showroom kèm địa chỉ, toạ độ và giờ mở cửa; danh mục xe demo theo từng showroom gồm mẫu, phiên bản, biển số, trạng thái và ngưỡng pin; lịch làm việc tư vấn viên để sinh khung suất; và knowledge base cho F10 theo mục 4.4.5.

### 8.4 Kế hoạch UAT

| Nhóm nghiệm thu | Kịch bản bắt buộc |
|---|---|
| Khách tự đặt (P1) | Đặt trọn luồng, nhận mã lịch, nhận nhắc, tự hủy, rồi xác nhận không có ai gọi lại |
| Khách đặt hộ (P2) | Đặt cho người khác, người lái nhận link riêng và tự xác nhận, rồi check-in bằng tên người lái |
| Người ngại công nghệ (P3) | Tìm được lối thoát về người thật ở mọi bước |
| Tư vấn viên (P4) | Nhận handoff giữ nguyên ngữ cảnh, không phải hỏi lại khách |
| Quản lý (P5) | Duyệt và từ chối khung VIP, đọc dashboard, xác nhận không có trùng lịch |
| QA | Toàn bộ AC ở mục 4.3 và 4.4, cùng 20 edge case ở mục 4.5 |

Tiêu chí đạt gồm bốn điều: 100% acceptance criteria của story P0 pass; M4 bằng 0 trong toàn bộ UAT; không có lỗi bảo mật thuộc nhóm NFR ở mục 5.2; và G6, tức tỷ lệ bịa đặt của F10, không quá 2% trên bộ eval.

### 8.5 Tài liệu và đào tạo

Tư vấn viên cần tài liệu về cách nhận handoff, đọc ngữ cảnh và đặc biệt là không gọi lại khách đã hủy. Quản lý showroom cần tài liệu về duyệt khung VIP, đọc dashboard và cập nhật trạng thái xe demo. Lễ tân cần tài liệu về màn hình check-in và cách tra cứu bằng cả tên người đặt lẫn tên người lái. Đội kỹ thuật đã có một phần tài liệu qua README và RUN_LOCAL, còn thiếu tài liệu vận hành và xử lý sự cố.

Điểm đào tạo quan trọng nhất, phải nhấn mạnh với mọi nhân viên: khách đã bấm hủy thì không được gọi lại để tư vấn thêm. Hành vi này phá thẳng lời hứa lõi của sản phẩm, và chính nó đã đẩy anh Duy đi ở E10.

### 8.6 Truyền thông tới người dùng

Trên website đặt banner tại trang xe với thông điệp đặt lịch lái thử được xác nhận ngay trong ba phút. Trên Zalo OA gửi tin giới thiệu cho khách đã có lịch sử tương tác. Tại showroom đặt standee hướng dẫn quét mã đặt lịch. Với nhân viên, chuẩn bị kịch bản giới thiệu ngắn để dùng khi khách gọi hotline.

---

## 9. Rủi ro, giả định và câu hỏi mở

### 9.1 Giả định

| Mã | Giả định | Mức rủi ro | Cách kiểm chứng |
|---|---|---|---|
| A1 | Khách Việt chịu đặt lái thử qua AI hội thoại thay vì gọi hoặc nhắn người thật, và tỷ lệ no-show cao chủ yếu đến từ ma sát khi đặt lịch chứ không phải vì ý định vốn thấp | Rất cao, đây là giả định rủi ro nhất của cả dự án | Dữ liệu từ thí điểm. Bằng chứng hiện có ở ca anh Duy nghiêng về cả hai: ý định vốn không cao (70%), nhưng chính trải nghiệm bất định kéo nó xuống 20% |
| A2 | Showroom có sẵn dữ liệu xe demo và lịch tư vấn viên đủ chính xác để truy vấn thời gian thực | Cao | DEP-1, DEP-2 |
| A3 | Tư vấn viên chấp nhận để agent tham gia vào việc sắp lịch của mình | Cao | Chưa phỏng vấn P4 và P5 |
| A4 | Persona P3 ngại công nghệ sẽ dùng được sản phẩm nếu có lối thoát về người thật | Trung bình | Chưa phỏng vấn |
| A5 | Zalo là kênh nhắc hiệu quả nhất | Thấp | Cả ba người phỏng vấn đều xác nhận |
| A6 | Nhịp ba tin nhắc là đủ và không gây phiền | Trung bình | A/B test kèm guardrail G1 và G2 |
| A7 | Knowledge base tĩnh đủ trả lời phần lớn câu hỏi tư vấn | Trung bình | Đo tỷ lệ "không biết" của F10 sau thí điểm |

Giả định A1 có một hàm ý quan trọng cho sản phẩm. Vì câu trả lời nghiêng về "cả hai", ta phải vừa giảm ma sát bằng cơ chế đổi hủy một chạm, vừa tăng cam kết bằng lời nhắc cụ thể rằng xe đã sẵn sàng. Không được chọn một trong hai.

### 9.2 Rủi ro và phương án giảm thiểu

| Mã | Rủi ro | Ảnh hưởng | Khả năng | Giảm thiểu |
|---|---|---|---|---|
| R-01 | Dữ liệu xe demo không cập nhật thật, agent hứa có xe nhưng tới nơi không có | Chí mạng. Theo E18 thì việc này còn tệ hơn gọi sales vì khách không biết trách ai | Cao | Không phát hành khi chưa có DEP-1. Ràng buộc pin và tồn kho ở tầng dữ liệu. Cảnh báo sớm khi xe đổi trạng thái (EC-05) |
| R-02 | ViVi bịa thông số, giá hoặc chính sách | Cao, vừa là rủi ro pháp lý vừa mất niềm tin | Cao nếu phát hành F10 mà chưa có RAG thật | R-T1 và R-T2, kèm bộ eval và guardrail G6. Thà nói không biết còn hơn đoán |
| R-03 | Nhân viên showroom né hệ thống và quay lại chốt lịch tay | Cao, sản phẩm thành vô nghĩa | Trung bình | Phỏng vấn P4 và P5 trước khi thiết kế màn hình nội bộ, kèm đào tạo. Đo tỷ lệ lịch tạo ngoài hệ thống |
| R-04 | Nhân viên gọi lại khách đã hủy | Cao, phá lời hứa lõi (E10) | Trung bình | R-N4 chặn ở tầng hệ thống, kèm đào tạo và guardrail G3 |
| R-05 | Không có bản Figma hi-fi nên giao diện dễ trôi dạt và khó nghiệm thu thiết kế | Trung bình | Đang xảy ra | Chốt một trong hai hướng: hoặc dựng Figma, hoặc lấy bản đang chạy làm chuẩn rồi viết design tokens |
| R-06 | Chi phí LLM và tin nhắn vượt ngân sách | Trung bình | Trung bình | Guardrail G4. Định tuyến ý định bằng model rẻ trước khi gọi LLM lớn. Luồng nút không tốn LLM |
| R-07 | Rò rỉ PII hoặc giấy phép lái xe qua log và prompt | Cao, rủi ro pháp lý | Thấp vì đã có cơ chế | Yêu cầu ở mục 5.2, guardrail G8, kiểm thử bảo mật trước phát hành |
| R-08 | Kết luận sản phẩm dựa trên mẫu n bằng 3 | Trung bình | Đang xảy ra | Mở rộng phỏng vấn (DEP-12). Ghi rõ giới hạn ở mọi tài liệu |
| R-09 | Thời hạn giữ chỗ 2 phút quá ngắn, khách rớt ở bước điền thông tin | Trung bình | Trung bình đến cao | Đo tỷ lệ `hold_expired`. Chạy A/B test 2 phút với 5 phút (OQ-2) |
| R-10 | Phụ thuộc một nhà cung cấp LLM | Trung bình | Trung bình | Luồng nút đã độc lập với LLM. Thiết kế cho phép đổi nhà cung cấp |
| R-11 | Nút Hủy quá dễ làm tăng hủy sát giờ | Thấp đến trung bình | Thấp | Guardrail G5. Dù sao hủy sát giờ vẫn tốt hơn no-show im lặng, vì ít nhất còn giải phóng được chỗ |

### 9.3 Câu hỏi mở

Mỗi câu hỏi phải có người trả lời và hạn cụ thể, nếu không nó sẽ nằm im tới lúc sprint bắt đầu.

| Mã | Câu hỏi | Người trả lời | Hạn | Chặn việc gì |
|---|---|---|---|---|
| OQ-1 | Có áp cơ chế giữ chỗ có điều kiện hoặc cọc nhẹ hoàn lại để tăng cam kết không? Câu này liên quan trực tiếp tới giả định A1 | PO, mentor, nghiệp vụ | Trước Phase 3 | Chiến lược giảm no-show |
| OQ-2 | Thời hạn giữ chỗ nên là bao lâu? Code hiện cố định 120 giây trong khi Concept Spec đề xuất 15 phút, chênh nhau rất xa. Có cấu hình theo showroom không? | PO, backend, vận hành | Trước thí điểm | R-B3 và rủi ro R-09 |
| OQ-3 | Ngưỡng pin tối thiểu để mở suất và để cho lái thử là bao nhiêu? | Vận hành showroom | Trước thí điểm | R-X3 |
| OQ-4 | Chính sách lưu và xóa giấy phép lái xe ra sao: giữ bao lâu, ai được xem, xóa tự động khi nào? | Pháp chế | Trước v1.1 | Yêu cầu ở mục 5.3 và UX copy |
| OQ-5 | Nếu người lái không xác nhận trước giờ hẹn thì có chặn lái không, hay cho check-in bằng bản gốc? | PO và vận hành | Trước Phase 2 | EC-03 |
| OQ-6 | Kênh ưu tiên cho bản tiếp theo là web hay Zalo OA? Người dùng nghiêng về Zalo | PO và mentor | Trước Phase 3 | Phạm vi Phase 3 |
| OQ-7 | Nhóm có được cấp quyền truy cập dữ liệu và khách thật của một showroom không? | Mentor và VinFast | Càng sớm càng tốt | Toàn bộ kế hoạch thí điểm và mọi baseline |
| OQ-8 | Nguồn nội dung chính thống cho knowledge base F10 lấy từ đâu, ai duyệt, cập nhật thế nào? | PO, phía VinFast cung cấp | Trước v1.1 | Toàn bộ F10 |
| OQ-9 | Khung giờ nào được coi là VIP hoặc đặc biệt cần quản lý duyệt tay? | Quản lý showroom | Trước Phase 2 | R-H2 |
| OQ-10 | Chọn nền tảng analytics nào? | PO và kỹ thuật | Trước v1.1 | Toàn bộ mục 2.4 và 2.5 |

---

## 10. Timeline và milestone

Mốc thời gian tính theo tuần kể từ ngày phê duyệt PRD. Ngày cụ thể chốt sau khi có câu trả lời cho OQ-7, vì quyền truy cập dữ liệu showroom quyết định toàn bộ lịch thí điểm.

| Mốc | Nội dung | Điều kiện hoàn thành | Dự kiến |
|---|---|---|---|
| M0. PRD approved | PRD v1.0 được mentor và đội kỹ thuật duyệt | Không còn câu hỏi chặn P0 | Tuần 0 |
| M1. Design freeze | Chốt màn hình M6 link người lái, M8 mẫu nhắc, M12 tư vấn; chốt UX copy ở mục 6.4 | Sau mốc này không đổi thiết kế nếu không qua change request | Tuần 2 |
| M2. Knowledge base ready | Nội dung F10 đã thu thập, làm sạch và index xong | OQ-8 đã trả lời, bộ eval có ít nhất 50 câu hỏi | Tuần 3 |
| M3. Dev complete v1.1 | Toàn bộ phần P0 còn thiếu đã code xong | Mọi acceptance criteria của story P0 đều có test | Tuần 6 |
| M4. Code freeze | Ngừng thêm tính năng, chỉ sửa lỗi | Không còn lỗi P0 hoặc P1 đang mở | Tuần 7 |
| M5. UAT | Nghiệm thu theo mục 8.4 | 100% AC của P0 pass, M4 bằng 0, G6 không quá 2% | Tuần 8 |
| M6. Pilot release | Thí điểm một showroom sau feature flag | Đã đào tạo nhân viên, analytics đã chạy | Tuần 9 |
| M7. Baseline đo được | Có số thật cho M1, M2, M3, M6 | Ít nhất 2 tuần dữ liệu thí điểm | Tuần 11 |
| M8. Go hoặc No-go mở rộng | Quyết định nhân rộng | Không guardrail nào chạm ngưỡng đỏ, M4 bằng 0 | Tuần 12 |

Đường găng của kế hoạch đi từ OQ-7 (quyền truy cập dữ liệu showroom) sang DEP-1 (tồn kho xe demo) rồi tới M6. Nếu OQ-7 không được duyệt, kế hoạch chuyển sang thí điểm mô phỏng với dữ liệu giả, và khi đó mọi chỉ số ở mục 2.4 không được coi là đã kiểm chứng.

---

## 11. Phụ lục

### 11.1 Kết quả research đã dùng

Về định tính, nhóm có ba bản chép phỏng vấn đầy đủ: anh Nguyên dài 22 phút 32 giây, anh Duy dài 28 phút 36 giây và chị Vy dài 29 phút 08 giây. Cả ba nằm trong file `docs/docs/User Empathy, Spec and PRD.pdf`, mục "ITVer 1/2/3".

Kịch bản phỏng vấn đã dùng gồm bảy chặng từ T1 đến T7 và bảy nguyên tắc hỏi: hỏi chuyện đã xảy ra chứ không hỏi giả định, không dẫn dắt, mỗi câu chỉ một ý, đào "vì sao" hai đến ba lần, dùng im lặng như một công cụ, không bán hàng và không thanh minh cho sản phẩm, và ghi nguyên văn những câu cảm xúc mạnh.

Về định lượng thứ cấp, nhóm dùng 10 phát hiện từ R1 đến R10 với nguồn ghi rõ ở mục 1.3.B.

### 11.2 Phân tích đối thủ

Mazda với mẫu CX-5 làm tốt hơn ở chỗ họ gọi xác nhận một lần và khi khách tới nơi thì có xe sẵn. Chị Vy kể rằng chồng chị vì thế mà có thiện cảm hơn, và kết quả là VF 7 bị đẩy xuống sau. Hyundai với mẫu Creta thì hưởng lợi từ việc anh Duy chuyển hướng sau trải nghiệm tồi (E14).

Điều đáng suy nghĩ là đối thủ không thắng bằng công nghệ, họ thắng bằng việc giữ đúng lời hứa. Gọi xác nhận một lần và có xe sẵn khi khách tới, chỉ vậy thôi. Đây vừa là tin xấu vì rào cản cạnh tranh rất thấp, vừa là tin tốt vì ta hoàn toàn có thể vượt lên bằng cách làm đúng những điều cơ bản, ở quy mô lớn hơn và nhất quán hơn.

### 11.3 Bảng thuật ngữ

| Thuật ngữ | Nghĩa |
|---|---|
| Booking | Một buổi hẹn lái thử, tức cam kết cụ thể về việc ai lái, xe gì, ở đâu, lúc nào. Đây là concept xương sống của sản phẩm |
| Slot, hay suất lái thử | Tổ hợp gồm showroom, khung giờ và một xe demo cụ thể theo phiên bản. Còn chỗ với sales mà không có xe đúng bản thì không phải là suất hợp lệ |
| Hold, hay giữ chỗ | Trạng thái tạm giữ một suất có thời hạn, chống người khác giành trong lúc khách điền thông tin |
| Người đặt (booker) | Người khởi tạo và theo dõi booking, có thể không phải người lái |
| Người lái (driver) | Người thật sự cầm lái. Ràng buộc giấy phép lái xe gắn vào đây chứ không gắn vào người đặt |
| GPLX | Giấy phép lái xe, thuộc nhóm dữ liệu nhạy cảm |
| No-show | Khách có lịch đã xác nhận nhưng không đến và cũng không báo |
| Show-rate | Tỷ lệ khách đến thật trên số lịch đã xác nhận, đây là chỉ số North Star M1 |
| HITL | Human-in-the-loop, tức đưa người thật vào đúng lúc cần, để tư vấn sâu hoặc duyệt khung đặc biệt |
| Double-booking | Hai booking cùng chiếm một suất. Ràng buộc cứng là con số này phải bằng 0 |
| Khóa giao dịch | Cơ chế database quyết định ai giữ chỗ trước khi có tranh chấp |
| Idempotency | Gửi cùng một yêu cầu nhiều lần chỉ tạo ra một kết quả, dùng để chống double-click và mạng chập chờn |
| Guardrail metric | Chỉ số bảo vệ, ngăn việc tối ưu một số làm hỏng số khác |
| JTBD | Jobs-to-be-Done, tức công việc thật mà người dùng cần hoàn thành |
| RAG | Retrieval-Augmented Generation, tức LLM trả lời dựa trên tài liệu truy xuất được thay vì dựa vào trí nhớ nội tại |
| ViVi | Tên gọi trợ lý AI của sản phẩm |
| B2B2C | Mô hình mà hãng hoặc showroom trả tiền (Customer), còn khách và nhân viên mới là người dùng thật (User) |

### 11.4 Ma trận truy vết

Bảng này đảm bảo mọi tính năng đều bắt nguồn từ một nỗi đau thật, và ngược lại, mọi nỗi đau lớn đều có tính năng phụ trách. Nếu một tính năng không nối được về cột trái thì cần cân nhắc bỏ.

| Nỗi đau hoặc nhu cầu | Bằng chứng | Tính năng | Quy tắc | Chỉ số |
|---|---|---|---|---|
| Chọn giờ nhưng chỉ nhận "đã tiếp nhận" | E1, E2 | F2, F4 | R-S1, R-B4 | M2, M3 |
| Chờ xác nhận vô định, hết chỗ mới báo sau | E9, R3 | F6 | R-A1, R-A2 | M2 |
| Ngại hủy nên no-show im lặng, rồi bị truy theo | E3, E10 | F5 | R-N4 | M5, M6 |
| Web, SMS và sales lệch giờ nhau, nhắc nhầm người | E8 | F4 | R-B6, R-N1 | M1 |
| Đặt hộ nhưng liên hệ dồn về người đặt, người lái vô hình | E5, E6 | F3 | R-K2, R-D4 | M1, M7 |
| Lộ giấy phép lái xe qua Zalo cá nhân | E7 | F3 | R-G1, R-G2 | G8 |
| Tới nơi như không có lịch, sai phiên bản hoặc pin yếu | E5, E9 | F7, F2 | R-D4, R-X1, R-X3 | M7 |
| Cần hỏi sâu về pin, vay, bảo hiểm | E17 | F8, F10.5 | R-H1, R-T4 | Tải HITL |
| Ý định tụt vì không được nhắc | E12, R2, R8 | F4 | R-N1, R-N2 | M1 |
| Trùng lịch, đây là nỗi đau doanh nghiệp | Đề bài | F2 | R-B2, R-S1 | M4 |
| Không biết chọn xe nào, cần được giải đáp | E15, E16 | F10.1 đến F10.3 | R-T1, R-T2 | M8 |
| Bị đẩy chốt khi mới đang tìm hiểu | E11 | Ràng buộc của F10 | R-T3 | G2 |

### 11.5 Cách mỗi vai đọc tài liệu này

Dev đọc mục 4.2 để suy ra data model và bảng chuyển trạng thái, mục 4.3 và 4.4 để lấy acceptance criteria, mục 5 cho yêu cầu phi chức năng, và mục 7 cho phụ thuộc.

QA đọc mục 4.3 và 4.4 vì acceptance criteria chính là test case, mục 4.5 cho edge case, mục 8.4 cho kế hoạch nghiệm thu, và mục 4.2 làm danh mục kiểm thử theo mã quy tắc.

Design đọc mục 3 để hiểu persona và hành trình, mục 6 cho màn hình, trạng thái và UX copy, và mục 4.5 cho các error state.

Vận hành showroom đọc mục 3.1 phần P4 và P5, mục 8.5 về đào tạo, và mục 4.2 để nắm những quy tắc ảnh hưởng tới công việc hằng ngày.

Mentor và người phê duyệt đọc mục 1 cho bằng chứng, mục 2 cho mục tiêu và chỉ số, mục 9 cho rủi ro và câu hỏi mở, mục 10 cho timeline.

---

Có một nguyên tắc xuyên suốt cả dự án, và nó đáng được nhắc lại ở cuối tài liệu này: đừng nhảy sang giai đoạn xây khi giai đoạn kiểm chứng chưa trả lời được giả định rủi ro nhất. Xây sớm quá thì rất dễ ra một sản phẩm mượt mà nhưng lại chữa nhầm bệnh.

Bản MVP hiện tại được dựng để kiểm chứng luồng và trải nghiệm, không phải để phát hành ngay. Giả định A1 và câu hỏi OQ-7 vẫn đang mở, và chính hai thứ đó quyết định sản phẩm này có chữa đúng bệnh hay không.

---

*PRD v1.0, dự án P-053, ngày 13/08/2026, Nguyễn Hoàng Minh (Product Owner).*
