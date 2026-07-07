# STAKEHOLDER REGISTER

| Role | Quyền lực (H/L) | Quan tâm (H/L) | Chiến lược tiếp cận |
|------|------------------|-----------------|----------------------|
| Giám thị coi thi | L | H | Thông báo quy trình mới, thu thập phản hồi về khả năng thực thi sau mỗi kỳ thi |
| Thí sinh dự thi | L | H | Gửi hướng dẫn sử dụng, kênh tiếp nhận khiếu nại kỳ thi |
| Quản trị viên hệ thống | H | H | Họp định kỳ về cấu hình, cần sign-off trước mỗi mùa thi |
| Cán bộ quản lý kỳ thi (phòng Đào tạo/TC) | H | Conway's Law | Phê duyệt quy trình nghiệp vụ, báo cáo tiến độ trước mỗi giai đoạn then chốt |
| Kỹ thuật viên IT hỗ trợ | L | L | Theo dõi log vận hành, chủ động liên hệ khi có sự cố |

---

# ELICITATION SUMMARY

## Mục tiêu nghiệp vụ
- **Vấn đề hiện tại**: Quy trình tổ chức kỳ thi thủ công, thiếu tập trung, dễ sai sót trong khâu điều phối
- **Kết quả mong muốn**: Số hóa toàn bộ vòng đời kỳ thi từ khâu chuẩn bị đến kết thúc
- **GHI CHÚ**: Không có chỉ tiêu định lượng trong yêu cầu → *Câu hỏi còn mở*

## Đối tượng người dùng

| Nhóm | Đặc điểm chính |
|------|----------------|
| Cán bộ quản lý kỳ thi | Số lượng: ít (2-5 người); am hiểu công nghệ trung bình; chủ yếu desktop |
| Giám thị coi thi | Số lượng: nhiều, thay đổi theo kỳ; đa dạng trình độ công nghệ; cần mobile/tablet tại phòng thi |
| Thí sinh dự thi | Số lượng: lớn; độ tuổi đa dạng; chủ yếu mobile để tra cứu, có thể desktop để đăng ký |
| Quản trị viên hệ thống | 1-2 người; chuyên môn kỹ thuật cao; desktop |

## Tính năng cốt lõi
*(Ưu tiên ước lượng dựa trên tần suất nhắc đến trong yêu cầu — yêu cầu rất ngắn, phân loại theo mức độ hiển nhiên)*

1. **Tạo và cấu hình kỳ thi** — thiết lập thông tin cơ bản (tên, thời gian, địa điểm)
2. **Quản lý danh sách thí sinh** — nhập/xuất, phân phòng thi
3. **Phân công giám thị** — gán giám thị theo ca/địa điểm
4. **Tra cứu thông tin kỳ thi** — thí sinh xem lịch, phòng, kết quả
5. **Ghi nhận điểm số** — nhập điểm sau kỳ thi
6. **Xuất báo cáo tổng hợp** — thống kê kỳ thi

## Ràng buộc

| Nhóm | Chi tiết |
|------|----------|
| **Thời gian** | Không đề cập |
| **Công nghệ** | Không đề cập |
| **Ngân sách** | Không đề cập |
| **Pháp lý/Tuân thủ** | Không đề cập *(suy luận: cần rà soát quy định bảo mật điểm thi, quyền riêng tư thí sinh)* |

## Câu hỏi còn mở

| Câu hỏi | Lý do cần làm rõ | Ảnh hưởng nếu không trả lời |
|---------|------------------|------------------------------|
| Quy mô kỳ thi: số thí sinh tối đa, số kỳ thi/năm? | Xác định kiến trúc chịu tải, phân vùng dữ liệu | Thiết kế không đáp ứng mùa cao điểm |
| Có cần tích hợp hệ thống Đào tạo hiện có (SSO, đồng bộ sinh viên)? | Ảnh hưởng phạm vi tích hợp, nhập liệu thủ công hay tự động | Lặp công nhập liệu, sai sót dữ liệu |
| Yêu cầu xác thực danh tính thí sinh như thế nào? | Quyết định quy trình đăng nhập, tra cứu kết quả | Rủi ro bảo mật, lộ điểm thi |
| Có cần tính năng chấm thi trực tuyến hay chỉ nhập điểm offline? | Phân biệt module cần xây dựng | Phạm vi dự án phình to hoặc thiếu chức năng |
| Loại hình kỳ thi: trắc nghiệm, tự luận, hay hỗn hợp? | Ảnh hưởng cách tổ chức phòng thi, chấm điểm | Không phù hợp quy trình thực tế |
| Có yêu cầu pháp lý/bảo mật đặc thù (GDPR, Thông tư Bộ GD&ĐT)? | Tuân thủ quy định lưu trữ, truy cập dữ liệu | Vi phạm pháp luật, rủi ro kiện tụng |
| Ngân sách và timeline dự kiến? | Lập kế hoạch phát triển, ưu tiên tính năng | Không khả thi về mặt triển khai |
| "Đơn giản" được định nghĩa như thế nào — MVP gồm những gì? | Phân biệt must-have vs nice-to-have | Phạm vi không rõ, tranh cãi khi bàn giao |