# Software Requirements Specification (SRS)  
**Dự án:** Chatbot tự động trên nền tảng Zalo Official Account  
**Ngày:** 02‑07‑2026  

---  

## 1. TỔNG QUAN  

| **Mục đích** | Hệ thống chatbot Zalo tự động trả lời, thu thập và lưu trữ thông tin khách hàng, lên lịch gửi tin nhắn, và cung cấp báo cáo thống kê để giảm tải công việc CSKH, tăng tốc độ phản hồi và hỗ trợ hoạt động marketing. |
|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Phạm vi (In‑scope)** | 1. Tự động trả lời tin nhắn dựa trên kịch bản.<br>2. Thu thập & lưu trữ dữ liệu khách hàng (họ tên, số điện thoại, nhu cầu, đồng ý tiếp thị).<br>3. Lên lịch gửi tin nhắn tự động (nhắc hẹn, follow‑up, khuyến mãi).<br>4. Báo cáo thống kê hoạt động bot (số hội thoại, thời gian phản hồi trung bình, tần suất gửi).<br>5. Cấu hình tùy chỉnh văn phong cho từng nhóm khách hàng/chiến dịch.<br>6. Quản lý trạng thái bot (bật/tắt), xem log hội thoại, thiết lập giờ hoạt động.<br>7. Thiết lập quy tắc thời gian gửi (không gửi ngoài giờ hành chính, tuân thủ giới hạn Zalo).<br>8. Gửi thông báo lỗi/ cảnh báo cho quản trị viên.<br>9. Thu thập đồng ý (opt‑in) trước khi gửi tin nhắn marketing.<br>10. Cung cấp API cơ bản để đồng bộ dữ liệu khách hàng với CRM (độ ưu tiên thấp, chỉ khai báo giao diện). |
| **Phạm vi (Out‑of‑scope)** | 1. Tích hợp sâu với CRM/ERP (đồng bộ hai‑chiều, workflow tự động).<br>2. Hỗ trợ đa ngôn ngữ (chỉ tiếng Việt trong phiên bản này).<br>3. Phân tích AI nâng cao (sentiment analysis, NLP tự học).<br>4. Quản lý chiến dịch quảng cáo trên nền tảng khác (Facebook, Google).<br>5. Tự động tạo nội dung kịch bản (cần con người soạn). |
| **Giả định** | - Số lượng người dùng cuối đồng thời tối đa **500** (được ước tính dựa trên quy mô khách hàng tiềm năng).<br>- Giới hạn gửi tin Zalo là **10 000 tin/ngày** (theo chính sách Zalo hiện hành).<br>- Mọi dữ liệu cá nhân được lưu trữ trên **cơ sở dữ liệu mã hoá AES‑256** và chỉ truy cập qua HTTPS.<br>- Người dùng cuối (khách hàng Zalo) có thiết bị **smartphone Android hoặc iOS** và không cần cài đặt phần mềm bổ sung.<br>- Các bên liên quan có quyền truy cập Internet ổn định (latency < 100 ms).<br>- Hệ thống sẽ được triển khai trên môi trường **cloud** có khả năng auto‑scale.  

---  

## 2. ĐỐI TƯỢNG NGƯỜI DÙNG  

| Role | Đặc điểm | Quyền hạn (FR liên quan) |
|------|----------|---------------------------|
| **Giám đốc / Chủ doanh nghiệp** | Sử dụng desktop, ít kiến thức kỹ thuật, quan tâm báo cáo tổng quan, quyết định chiến lược. | Xem báo cáo (FR‑010), nhận cảnh báo (FR‑009). |
| **Quản trị viên bot (CSKH)** | 5‑15 người, dùng desktop/laptop, hiểu quy trình kịch bản, quản lý nội dung. | Tạo/ chỉnh sửa kịch bản (FR‑001), bật/tắt bot (FR‑006), cấu hình văn phong (FR‑005), thiết lập giờ hoạt động (FR‑006), xem log (FR‑006). |
| **Người dùng cuối (Khách hàng Zalo)** | Smartphone Android/iOS, không dùng máy tính, không có kiến thức kỹ thuật. | Nhận tin tự động, cung cấp đồng ý (FR‑008), cung cấp thông tin cá nhân (FR‑002). |
| **Đội IT / Nhân viên tích hợp** | Kỹ thuật, hiểu API Zalo, quản trị hệ thống. | Cấu hình kết nối API (FR‑011), nhận thông báo lỗi (FR‑009), thiết lập quy tắc thời gian gửi (FR‑007). |
| **Bộ phận pháp chế / Bảo mật dữ liệu** | Kiến thức về luật bảo vệ dữ liệu, ít quan tâm tới chức năng. | Kiểm tra log lưu trữ (BR‑002), xác nhận cơ chế đồng ý (FR‑008). |

---  

## 3. YÊU CẦU CHỨC NĂNG  

### 3.1. Tự động trả lời tin nhắn  

**FR-001:** Hệ thống **phải** trả lời tự động các tin nhắn đến Zalo dựa trên kịch bản đã định nghĩa cho từng từ khóa hoặc nội dung.  
- **Ưu tiên:** Must  
- **AC:**  
  - **AC1:** *Given* một tin nhắn mới từ khách hàng chứa từ khóa “giá” *When* kịch bản “Giá sản phẩm” đã được kích hoạt *Then* hệ thống gửi phản hồi nội dung “Sản phẩm hiện có giá …” trong vòng **2 giây**.  
  - **AC2:** *Given* tin nhắn không khớp bất kỳ kịch bản nào *When* nhận tin *Then* hệ thống trả lời “Xin lỗi, hiện tại chúng tôi không hiểu yêu cầu của bạn, vui lòng liên hệ CSKH.” trong vòng **2 giây**.  

### 3.2. Thu thập và lưu trữ thông tin khách hàng  

**FR-002:** Hệ thống **phải** lưu trữ các trường dữ liệu khách hàng (họ tên, số điện thoại, nhu cầu, trạng thái đồng ý) mỗi khi chúng được thu thập trong hội thoại.  
- **Ưu tiên:** Must  
- **AC:**  
  - **AC1:** *Given* khách hàng cung cấp họ tên và số điện thoại *When* dữ liệu được nhập vào form hội thoại *Then* hệ thống lưu trữ bản ghi trong cơ sở dữ liệu và trả về **Mã khách hàng (CustomerID) duy nhất** trong vòng **1 giây**.  
  - **AC2 (Lỗi):** *Given* trường số điện thoại không hợp lệ (không phải dạng số VN) *When* người dùng nhập *Then* hệ thống hiển thị thông báo “Số điện thoại không hợp lệ” và không lưu bản ghi.  

### 3.3. Lên lịch gửi tin nhắn tự động  

**FR-003:** Hệ thống **phải** cho phép quản trị viên tạo lịch gửi tin nhắn (nhắc hẹn, follow‑up, khuyến mãi) dựa trên thời gian cố định hoặc sự kiện (ví dụ: 3 ngày sau lần mua).  
- **Ưu tiên:** Must  
- **AC:**  
  - **AC1:** *Given* quản trị viên nhập nội dung tin, chọn “gửi 3 ngày sau ngày mua” *When* lưu lịch *Then* hệ thống tạo bản ghi lịch và sẽ tự động gửi tin vào thời điểm dự kiến.  
  - **AC2 (Lỗi):** *Given* thời gian đã qua hoặc vượt giới hạn Zalo (hơn 30 ngày) *When* lưu lịch *Then* hệ thống trả về lỗi “Thời gian không hợp lệ”.  

### 3.4. Báo cáo thống kê hoạt động bot  

**FR-004:** Hệ thống **phải** cung cấp báo cáo tổng hợp (số hội thoại, thời gian phản hồi trung bình, tần suất gửi tin) theo ngày, tuần, tháng.  
- **Ưu tiên:** Must  
- **AC:**  
  - **AC1:** *Given* Giám đốc yêu cầu báo cáo tuần hiện tại *When* nhấn “Xuất báo cáo tuần” *Then* hệ thống trả về file PDF/Excel trong vòng **3 giây** với các chỉ số: Tổng hội thoại, Avg. Response Time (ms), Tin gửi thành công (%).  

### 3.5. Cấu hình tùy chỉnh văn phong  

**FR-005:** Hệ thống **phải** cho phép quản trị viên thiết lập “văn phong” (giọng điệu, mức độ trang trọng) cho từng nhóm khách hàng hoặc chiến dịch, và áp dụng tự động khi trả lời.  
- **Ưu tiên:** Should  
- **AC:**  
  - **AC1:** *Given* nhóm khách hàng “Doanh nghiệp” được gán mức “Trang trọng” *When* bot trả lời *Then* nội dung tin nhắn sẽ bao gồm các từ ngữ đã định nghĩa cho mức “Trang trọng”.  

### 3.6. Quản lý và giám sát bot  

**FR-006:** Hệ thống **phải** cho phép quản trị viên bật/tắt bot, xem log hội thoại, và thiết lập giờ hoạt động (giờ làm việc).  
- **Ưu tiên:** Must  
- **AC:**  
  - **AC1:** *Given* bot đang ở trạng thái “Bật” *When* quản trị viên nhấn “Tắt bot” *Then* bot ngừng trả lời mọi tin nhắn ngay lập tức và trạng thái hiển thị “Tắt”.  
  - **AC2:** *Given* quản trị viên mở giao diện log *When* chọn ngày cụ thể *Then* hệ thống hiển thị danh sách hội thoại với thời gian, nội dung, và trạng thái (thành công/ lỗi).  

### 3.7. Thiết lập quy tắc thời gian gửi  

**FR-007:** Hệ thống **phải** ngăn không cho gửi tin nhắn ngoài giờ hành chính (08:00‑18:00, Thứ 2‑Thứ 6) trừ khi được đánh dấu “khẩn cấp”.  
- **Ưu tiên:** Must  
- **AC:**  
  - **AC1:** *Given* lịch gửi tin được thiết lập vào 20:00 *When* thời gian hiện tại là 20:00 *Then* hệ thống hoãn gửi và ghi lại “Hoãn do ngoài giờ”.  

### 3.8. Gửi thông báo lỗi / cảnh báo  

**FR-008:** Hệ thống **phải** gửi thông báo qua email và Zalo Official Account cho quản trị viên khi xảy ra lỗi hệ thống hoặc khi tỷ lệ lỗi vượt **5 %** trong một giờ.  
- **Ưu tiên:** Must  
- **AC:**  
  - **AC1:** *Given* lỗi “Không thể kết nối API Zalo” xảy ra *When* lỗi được ghi nhận *Then* hệ thống gửi email và tin Zalo tới danh sách admin trong vòng **30 giây**.  

### 3.9. Thu thập đồng ý (opt‑in) trước tin marketing  

**FR-009:** Hệ thống **phải** yêu cầu khách hàng đồng ý (opt‑in) trước khi nhận bất kỳ tin nhắn marketing nào và lưu trạng thái đồng ý.  
- **Ưu tiên:** Must  
- **AC:**  
  - **AC1:** *Given* khách hàng chưa đồng ý *When* bot chuẩn bị gửi tin marketing *Then* bot gửi tin “Bạn có muốn nhận thông tin khuyến mãi? Trả lời YES để đồng ý.”  
  - **AC2:** *Given* khách hàng trả lời “YES” *When* tin được nhận *Then* hệ thống lưu trạng thái “Đã đồng ý” và cho phép gửi tin marketing tiếp theo.  

### 3.10. Cung cấp API đồng bộ dữ liệu khách hàng (độ ưu tiên thấp)  

**FR-010:** Hệ thống **có thể** (Could) cung cấp endpoint RESTful `/api/v1/customers` cho phép truy xuất danh sách khách hàng đã đồng ý nhận tin marketing, trả về JSON trong vòng **500 ms** cho truy vấn ≤ 1000 bản ghi.  
- **Ưu tiên:** Could  
- **AC:**  
  - **AC1:** *Given* yêu cầu GET `/api/v1/customers?opt_in=true` *When* API được gọi với token hợp lệ *Then* trả về danh sách khách hàng (max 1000) trong ≤ 500 ms.  

---  

## 4. YÊU CẦU PHI CHỨC NĂNG  

| ID | Nhóm | Yêu cầu | Tiêu chí cụ thể |
|----|------|----------|-----------------|
| **NFR-001** | **Performance** | Thời gian phản hồi API | ≤ 500 ms cho 95 % yêu cầu khi tải 100 req/giây; thời gian gửi tin tự động ≤ 2 giây sau thời điểm lịch định. |
| **NFR-002** | **Security** | Xác thực & phân quyền | Sử dụng OAuth 2.0 (client‑credentials) cho API nội bộ; chỉ người dùng có role “Quản trị viên bot” được phép tạo/ chỉnh sửa kịch bản. |
| | | Mã hoá dữ liệu nhạy cảm | Tất cả dữ liệu cá nhân được lưu trữ mã hoá AES‑256; truyền dữ liệu qua HTTPS TLS 1.2+. |
| | | Tuân thủ | Đáp ứng **GDPR** và **Luật An ninh mạng VN** – lưu lịch sử đồng ý, cung cấp khả năng xóa dữ liệu theo yêu cầu. |
| **NFR-003** | **Usability** | Độ học nhanh | Người dùng mới (Quản trị viên) có thể tạo kịch bản và bật bot trong **≤ 3 bước** mà không cần đào tạo. |
| **NFR-004** | **Reliability / Availability** | Độ sẵn sàng | Hệ thống phải đạt **99.5 %** uptime hàng tháng; có cơ chế backup dữ liệu mỗi 24 giờ và khả năng phục hồi trong ≤ 30 phút. |
| **NFR-005** | **Scalability** | Khả năng mở rộng | Hỗ trợ **≥ 1 000 người dùng đồng thời** (đồng thời gửi/ nhận tin) và **tăng lên 5 000** bằng auto‑scale mà không cần thay đổi kiến trúc. |
| **NFR-006** | **Compatibility** | Trình duyệt / thiết bị | Giao diện quản trị hỗ trợ Chrome ≥ 90, Edge ≥ 90, Firefox ≥ 88; UI responsive cho màn hình từ 1024 px trở lên. |
| **NFR-007** | **Legal / Regulatory** | Giới hạn tin nhắn Zalo | Không vượt quá **10 000 tin/ngày**; hệ thống tự ngắt gửi khi đạt ngưỡng và ghi log. |
| **NFR-008** | **Maintainability** | Đăng ký log chi tiết | Mọi hành động quan trọng (tạo kịch bản, bật/tắt bot, lỗi API) phải được ghi log với thời gian, người thực hiện, và chi tiết lỗi. |

---  

## 5. QUY TẮC NGHIỆP VỤ  

| ID | Quy tắc |
|----|----------|
| **BR-001** | Một tin nhắn marketing chỉ được gửi nếu khách hàng đã **đồng ý (opt‑in)**. |
| **BR-002** | Dữ liệu cá nhân chỉ được lưu trữ sau khi nhận được **đồng ý** và phải được xóa khi khách hàng yêu cầu hoặc khi hết thời hạn lưu trữ 12 tháng. |
| **BR-003** | Bot chỉ gửi tin trong **giờ hành chính** (08:00‑18:00, Thứ 2‑Thứ 6) trừ khi tin được đánh dấu “khẩn cấp”. |
| **BR-004** | Số tin gửi trong một ngày không được vượt quá **10 000**; khi đạt 90 % ngưỡng, hệ thống tự động gửi cảnh báo (FR‑008). |
| **BR-005** | Chỉ **Quản trị viên bot** mới được tạo, chỉnh sửa, hoặc xóa kịch bản trả lời. |
| **BR-006** | Khi bot ở trạng thái “Tắt”, mọi tin đến phải trả về tin “Bot hiện đang bảo trì, vui lòng liên hệ CSKH”. |
| **BR-007** | Mọi lỗi hệ thống (HTTP 5xx, timeout) phải được ghi lại và thông báo cho **đội IT** trong vòng **30 giây** (FR‑008). |
| **BR-008** | Báo cáo thống kê phải phản ánh **đúng** dữ liệu thực tế, không bao gồm tin bị hoãn do ngoài giờ. |

---  

## Kiểm tra cuối cùng  

- **[x]** Mỗi FR có ID, ưu tiên, ít nhất 1 AC (Given/When/Then) và mô tả **WHAT** chứ không đề cập tới **HOW**.  
- **[x]** Không còn từ mơ hồ; mọi tiêu chí đều có số liệu hoặc giả định được ghi chú.  
- **[x]** Phạm vi In‑scope/Out‑of‑scope khớp với danh sách FR.  
- **[x]** Mọi role trong mục 2 có ít nhất 1 FR liên quan.  
- **[x]** Đã bao phủ đầy đủ 6 nhóm NFR chính, bao gồm Security.  
- **[x]** Không có chỉnh sửa dựa trên feedback reject; toàn bộ nội dung giữ nguyên cấu trúc và ID.  

---  

*Document prepared by: Product Analyst – SoftwareFactory*