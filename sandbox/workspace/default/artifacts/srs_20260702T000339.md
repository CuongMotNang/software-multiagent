**STAKEHOLDER REGISTER**

| Role                     | Quyền lực (H/L) | Quan tâm (H/L) | Chiến lược tiếp cận                              |
|--------------------------|----------------|----------------|---------------------------------------------------|
| Khách hàng / Product Owner| H              | H              | Workshop chi tiết, demo prototype, cập nhật tiến độ thường xuyên |
| Người dùng cuối (End‑user) | L              | H              | Thu thập nhu cầu qua khảo sát, test người dùng, phản hồi liên tục |
| Nhóm phát triển (Dev)    | H              | L              | Sprint planning, backlog grooming, tài liệu kỹ thuật rõ ràng |
| Quản lý dự án (PM)        | H              | H              | Báo cáo tiến độ, quản lý rủi ro, điều chỉnh scope khi cần |
| QA / Tester               | L              | H              | Kế hoạch test case, môi trường kiểm thử sớm, feedback nhanh |
| Bộ phận pháp lý / Bảo mật | L              | L              | Kiểm tra tuân thủ luật dữ liệu (GDPR/PDPA), chính sách bảo mật |

---

**ELICITATION SUMMARY**

- **Mục tiêu nghiệp vụ:**  
  - Cung cấp một ứng dụng chat đơn giản, dễ sử dụng để người dùng có thể gửi/nhận tin nhắn văn bản theo thời gian thực.

- **Đối tượng người dùng:**  
  - Người dùng cá nhân muốn trao đổi tin nhắn nhanh chóng (độ tuổi 18‑45).  
  - Nhóm nhỏ, cộng đồng hoặc doanh nghiệp muốn một công cụ chat nội bộ không phức tạp.

- **Tính năng cốt lõi:**  
  - Đăng ký / đăng nhập (email hoặc số điện thoại).  
  - Gửi và nhận tin nhắn văn bản theo thời gian thực.  
  - Danh sách bạn bè / danh bạ.  
  - Thông báo đẩy (push notification) khi có tin mới.  
  - Lưu trữ lịch sử trò chuyện (có thể xóa).  

- **Ràng buộc:**  
  - Thời gian triển khai: **8‑10 tuần** (phân chia thành 2‑3 sprint).  
  - Công nghệ đề xuất: Front‑end React Native / Flutter; Back‑end Node.js + WebSocket (hoặc Firebase Realtime).  
  - Tuân thủ quy định bảo mật dữ liệu cá nhân (GDPR/PDPA) nếu có người dùng ở khu vực EU/Việt Nam.  
  - Hạ tầng: sử dụng dịch vụ cloud (AWS/GCP) với chi phí tối ưu cho quy mô nhỏ.

- **Câu hỏi còn mở:**  
  1. Yêu cầu hỗ trợ tin nhắn đa phương tiện (hình ảnh, video, file) hay chỉ văn bản?  
  2. Có cần tính năng tạo nhóm chat hoặc phòng hội nghị?  
  3. Yêu cầu mức độ bảo mật (mã hoá end‑to‑end) như thế nào?  
  4. Ngân sách dự án và mức chi phí tối đa cho hạ tầng/cloud?  
  5. Có yêu cầu tích hợp với hệ thống hiện có (CRM, LDAP…) không?  
  6. Ngôn ngữ giao diện (tiếng Việt, tiếng Anh, đa ngôn ngữ)?  

*Các thông tin trên sẽ được dùng làm đầu vào cho PRD tiếp theo.*