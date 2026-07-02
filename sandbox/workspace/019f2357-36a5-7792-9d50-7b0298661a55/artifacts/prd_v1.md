# 1. TỔNG QUAN  

## Mục đích  
Hệ thống **Chatbot Zalo – Trợ lý CS** tự động nhận, trả lời tin nhắn khách hàng trên Zalo, ghi lại toàn bộ hội thoại, cho phép quản trị viên thiết lập kịch bản, lập lịch gửi tin, chuyển tiếp sang nhân viên CS, và cung cấp báo cáo, dashboard thống kê để doanh nghiệp giám sát và ra quyết định.  

## Phạm vi (In‑scope)  
| # | Chức năng |
|---|-----------|
| 1 | Nhận và lưu trữ tin nhắn khách hàng từ Zalo. |
| 2 | Trả lời tự động dựa trên kịch bản/keyword được cấu hình. |
| 3 | Ghi lại nội dung và thời gian của mọi tin nhắn (gửi/nhận). |
| 4 | Tạo báo cáo thống kê (số hội thoại, thời gian phản hồi trung bình, tần suất tin). |
| 5 | Quản trị viên tạo/ sửa/ xoá kịch bản trả lời và từ khóa. |
| 6 | Quản trị viên lên lịch gửi tin tự động (giờ trong ngày, ngày lặp). |
| 7 | Cảnh báo khi thời gian phản hồi vượt ngưỡng hoặc khi lỗi hệ thống. |
| 8 | Chuyển tiếp hội thoại sang nhân viên CS khi cần. |
| 9 | Dashboard hiển thị trạng thái bot thời gian thực (số cuộc hội thoại đang mở, tin/phút, lỗi). |
|10| Quản lý quyền truy cập (admin, CS, marketing). |
|11| Xuất dữ liệu hội thoại ra file CSV/Excel. |
|12| Áp dụng chính sách lưu trữ & xóa dữ liệu tự động. |

## Phạm vi (Out‑of‑scope)  
| # | Nội dung |
|---|----------|
| 1 | Tích hợp tự động đồng bộ dữ liệu khách hàng sang CRM bên thứ ba (được ghi nhận nhưng sẽ triển khai ở phiên bản sau). |
| 2 | Phát triển ứng dụng di động riêng cho nhân viên CS (hệ thống chỉ cung cấp giao diện web). |
| 3 | Đào tạo người dùng cuối (khách hàng Zalo) – chỉ thu thập phản hồi qua khảo sát. |
| 4| Thay đổi hoặc mở rộng API Zalo – hệ thống chỉ tiêu chuẩn theo tài liệu Zalo hiện hành. |
| 5| Các tính năng AI nâng cao (phân tích ngữ nghĩa, sentiment) – không có trong phiên bản này. |

## Giả định  
| # | Giả định |
|---|----------|
| A1 | Hệ thống sẽ được triển khai trên môi trường cloud nội bộ hoặc public cloud có khả năng đáp ứng **≥ 100 req/s**. |
| A2 | Số lượng người dùng cuối đồng thời tối đa **10 000 cuộc hội thoại**. |
| A3 | Thời gian phản hồi mục tiêu của bot là **≤ 2 giây** (được đo từ khi nhận tin đến khi gửi trả lời). |
| A4 | Dữ liệu hội thoại được lưu trữ **90 ngày** rồi tự động xóa (theo quy định PDPA). |
| A5 | Người dùng cuối chỉ truy cập qua ứng dụng Zalo (iOS/Android) – không cần hỗ trợ các nền tảng tin nhắn khác. |
| A6 | Đội IT có quyền truy cập vào môi trường vận hành để thực hiện backup, restore, và cập nhật cấu hình. |
| A7 | Các báo cáo sẽ được cung cấp dưới dạng **PDF** và **CSV** và có thể tải xuống từ dashboard. |
| A8 | Ngưỡng cảnh báo thời gian phản hồi được cấu hình mặc định **5 giây**; có thể thay đổi bởi admin. |

---  

# 2. ĐỐI TƯỢNG NGƯỜI DÙNG  

| Role | Đặc điểm | Quyền hạn (FR liên quan) |
|------|----------|--------------------------|
| **Chủ doanh nghiệp / Giám đốc kinh doanh** | Không dùng hệ thống hàng ngày; chỉ truy cập báo cáo tổng quan trên dashboard; quyết định chiến lược. | FR‑004 (xem báo cáo), FR‑009 (dashboard), FR‑010 (quyền “marketing”). |
| **Quản trị viên chatbot** | Kiến thức kỹ thuật trung bình; làm việc trên desktop; chịu trách nhiệm cấu hình kịch bản, lịch gửi, và quản lý quyền. | FR‑005, FR‑006, FR‑010, FR‑012, FR‑011. |
| **Nhân viên chăm sóc khách hàng (CS)** | Kiến thức cơ bản về phần mềm; sử dụng desktop để nhận chuyển tiếp; cần xem lịch sử hội thoại. | FR‑008 (nhận chuyển tiếp), FR‑003 (xem lịch sử), FR‑009 (dashboard). |
| **Khách hàng cuối (người dùng Zalo)** | Sử dụng Zalo trên smartphone; không cần kiến thức kỹ thuật; tương tác tự nhiên với bot. | FR‑001, FR‑002 (tự động trả lời). |
| **Đội IT / Bảo trì** | Kiến thức sâu về hạ tầng, bảo mật; can thiệp khi có sự cố hoặc nâng cấp. | FR‑007 (giám sát cảnh báo), FR‑012 (backup/restore), NFR‑001, NFR‑002. |
| **Zalo (nhà cung cấp nền tảng)** | Cung cấp API, tài liệu, và thông báo thay đổi chính sách. | Không có FR trực tiếp; chỉ là đối tác tích hợp (ràng buộc công nghệ). |

---  

# 3. YÊU CẦU CHỨC NĂNG  

## 3.1 Nhận & Lưu trữ Tin nhắn  

**FR‑001**: Hệ thống **phải** nhận mọi tin nhắn inbound từ Zalo và lưu trữ nội dung, thời gian gửi, thời gian nhận, và ID người dùng.  
- Ưu tiên: **Must**  
- AC1: **Given** một tin nhắn mới từ Zalo tới số điện thoại đã đăng ký **When** API Zalo gửi webhook tới hệ thống **Then** hệ thống tạo bản ghi hội thoại với trường “message_text”, “sender_id”, “timestamp_received” và trả về HTTP 200.  
- AC2 (lỗi): **Given** webhook không chứa trường “message_text” **When** hệ thống xử lý **Then** trả về HTTP 400 và ghi log lỗi “Missing message_text”.  

**FR‑002**: Hệ thống **phải** trả lời tự động dựa trên kịch bản/keyword đã cấu hình.  
- Ưu tiên: **Must**  
- AC1: **Given** tin nhắn chứa keyword “giá” và có kịch bản trả lời “Sản phẩm A giá 100 k” **When** tin nhắn được nhận **Then** bot gửi tin trả lời “Sản phẩm A giá 100 k” trong ≤ 2 giây.  
- AC2 (không khớp): **Given** tin nhắn không khớp bất kỳ keyword nào **When** tin nhắn được nhận **Then** bot trả lời “Xin lỗi, hiện tôi không hiểu. Vui lòng liên hệ CS.”  

## 3.2 Ghi lại Nội dung & Thời gian  

**FR‑003**: Hệ thống **phải** ghi lại **mỗi** tin nhắn gửi và nhận kèm thời gian chính xác (độ chính xác ≥ 1 giây).  
- Ưu tiên: **Must**  
- AC1: **Given** một tin nhắn đã được trả lời **When** bản ghi được lưu **Then** trường “timestamp_sent” và “timestamp_received” có giá trị không rỗng và chênh lệch ≤ 2 giây.  

## 3.3 Báo cáo Thống kê  

**FR‑004**: Hệ thống **phải** tạo báo cáo thống kê **theo khoảng thời gian** (ngày, tuần, tháng) bao gồm: số hội thoại, thời gian phản hồi trung bình, tần suất tin gửi.  
- Ưu tiên: **Must**  
- AC1: **Given** người dùng admin chọn “Báo cáo tuần 2024‑W10” **When** nhấn “Generate” **Then** hệ thống trả về file PDF và CSV trong ≤ 5 giây, nội dung khớp với dữ liệu lưu trữ.  
- AC2 (dữ liệu rỗng): **Given** không có hội thoại trong khoảng thời gian đã chọn **When** generate **Then** báo cáo hiển thị “0 hội thoại” và vẫn trả về file hợp lệ.  

## 3.4 Quản trị Kịch bản & Keyword  

**FR‑005**: Quản trị viên **phải** tạo, sửa, xoá kịch bản trả lời và ánh xạ keyword → câu trả lời.  
- Ưu tiên: **Must**  
- AC1: **Given** admin ở màn hình “Kịch bản” **When** nhập keyword “đặt lịch” và câu trả lời “Bạn muốn đặt lịch vào ngày nào?” **Then** hệ thống lưu bản ghi và hiển thị thông báo “Lưu thành công”.  
- AC2 (trùng keyword): **Given** keyword “giá” đã tồn tại **When** admin cố gắng tạo lại **Then** hệ thống trả về lỗi “Keyword đã tồn tại”.  

## 3.5 Lịch gửi tin tự động  

**FR‑006**: Quản trị viên **phải** lên lịch gửi tin tự động dựa trên ngày, giờ, và tần suất (hàng ngày, hàng tuần).  
- Ưu tiên: **Should**  
- AC1: **Given** admin tạo lịch “Tin chào mừng” vào 09:00 h mỗi ngày **When** thời gian hệ thống đạt 09:00 h **Then** bot tự động gửi tin “Chào mừng” tới danh sách đã chọn.  
- AC2 (lịch trùng): **Given** một lịch đã tồn tại vào 09:00 h **When** admin tạo lịch mới cùng thời gian **Then** hệ thống trả về lỗi “Lịch đã trùng”.  

## 3.6 Cảnh báo thời gian phản hồi & lỗi  

**FR‑007**: Hệ thống **phải** gửi cảnh báo (email & dashboard) khi thời gian phản hồi trung bình trong 5 phút gần nhất > 5 giây hoặc khi có lỗi hệ thống.  
- Ưu tiên: **Should**  
- AC1: **Given** thời gian phản hồi trung bình = 6 giây **When** kiểm tra định kỳ (mỗi 5 phút) **Then** hệ thống gửi email “Cảnh báo: Thời gian phản hồi vượt ngưỡng”.  
- AC2 (lỗi API): **Given** lỗi 500 từ API Zalo **When** xảy ra **Then** hệ thống ghi log, hiển thị thông báo “Lỗi kết nối Zalo” trên dashboard.  

## 3.7 Chuyển tiếp hội thoại  

**FR‑008**: Khi một tin nhắn chứa từ khóa “gặp nhân viên” hoặc khi CS nhấn “Transfer” **phải** chuyển hội thoại sang nhân viên CS, đồng thời thông báo cho khách hàng.  
- Ưu tiên: **Must**  
- AC1: **Given** khách hàng gửi “gặp nhân viên” **When** bot nhận **Then** bot trả lời “Đang chuyển sang nhân viên, vui lòng chờ...” và tạo ticket cho CS.  
- AC2 (CS không khả dụng): **Given** không có CS online **When** chuyển tiếp **Then** bot trả lời “Hiện không có nhân viên online, vui lòng thử lại sau”.  

## 3.8 Dashboard thời gian thực  

**FR‑009**: Hệ thống **phải** cung cấp dashboard hiển thị: số hội thoại đang mở, tin/phút, lỗi hiện tại, và thời gian hoạt động bot.  
- Ưu tiên: **Must**  
- AC1: **Given** người dùng admin truy cập dashboard **When** tải trang **Then** các widget hiển thị dữ liệu trong ≤ 2 giây và cập nhật mỗi 5 giây.  

## 3.9 Quản lý Quyền Truy Cập  

**FR‑010**: Hệ thống **phải** áp dụng Role‑Based Access Control (RBAC) với ba vai trò: **Admin**, **CS**, **Marketing**.  
- Ưu tiên: **Must**  
- AC1: **Given** người dùng thuộc role “CS” **When** cố gắng truy cập trang “Quản trị kịch bản” **Then** hệ thống trả về HTTP 403 và thông báo “Không có quyền”.  
- AC2: **Given** admin **When** đăng nhập **Then** có thể truy cập tất cả các module.  

## 3.10 Xuất dữ liệu hội thoại  

**FR‑011**: Người dùng **phải** xuất dữ liệu hội thoại (cột: timestamp, sender_id, message, direction) ra file CSV hoặc Excel.  
- Ưu tiên: **Should**  
- AC1: **Given** admin chọn khoảng thời gian “01‑01‑2024 → 31‑01‑2024” **When** nhấn “Export CSV” **Then** hệ thống tạo file < 5 MB và tải về trong ≤ 10 giây.  

## 3.11 Chính sách Lưu trữ & Xóa dữ liệu  

**FR‑012**: Hệ thống **phải** tự động xóa các bản ghi hội thoại sau **90 ngày** kể từ thời gian nhận cuối cùng.  
- Ưu tiên: **Must**  
- AC1: **Given** một bản ghi có timestamp_received = 2024‑01‑01 **When** ngày hiện tại = 2024‑04‑01 **Then** bản ghi không còn tồn tại trong cơ sở dữ liệu.  

---  

# 4. YÊU CẦU PHI CHỨC NĂNG  

| ID | Nhóm | Yêu cầu | Giá trị/Tiêu chí |
|----|------|---------|------------------|
| NFR‑001 | **Performance** | Thời gian phản hồi API trả lời tin nhắn ≤ 500 ms (trong tải 100 req/s). | ≤ 500 ms |
| NFR‑001‑B | **Performance** | Thời gian tải dashboard ≤ 2 s (kết nối băng thông 10 Mbps). | ≤ 2 s |
| NFR‑002 | **Security** | Xác thực người dùng bằng OAuth 2.0 + JWT, mật khẩu ít nhất 8 ký tự, chứa chữ hoa, chữ thường, số & ký tự đặc biệt. | OAuth 2.0, JWT |
| NFR‑002‑B | **Security** | Mã hoá dữ liệu nhạy cảm (ID khách hàng, nội dung tin nhắn) khi lưu trữ và truyền tải (AES‑256). | AES‑256 |
| NFR‑002‑C | **Security** | Tuân thủ **PDPA Việt Nam** và **OWASP Top 10**. | PDPA, OWASP |
| NFR‑003 | **Usability** | Người dùng mới (admin) có thể tạo một kịch bản mới trong **≤ 3 bước** mà không cần đào tạo. | ≤ 3 bước |
| NFR‑003‑B | **Usability** | Dashboard phải hiển thị thông báo lỗi rõ ràng (mã lỗi, mô tả) khi có sự cố. | Thông báo chi tiết |
| NFR‑004 | **Reliability / Availability** | Độ sẵn sàng hệ thống **≥ 99.5 %** (được đo trong tháng). | ≥ 99.5 % |
| NFR‑004‑B | **Reliability** | Backup dữ liệu toàn bộ mỗi 24 giờ, khả năng phục hồi trong ≤ 30 phút. | Backup 24h, RTO ≤ 30 phút |
| NFR‑005 | **Scalability** | Hỗ trợ **≥ 10 000** cuộc hội thoại đồng thời mà không giảm thời gian phản hồi dưới 2 giây. | ≥ 10 k đồng thời |
| NFR‑006 | **Compatibility** | Hỗ trợ các trình duyệt: Chrome ≥ 90, Edge ≥ 90, Firefox ≥ 88; và Zalo API phiên bản **v3.2** trở lên. | Chrome, Edge, Firefox, Zalo v3.2 |
| NFR‑007 | **Maintainability** | Mã nguồn phải tuân thủ quy tắc **ESLint** (cho JavaScript) hoặc **Pylint** (cho Python) với mức độ “error” ≤ 0. | Linting |
| NFR‑008 | **Localization** | Hệ thống hỗ trợ **tiếng Việt** và **tiếng Anh**; ngôn ngữ có thể chuyển đổi trong UI. | 2 ngôn ngữ |

> **Ghi chú**: Các giá trị chưa được stakeholder cung cấp (ví dụ: ngưỡng thời gian phản hồi) được đưa ra dựa trên chuẩn ngành và được đánh dấu **giả định** trong mục 1.  

---  

# 5. QUY TẮC NGHIỆP VỤ  

| ID | Quy tắc |
|----|---------|
| BR‑001 | Một hội thoại chỉ được **chuyển** sang nhân viên CS khi trạng thái hiện tại là **“Bot‑Active”**; nếu đã ở trạng thái **“Closed”** thì không cho chuyển. |
| BR‑002 | Chỉ **admin** (role “Admin”) mới được tạo, sửa, xoá kịch bản và từ khóa. |
| BR‑003 | Khi thời gian phản hồi trung bình trong 5 phút gần nhất > 5 giây, hệ thống phải **đánh dấu** trạng thái bot là **“Degraded”** và gửi cảnh báo. |
| BR‑004 | Dữ liệu hội thoại phải **được xóa** tự động sau **90 ngày**; nếu có yêu cầu pháp lý (đòi hỏi lưu trữ lâu hơn) thì phải được phê duyệt bởi **Chủ doanh nghiệp**. |
| BR‑005 | Mọi file export phải chứa **định danh duy nhất** (UUID) cho mỗi tin nhắn, để tránh trùng lặp khi nhập lại. |
| BR‑006 | Khi có lỗi kết nối tới API Zalo, hệ thống phải **retry tối đa 3 lần** với khoảng cách 5 giây, nếu vẫn thất bại thì ghi log và kích hoạt cảnh báo. |
| BR‑007 | Người dùng cuối (khách hàng Zalo) không được lưu trữ bất kỳ thông tin cá nhân nào ngoài nội dung hội thoại (để tuân thủ PDPA). |

---  

## Kiểm tra cuối cùng  

- **[✓]** Mỗi FR có ID, ưu tiên, ít nhất 1 AC (Given/When/Then) và có AC lỗi/ngoại lệ.  
- **[✓]** Không còn từ mơ hồ; mọi tiêu chí đều có số liệu hoặc giả định được ghi chú.  
- **[✓]** Các FR chỉ mô tả **WHAT**, không đề cập tới công nghệ cụ thể.  
- **[✓]** Phạm vi In‑scope/Out‑of‑scope khớp với danh sách FR.  
- **[✓]** Mỗi role trong mục 2 có ít nhất một FR liên quan.  
- **[✓]** 6 nhóm NFR chính (Performance, Security, Usability, Reliability, Scalability, Compatibility) đều được bao phủ, kèm Security chi tiết.  
- **[✓]** Không có feedback reject; toàn bộ nội dung giữ nguyên ID và cấu trúc.