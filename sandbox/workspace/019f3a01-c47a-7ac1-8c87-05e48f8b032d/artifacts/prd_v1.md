# STAKEHOLDER REGISTER

| Role | Quyền lực (H/L) | Quan tâm (H/L) | Chiến lược tiếp cận |
|------|------------------|-----------------|----------------------|
| Giáo viên/Cán bộ coi thi | H | H | Họp xác nhận quy trình tạo đề và chấm điểm, cần sign-off trước khi triển khai |
| Học sinh/Sinh viên thi | L | H | Khảo sát UX sau mỗi phiên bản thử nghiệm, thu thập phản hồi về trải nghiệm làm bài |
| Quản trị viên hệ thống trường học | H | L | Báo cáo định kỳ về tình trạng vận hành, cần thông báo trước khi bảo trì |
| Nhân viên kỹ thuật IT trường | L | L | Theo dõi qua ticket hỗ trợ, chủ động liên hệ khi có lỗi nghiêm trọng |
| Ban giám hiệu/Phòng đào tạo | H | H | Trình bày KPI đánh giá hiệu quả kỳ thi, cần phê duyệt ngân sách và phạm vi |

---

# ELICITATION SUMMARY

## Mục tiêu nghiệp vụ
- **Vấn đề**: Quy trình tổ chức kỳ thi thủ công (tạo đề, in ấn, chấm điểm, lưu trữ) tốn nhiều thời gian và dễ sai sót
- **Kết quả mong muốn**: Đơn giản hóa toàn bộ quy trình quản lý kỳ thi trên một ứng dụng thống nhất
- ⚠️ **Chưa có mục tiêu định lượng** → xem "Câu hỏi còn mở"

## Đối tượng người dùng
| Nhóm | Đặc điểm chính |
|------|----------------|
| Giáo viên ra đề/chấm điểm | Số lượng chưa rõ; am hiểu công nghệ trung bình; chủ yếu desktop |
| Học sinh/Sinh viên dự thi | Số lượng chưa rõ; am hiểu công nghệ cao (Gen Z); desktop và mobile |
| Quản trị viên/IT trường | Ít người; am hiểu công nghệ cao; desktop |

## Tính năng cốt lõi
*(Ưu tiên ước lượng dựa trên mức độ cốt lõi của "quản lý kỳ thi đơn giản")*

1. **Tạo và lưu trữ đề thi** — biên soạn câu hỏi, tổ chức thành đề, lưu ngân hàng đề
2. **Tổ chức phát đề thi** — gán đề cho ca thi, phân phối đến người dự thi
3. **Làm bài thi** — người dự thi truy cập và hoàn thành bài trong khung thời gian
4. **Chấm điểm và cho điểm** — tính điểm tự động (nếu trắc nghiệm) hoặc hỗ trợ chấm thủ công
5. **Xem kết quả và báo cáo** — hiển thị điểm, thống kê kỳ thi cho giáo viên và học sinh
6. **Quản lý danh sách người dự thi** — nhập/xuất danh sách, phân ca thi *(suy luận từ yêu cầu "quản lý kỳ thi")*

## Ràng buộc

| Nhóm | Chi tiết |
|------|----------|
| **Thời gian** | Không đề cập |
| **Công nghệ** | Không đề cập nền tảng bắt buộc; không đề cập tích hợp hệ thống cũ |
| **Ngân sách** | Không đề cập |
| **Pháp lý/Tuân thủ** | Không đề cập; suy luận: cần đảm bảo tính toàn vẹn dữ liệu điểm, chống gian lận thi |

## Câu hỏi còn mở

| Câu hỏi | Lý do cần làm rõ | Ảnh hưởng nếu không trả lời |
|---------|------------------|------------------------------|
| Quy mô kỳ thi: bao nhiêu người dự thi đồng thời tối đa? | Ảnh hưởng thiết kế NFR hiệu năng | Không thể đánh giá khả năng chịu tải |
| Loại hình câu hỏi chỉ trắc nghiệm hay có tự luận? | Quyết định quy trình chấm điểm | Ảnh hưởng module chấm điểm và UX làm bài |
| Có cần giám sát chống gian lận (camera, chống copy) không? | Yêu cầu tuân thủ và bảo mật | Có thể thiếu tính năng cần thiết cho kỳ thi nghiêm túc |
| Yêu cầu triển khai on-premise hay cloud? | Ràng buộc kỹ thuật và bảo mật | Ảnh hưởng kiến trúc triển khai |
| Có tích hợp với hệ thống LMS/SIS hiện có không? | Phạm vi tích hợp | Có thể cần làm lại nếu bỏ qua |
| Thời hạn mong muốn đưa vào sử dụng? | Lập kế hoạch phát triển | Không thể ước lượng timeline hợp lý |
| Ngân sách dự kiến hoặc ràng buộc thương mại? | Phạm vi MVP vs full feature | Nguy cơ over-engineering hoặc thiếu tính năng |
| Có yêu cầu xuất báo cáo theo mẫu cụ thể của trường/Bộ không? | Tuân thủ quy định | Có thể không đáp ứng được quy trình báo cáo hiện tại |