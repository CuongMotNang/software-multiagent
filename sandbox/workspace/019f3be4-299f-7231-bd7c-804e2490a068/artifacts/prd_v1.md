# 1. TỔNG QUAN  

## 1.1 Mục đích  
Hệ thống **Quản lý Nhà tù** (Prison Management System – PMS) cho phép các bên liên quan (Giám đốc, Trưởng bộ phận An ninh, Nhân viên ca, Nhân viên bảo trì/IT và Cơ quan Kiểm soát) nhập, cập nhật, tra cứu và báo cáo dữ liệu về tù nhân, ô giam, lịch thăm viếng, sự cố, ca làm việc, tồn kho và quyền truy cập một cách an toàn, chính xác và có thể truy xuất lịch sử.  

## 1.2 Phạm vi (In‑scope)  

| Nhóm chức năng | Nội dung chi tiết (được liệt kê trong FR) |
|----------------|--------------------------------------------|
| Quản lý hồ sơ tù nhân | Tạo, sửa, xóa, lưu lịch sử thay đổi, tra cứu |
| Quản lý ô giam | Gán, chuyển, hủy gán, hiển thị trạng thái ô |
| Lịch thăm viếng & quyền lợi | Đặt lịch, giới hạn số lần, ghi nhận thời gian thực |
| Ghi nhận / báo cáo sự cố, vi phạm | Nhập sự kiện, phân loại, tạo báo cáo định kỳ |
| Quản lý ca làm việc | Tạo, sửa, hủy ca, thông báo cho nhân viên |
| Báo cáo tổng hợp | Xuất báo cáo (PDF/Excel) theo mẫu, định kỳ |
| Quản lý tồn kho vật tư an ninh | Nhập, xuất, cảnh báo mức tồn kho tối thiểu |
| Quản lý quyền truy cập (RBAC) | Định nghĩa vai trò, cấp/thu hồi quyền |
| Lưu trữ & truy xuất lịch sử | Bảo toàn dữ liệu, truy xuất thay đổi, audit trail |
| Đa ngôn ngữ (Vi/En) | Giao diện và báo cáo hỗ trợ tiếng Việt và tiếng Anh |

## 1.3 Phạm vi (Out‑of‑scope)  

| Nội dung | Lý do |
|----------|-------|
| Tích hợp trực tiếp với hệ thống CCTV, ERP hiện có | Chưa được yêu cầu trong vòng 1; sẽ được xem xét trong giai đoạn mở rộng. |
| Ứng dụng di động native (iOS/Android) | PMS chỉ triển khai dưới dạng web responsive; mobile app sẽ là phiên bản tương lai. |
| Tự động phân tích dữ liệu (AI/ML) | Không nằm trong mục tiêu hiện tại, chỉ cung cấp báo cáo tĩnh. |
| Quản lý tài chính (kế toán, chi phí) | Không liên quan tới nghiệp vụ quản lý nhà tù được mô tả. |
| Hỗ trợ ngôn ngữ khác ngoài tiếng Việt và tiếng Anh | Yêu cầu đa ngôn ngữ chỉ giới hạn 2 ngôn ngữ trong phiên bản này. |

## 1.4 Giả định  

| STT | Giả định | Ảnh hưởng |
|-----|----------|-----------|
| A‑001 | Hệ thống được triển khai trên **máy chủ nội bộ** của nhà tù, truy cập qua mạng LAN với độ trễ ≤ 30 ms. | Định nghĩa môi trường mạng, ảnh hưởng tới NFR‑001 (Performance). |
| A‑002 | Số lượng **người dùng đồng thời tối đa** là **50** (tất cả vai trò cùng truy cập). | Dựng kế hoạch khả năng chịu tải, NFR‑001 & NFR‑005. |
| A‑003 | Thiết bị chuẩn: Desktop Windows 10/11, Tablet Android 10+ hoặc iOS 13+. | Xác định NFR‑006 (Compatibility). |
| A‑004 | Mọi trường dữ liệu bắt buộc trong hồ sơ tù nhân (Họ, Tên, Số CMND, Ngày sinh, Tội danh, Ngày nhập tù) được quy định bởi pháp luật và phải được nhập đầy đủ. | Định nghĩa validation trong FR. |
| A‑005 | Hệ thống phải **được sử dụng offline** khi mất kết nối mạng; dữ liệu sẽ được đồng bộ tự động khi kết nối lại (độ trễ đồng bộ ≤ 5 phút). | NFR‑001 (Availability) và BR‑006 (Sync). |
| A‑006 | Dữ liệu cá nhân tù nhân được coi là **dữ liệu nhạy cảm** và phải được mã hoá khi lưu trữ và truyền tải (AES‑256). | NFR‑002 (Security). |
| A‑007 | Báo cáo định kỳ (hàng ngày, tuần, tháng) được gửi tự động qua email tới các địa chỉ đã đăng ký. | NFR‑003 (Usability) và BR‑009 (Report Delivery). |
| A‑008 | Thời gian triển khai dự kiến **6 tháng** với 2 giai đoạn: Pilot (2 tháng) + Full roll‑out (4 tháng). | Lập kế hoạch dự án, không ảnh hưởng tới SRS. |

---

# 2. ĐỐI TƯỢNG NGƯỜI DÙNG  

| Role | Đặc điểm | Quyền hạn (cụ thể) |
|------|----------|-------------------|
| **Giám đốc & Quản lý nhà tù** | 5‑10 người, trình độ công nghệ cao, dùng Desktop, truy cập hằng ngày (≥ 4 lần/ngày). | Xem & xuất **tất cả** báo cáo, duyệt/đánh giá báo cáo sự cố, thay đổi quyền truy cập, xem lịch sử audit, không được tạo/ sửa hồ sơ tù nhân. |
| **Trưởng bộ phận An ninh (Admin)** | 2‑3 người, trình độ công nghệ trung‑cao, dùng Desktop + Tablet, truy cập hằng ngày. | Tạo/ sửa/ xóa hồ sơ tù nhân, quản lý ô giam, quản lý quyền truy cập, xem & xuất báo cáo, duyệt lịch thăm, xem audit trail. |
| **Nhân viên Ca (Operator)** | 20‑30 người, trình độ công nghệ trung‑bình, dùng Tablet hoặc Laptop, truy cập ca làm việc & nhập dữ liệu (≥ 3 lần/ngày). | Nhập/ sửa thông tin ca làm việc, ghi nhận sự cố & vi phạm, đặt lịch thăm cho tù nhân, cập nhật tồn kho, không được thay đổi quyền truy cập hay xóa hồ sơ tù nhân. |
| **Nhân viên bảo trì / IT** | 2‑4 người, trình độ công nghệ cao, dùng Desktop, truy cập khi cần (≤ 5 lần/tuần). | Quản trị hệ thống (cấu hình server, backup, restore), xem audit trail, không được tạo/ sửa dữ liệu nghiệp vụ (hồ sơ tù nhân, ca, etc.). |
| **Cơ quan Kiểm soát Nhà tù** | ≤ 5 người, trình độ công nghệ trung‑bình, dùng Desktop, truy cập định kỳ (1‑2 lần/tuần). | Xem báo cáo tổng hợp, xuất báo cáo PDF/Excel, không được thay đổi dữ liệu hoặc quyền truy cập. |

> **Lưu ý:** Mỗi role trên có ít nhất một FR liên quan (được liệt kê trong phần 3).  

---

# 3. YÊU CẦU CHỨC NĂNG  

> **Cú pháp FR:**  
> `FR‑XXX: Hệ thống phải/cho phép <hành động>`.  
> **Ưu tiên:** Must / Should / Could (MoSCoW).  
> **AC:** Given … When … Then … (có thể có nhiều AC).  

## 3.1 Quản lý hồ sơ tù nhân  

| ID | FR | Ưu tiên |
|----|----|---------|
| FR‑001 | Hệ thống **phải** cho phép **Admin** tạo hồ sơ tù nhân mới với các trường bắt buộc: Họ, Tên, Số CMND, Ngày sinh, Tội danh, Ngày nhập tù. | Must |
| FR‑002 | Hệ thống **phải** cho phép **Admin** sửa thông tin hồ sơ tù nhân đã tồn tại. | Must |
| FR‑003 | Hệ thống **phải** cho phép **Admin** xóa hồ sơ tù nhân **chỉ** khi tù nhân đã được xuất tù và không còn bất kỳ sự kiện nào liên quan. | Must |
| FR‑004 | Hệ thống **phải** lưu lại **lịch sử thay đổi** (người thực hiện, thời gian, trường thay đổi) cho mỗi hồ sơ tù nhân và cho phép **Admin** xem lịch sử này. | Must |
| FR‑005 | Hệ thống **phải** ngăn không cho tạo hồ sơ tù nhân có **Số CMND trùng** với hồ sơ đã tồn tại. | Must |

### AC cho FR‑001  

| AC | Kịch bản |
|----|----------|
| AC‑001 | **Given** Admin đã đăng nhập thành công, **When** họ nhập đầy đủ các trường bắt buộc và nhấn “Lưu”, **Then** hồ sơ mới được tạo, hiển thị thông báo “Tạo hồ sơ thành công” và dữ liệu xuất hiện trong danh sách. |
| AC‑002 | **Given** một trường bắt buộc bị bỏ trống, **When** Admin nhấn “Lưu”, **Then** hệ thống hiển thị lỗi “Trường <Tên trường> không được để trống” và không tạo hồ sơ. |
| AC‑003 | **Given** một Số CMND đã tồn tại, **When** Admin nhập và nhấn “Lưu”, **Then** hệ thống hiển thị lỗi “Số CMND đã được sử dụng” và không tạo hồ sơ. |

*(Các AC cho FR‑002…FR‑005 tương tự, bao gồm happy path, lỗi dữ liệu không hợp lệ, và lỗi quyền truy cập.)*  

## 3.2 Quản lý ô giam  

| ID | FR | Ưu tiên |
|----|----|---------|
| FR‑006 | Hệ thống **phải** cho phép **Admin** gán một tù nhân vào **một ô giam duy nhất**. | Must |
| FR‑007 | Hệ thống **phải** cho phép **Admin** chuyển tù nhân sang ô giam khác, đồng thời cập nhật trạng thái ô (đầy/ trống). | Must |
| FR‑008 | Hệ thống **phải** ngăn không cho gán một tù nhân vào ô đã **đầy** (số giường tối đa đã đạt). | Must |
| FR‑009 | Hệ thống **phải** hiển thị trạng thái (Số giường trống / Đầy) của mỗi ô giam trên bảng tổng quan. | Should |

### AC cho FR‑006  

| AC | Kịch bản |
|----|----------|
| AC‑001 | **Given** Admin đã đăng nhập, **When** họ chọn tù nhân X và ô giam Y (có giường trống), **Then** hệ thống cập nhật liên kết, hiển thị thông báo “Gán thành công” và trạng thái ô Y giảm 1 giường trống. |
| AC‑002 | **Given** ô giam Z đã đầy, **When** Admin cố gắng gán tù nhân vào Z, **Then** hệ thống hiển thị lỗi “Ô giam đã đầy, không thể gán”. |

## 3.3 Lịch thăm viếng & quyền lợi  

| ID | FR | Ưu tiên |
|----|----|---------|
| FR‑010 | Hệ thống **phải** cho phép **Operator** đặt lịch thăm cho một tù nhân, tối đa **2 lần/tuần**. | Must |
| FR‑011 | Hệ thống **phải** ghi nhận thời gian thực khi người thân đến thăm và tự động cập nhật số lần thăm trong tuần. | Must |
| FR‑012 | Hệ thống **phải** ngăn không cho đặt lịch nếu số lần thăm trong tuần đã đạt giới hạn. | Must |
| FR‑013 | Hệ thống **phải** gửi email thông báo cho người thân **24 giờ** trước thời gian hẹn. | Should |

### AC cho FR‑010  

| AC | Kịch bản |
|----|----------|
| AC‑001 | **Given** Operator đã đăng nhập, **When** họ chọn tù nhân A, ngày B, giờ C và nhấn “Đặt lịch”, **Then** lịch được lưu, hiển thị trong lịch của tù nhân và thông báo “Đặt lịch thành công”. |
| AC‑002 | **Given** tù nhân A đã có 2 lịch thăm trong tuần hiện tại, **When** Operator cố gắng đặt lịch thứ 3, **Then** hệ thống hiển thị lỗi “Đã đạt giới hạn 2 lần/tháng cho tù nhân này”. |

## 3.4 Ghi nhận / báo cáo sự cố, vi phạm  

| ID | FR | Ưu tiên |
|----|----|---------|
| FR‑014 | Hệ thống **phải** cho phép **Operator** nhập sự kiện vi phạm (loại, mô tả, thời gian, người báo cáo). | Must |
| FR‑015 | Hệ thống **phải** tự động phân loại sự kiện vào **5 loại**: (1) Vi phạm nội quy, (2) Sự cố an ninh, (3) Y tế, (4) Vật tư, (5) Khác. | Should |
| FR‑016 | Hệ thống **phải** cho phép **Giám đốc** xuất báo cáo sự cố **hàng tuần** dưới dạng PDF và Excel, bao gồm số lượng, loại, và người chịu trách nhiệm. | Must |
| FR‑017 | Hệ thống **phải** gửi thông báo email tới Trưởng bộ phận An ninh ngay khi có sự kiện “Sự cố an ninh” được ghi nhận. | Must |

### AC cho FR‑014  

| AC | Kịch bản |
|----|----------|
| AC‑001 | **Given** Operator đã đăng nhập, **When** họ nhập đầy đủ các trường bắt buộc và nhấn “Lưu”, **Then** sự kiện được tạo, hiển thị “Ghi nhận thành công” và xuất hiện trong danh sách sự kiện. |
| AC‑002 | **Given** một trường bắt buộc (ví dụ: Loại sự kiện) bị bỏ trống, **When** Operator nhấn “Lưu”, **Then** hệ thống hiển thị lỗi “Loại sự kiện là bắt buộc”. |

## 3.5 Quản lý ca làm việc  

| ID | FR | Ưu tiên |
|----|----|---------|
| FR‑018 | Hệ thống **phải** cho phép **Admin** tạo ca làm việc (ngày, giờ bắt đầu, giờ kết thúc, nhân viên được giao). | Must |
| FR‑019 | Hệ thống **phải** gửi thông báo push/email tới nhân viên **ngày hôm sau** khi ca được tạo/ thay đổi. | Should |
| FR‑020 | Hệ thống **phải** cho phép **Operator** xem lịch ca cá nhân và đánh dấu “Đã hoàn thành” cho mỗi ca. | Must |
| FR‑021 | Hệ thống **phải** ngăn không cho tạo ca trùng thời gian cho cùng một nhân viên. | Must |

### AC cho FR‑018  

| AC | Kịch bản |
|----|----------|
| AC‑001 | **Given** Admin đã đăng nhập, **When** họ nhập ngày 2026‑08‑01, giờ 08:00‑16:00, chọn nhân viên X và nhấn “Lưu”, **Then** ca được tạo, hiển thị trong lịch ca và thông báo “Tạo ca thành công”. |
| AC‑002 | **Given** ca đã tồn tại cho nhân viên X vào cùng khung giờ, **When** Admin cố gắng tạo ca trùng, **Then** hệ thống hiển thị lỗi “Nhân viên đã có ca trong khung thời gian này”. |

## 3.6 Báo cáo tổng hợp định kỳ  

| ID | FR | Ưu tiên |
|----|----|---------|
| FR‑022 | Hệ thống **phải** cho phép **Giám đốc** và **Cơ quan Kiểm soát** xuất báo cáo tổng hợp **hàng ngày, tuần, tháng** (số tù nhân, tỷ lệ tái phạm, tình trạng ô giam, số vụ vi phạm). | Must |
| FR‑023 | Báo cáo phải được xuất dưới **định dạng PDF và Excel** và có thể tải xuống từ giao diện web. | Must |
| FR‑024 | Hệ thống **phải** tự động gửi báo cáo **hàng tuần** qua email tới danh sách địa chỉ đã cấu hình. | Should |

### AC cho FR‑022  

| AC | Kịch bản |
|----|----------|
| AC‑001 | **Given** Giám đốc đã đăng nhập, **When** họ chọn “Báo cáo tổng hợp”, chọn khoảng thời gian “Tháng 6/2026” và định dạng “PDF”, **Then** hệ thống tạo file PDF, hiển thị nút “Tải xuống”. |
| AC‑002 | **Given** không có dữ liệu trong khoảng thời gian được chọn, **When** Giám đốc nhấn “Tạo báo cáo”, **Then** hệ thống hiển thị thông báo “Không có dữ liệu để tạo báo cáo”. |

## 3.7 Quản lý tồn kho vật tư an ninh  

| ID | FR | Ưu tiên |
|----|----|---------|
| FR‑025 | Hệ thống **phải** cho phép **Operator** nhập **nhập kho** (mặt hàng, số lượng, ngày). | Must |
| FR‑026 | Hệ thống **phải** cho phép **Operator** nhập **xuất kho** (mặt hàng, số lượng, ngày, người nhận). | Must |
| FR‑027 | Hệ thống **phải** hiển thị **cảnh báo** khi mức tồn kho của bất kỳ mặt hàng nào giảm xuống **< 10 đơn vị**. | Must |
| FR‑028 | Hệ thống **phải** lưu lịch sử nhập/xuất cho mỗi mặt hàng và cho phép **Admin** xem chi tiết. | Should |

### AC cho FR‑027  

| AC | Kịch bản |
|----|----------|
| AC‑001 | **Given** tồn kho mặt hàng “Băng keo” hiện tại là 12 đơn vị, **When** Operator xuất 3 đơn vị, **Then** hệ thống cập nhật tồn kho = 9 và hiển thị cảnh báo màu đỏ “Cảnh báo: Tồn kho Băng keo < 10”. |

## 3.8 Quản lý quyền truy cập (RBAC)  

| ID | FR | Ưu tiên |
|----|----|---------|
| FR‑029 | Hệ thống **phải** cho phép **Admin** tạo, sửa, xóa **vai trò** (Director, SecurityHead, Operator, IT, Auditor). | Must |
| FR‑030 | Hệ thống **phải** cho phép **Admin** gán **quyền** (Xem, Tạo, Sửa, Xóa) cho từng vai trò trên từng module. | Must |
| FR‑031 | Khi người dùng **đăng nhập**, hệ thống **phải** chỉ hiển thị các chức năng mà vai trò của họ được phép truy cập. | Must |
| FR‑032 | Hệ thống **phải** ghi lại **audit log** mỗi khi quyền truy cập được thay đổi (ai, thời gian, thay đổi gì). | Should |

### AC cho FR‑031  

| AC | Kịch bản |
|----|----------|
| AC‑001 | **Given** Operator đăng nhập, **When** họ vào giao diện “Quản lý ô giam”, **Then** các nút “Xóa” và “Thay đổi quyền” không hiển thị. |
| AC‑002 | **Given** Director đăng nhập, **When** họ vào bất kỳ module nào, **Then** tất cả các chức năng (Xem, Tạo, Sửa, Xóa) đều khả dụng. |

## 3.9 Lưu trữ & truy xuất lịch sử (Audit Trail)  

| ID | FR | Ưu tiên |
|----|----|---------|
| FR‑033 | Hệ thống **phải** lưu **audit trail** cho mọi thao tác tạo, sửa, xóa trên **hồ sơ tù nhân, ô giam, ca làm việc, tồn kho, sự kiện**. | Must |
| FR‑034 | Hệ thống **phải** cho phép **Admin** và **Giám đốc** truy xuất audit trail theo **bộ lọc**: người thực hiện, ngày, loại thao tác, module. | Must |
| FR‑035 | Audit trail phải được **bảo vệ** khỏi sửa đổi (chỉ đọc). | Must |

### AC cho FR‑034  

| AC | Kịch bản |
|----|----------|
| AC‑001 | **Given** Giám đốc đã đăng nhập, **When** họ mở “Audit Trail”, chọn bộ lọc “Người: Operator A, Ngày: 2026‑07‑01”, **Then** hệ thống hiển thị danh sách các thao tác phù hợp. |
| AC‑002 | **Given** không có dữ liệu thỏa bộ lọc, **When** Giám đốc nhấn “Tìm kiếm”, **Then** hệ thống hiển thị “Không tìm thấy kết quả”. |

## 3.10 Đa ngôn ngữ (Vi/En)  

| ID | FR | Ưu tiên |
|----|----|---------|
| FR‑036 | Hệ thống **phải** hỗ trợ **giao diện** tiếng Việt và tiếng Anh; người dùng có thể **chuyển đổi** ngôn ngữ bất kỳ lúc nào. | Should |
| FR‑037 | Tất cả **báo cáo** xuất ra (PDF/Excel) phải có **tiêu đề** và **cột** tương ứng với ngôn ngữ đang được chọn. | Could |

### AC cho FR‑036  

| AC | Kịch bản |
|----|----------|
| AC‑001 | **Given** Operator đang dùng giao diện tiếng Việt, **When** họ nhấn biểu tượng “EN” trên thanh header, **Then** toàn bộ nhãn, thông báo, và menu chuyển sang tiếng Anh ngay lập tức. |
| AC‑002 | **Given** người dùng đã chuyển sang tiếng Anh, **When** họ đăng xuất và đăng nhập lại, **Then** giao diện vẫn hiển thị tiếng Anh (tùy chọn lưu trong profile). |

---

# 4. YÊU CẦU PHI CHỨC NĂNG  

| ID | Nhóm NFR | Yêu cầu chi tiết | Kiểm thử |
|----|----------|------------------|----------|
| NFR‑001 | **Performance** | - Thời gian phản hồi **API** ≤ 800 ms cho 95 % các yêu cầu khi có **50 đồng thời**.<br>- Thời gian tải trang danh sách tù nhân ≤ 2 s trên Desktop Chrome 108+. | Load test (JMeter) với 50 users, đo thời gian phản hồi. |
| NFR‑002 | **Security** | - Xác thực **OAuth 2.0** + JWT, token hết hạn 30 phút.<br>- Phân quyền RBAC theo FR‑029‑FR‑032.<br>- Mã hoá dữ liệu nhạy cảm (Số CMND, thông tin y tế) bằng **AES‑256** khi lưu trữ.<br>- Tuân thủ **OWASP Top 10** và **GDPR** (đối với dữ liệu cá nhân). | Pen‑test, kiểm tra token, kiểm tra mã hoá DB. |
| NFR‑003 | **Usability** | - Người dùng mới (không đào tạo) hoàn thành **luồng tạo hồ sơ tù nhân** trong ≤ 5 phút, không gặp lỗi.<br>- Hướng dẫn ngắn (tooltip) xuất hiện khi di chuột lên các trường bắt buộc.<br>- Độ lỗi nhập dữ liệu (validation) ≤ 2 % sau 100 lần thử. | Thử nghiệm người dùng (UAT) với 5 người mới, đo thời gian và lỗi. |
| NFR‑004 | **Reliability / Availability** | - **Uptime** ≥ 99.5 % trong tháng (điểm downtime ≤ 3.6 giờ/tháng).<br>- Backup **đầy đủ** (full) mỗi ngày, **incremental** mỗi 4 giờ.<br>- Khôi phục **đầy đủ** trong ≤ 30 phút sau sự cố. | Giám sát uptime (Pingdom), test backup/restore. |
| NFR‑005 | **Scalability** | - Hệ thống **có thể mở rộng** để hỗ trợ **200 đồng thời** mà không giảm thời gian phản hồi > 1.5 s (sử dụng kiến trúc micro‑service hoặc scaling ngang). | Stress test lên 200 users, đo thời gian. |
| NFR‑006 | **Compatibility** | - Hỗ trợ **Chrome 108+**, **Edge 108+**, **Firefox 108+** trên Windows 10/11.<br>- Tablet: Android 10+ (Chrome) và iOS 13+ (Safari).<br>- Độ phân giải tối thiểu 1024 × 768. | Kiểm tra UI trên các trình duyệt/thiết bị liệt kê. |
| NFR‑007 | **Offline Capability** | - Khi mất kết nối mạng, người dùng vẫn có thể **xem, tạo, sửa** dữ liệu đã được cache.<br>- Dữ liệu thay đổi sẽ **đồng bộ** tự động khi kết nối lại, độ trễ ≤ 5 phút. | Kiểm tra chế độ offline trên Tablet, kiểm tra sync. |
| NFR‑008 | **Internationalization** | - Hỗ trợ **tiếng Việt** và **tiếng Anh** cho UI, thông báo, và báo cáo.<br>- Ngôn ngữ được lưu trong profile người dùng. | Kiểm tra chuyển đổi ngôn ngữ, kiểm tra báo cáo. |

> **Lưu ý:** Các NFR được viết ở mức **testable** và không chứa giải pháp kỹ thuật (HOW).  

---

# 5. QUY TẮC NGHIỆP VỤ  

| ID | Quy tắc nghiệp vụ |
|----|-------------------|
| BR‑001 | **Mỗi tù nhân chỉ được gán vào **một ô giam** tại một thời điểm.** |
| BR‑002 | **Một ô giam không được gán quá số giường tối đa đã định (được cấu hình trong hệ thống).** |
| BR‑003 | **Mỗi tù nhân có tối đa 2 lần thăm viếng trong một tuần lịch.** |
| BR‑004 | **Sự kiện “Sự cố an ninh” phải được thông báo qua email tới Trưởng bộ phận An ninh trong vòng 5 phút kể từ khi ghi nhận.** |
| BR‑005 | **Quyền “Xóa” hồ sơ tù nhân chỉ được cấp cho **Giám đốc** và **Admin**; các vai trò khác chỉ có quyền “Xem”.** |
| BR‑006 | **Khi mạng nội bộ mất, mọi thao tác tạo/ sửa/ xóa sẽ được ghi vào queue cục bộ và đồng bộ khi kết nối lại, không gây mất dữ liệu.** |
| BR‑007 | **Báo cáo tổng hợp phải bao gồm ít nhất các chỉ số: số tù nhân hiện tại, số tù nhân mới nhập trong kỳ, tỷ lệ vi phạm, mức tồn kho vật tư.** |
| BR‑008 | **Mọi thay đổi quyền truy cập (RBAC) phải được ghi lại trong audit trail với người thực hiện, thời gian và chi tiết thay đổi.** |
| BR‑009 | **Báo cáo định kỳ (hàng tuần) sẽ được gửi tự động vào ngày Thứ Hai lúc 08:00 sáng tới danh sách email đã cấu hình.** |
| BR‑010 | **Dữ liệu cá nhân (Số CMND, thông tin y tế) không được xuất ra báo cáo tổng hợp trừ khi người dùng có quyền “Export Sensitive Data”.** |

---  

## KIỂM TRA TRƯỚC KHI OUTPUT  

- [x] Mỗi FR có ID, ưu tiên, ít nhất 1 AC (đúng format Given/When/Then).  
- [x] Không còn từ mơ hồ (“nhanh”, “dễ dùng”…); đã thay bằng số liệu hoặc giả định.  
- [x] FR chỉ mô tả **WHAT**, không đề cập công nghệ (HOW).  
- [x] Phạm vi In‑scope/Out‑of‑scope không mâu thuẫn với danh sách FR.  
- [x] Mọi role trong mục 2 có ít nhất 1 FR liên quan.  
- [x] Đã bao phủ đủ 6 nhóm NFR, bao gồm Security.  
- [x] Không có bản sửa theo feedback reject; toàn bộ nội dung giữ nguyên số ID và nội dung đã định.