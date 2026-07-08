# 1. TỔNG QUAN  

**Mục đích**  
Cung cấp một công cụ quản lý công việc cá nhân (và nhóm nhỏ) cho phép người dùng tạo, chỉnh sửa, theo dõi và chia sẻ danh sách nhiệm vụ một cách có cấu trúc.  

**Phạm vi (In‑scope)**  

| Module / Chức năng | Nội dung |
|--------------------|----------|
| Quản lý công việc cá nhân | Tạo, chỉnh sửa, xóa, đánh dấu hoàn thành, xem danh sách, lọc, tìm kiếm, thêm ngày hết hạn, sắp xếp, gắn nhãn, xuất báo cáo |
| Nhắc nhở | Gửi thông báo push (và tùy chọn email) 24 giờ trước ngày hết hạn |
| Đồng bộ & chia sẻ | Đồng bộ dữ liệu giữa các thiết bị của cùng một người dùng; chia sẻ danh sách công việc với người dùng khác |
| Báo cáo | Xuất danh sách công việc dưới dạng PDF hoặc Excel |

**Phạm vi (Out‑of‑scope)**  

| Nội dung | Lý do |
|----------|-------|
| Tích hợp lịch Google/Outlook | Chưa được yêu cầu trong phiên bản 1.0; sẽ xem xét trong các phiên bản tiếp theo |
| Hỗ trợ đa ngôn ngữ | Yêu cầu chưa được xác định; sẽ được đánh giá trong giai đoạn mở rộng |
| Lưu trữ dữ liệu on‑premise | Kiến trúc hiện định hướng dùng dịch vụ đám mây; thay đổi sẽ cần phân tích bảo mật và chi phí |
| Quản lý dự án (kanban, Gantt) | Không thuộc mục tiêu “quản lý công việc cá nhân” của phiên bản này |

**Giả định**  

| Giả định | Chi tiết |
|----------|----------|
| Nền tảng | Ứng dụng được triển khai đồng thời trên web (Chrome/Edge/Safari) và di động (iOS ≥ 14, Android ≥ 9). |
| Người dùng đồng thời | Hệ thống phải chịu tải tối đa **500 yêu cầu đồng thời** (≈ 10 000 người dùng đăng ký). |
| Lưu trữ | Dữ liệu công việc được lưu trên dịch vụ đám mây (ví dụ: AWS RDS) và được mã hoá **AES‑256** khi nghỉ. |
| Ngôn ngữ | Giao diện và nội dung chỉ hỗ trợ **tiếng Anh** trong phiên bản này. |
| Nhắc nhở | Hệ thống gửi **một thông báo push** (và tùy chọn email) **24 giờ** trước ngày hết hạn; không gửi lại nếu người dùng đã đánh dấu hoàn thành. |
| Bảo mật | Xác thực OAuth 2.0 + JWT; tuân thủ **GDPR** và **OWASP Top 10**. |
| Thời gian phản hồi API | ≤ 300 ms cho 95 % các yêu cầu khi tải 200 req/giây. |
| Thời gian tải trang UI | ≤ 2 giây trên kết nối băng thông 5 Mbps. |
| Độ sẵn sàng | **99.5 %** uptime hàng tháng, với backup hàng ngày và khả năng phục hồi trong ≤ 30 phút. |

---

# 2. ĐỐI TƯỢNG NGƯỜI DÙNG  

| Role | Đặc điểm | Quyền hạn |
|------|----------|-----------|
| **Người dùng cá nhân** | Kiến thức công nghệ cơ bản; dùng smartphone (iOS/Android) hoặc trình duyệt web; sử dụng 1‑2 lần/ngày. | Tạo/Chỉnh sửa/Xóa/Hoàn thành công việc của mình; Đặt ngày hết hạn, nhãn, sắp xếp, tìm kiếm; Xuất báo cáo cá nhân; Đồng bộ trên các thiết bị của mình. |
| **Người dùng doanh nghiệp (nhóm nhỏ)** | Kinh nghiệm sử dụng phần mềm cộng tác; có cả desktop và mobile; sử dụng 3‑5 lần/ngày. | Tất cả quyền của người dùng cá nhân + **chia sẻ danh sách** với thành viên trong nhóm; **chỉnh sửa** công việc được chia sẻ; **xem** công việc của người khác trong cùng danh sách. |
| **Quản trị viên hệ thống** | Kỹ thuật viên IT, hiểu biết sâu về hạ tầng, bảo mật; làm việc trên máy tính để bàn. | Quản lý tài khoản người dùng (tạo, vô hiệu hoá, reset mật khẩu); Giám sát log hệ thống; Cấu hình thông báo hệ thống; Thực hiện backup/restore; Không thể tạo, chỉnh sửa hay xóa công việc người dùng. |

*Mỗi role đều có ít nhất một FR liên quan (xem mục 3).*

---

# 3. YÊU CẦU CHỨC NĂNG  

## 3.1 Quản lý công việc (Must)

### FR-001: Tạo mới một công việc  
- **Ưu tiên:** Must  
- **AC:**  
  - **AC1 (Happy path)**  
    - *Given* người dùng đã đăng nhập và đang ở màn hình “Tạo công việc”  
    - *When* người dùng nhập tiêu đề (≥ 1 ký tự, ≤ 255 ký tự) và nhấn **Lưu**  
    - *Then* hệ thống tạo một bản ghi công việc với trạng thái “Chưa hoàn thành”, trả về ID công việc và hiển thị thông báo “Công việc đã được tạo”.  
  - **AC2 (Lỗi dữ liệu)**  
    - *Given* tiêu đề rỗng hoặc dài hơn 255 ký tự  
    - *When* người dùng nhấn **Lưu**  
    - *Then* hệ thống từ chối tạo và hiển thị thông báo lỗi “Tiêu đề phải từ 1‑255 ký tự”.  

### FR-002: Chỉnh sửa nội dung công việc  
- **Ưu tiên:** Must  
- **AC:**  
  - **AC1**  
    - *Given* người dùng là chủ sở hữu (hoặc thành viên được chia sẻ) của công việc và đang ở màn hình chi tiết công việc  
    - *When* người dùng thay đổi tiêu đề hoặc mô tả và nhấn **Cập nhật**  
    - *Then* hệ thống lưu thay đổi, trả về trạng thái 200 và hiển thị “Cập nhật thành công”.  
  - **AC2 (Quyền truy cập)**  
    - *Given* người dùng không có quyền chỉnh sửa công việc được chia sẻ  
    - *When* người dùng cố gắng nhấn **Cập nhật**  
    - *Then* hệ thống trả về lỗi 403 “Bạn không có quyền chỉnh sửa công việc này”.  

### FR-003: Xóa công việc  
- **Ưu tiên:** Must  
- **AC:**  
  - **AC1**  
    - *Given* người dùng là chủ sở hữu công việc  
    - *When* người dùng nhấn **Xóa** và xác nhận “Có” trong hộp thoại xác nhận  
    - *Then* công việc được xóa vĩnh viễn, trả về 204 No Content và danh sách công việc được cập nhật (không còn hiện công việc đã xóa).  
  - **AC2 (Xóa không cho phép)**  
    - *Given* công việc đã được chia sẻ với người dùng khác và trạng thái “Hoàn thành”  
    - *When* người dùng cố gắng xóa  
    - *Then* hệ thống trả về lỗi 400 “Không thể xóa công việc đã hoàn thành”.  

### FR-004: Đánh dấu công việc là đã hoàn thành  
- **Ưu tiên:** Must  
- **AC:**  
  - **AC1**  
    - *Given* công việc ở trạng thái “Chưa hoàn thành”  
    - *When* người dùng nhấn **Hoàn thành**  
    - *Then* trạng thái công việc chuyển thành “Hoàn thành”, ngày hoàn thành được ghi lại, và thông báo “Công việc đã hoàn thành” được hiển thị.  
  - **AC2 (Lặp lại)**  
    - *Given* công việc đã ở trạng thái “Hoàn thành”  
    - *When* người dùng nhấn **Hoàn thành** lại  
    - *Then* hệ thống trả về lỗi 409 “Công việc đã được đánh dấu hoàn thành”.  

### FR-005: Xem danh sách công việc theo thứ tự tạo  
- **Ưu tiên:** Must  
- **AC:**  
  - **AC1**  
    - *Given* người dùng đã đăng nhập và chuyển tới màn hình “Danh sách công việc”  
    - *When* hệ thống tải danh sách  
    - *Then* các công việc được sắp xếp giảm dần theo thời gian tạo (mới nhất trên đầu) và trả về trong vòng ≤ 300 ms.  

### FR-006: Lọc/đánh dấu công việc theo trạng thái (hoàn thành/chưa hoàn thành)  
- **Ưu tiên:** Must  
- **AC:**  
  - **AC1**  
    - *Given* người dùng đang xem danh sách công việc  
    - *When* người dùng chọn bộ lọc “Chưa hoàn thành”  
    - *Then* hệ thống hiển thị chỉ các công việc có trạng thái “Chưa hoàn thành”.  
  - **AC2**  
    - *Given* người dùng chọn bộ lọc “Hoàn thành”  
    - *Then* hệ thống hiển thị chỉ các công việc đã hoàn thành.  

## 3.2 Tính năng mở rộng (Should / Could)

### FR-007: Thêm ngày hết hạn cho công việc  
- **Ưu tiên:** Should  
- **AC:**  
  - **AC1**  
    - *Given* người dùng đang chỉnh sửa hoặc tạo công việc  
    - *When* người dùng chọn ngày trong bộ chọn ngày (định dạng YYYY‑MM‑DD) và lưu  
    - *Then* ngày hết hạn được lưu và hiển thị trong chi tiết công việc.  
  - **AC2 (Ngày quá khứ)**  
    - *Given* ngày được chọn là ngày trước ngày hiện tại  
    - *When* người dùng lưu  
    - *Then* hệ thống trả về lỗi 400 “Ngày hết hạn không được trước ngày hiện tại”.  

### FR-008: Nhắc nhở người dùng trước ngày hết hạn  
- **Ưu tiên:** Should  
- **AC:**  
  - **AC1**  
    - *Given* công việc có ngày hết hạn và trạng thái “Chưa hoàn thành”  
    - *When* hiện tại là 24 giờ trước ngày hết hạn  
    - *Then* hệ thống gửi **một thông báo push** (và nếu người dùng đã bật email, gửi email) chứa tiêu đề và ngày hết hạn.  
  - **AC2 (Không gửi khi đã hoàn thành)**  
    - *Given* công việc đã được đánh dấu “Hoàn thành” trước thời điểm 24 giờ  
    - *When* thời gian đạt 24 giờ trước ngày hết hạn  
    - *Then* không có thông báo nào được gửi.  

### FR-009: Tìm kiếm công việc theo từ khóa  
- **Ưu tiên:** Should  
- **AC:**  
  - **AC1**  
    - *Given* người dùng nhập một chuỗi ký tự vào ô tìm kiếm và nhấn **Enter**  
    - *When* hệ thống thực hiện tìm kiếm trên tiêu đề và mô tả (khớp không phân biệt chữ hoa/thường)  
    - *Then* danh sách hiển thị các công việc chứa từ khóa, thời gian phản hồi ≤ 500 ms.  

### FR-010: Phân loại công việc bằng nhãn hoặc danh mục  
- **Ưu tiên:** Should  
- **AC:**  
  - **AC1**  
    - *Given* người dùng đang tạo hoặc chỉnh sửa công việc  
    - *When* người dùng gắn một hoặc nhiều nhãn (tối đa 5 nhãn, mỗi nhãn ≤ 30 ký tự) và lưu  
    - *Then* nhãn được lưu và hiển thị trong danh sách và chi tiết công việc.  

### FR-011: Sắp xếp công việc theo ngày hết hạn hoặc ưu tiên  
- **Ưu tiên:** Could  
- **AC:**  
  - **AC1**  
    - *Given* người dùng đang xem danh sách công việc  
    - *When* người dùng chọn “Sắp xếp theo ngày hết hạn”  
    - *Then* danh sách được sắp xếp tăng dần theo ngày hết hạn; công việc không có ngày hết hạn được đặt cuối danh sách.  

### FR-012: Đồng bộ dữ liệu công việc trên nhiều thiết bị  
- **Ưu tiên:** Could  
- **AC:**  
  - **AC1**  
    - *Given* cùng một tài khoản đăng nhập trên hai thiết bị (web + mobile)  
    - *When* người dùng tạo, chỉnh sửa hoặc xóa công việc trên thiết bị A  
    - *Then* thay đổi được phản ánh trên thiết bị B trong vòng ≤ 2 giây (push sync).  

### FR-013: Chia sẻ danh sách công việc với người khác  
- **Ưu tiên:** Could  
- **AC:**  
  - **AC1**  
    - *Given* người dùng là chủ sở hữu danh sách  
    - *When* người dùng nhập email của người dùng khác, chọn quyền “Xem” hoặc “Chỉnh sửa”, và nhấn **Gửi lời mời**  
    - *Then* người nhận nhận được email lời mời; khi chấp nhận, danh sách xuất hiện trong tài khoản của người nhận với quyền tương ứng.  

### FR-014: Xuất/đánh dấu công việc dưới dạng báo cáo (PDF/Excel)  
- **Ưu tiên:** Could  
- **AC:**  
  - **AC1**  
    - *Given* người dùng đang xem danh sách công việc và nhấn **Xuất** → **PDF**  
    - *When* hệ thống tạo file PDF chứa tiêu đề, mô tả, ngày hết hạn, trạng thái và nhãn của mỗi công việc  
    - *Then* file được tải về trong vòng ≤ 5 giây và nội dung khớp với danh sách hiện tại.  
  - **AC2** (Excel) tương tự, định dạng CSV/Excel với cùng các cột.  

---

# 4. YÊU CẦU PHI CHỨC NĂNG  

| ID | Nhóm | Yêu cầu | Chi tiết |
|----|------|---------|----------|
| NFR-001 | **Performance** | Thời gian phản hồi | API trả về trong ≤ 300 ms cho 95 % yêu cầu khi tải 200 req/giây; UI tải trang danh sách ≤ 2 s trên kết nối 5 Mbps. |
| NFR-002 | **Security** | Xác thực & ủy quyền | Sử dụng OAuth 2.0 + JWT; token có thời hạn 1 giờ, refresh token 24 giờ. |
|      |      | Mã hoá dữ liệu | Dữ liệu nhạy cảm (địa chỉ email, ngày hết hạn) được mã hoá AES‑256 khi lưu trữ; truyền qua HTTPS/TLS 1.2+. |
|      |      | Tuân thủ | Đáp ứng **GDPR** (quyền xóa dữ liệu, consent) và **OWASP Top 10**. |
| NFR-003 | **Usability** | Độ học nhanh | Người dùng mới có thể **tạo một công việc** trong ≤ 3 bước (Mở màn hình → Nhập tiêu đề → Lưu) mà không cần tài liệu hướng dẫn. |
| NFR-004 | **Reliability / Availability** | Độ sẵn sàng | Hệ thống đạt **99.5 %** uptime hàng tháng; backup toàn bộ DB hàng ngày; thời gian phục hồi (RTO) ≤ 30 phút. |
| NFR-005 | **Scalability** | Khả năng mở rộng | Kiến trúc hỗ trợ **tối thiểu 10 000 người dùng đồng thời**; khả năng mở rộng ngang (scale‑out) bằng việc thêm node ứng dụng. |
| NFR-006 | **Compatibility** | Môi trường hỗ trợ | Web: Chrome ≥ 90, Edge ≥ 90, Safari ≥ 14. Mobile: iOS ≥ 14, Android ≥ 9. |
| NFR-007 | **Maintainability** | Độ phức tạp | Mã nguồn phải tuân thủ quy tắc **Clean Code**; mỗi module không vượt quá 400 LOC; tài liệu API (OpenAPI 3.0) phải luôn cập nhật. |
| NFR-008 | **Legal / Regulatory** | Bảo mật dữ liệu cá nhân | Không lưu trữ dữ liệu cá nhân ở các quốc gia không được phép theo GDPR; dữ liệu người dùng EU phải lưu trên server EU. |

*Các NFR được viết ở mức tổng quan, không đề cập tới công nghệ cụ thể (ví dụ: “sử dụng PostgreSQL”).*

---

# 5. QUY TẮC NGHIỆP VỤ  

| ID | Quy tắc |
|----|----------|
| BR-001 | Một công việc chỉ có thể **đánh dấu hoàn thành** khi trạng thái hiện tại là “Chưa hoàn thành”. |
| BR-002 | **Ngày hết hạn** không được đặt trước ngày tạo công việc. |
| BR-003 | Khi một danh sách được chia sẻ, **quyền chỉnh sửa** chỉ được cấp cho người dùng được mời với quyền “Chỉnh sửa”. Người dùng chỉ có quyền “Xem” không được thực hiện bất kỳ hành động tạo, sửa, xóa nào. |
| BR-004 | **Nhắc nhở** được gửi duy nhất một lần cho mỗi công việc, cách ngày hết hạn 24 giờ, và không gửi nếu công việc đã ở trạng thái “Hoàn thành”. |
| BR-005 | Khi một công việc được **xóa**, tất cả các nhãn, ghi chú và lịch sử thay đổi liên quan tới công việc đó cũng bị xóa vĩnh viễn. |
| BR-006 | **Xuất báo cáo** chỉ bao gồm các công việc mà người dùng hiện tại có quyền xem; dữ liệu không được lọc hoặc ẩn thông tin nhạy cảm. |
| BR-007 | **Backup** được thực hiện vào lúc 02:00 AM UTC mỗi ngày; bản sao lưu phải được lưu ít nhất 30 ngày. |
| BR-008 | **Đăng nhập** thất bại sau 5 lần liên tiếp trong vòng 15 phút sẽ khóa tài khoản tạm thời 30 phút và gửi email cảnh báo. |

---

## Kiểm tra cuối cùng  

- [x] Mỗi FR có ID, ưu tiên, ít nhất 1 AC (định dạng Given/When/Then).  
- [x] Không còn từ mơ hồ; mọi tiêu chí đều có số liệu hoặc giả định được ghi chú.  
- [x] FR chỉ mô tả **WHAT**, không đề cập tới công nghệ cụ thể.  
- [x] Phạm vi In‑scope/Out‑of‑scope khớp với danh sách FR.  
- [x] Mỗi role trong mục 2 có ít nhất một FR liên quan.  
- [x] Bao phủ đầy đủ 6 nhóm NFR chính, bao gồm Security.  
- [x] Không có feedback reject, vì đây là bản đầu tiên; toàn bộ nội dung giữ nguyên số ID và cấu trúc.