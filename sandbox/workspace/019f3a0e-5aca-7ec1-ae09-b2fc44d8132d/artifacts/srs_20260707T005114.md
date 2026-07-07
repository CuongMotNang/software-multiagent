# STAKEHOLDER REGISTER

| Role | Quyền lực (H/L) | Quan tâm (H/L) | Chiến lược tiếp cận |
|------|------------------|-----------------|----------------------|
| Giáo viên/Cán bộ coi thi | H | H | Họp xác nhận quy trình ra đề và chấm thi, cần sign-off trước khi triển khai thử nghiệm |
| Thí sinh | L | H | Khảo sát UX sau mỗi kỳ thi, thu thập phản hồi qua form ngắn |
| Quản trị viên hệ thống | H | L | Báo cáo định kỳ cuối tuần, chỉ escalate khi có vấn đề kỹ thuật nghiêm trọng |
| Ban giám hiệu/Quản lý đơn vị tổ chức thi | H | H | Duyệt báo cáo tổng kết kỳ thi, cần approval trước mỗi đợt thi chính thức |
| Nhân viên kỹ thuật hỗ trợ thi | L | H | Thông báo lịch cập nhật hệ thống, hỗ trợ kịch bản xử lý sự cố |

---

# ELICITATION SUMMARY

- **Mục tiêu nghiệp vụ**
  - Đơn giản hóa quy trình tổ chức và quản lý kỳ thi (hiện tại chưa rõ quy trình thủ công đang gặp vấn đề gì cụ thể)
  - Giảm thiểu sai sót trong khâu tổ chức thi và lưu trữ kết quả
  - *Cờ câu hỏi mở: Chưa có mục tiêu định lượng (VD: giảm bao nhiêu % thời gian, chi phí)*

- **Đối tượng người dùng**

  | Nhóm người dùng | Đặc điểm chính |
  |-----------------|---------------|
  | Giáo viên/Cán bộ coi thi | Số lượng chưa rõ; am hiểu công nghệ trung bình; chủ yếu desktop để ra đề/chấm điểm, có thể mobile để giám sát |
  | Thí sinh | Số lượng chưa rõ; am hiểu công nghệ cao; chủ yếu mobile/tablet để làm bài, có thể desktop |
  | Quản trị viên hệ thống | Ít người (suy luận từ "đơn giản"); am hiểu công nghệ cao; desktop |
  | Ban giám hiệu/Quản lý | Số lượng ít; am hiểu công nghệ thấp-trung bình; desktop để xem báo cáo |

- **Tính năng cốt lõi** (theo độ ưu tiên ước lượng)

  1. **Tạo và quản lý đề thi** — soạn câu hỏi, lập đề, lưu ngân hàng đề
  2. **Lên lịch tổ chức kỳ thi** — đặt thời gian, địa điểm, gán giám thị
  3. **Đăng ký và xếp phòng thi** — quản lý danh sách thí sinh, phân phòng
  4. **Tổ chức thi trực tuyến hoặc giám sát thi** — *(chưa rõ hình thức: online/offline/hybrid)*
  5. **Chấm điểm và công bố kết quả** — nhập điểm, tính điểm tự động (nếu có), xuất bảng điểm
  6. **Lưu trữ và tra cứu kết quả** — lịch sử kỳ thi, báo cáo thống kê

- **Ràng buộc**

  | Nhóm | Chi tiết |
  |------|----------|
  | Thời gian | Không đề cập |
  | Công nghệ | Không đề cập (không rõ nền tảng di động/web/desktop; không rõ tích hợp hệ thống cũ) |
  | Ngân sách | Không đề cập |
  | Pháp lý/Tuân thủ | Không đề cập (suy luận: cần rà soát quy định bảo mật điểm thi, quyền riêng tư thí sinh nếu áp dụng cho giáo dục chính quy) |

- **Câu hỏi còn mở**

  | Câu hỏi | Lý do cần làm rõ | Ảnh hưởng nếu không trả lời |
  |---------|------------------|------------------------------|
  | Hình thức thi là online, offline hay hybrid? | Quyết định toàn bộ luồng nghiệp vụ giám sát và chống gian lận | Thiết kế sai phạm vi tính năng, lãng phí công sức |
  | Quy mô: số lượng thí sinh, số kỳ thi/năm, số môn thi? | Ảnh hưởng đến phân tích NFR hiệu năng và khả năng mở rộng | Thiết kế không đáp ứng tải thực tế hoặc dư thừa quá mức |
  | Có cần tích hợp với hệ thống quản lý học tập (LMS) hay CSDL sinh viên hiện có? | Quyết định phạm vi tích hợp và nhập liệu | Làm lại module đồng bộ dữ liệu, tăng chi phí |
  | Ai được phép xem/chỉnh sửa điểm? Phân quyền chi tiết? | Ảnh hưởng đến thiết kế phân quyền và audit trail | Lỗ hổng bảo mật hoặc thiếu truy xuất nguồn gốc |
  | Có cần chấm tự động (trắc nghiệm) hay chỉ chấm thủ công/tự luận? | Ảnh hưởng đến module chấm điểm | Thiếu hoặc thừa tính năng chấm điểm |
  | Yêu cầu báo cáo/thống kê cụ thể? | Ảnh hưởng đến module báo cáo | Không đáp ứng nhu cầu quản lý của lãnh đạo |
  | Ràng buộc pháp lý/bảo mật đặc thù ngành giáo dục? | Ảnh hưởng đến thiết kế bảo mật và lưu trữ | Vi phạm quy định, rủi ro pháp lý |
  | Ngân sách và timeline dự kiến? | Ảnh hưởng đến phạm vi MVP và lộ trình phát triển | Phạm vi tràn lan hoặc cắt giảm không đúng chỗ |