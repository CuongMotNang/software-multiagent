# SOFTWARE REQUIREMENTS SPECIFICATION (SRS)

**Dự án:** Personal Task Manager — Ứng dụng Quản lý Công việc Cá nhân Đơn giản  
**Phiên bản:** 1.0  
**Ngày lập:** 2024  
**Trạng thái:** Draft — Chờ phê duyệt Product Owner

---

# 1. TỔNG QUAN

## 1.1 Mục đích
Hệ thống cung cấp công cụ quản lý công việc cá nhân/hàng ngày với độ phức tạp tối thiểu, cho phép người dùng tạo, theo dõi và hoàn thành nhiệm vụ mà không cần đào tạo hoặc cấu hình phức tạp.

## 1.2 Phạm vi (In-scope)

| STT | Chức năng | Mô tả ngắn |
|-----|-----------|------------|
| 1 | Tạo nhiệm vụ mới | Thêm công việc với tiêu đề bắt buộc, mô tả tùy chọn |
| 2 | Đánh dấu hoàn thành | Chuyển trạng thái nhiệm vụ sang "done" |
| 3 | Xem danh sách nhiệm vụ | Hiển thị tất cả nhiệm vụ, phân biệt chưa hoàn thành/đã hoàn thành |
| 4 | Xóa nhiệm vụ | Loại bỏ nhiệm vụ khỏi hệ thống |
| 5 | Lưu trữ dữ liệu bền vững | Dữ liệu không mất khi đóng ứng dụng |

## 1.3 Phạm vi (Out-of-scope)

| STT | Hạng mục | Lý do loại trừ |
|-----|----------|----------------|
| 1 | Đăng ký/Đăng nhập người dùng | Giảm độ phức tạp, phiên bản MVP tập trung vào trải nghiệm nhanh |
| 2 | Đồng bộ đa thiết bị | Chưa có yêu cầu rõ ràng, tăng phức tạp kỹ thuật |
| 3 | Chia sẻ nhiệm vụ với người khác | Ngoài phạm vi "cá nhân" |
| 4 | Thông báo/reminder | Giữ độ đơn giản cốt lõi |
| 5 | Phân loại theo danh mục/project | Có thể xem xét ở phiên bản sau nếu phản hồi người dùng yêu cầu |
| 6 | Ứng dụng native mobile (iOS/Android) | Chưa xác định nền tảng ưu tiên; phiên bản này tập trung web-based |
| 7 | Lập lịch tái diễn (recurring tasks) | Tăng độ phức tạp vượt mức "đơn giản" |

## 1.4 Giả định

| ID | Giả định | Cơ sở |
|----|----------|-------|
| ASS-001 | Người dùng sử dụng thiết bị có trình duyệt web hiện đại | Đa số người dùng cá nhân có ít nhất 1 thiết bị như vậy |
| ASS-002 | Mỗi thiết bị = 1 người dùng ẩn danh (không đăng nhập) | Out-of-scope đăng ký/đăng nhập |
| ASS-003 | Dữ liệu lưu trữ tại local (browser storage) là đủ cho MVP | Chưa có yêu cầu server-side hoặc đồng bộ |
| ASS-004 | Tiêu đề nhiệm vụ đủ định danh, không cần ID hiển thị | Trải nghiệm đơn giản |
| ASS-005 | Người dùng chấp nhận mất dữ liệu khi xóa cache trình duyệt hoặc đổi thiết bị | Giả định rủi ro chấp nhận được cho MVP |

---

# 2. ĐỐI TƯỢNG NGƯỜI DÙNG

| Role | Đặc điểm | Quyền hạn |
|------|----------|-----------|
| **Người dùng cuối (End User)** | • Am hiểu CNTT: đa dạng từ cơ bản đến nâng cao<br>• Thiết bị: chưa xác định, giả định có trình duyệt web<br>• Tần suất: hàng ngày, phiên làm việc ngắn (< 5 phút/lần)<br>• Mục tiêu: ghi nhanh việc cần làm, không quản lý phức tạp | **Được phép:**<br>• Tạo nhiệm vụ mới<br>• Xem danh sách nhiệm vụ<br>• Đánh dấu hoàn thành<br>• Xóa nhiệm vụ<br><br>**Không được phép:**<br>• Truy cập dữ liệu người dùng khác<br>• Khôi phục nhiệm vụ đã xóa (không có undo) |

> **Lưu ý:** Do không có hệ thống đăng nhập, "người dùng" được định nghĩa là phiên sử dụng trên một trình duyệt/thiết bị cụ thể.

---

# 3. YÊU CẦU CHỨC NĂNG

### 3.1 Quản lý nhiệm vụ

---

**FR-001: Hệ thống cho phép người dùng tạo nhiệm vụ mới với tiêu đề**
- Ưu tiên: Must
- AC1 (Happy path):  
  Given người dùng đang ở giao diện chính  
  When nhập tiêu đề nhiệm vụ (1–200 ký tự) và xác nhận tạo  
  Then nhiệm vụ xuất hiện trong danh sách với trạng thái "chưa hoàn thành" và thời điểm tạo được ghi nhận

- AC2 (Tiêu đề rỗng):  
  Given người dùng đang tạo nhiệm vụ  
  When để trống tiêu đề và xác nhận  
  Then hệ thống hiển thị thông báo lỗi "Tiêu đề không được để trống" và không tạo nhiệm vụ

- AC3 (Tiêu đề vượt quá độ dài):  
  Given người dùng đang nhập tiêu đề  
  When nhập quá 200 ký tự  
  Then hệ thống ngăn nhập thêm và hiển thị đếm ký tự "0/200"

---

**FR-002: Hệ thống cho phép người dùng thêm mô tả tùy chọn cho nhiệm vụ**
- Ưu tiên: Must
- AC1:  
  Given người dùng đang tạo hoặc chỉnh sửa nhiệm vụ  
  When nhập mô tả (0–1000 ký tự) và xác nhận  
  Then mô tả được lưu kèm theo nhiệm vụ

- AC2:  
  Given người dùng tạo nhiệm vụ  
  When không nhập mô tả và xác nhận  
  Then nhiệm vụ được tạo với mô tả rỗng, không báo lỗi

---

**FR-003: Hệ thống cho phép người dùng xem danh sách tất cả nhiệm vụ**
- Ưu tiên: Must
- AC1:  
  Given người dùng mở ứng dụng  
  When trang chính được tải  
  Then hiển thị danh sách nhiệm vụ sắp xếp theo thời gian tạo giảm dần (mới nhất trước), phân biệt rõ trạng thái chưa hoàn thành/đã hoàn thành

- AC2 (Danh sách rỗng):  
  Given chưa có nhiệm vụ nào được tạo  
  When trang chính được tải  
  Then hiển thị trạng thái rỗng với hướng dẫn "Nhấn để thêm việc cần làm đầu tiên"

---

**FR-004: Hệ thống cho phép người dùng đánh dấu nhiệm vụ đã hoàn thành**
- Ưu tiên: Must
- AC1 (Happy path):  
  Given nhiệm vụ đang ở trạng thái "chưa hoàn thành"  
  When người dùng chọn đánh dấu hoàn thành  
  Then trạng thái chuyển sang "đã hoàn thành", nhiệm vụ di chuyển xuống cuối danh sách hoặc vào nhóm "Đã xong", thời điểm hoàn thành được ghi nhận

- AC2 (Đánh dấu lại):  
  Given nhiệm vụ đã hoàn thành  
  When người dùng chọn bỏ đánh dấu hoàn thành  
  Then trạng thái quay lại "chưa hoàn thành", nhiệm vụ trở lại vị trí theo thời gian tạo

---

**FR-005: Hệ thống cho phép người dùng xóa nhiệm vụ**
- Ưu tiên: Must
- AC1 (Happy path):  
  Given nhiệm vụ tồn tại trong danh sách  
  When người dùng chọn xóa và xác nhận  
  Then nhiệm vụ bị xóa khỏi danh sách, không còn hiển thị, không thể khôi phục

- AC2 (Hủy thao tác):  
  Given người dùng vừa chọn xóa  
  When chọn "Hủy" trong hộp thoại xác nhận  
  Then nhiệm vụ giữ nguyên, không có thay đổi

---

**FR-006: Hệ thống cho phép người dùng chỉnh sửa tiêu đề và mô tả nhiệm vụ chưa hoàn thành**
- Ưu tiên: Should
- AC1:  
  Given nhiệm vụ ở trạng thái "chưa hoàn thành"  
  When người dùng chọn chỉnh sửa, thay đổi thông tin và xác nhận  
  Then nhiệm vụ được cập nhật với thông tin mới, thời gian sửa đổi được ghi nhận

- AC2:  
  Given nhiệm vụ đã hoàn thành  
  When người dùng cố gắng chỉnh sửa  
  Then hệ thống chỉ cho phép bỏ đánh dấu hoàn thành trước, không chỉnh sửa trực tiếp

---

**FR-007: Hệ thống cho phép người dùng lọc nhiệm vụ theo trạng thái**
- Ưu tiên: Should
- AC1:  
  Given danh sách có cả nhiệm vụ chưa hoàn thành và đã hoàn thành  
  When người dùng chọn lọc "Chưa xong"  
  Then chỉ hiển thị nhiệm vụ chưa hoàn thành

- AC2:  
  When người dùng chọn lọc "Tất cả"  
  Then hiển thị toàn bộ nhiệm vụ theo thứ tự mặc định

---

### 3.2 Lưu trữ dữ liệu

---

**FR-008: Hệ thống phải lưu trữ dữ liệu nhiệm vụ bền vững qua các phiên sử dụng**
- Ưu tiên: Must
- AC1:  
  Given người dùng đã tạo nhiệm vụ  
  When đóng trình duyệt, mở lại ứng dụng  
  Then toàn bộ nhiệm vụ và trạng thái được khôi phục chính xác

- AC2:  
  Given người dùng đã đánh dấu hoàn thành nhiệm vụ  
  When khởi động lại thiết bị và mở lại ứng dụng  
  Then trạng thái "đã hoàn thành" được giữ nguyên

---

# 4. YÊU CẦU PHI CHỨC NĂNG

| ID | Nhóm | Yêu cầu | Giả định/Ghi chú |
|----|------|---------|------------------|
| **NFR-001** | **Performance** | • Thời gian tải trang ban đầu ≤ 2 giây trên kết nối 3G (1.5 Mbps)<br>• Thời gian phản hồi khi tạo/xóa/đánh dấu nhiệm vụ ≤ 300ms<br>• Dung lượng ứng dụng (bundle) ≤ 500KB gzip | Giả định: người dùng có thể dùng mạng chậm |
| **NFR-002** | **Security** | • Dữ liệu lưu tại client-side (localStorage/IndexedDB), không truyền qua mạng → không cần mã hóa truyền tải<br>• Không lưu thông tin nhạy cảm (không có PII theo thiết kế)<br>• Tuân thủ OWASP Top 10 cho ứng dụng client-side (XSS prevention, input sanitization) | Giả định: không có server, không có xác thực |
| **NFR-003** | **Usability** | • Người dùng mới hoàn thành tạo nhiệm vụ đầu tiên trong ≤ 30 giây kể từ khi mở ứng dụng<br>• Không có hướng dẫn sử dụng bắt buộc (no onboarding tour)<br>• Giao diện hiển thị tối đa 2 màu sắc trạng thái (chưa xong/đã xong) để tránh nhầm lẫn | Giả định: "đơn giản" = ít bước, ít lựa chọn |
| **NFR-004** | **Reliability/Availability** | • Uptime khả dụng: 100% tại client-side (không phụ thuộc server)<br>• Không có yêu cầu backup vì dữ liệu local<br>• Tỷ lệ lỗi khi đọc/ghi localStorage < 0.1% | Giả định: rủi ro mất dữ liệu local do người dùng xóa cache là chấp nhận được |
| **NFR-005** | **Scalability** | • Hỗ trợ tối thiểu 500 nhiệm vụ lưu trữ mỗi thiết bị mà không giảm hiệu năng đáng kể<br>• Không giới hạn cứng số nhiệm vụ, nhưng cảnh báo khi vượt 1000 nhiệm vụ | Giả định: người dùng cá nhân không có > 500 việc đồng thời |
| **NFR-006** | **Compatibility** | • Trình duyệt: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+<br>• Thiết bị: desktop, tablet, mobile (responsive design)<br>• Kích thước màn hình hỗ trợ: 320px–2560px chiều rộng | Giả định: không hỗ trợ IE11 hoặc trình duyệt legacy |
| **NFR-007** | **Accessibility** *(bổ sung)* | • Tuân thủ WCAG 2.1 Level AA<br>• Tương thích với screen reader (ARIA labels cho checkbox, delete button)<br>• Tỷ lệ tương phản màu chữ/nền ≥ 4.5:1 | Giả định: người dùng có khuyết tật thị giác vẫn cần sử dụng |

---

# 5. QUY TẮC NGHIỆP VỤ

| ID | Quy tắc nghiệp vụ |
|----|-------------------|
| **BR-001** | Một nhiệm vụ phải có tiêu đề không rỗng và không chỉ chứa khoảng trắng |
| **BR-002** | Tiêu đề nhiệm vụ được chuẩn hóa: loại bỏ khoảng trắng đầu/cuối, thu gọn nhiều khoảng trắng liên tiếp thành một |
| **BR-003** | Nhiệm vụ đã hoàn thành không thể chỉnh sửa nội dung trực tiếp; muốn chỉnh sửa phải bỏ đánh dấu hoàn thành trước |
| **BR-004** | Thứ tự hiển thị mặc định: chưa hoàn thành trước đã hoàn thành; trong mỗi nhóm, sắp xếp theo thời gian tạo giảm dần |
| **BR-005** | Xóa nhiệm vụ là hành động không thể hoàn tác (hard delete), không lưu lịch sử |
| **BR-006** | Mỗi thiết bị/trình duyệt là một không gian dữ liệu độc lập; không có cơ chế đồng bộ hoặc chia sẻ giữa các thiết bị |

---

## PHỤ LỤC: Câu hỏi mở cần làm rõ trước khi thiết kế

| ID | Câu hỏi | Ảnh hưởng đến |
|----|---------|---------------|
| OPEN-001 | Nền tảng triển khai cuối cùng: web app, PWA, hay hybrid? | Kiến trúc triển khai, khả năng offline |
| OPEN-002 | Có cần đồng bộ đa thiết bị trong tương lai không? | Quyết định lưu trữ local-only hay chuẩn bị backend |
| OPEN-003 | Có cần export/import dữ liệu? | Backup/phục hồi, di chuyển thiết bị |
| OPEN-004 | Ngôn ngữ giao diện: chỉ Tiếng Việt hay đa ngôn ngữ? | i18n architecture |
| OPEN-005 | Có cần dark mode? | Design system, CSS architecture |

---

**Người lập:** Product Analyst — SoftwareFactory  
**Ngày cập nhật:** [Ngày hiện tại]  
**Trạng thái review:** Chờ Product Owner sign-off trước khi chuyển Solution Architect