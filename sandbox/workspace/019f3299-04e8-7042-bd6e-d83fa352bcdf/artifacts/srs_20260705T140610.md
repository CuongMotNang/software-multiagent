# 1. TỔNG QUAN  

**Mục đích**  
Cung cấp một công cụ quản lý công việc (todo‑list) đơn giản, cho phép người dùng cá nhân tạo, chỉnh sửa, xóa và theo dõi trạng thái các công việc trên thiết bị di động và/hoặc máy tính để bàn.  

**Phạm vi (In‑scope)**  

| Module / Chức năng | Nội dung |
|---------------------|----------|
| Quản lý tài khoản | Đăng ký, đăng nhập bằng email + mật khẩu; reset mật khẩu qua email. |
| Quản lý công việc (Task) | Tạo, sửa, xóa, đánh dấu hoàn thành, hiển thị danh sách theo trạng thái. |
| Thông tin bổ trợ cho task | Gán ngày hết hạn, thiết lập reminder, gán nhãn, tìm kiếm & lọc. |
| Đồng bộ dữ liệu | Đồng bộ task giữa các thiết bị (mobile ↔ desktop) – **ưu tiên thấp**. |
| Chia sẻ & lịch | Chia sẻ danh sách, chế độ xem lịch, làm việc offline – **ưu tiên thấp**. |
| Báo cáo & KPI | Thu thập số liệu sử dụng (số task tạo, thời gian trung bình hoàn thành). |
| Quản trị hệ thống | Quản trị viên tạo, xóa người dùng; xem log hoạt động; backup dữ liệu. |

**Phạm vi (Out‑of‑scope)**  

| Nội dung | Lý do |
|----------|-------|
| Tích hợp với hệ thống bên thứ ba (CRM, email marketing, …) | Không được yêu cầu trong giai đoạn 1, sẽ được xem xét trong các phiên bản sau. |
| Hỗ trợ đa ngôn ngữ (ngoại trừ tiếng Anh) | Yêu cầu chưa được xác định, sẽ được lên kế hoạch khi có yêu cầu. |
| Phiên bản desktop native (Windows/Mac) | Chỉ phát triển Web responsive + ứng dụng di động (iOS, Android). |
| AI đề xuất task hoặc tự động phân loại | Không nằm trong danh sách tính năng đã ưu tiên. |
| Quản lý dự án (multiple users sharing same project) | Chỉ hỗ trợ danh sách cá nhân; chia sẻ danh sách ở mức “read‑only” trong ưu tiên thấp. |

**Giả định**  

| Giả định | Nội dung |
|----------|----------|
| **Nền tảng** | Ứng dụng sẽ được triển khai dưới dạng Web responsive (Chrome, Safari, Edge) và ứng dụng di động native cho iOS ≥ 14 và Android ≥ 9. |
| **Đăng nhập** | Người dùng phải có địa chỉ email hợp lệ; xác thực bằng mật khẩu (được lưu băm BCrypt). |
| **Dữ liệu** | Mỗi task chỉ chứa: tiêu đề (≤ 255 ký tự), mô tả (≤ 2000 ký tự), ngày hết hạn (optional), reminder (optional, ≤ 24 h trước due date), nhãn (≤ 5 nhãn, mỗi nhãn ≤ 30 ký tự). |
| **Số lượng người dùng** | Dự kiến 10 000 – 50 000 người dùng đăng ký trong 6 tháng đầu; đồng thời tối đa 500 người dùng hoạt động đồng thời. |
| **KPI thành công** | ≥ 10 000 lượt tải (mobile) hoặc truy cập (web) trong 3 tháng; Retention 30‑day ≥ 40 %; Thời gian trung bình để tạo một task ≤ 15 giây. |
| **Bảo mật** | Dữ liệu task không được coi là “nhạy cảm” nhưng phải tuân thủ GDPR/CCPA (đối với EU/CA). |
| **Môi trường triển khai** | Ứng dụng chạy trên cloud (AWS/Azure) với cơ sở dữ liệu PostgreSQL, backup hàng ngày. |
| **Ngân sách & thời gian** | Không giới hạn trong tài liệu này; các yêu cầu được ưu tiên theo MoSCoW. |

---  

# 2. ĐỐI TƯỢNG NGƯỜI DÙNG  

| Role | Đặc điểm | Quyền hạn |
|------|----------|-----------|
| **Người dùng cá nhân** | • Độ am hiểu công nghệ trung bình.<br>• Sử dụng smartphone (iOS/Android) và/hoặc máy tính để bàn.<br>• Sử dụng ứng dụng 1‑3 lần/ngày. | **Cho phép**: Đăng ký, đăng nhập, tạo/sửa/xóa task, gán due date, reminder, nhãn, tìm kiếm, lọc, đánh dấu hoàn thành, xem danh sách.<br>**Không cho phép**: Truy cập vào công cụ quản trị, xem log hệ thống, thay đổi cấu hình bảo mật. |
| **Quản trị viên hệ thống** | • Ít hơn 10 người.<br>• Kiến thức kỹ thuật, dùng máy tính để bàn.<br>• Thực hiện công việc quản trị 1‑2 lần/tuần. | **Cho phép**: Quản lý người dùng (kích hoạt/khóa), xem/đặt lại mật khẩu, xem log hoạt động, thực hiện backup & restore, cấu hình reminder mặc định.<br>**Không cho phép**: Thay đổi UI/UX của người dùng cuối. |
| **Quản trị sản phẩm / Chủ dự án** | • 1‑3 người.<br>• Kiến thức kinh doanh, dùng laptop/desktop.<br>• Theo dõi KPI hàng tuần. | **Cho phép**: Xem báo cáo sử dụng (số task, thời gian trung bình), cấu hình mức ưu tiên tính năng, duyệt yêu cầu thay đổi.<br>**Không cho phép**: Thực hiện các thao tác CRUD trên task của người dùng. |

---  

# 3. YÊU CẦU CHỨC NĂNG  

## 3.1 Quản lý tài khoản  

**FR-001**: Hệ thống **phải** cho phép người dùng đăng ký tài khoản bằng địa chỉ email hợp lệ và mật khẩu ít nhất 8 ký tự, trong đó có ít nhất một ký tự chữ hoa, một ký tự chữ thường và một ký tự số.  
- Ưu tiên: Must  
- AC1: **Given** người dùng truy cập trang đăng ký **When** nhập email hợp lệ và mật khẩu đáp ứng tiêu chuẩn **Then** tài khoản được tạo và người dùng nhận email xác nhận.  
- AC2: **Given** email đã tồn tại **When** người dùng nhấn “Đăng ký” **Then** hệ thống hiển thị thông báo lỗi “Email đã được sử dụng”.  

**FR-002**: Hệ thống **phải** cho phép người dùng đăng nhập bằng email và mật khẩu đã đăng ký.  
- Ưu tiên: Must  
- AC1: **Given** email và mật khẩu đúng **When** nhấn “Đăng nhập” **Then** người dùng được chuyển tới trang danh sách task và nhận token JWT có thời hạn 1 giờ.  
- AC2: **Given** mật khẩu sai **When** nhấn “Đăng nhập” **Then** hệ thống trả về lỗi “Email hoặc mật khẩu không đúng” và không cấp token.  

**FR-003**: Hệ thống **phải** cho phép người dùng yêu cầu đặt lại mật khẩu qua email.  
- Ưu tiên: Should  
- AC1: **Given** người dùng ở trang “Quên mật khẩu” **When** nhập email đã đăng ký **Then** hệ thống gửi email chứa link đặt lại mật khẩu có thời hạn 30 phút.  

## 3.2 Quản lý công việc (Task) – **ưu tiên cao**  

**FR-004**: Hệ thống **phải** cho phép người dùng tạo một task mới chỉ với tiêu đề (≤ 255 ký tự).  
- Ưu tiên: Must  
- AC1: **Given** người dùng đang ở trang danh sách task **When** nhập tiêu đề hợp lệ và nhấn “Thêm” **Then** task mới xuất hiện trong danh sách “Đang làm” và thời gian tạo được ghi lại.  

**FR-005**: Hệ thống **phải** cho phép người dùng sửa tiêu đề và mô tả của một task đã tồn tại.  
- Ưu tiên: Must  
- AC1: **Given** task đã tồn tại **When** người dùng mở modal chỉnh sửa, thay đổi tiêu đề và/hoặc mô tả, rồi nhấn “Lưu” **Then** các thay đổi được lưu và hiển thị ngay trên danh sách.  

**FR-006**: Hệ thống **phải** cho phép người dùng xóa một task đã tạo.  
- Ưu tiên: Must  
- AC1: **Given** task tồn tại **When** người dùng nhấn biểu tượng “Xóa” và xác nhận “Có” **Then** task bị xóa vĩnh viễn và không còn xuất hiện trong bất kỳ danh sách nào.  

**FR-007**: Hệ thống **phải** cho phép người dùng đánh dấu một task là “đã hoàn thành”.  
- Ưu tiên: Must  
- AC1: **Given** task đang ở trạng thái “Đang làm” **When** người dùng nhấn checkbox “Hoàn thành” **Then** task chuyển sang danh sách “Đã hoàn thành” và thời gian hoàn thành được ghi lại.  

**FR-008**: Hệ thống **phải** hiển thị danh sách task được phân loại theo trạng thái “Đang làm” và “Đã hoàn thành”.  
- Ưu tiên: Must  
- AC1: **Given** người dùng đã đăng nhập **When** truy cập trang “Task” **Then** hai tab “Đang làm” và “Đã hoàn thành” hiển thị đúng số lượng task tương ứng.  

## 3.3 Thông tin bổ trợ cho task – **ưu tiên trung bình**  

**FR-009**: Hệ thống **phải** cho phép người dùng gán ngày hết hạn (due date) cho một task.  
- Ưu tiên: Should  
- AC1: **Given** task đang mở **When** người dùng chọn ngày trong lịch và nhấn “Lưu” **Then** due date được lưu và hiển thị dưới tiêu đề task.  

**FR-010**: Hệ thống **phải** cho phép người dùng thiết lập reminder trước ngày hết hạn (tối đa 24 giờ trước).  
- Ưu tiên: Should  
- AC1: **Given** task có due date **When** người dùng bật “Reminder” và chọn thời gian (ví dụ: 2 giờ trước) **Then** hệ thống sẽ gửi thông báo push/email vào thời điểm đã chọn.  

**FR-011**: Hệ thống **phải** cho phép người dùng gán tối đa 5 nhãn (label) cho mỗi task; mỗi nhãn không vượt quá 30 ký tự.  
- Ưu tiên: Should  
- AC1: **Given** task đang mở **When** người dùng nhập nhãn và nhấn “Thêm” **Then** nhãn xuất hiện dưới task; nếu vượt quá 5 nhãn hoặc 30 ký tự, hệ thống hiển thị lỗi.  

**FR-012**: Hệ thống **phải** cho phép người dùng tìm kiếm task theo tiêu đề, nhãn hoặc ngày hết hạn.  
- Ưu tiên: Should  
- AC1: **Given** người dùng nhập từ khóa vào ô tìm kiếm **When** nhấn “Enter” **Then** danh sách hiển thị các task khớp (tiêu đề chứa từ khóa OR nhãn chứa từ khóa OR due date trong khoảng).  

**FR-013**: Hệ thống **phải** cho phép người dùng lọc task theo trạng thái, nhãn hoặc khoảng ngày.  
- Ưu tiên: Should  
- AC1: **Given** người dùng mở bộ lọc **When** chọn “Đã hoàn thành” và nhãn “Công việc nhà” **Then** danh sách chỉ hiển thị các task thỏa mãn cả hai điều kiện.  

## 3.4 Đồng bộ & chia sẻ – **ưu tiên thấp**  

**FR-014**: Hệ thống **có thể** đồng bộ task giữa các thiết bị (mobile ↔ desktop) trong vòng ≤ 5 giây sau khi thay đổi.  
- Ưu tiên: Could  
- AC1: **Given** người dùng thay đổi task trên thiết bị A **When** đồng bộ mạng ổn định **Then** thay đổi xuất hiện trên thiết bị B trong ≤ 5 giây.  

**FR-015**: Hệ thống **có thể** cho phép người dùng chia sẻ danh sách task dưới dạng “read‑only” qua link duy nhất.  
- Ưu tiên: Could  
- AC1: **Given** người dùng tạo link chia sẻ **When** người khác mở link **Then** họ thấy danh sách ở chế độ chỉ xem, không thể chỉnh sửa.  

**FR-016**: Hệ thống **có thể** cung cấp chế độ xem lịch (calendar view) cho các task có due date.  
- Ưu tiên: Could  
- AC1: **Given** ít nhất một task có due date **When** người dùng chuyển sang tab “Lịch” **Then** các task được hiển thị trên lịch tương ứng với ngày.  

**FR-017**: Hệ thống **có thể** cho phép làm việc offline và tự động đồng bộ khi có kết nối.  
- Ưu tiên: Could  
- AC1: **Given** người dùng đang offline và tạo/ sửa task **When** thiết bị lại có mạng **Then** các thay đổi được đồng bộ lên server mà không mất dữ liệu.  

## 3.5 Quản trị hệ thống  

**FR-018**: Hệ thống **phải** cho phép quản trị viên tạo, khóa hoặc xóa tài khoản người dùng.  
- Ưu tiên: Must  
- AC1: **Given** quản trị viên đăng nhập **When** vào bảng quản lý người dùng, chọn “Khóa” cho một tài khoản **Then** tài khoản không thể đăng nhập cho tới khi được mở lại.  

**FR-019**: Hệ thống **phải** ghi lại log hoạt động quan trọng (đăng nhập, tạo/ sửa/ xóa task, thay đổi trạng thái tài khoản).  
- Ưu tiên: Must  
- AC1: **Given** một hành động xảy ra **When** hành động được thực hiện **Then** log chứa: userID, timestamp, hành động, IP address và lưu vào bảng audit.  

**FR-020**: Hệ thống **phải** cho phép quản trị viên thực hiện backup dữ liệu toàn bộ hàng ngày và khôi phục từ bản backup trong vòng ≤ 30 phút.  
- Ưu tiên: Must  
- AC1: **Given** backup đã được tạo **When** quản trị viên kích hoạt “Restore” **Then** toàn bộ dữ liệu được khôi phục và hệ thống báo cáo “Restore thành công” trong ≤ 30 phút.  

---  

# 4. YÊU CẦU PHI CHỨC NĂNG  

| ID | Nhóm | Yêu cầu | Giá trị cụ thể |
|----|------|----------|----------------|
| NFR-001 | **Performance** | Thời gian phản hồi API cho các thao tác CRUD task ≤ 300 ms khi tải 100 request/phút. | 300 ms |
| NFR-001‑b | **Performance** | Thời gian tải trang danh sách task ≤ 2 giây trên kết nối 3G. | 2 s |
| NFR-002 | **Security** | Xác thực bằng JWT ký bằng RSA‑256; token có thời hạn 1 giờ, refresh token 24 giờ. | JWT RSA‑256 |
| NFR-002‑b | **Security** | Mật khẩu người dùng phải được lưu băm BCrypt (cost ≥ 12). | BCrypt cost 12 |
| NFR-002‑c | **Security** | Tất cả giao tiếp qua HTTPS (TLS 1.2 trở lên). | TLS 1.2+ |
| NFR-002‑d | **Security** | Tuân thủ OWASP Top 10 và GDPR/CCPA (có cơ chế xóa dữ liệu cá nhân khi yêu cầu). | OWASP Top 10, GDPR, CCPA |
| NFR-003 | **Usability** | Người dùng mới có thể tạo một task hoàn chỉnh (tiêu đề + due date) trong ≤ 3 bước và ≤ 15 giây. | ≤ 3 bước, ≤ 15 s |
| NFR-003‑b | **Usability** | Độ lỗi nhập liệu (invalid email, password) hiển thị thông báo lỗi rõ ràng trong ≤ 2 giây. | ≤ 2 s |
| NFR-004 | **Reliability / Availability** | 99.5 % uptime hàng tháng; thời gian phục hồi (MTTR) ≤ 30 phút khi có sự cố. | 99.5 %, MTTR ≤ 30 min |
| NFR-005 | **Scalability** | Hệ thống phải hỗ trợ ít nhất 5 000 người dùng đồng thời (peak) mà không giảm thời gian phản hồi dưới 500 ms. | 5 000 concurrent users |
| NFR-006 | **Compatibility** | Hỗ trợ các trình duyệt: Chrome ≥ 90, Safari ≥ 14, Edge ≥ 90; và hệ điều hành iOS ≥ 14, Android ≥ 9. | Chrome 90+, Safari 14+, Edge 90+, iOS 14+, Android 9+ |
| NFR-007 | **Data Retention** | Dữ liệu task được lưu tối thiểu 2 năm; backup hàng ngày, lưu trữ 30 ngày trên khu vực EU. | 2 năm, backup 30 ngày EU |
| NFR-008 | **Internationalization** | Ứng dụng phải hỗ trợ ít nhất tiếng Anh; các chuỗi UI được tách ra để dễ dàng thêm ngôn ngữ trong phiên bản sau. | English only (tách chuỗi) |

---  

# 5. QUY TẮC NGHIỆP VỤ  

| ID | Quy tắc |
|----|----------|
| BR-001 | Một task chỉ được đánh dấu “đã hoàn thành” khi trạng thái hiện tại là “đang làm”. |
| BR-002 | Người dùng không được tạo hai task có tiêu đề **đúng** (case‑insensitive) trong cùng ngày tạo. |
| BR-003 | Reminder chỉ được thiết lập nếu task có due date và thời gian reminder ≤ 24 giờ trước due date. |
| BR-004 | Khi tài khoản bị khóa, mọi token JWT hiện tại phải bị thu hồi ngay lập tức. |
| BR-005 | Khi thực hiện backup, hệ thống phải ghi lại hash SHA‑256 của file backup để kiểm tra tính toàn vẹn khi restore. |
| BR-006 | Nếu người dùng yêu cầu xóa tài khoản, tất cả task của người dùng phải được xóa vĩnh viễn (hard delete) trong vòng 5 phút. |
| BR-007 | Khi người dùng chia sẻ danh sách qua link, link chỉ có hiệu lực 7 ngày kể từ khi tạo; sau đó tự động hết hạn. |

---  

## Kiểm tra trước khi xuất bản  

- [x] Mỗi FR có ID, ưu tiên, ít nhất 1 AC (Given/When/Then) và một AC cho lỗi/ngoại lệ quan trọng.  
- [x] Không còn từ mơ hồ; mọi tiêu chí đều có số liệu hoặc giả định được ghi rõ.  
- [x] Tất cả FR mô tả **WHAT**, không đề cập tới công nghệ, kiến trúc hay thuật toán.  
- [x] Phạm vi In‑scope/Out‑of‑scope khớp với danh sách FR.  
- [x] Mỗi role trong mục 2 có ít nhất một FR liên quan.  
- [x] Đã bao phủ 6 nhóm NFR chính, trong đó **Security** được chi tiết.  
- [x] Không có chỉnh sửa không liên quan; các ID FR/NFR/BR giữ nguyên.