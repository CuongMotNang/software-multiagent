# Software Requirements Specification (SRS)  
**Simple Todo App – “TodoLite”**  

**Version:** 1.0 – 05 July 2026  
**Prepared by:** Product Analyst – SoftwareFactory  

---  

## 1. TỔNG QUAN  

### 1.1 Mục đích  
Cung cấp cho người dùng cá nhân một công cụ quản lý công việc (todo) **nhẹ**, **đồng bộ** và **không quảng cáo** trên web, iOS và Android, cho phép tạo, chỉnh sửa, sắp xếp, đánh dấu hoàn thành, tìm kiếm và xuất/nhập dữ liệu.

### 1.2 Phạm vi (In‑scope)  
| Module / Chức năng | Nội dung |
|---------------------|----------|
| Quản lý Todo (CRUD) | Tạo, đọc, cập nhật, xóa todo; đánh dấu hoàn thành; sắp xếp kéo‑thả; lọc, tìm kiếm. |
| Xác thực & ủy quyền | Đăng ký, đăng nhập (email/password) + OAuth (Google, Apple). |
| Đồng bộ đa thiết bị | Lưu trữ cloud, đồng bộ thời gian thực, cập nhật UI ≤ 5 s. |
| Nhắc nhở & hạn chót | Đặt ngày hết hạn, gửi push notification 1 ngày trước deadline. |
| Giao diện người dùng | Responsive UI (desktop ≥ 1024 px, tablet, mobile), chế độ Light/Dark, hỗ trợ accessibility (WCAG 2.1 AA). |
| Export / Import | Xuất danh sách todo dưới dạng CSV, nhập CSV hợp lệ. |
| Tìm kiếm nhanh | Fuzzy search trên tiêu đề và mô tả. |
| Cài đặt cá nhân | Lưu theme, ngôn ngữ (Vi/En). |
| Hỗ trợ offline (phiên bản MVP) | Tạo/ chỉnh sửa khi không có kết nối, đồng bộ khi online. |

### 1.3 Phạm vi (Out‑of‑scope)  
| Nội dung | Lý do |
|----------|-------|
| Quản lý dự án đa‑người dùng, chia sẻ danh sách với người khác | Không phải mục tiêu MVP; sẽ được xem xét trong các phiên bản mở rộng. |
| Tích hợp với lịch Google/Outlook | Không yêu cầu trong bản đầu; có thể thêm sau. |
| Báo cáo thống kê chi tiết (biểu đồ, thời gian hoàn thành) | Không nằm trong core features. |
| Đa ngôn ngữ ngoài Tiếng Việt & Tiếng Anh | Được ghi lại trong NFR‑08 (i18n) nhưng không triển khai trong MVP. |
| Tích hợp thanh toán / gói premium | Ứng dụng miễn phí, không quảng cáo; không có kế hoạch thu phí trong MVP. |

### 1.4 Giả định  
| # | Giả định |
|---|----------|
| A1 | Người dùng có kết nối internet ổn định khi thực hiện đồng bộ (đối với tính năng sync thời gian thực). |
| A2 | Thiết bị người dùng hỗ trợ trình duyệt hiện đại (Chrome ≥ 90, Safari ≥ 14, Firefox ≥ 88) hoặc hệ điều hành iOS ≥ 13 / Android ≥ 8. |
| A3 | Định dạng CSV tuân thủ UTF‑8, các cột cố định: `ID,Title,Description,Status,DueDate,Labels`. |
| A4 | Thông báo push được gửi qua dịch vụ Firebase Cloud Messaging (FCM) và người dùng đã cho phép nhận thông báo. |
| A5 | Người dùng cuối không có yêu cầu đặc thù về bảo mật doanh nghiệp (ví dụ: SSO nội bộ). |

---  

## 2. ĐỐI TƯỢNG NGƯỜI DÙNG  

| Role | Đặc điểm | Quyền hạn |
|------|----------|-----------|
| **End‑User** | • Độ tuổi 15‑65+ <br>• Sử dụng laptop, tablet hoặc smartphone <br>• Tần suất sử dụng: 1‑5 lần/ngày | **Được phép**: Đăng ký, đăng nhập, tạo, đọc, chỉnh sửa, xóa, đánh dấu hoàn thành, sắp xếp, lọc, tìm kiếm, đặt hạn chót, nhận nhắc nhở, chuyển theme, export/import CSV, thay đổi cài đặt cá nhân, sử dụng chế độ offline.<br>**Không được phép**: Truy cập dữ liệu của người dùng khác, thay đổi cấu hình hệ thống, xem log server. |
| **System (Internal Service)** | • Thành phần backend, cloud storage, notification service <br>• Không có giao diện người dùng | **Được phép**: Lưu, đọc, cập nhật, xóa todo; gửi thông báo; thực hiện backup/restore; giám sát uptime.<br>**Không được phép**: Thay đổi quyền người dùng, truy cập dữ liệu không được mã hoá. |
| **Admin (Ops / Support)** – *phạm vi chỉ cho mục bảo trì* | • Nhân viên DevOps, QA <br>• Truy cập qua VPN, xác thực đa yếu tố | **Được phép**: Xem báo cáo uptime, khởi động backup, khôi phục dữ liệu, xem log audit.<br>**Không được phép**: Thay đổi nội dung todo của người dùng, thay đổi UI/UX. |

---  

## 3. YÊU CẦU CHỨC NĂNG  

### 3.1 Quản lý Todo  

#### FR‑001: Tạo Todo  
- **Ưu tiên:** Must  
- **AC1:**  
  - **Given** người dùng đã đăng nhập và đang ở màn hình danh sách todo,  
  - **When** người dùng nhập tiêu đề (độ dài 1‑200 ký tự) và nhấn `Enter` hoặc nút “Add”,  
  - **Then** một mục todo mới với trạng thái **Pending** xuất hiện trong danh sách trong ≤ 300 ms, API `POST /todos` trả về HTTP 201 và payload chứa `id`.  

- **AC2 (Lỗi):**  
  - **Given** tiêu đề rỗng hoặc dài hơn 200 ký tự,  
  - **When** người dùng nhấn “Add”,  
  - **Then** hệ thống hiển thị thông báo lỗi “Title must be 1‑200 characters” và không gửi yêu cầu tới API.  

#### FR‑002: Đọc danh sách Todo (Read)  
- **Ưu tiên:** Must  
- **AC1:**  
  - **Given** người dùng đã đăng nhập,  
  - **When** màn hình Todo được tải,  
  - **Then** hệ thống gọi API `GET /todos` và hiển thị toàn bộ todo của người dùng trong ≤ 1 s (tải trên mạng 3G).  

#### FR‑003: Cập nhật Todo (Edit)  
- **Ưu tiên:** Should  
- **AC1:**  
  - **Given** người dùng đang xem một todo,  
  - **When** người dùng mở modal edit, thay đổi bất kỳ trường (title, description, dueDate, labels) và nhấn “Save”,  
  - **Then** UI cập nhật ngay trong ≤ 300 ms, API `PUT /todos/:id` trả về HTTP 200 và dữ liệu được lưu.  

- **AC2 (Lỗi):**  
  - **Given** tiêu đề mới rỗng hoặc > 200 ký tự,  
  - **When** người dùng nhấn “Save”,  
  - **Then** hiển thị thông báo lỗi và không gửi yêu cầu cập nhật.  

#### FR‑004: Xóa Todo  
- **Ưu tiên:** Must  
- **AC1:**  
  - **Given** người dùng nhấn icon “Trash” trên một todo,  
  - **When** người dùng xác nhận “Are you sure?”,  
  - **Then** API `DELETE /todos/:id` trả về HTTP 204, todo biến mất khỏi UI trong ≤ 300 ms.  

- **AC2 (Lỗi):**  
  - **Given** API trả về lỗi 404 (todo không tồn tại),  
  - **When** người dùng xác nhận xóa,  
  - **Then** hiển thị thông báo “Todo not found – it may have been removed on another device”.  

#### FR‑005: Đánh dấu Todo hoàn thành  
- **Ưu tiên:** Must  
- **AC1:**  
  - **Given** người dùng nhìn thấy một todo ở trạng thái **Pending**,  
  - **When** người dùng click vào checkbox,  
  - **Then** trạng thái thay đổi thành **Done**, UI chuyển sang màu xám và gạch chân, todo di chuyển vào tab “Completed” trong ≤ 300 ms, API `PATCH /todos/:id` trả về HTTP 200.  

- **AC2 (Lỗi):**  
  - **Given** todo đã ở trạng thái **Done**,  
  - **When** người dùng click lại checkbox,  
  - **Then** không có thay đổi nào và hệ thống trả về thông báo “Todo already completed”.  

#### FR‑006: Sắp xếp Todo (Drag‑Drop)  
- **Ưu tiên:** Could  
- **AC1:**  
  - **Given** người dùng đang ở danh sách “Pending”,  
  - **When** người dùng kéo một todo lên vị trí mới,  
  - **Then** vị trí được cập nhật trong UI ngay, và API `PUT /todos/:id/order` (hoặc batch) trả về HTTP 200 trong ≤ 500 ms.  

#### FR‑007: Lọc & Sắp xếp Todo  
- **Ưu tiên:** Should  
- **AC1 (Lọc):**  
  - **Given** người dùng mở bộ lọc,  
  - **When** người dùng chọn một hoặc nhiều nhãn, trạng thái, hoặc khoảng ngày,  
  - **Then** danh sách hiển thị chỉ các todo thỏa mãn tiêu chí trong ≤ 400 ms.  

- **AC2 (Sắp xếp):**  
  - **Given** người dùng chọn “Sort by Due Date Asc”,  
  - **When** danh sách được cập nhật,  
  - **Then** các todo được sắp xếp tăng dần theo `dueDate`.  

#### FR‑008: Tìm kiếm nhanh  
- **Ưu tiên:** Should  
- **AC1:**  
  - **Given** người dùng nhập một chuỗi ký tự vào thanh search,  
  - **When** người dùng gõ,  
  - **Then** danh sách được lọc theo fuzzy match trên `title` và `description` trong ≤ 300 ms, cập nhật kết quả mỗi khi người dùng nhập ký tự mới.  

#### FR‑009: Đặt ngày hết hạn (Due Date)  
- **Ưu tiên:** Should  
- **AC1:**  
  - **Given** người dùng đang tạo hoặc chỉnh sửa một todo,  
  - **When** người dùng chọn ngày trong date‑picker (định dạng ISO 8601),  
  - **Then** trường `dueDate` được lưu và hiển thị dưới dạng `DD/MM/YYYY`.  

#### FR‑010: Gửi nhắc nhở (Reminder)  
- **Ưu tiên:** Should  
- **AC1:**  
  - **Given** một todo có `dueDate` trong tương lai,  
  - **When** thời gian hiện tại là 1 ngày trước `dueDate`,  
  - **Then** hệ thống gửi push notification “Todo “<title>” is due tomorrow” tới thiết bị đã đăng nhập.  

- **AC2 (Lỗi):**  
  - **Given** `dueDate` đã qua,  
  - **When** hệ thống kiểm tra,  
  - **Then** không gửi thông báo.  

#### FR‑011: Đăng ký tài khoản (Email/Password)  
- **Ưu tiên:** Must  
- **AC1:**  
  - **Given** người dùng ở màn hình đăng ký,  
  - **When** người dùng nhập email hợp lệ và mật khẩu ≥ 8 ký tự, trong đó ít nhất một chữ số, và nhấn “Register”,  
  - **Then** hệ thống tạo tài khoản, gửi email xác thực, trả về HTTP 201, và hiển thị thông báo “Verification email sent”.  

- **AC2 (Lỗi):**  
  - **Given** email đã tồn tại,  
  - **When** người dùng nhấn “Register”,  
  - **Then** hiển thị lỗi “Email already in use”.  

#### FR‑012: Đăng nhập (Email/Password)  
- **Ưu tiên:** Must  
- **AC1:**  
  - **Given** người dùng đã xác thực email,  
  - **When** người dùng nhập email và mật khẩu đúng và nhấn “Login”,  
  - **Then** API `POST /auth/login` trả về JWT (hết hạn 1 h) và UI chuyển tới màn hình danh sách todo trong ≤ 500 ms.  

- **AC2 (Lỗi):**  
  - **Given** mật khẩu sai,  
  - **When** người dùng nhấn “Login”,  
  - **Then** hiển thị lỗi “Invalid credentials”.  

#### FR‑013: Đăng nhập bằng OAuth (Google / Apple)  
- **Ưu tiên:** Must  
- **AC1:**  
  - **Given** người dùng nhấn nút “Sign in with Google”,  
  - **When** quá trình OAuth hoàn tất thành công,  
  - **Then** hệ thống nhận token, tạo/đăng nhập tài khoản nội bộ, trả về JWT và chuyển tới danh sách todo trong ≤ 800 ms.  

- **AC2 (Lỗi):**  
  - **Given** người dùng hủy quá trình OAuth,  
  - **When** OAuth trả về lỗi,  
  - **Then** hiển thị thông báo “Authentication cancelled”.  

#### FR‑014: Đồng bộ đa thiết bị (Realtime)  
- **Ưu tiên:** Must  
- **AC1:**  
  - **Given** người dùng đang đăng nhập trên thiết bị A và thực hiện thay đổi (tạo, edit, delete, complete) một todo,  
  - **When** thay đổi được ghi vào cloud,  
  - **Then** thiết bị B nhận sự kiện `onSnapshot` và cập nhật UI trong ≤ 5 s, đồng thời phản hồi API < 500 ms.  

#### FR‑015: Chuyển đổi Theme (Light/Dark)  
- **Ưu tiên:** Could  
- **AC1:**  
  - **Given** người dùng ở màn hình Settings,  
  - **When** người dùng bật toggle “Dark mode”,  
  - **Then** UI chuyển sang theme dark ngay lập tức, và lựa chọn được lưu trong profile (`theme: "dark"`).  

#### FR‑016: Export CSV  
- **Ưu tiên:** Could  
- **AC1:**  
  - **Given** người dùng đã đăng nhập và ở màn hình Settings,  
  - **When** người dùng nhấn “Export CSV”,  
  - **Then** trình duyệt tải về file `todolist_<timestamp>.csv` (UTF‑8) chứa các cột: `ID,Title,Description,Status,DueDate,Labels`.  

#### FR‑017: Import CSV  
- **Ưu tiên:** Could  
- **AC1:**  
  - **Given** người dùng đã chọn file CSV hợp lệ,  
  - **When** người dùng nhấn “Import”,  
  - **Then** hệ thống kiểm tra định dạng; các bản ghi mới được tạo, các bản ghi trùng `ID` được cập nhật; hiển thị thông báo “X items imported, Y items updated”.  

- **AC2 (Lỗi):**  
  - **Given** file không phải CSV hoặc thiếu cột bắt buộc,  
  - **When** người dùng nhấn “Import”,  
  - **Then** hiển thị lỗi “Invalid file format – required columns: ID, Title, …”.  

#### FR‑018: Responsive UI  
- **Ưu tiên:** Must  
- **AC1:**  
  - **Given** thiết bị có chiều rộng ≥ 1024 px (desktop),  
  - **When** người dùng mở ứng dụng,  
  - **Then** layout hiển thị ba cột (header, sidebar, content) và không có thanh cuộn ngang.  

- **AC2:**  
  - **Given** thiết bị có chiều rộng 600‑1023 px (tablet) hoặc < 600 px (mobile),  
  - **When** người dùng mở ứng dụng,  
  - **Then** UI tự động chuyển sang layout một cột, các nút đủ lớn để thao tác bằng ngón tay, và không có phần tử bị cắt.  

#### FR‑019: Offline Support (Optional – MVP)  
- **Ưu tiên:** Could  
- **AC1:**  
  - **Given** người dùng mất kết nối internet,  
  - **When** người dùng tạo, chỉnh sửa hoặc đánh dấu hoàn thành một todo,  
  - **Then** thay đổi được lưu trong local IndexedDB và UI phản hồi ngay; khi kết nối lại, các thay đổi được đồng bộ tới cloud trong ≤ 5 s.  

#### FR‑020: Đăng xuất  
- **Ưu tiên:** Must  
- **AC1:**  
  - **Given** người dùng đang đăng nhập,  
  - **When** người dùng chọn “Logout”,  
  - **Then** token JWT bị xóa khỏi storage, UI chuyển về màn hình đăng nhập trong ≤ 300 ms.  

---

### 3.2 YÊU CẦU PHI CHỨC NĂNG  

| ID | Nhóm | Yêu cầu | Mục tiêu / Metric |
|----|------|----------|-------------------|
| NFR‑001 | **Performance** | Thời gian phản hồi API cho mọi thao tác CRUD ≤ 500 ms (điều kiện tải 100 req/giây). | Đảm bảo trải nghiệm mượt. |
| NFR‑002 | **Performance – Load time** | Thời gian tải trang danh sách todo < 1 s trên mạng 3G. | Tránh cảm giác chậm. |
| NFR‑003 | **Security** | Giao tiếp qua TLS 1.2+; mật khẩu lưu bằng bcrypt (cost ≥ 12); JWT ký bằng HS256, thời hạn 1 h, refresh token 24 h. | Bảo vệ dữ liệu người dùng. |
| NFR‑004 | **Security – OWASP** | Không có lỗ hổng Critical/High theo OWASP Top 10 sau penetration test. | Ngăn chặn tấn công. |
| NFR‑005 | **Usability** | Người dùng mới (độ tuổi 15‑65) hoàn thành luồng “Create → Complete” trong ≤ 3 bước, không cần tài liệu hướng dẫn. | Đánh giá qua user test. |
| NFR‑006 | **Reliability / Availability** | 99.9 % uptime hàng tháng; thời gian phục hồi (MTTR) ≤ 30 phút cho lỗi dịch vụ. | Đảm bảo dữ liệu luôn sẵn sàng. |
| NFR‑007 | **Scalability** | Hệ thống chịu tải 10 k đồng thời (các thiết bị kết nối) với response ≤ 500 ms, không lỗi > 0.1 %. | Đáp ứng tăng trưởng người dùng. |
| NFR‑008 | **Compatibility** | Hỗ trợ Chrome ≥ 90, Safari ≥ 14, Firefox ≥ 88, Edge ≥ 90; iOS ≥ 13, Android ≥ 8. | Đảm bảo trải nghiệm trên hầu hết thiết bị. |
| NFR‑009 | **Accessibility** | Đạt chuẩn WCAG 2.1 AA (độ tương phản ≥ 4.5:1, hỗ trợ navigation bằng bàn phím, ARIA labels). | Đáp ứng nhu cầu người khuyết tật. |
| NFR‑010 | **Data Privacy** | Tuân thủ GDPR & CCPA: cho phép người dùng yêu cầu xóa tài khoản & dữ liệu, lưu trữ consent. | Pháp lý. |
| NFR‑011 | **Maintainability** | Code coverage ≥ 80 % (unit + integration), linting không lỗi, CI pipeline tự động chạy test và báo cáo. | Dễ bảo trì, giảm bug. |
| NFR‑012 | **Internationalization (i18n)** | Hỗ trợ Tiếng Việt và Tiếng Anh; định dạng ngày hiển thị theo locale người dùng. | Mở rộng thị trường. |
| NFR‑013 | **Backup & Recovery** | Sao lưu DB hàng ngày; khả năng khôi phục dữ liệu trong ≤ 4 h, độ mất mát dữ liệu ≤ 0 % (point‑in‑time). | Đảm bảo an toàn dữ liệu. |
| NFR‑014 | **Device Compatibility (Responsive)** | UI không có lỗi layout trên các độ phân giải: desktop ≥ 1024 px, tablet 600‑1023 px, mobile < 600 px. | Đảm bảo trải nghiệm đa thiết bị. |

> **Lưu ý:** Các NFR được viết dưới dạng đo lường để có thể kiểm thử tự động hoặc bằng công cụ giám sát.

---

## 4. QUY TẮC NGHIỆP VỤ  

| ID | Quy tắc nghiệp vụ |
|----|-------------------|
| BR‑001 | **Quyền sở hữu:** Người dùng chỉ có thể xem, chỉnh sửa, xóa, hoặc đánh dấu hoàn thành các todo mà họ đã tạo. |
| BR‑002 | **Hoàn thành:** Todo chỉ được chuyển sang trạng thái “Done” nếu hiện tại ở trạng thái “Pending”. |
| BR‑003 | **Đồng bộ:** Khi một thiết bị thực hiện thay đổi, tất cả các thiết bị khác của cùng một người dùng phải nhận cập nhật trong ≤ 5 s; nếu không, hệ thống sẽ ghi lại lỗi đồng bộ và thông báo “Sync failed – will retry”. |
| BR‑004 | **Nhắc nhở:** Thông báo push chỉ được gửi một lần cho mỗi todo, và chỉ khi `dueDate` còn cách hiện tại **≥ 1 ngày**. |
| BR‑005 | **Export/Import:** Chỉ người dùng đã xác thực (đăng nhập) mới được thực hiện export hoặc import CSV. |
| BR‑006 | **Password Policy:** Mật khẩu phải có ít nhất 8 ký tự, bao gồm ít nhất một chữ số và một ký tự chữ cái. |
| BR‑07 | **Xóa tài khoản:** Khi người dùng yêu cầu xóa tài khoản, toàn bộ todo liên quan phải bị xóa vĩnh viễn trong vòng 24 h và không thể khôi phục. |
| BR‑08 | **Thời gian hoạt động token:** JWT hết hạn sau 1 h; khi token hết hạn, yêu cầu API trả về 401 và yêu cầu người dùng đăng nhập lại. |

---  

## 5. KIỂM TRA TRƯỚC KHI OUTPUT (Checklist)  

- [x] Mỗi FR có ID, ưu tiên, ít nhất 1 AC theo format **Given/When/Then** (có AC happy và lỗi).  
- [x] Không còn từ mơ hồ; mọi tiêu chí đều có số liệu hoặc giả định được ghi rõ.  
- [x] FR chỉ mô tả **WHAT**, không đề cập công nghệ (không nhắc tới Firebase, React, v.v.).  
- [x] Phạm vi In‑scope/Out‑of‑scope khớp với danh sách FR.  
- [x] Tất cả role (End‑User, System, Admin) đều có ít nhất một FR liên quan.  
- [x] Đã bao phủ đầy đủ 6 nhóm NFR chính, bao gồm Security.  
- [x] Không có phần nào được thay đổi không liên quan (phiên bản này không phải bản sửa).  

---  

*End of SRS.*