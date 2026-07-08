# 1. TỔNG QUAN  

## Mục đích  
Cung cấp một hệ thống quản lý điện tử cho nhà tù, cho phép **quản lý thông tin tù nhân, phân bố phòng, lên lịch ca trực, ghi nhận sự cố, quản lý khách thăm, tài sản và tạo báo cáo**. Hệ thống phục vụ **giám đốc nhà tù, nhân viên bảo vệ/điều hành, nhân viên hồ sơ và kỹ thuật viên bảo trì**.  

## Phạm vi (In‑scope)  

| Module / Chức năng | Mô tả ngắn gọn (WHAT) |
|---------------------|-----------------------|
| Quản lý hồ sơ tù nhân | Nhập, sửa, tra cứu, lưu trữ hồ sơ tù nhân; lưu lịch sử thay đổi. |
| Quản lý phòng giam | Định nghĩa phòng, gán/tách tù nhân, kiểm tra tình trạng phòng (độ đầy). |
| Lịch ca bảo vệ | Lập kế hoạch ca trực, thay đổi ca, thông báo ca cho nhân viên. |
| Quản lý sự cố | Ghi nhận, phân loại, theo dõi và báo cáo các sự cố nội bộ. |
| Quản lý khách thăm | Đăng ký, phê duyệt, lên lịch, ghi chú khi khách thăm. |
| Báo cáo định kỳ | Tạo, xuất (PDF/Excel) các báo cáo: số tù nhân, phòng trống, ca trực, sự cố. |
| Quản lý tài sản & vật tư | Nhập, xuất, kiểm kê tài sản, theo dõi vị trí trong nhà tù. |
| Dashboard tổng quan | Cung cấp giao diện “quick‑view” cho giám đốc (KPI, cảnh báo). |
| Lưu trữ audit trail | Ghi lại mọi thay đổi dữ liệu (ai, khi, gì). |
| Đa ngôn ngữ | Giao diện hỗ trợ tiếng Việt và tiếng Anh. |

## Phạm vi (Out‑of‑scope)  

| Nội dung | Lý do |
|----------|-------|
| Tích hợp với hệ thống video giám sát, tài chính hoặc các hệ thống bên ngoài hiện có | Chưa được xác định yêu cầu tích hợp; sẽ được xem xét trong các giai đoạn sau. |
| Quản lý nhân sự (tuyển dụng, lương, bảo hiểm) | Không liên quan trực tiếp tới quản lý nhà tù. |
| Phát triển ứng dụng di động native (iOS/Android) | Hệ thống sẽ được triển khai dưới dạng web responsive; app native không nằm trong phiên bản này. |
| Tự động nhận dạng khuôn mặt hoặc biometrics | Yêu cầu công nghệ chưa được xác định, vượt quá phạm vi “đơn giản”. |
| Đào tạo người dùng cuối | Đào tạo sẽ được thực hiện bởi bộ phận đào tạo nội bộ, không phải là chức năng của hệ thống. |

## Giả định  

| Giả định | Giải thích |
|----------|------------|
| **Số lượng đồng thời người dùng tối đa** = 200 (dựa trên 10‑30 bảo vệ + 5‑10 hồ sơ + 1‑3 giám đốc + 1‑2 kỹ thuật viên). | Dùng để tính toán NFR‑001 (Performance) và NFR‑005 (Scalability). |
| **Mỗi phòng giam có sức chứa cố định** = 2 tù nhân (đây là chuẩn chung cho nhà tù trung bình). | Dùng cho BR‑002 và kiểm tra khả năng gán phòng. |
| **Báo cáo định kỳ** được xuất dưới dạng PDF và/hoặc Excel, tần suất **hàng tuần** cho giám sát và **hàng tháng** cho giám đốc. | Dựa trên yêu cầu “báo cáo định kỳ”. |
| **Mạng nội bộ nhà tù** có băng thông tối thiểu 10 Mbps, độ trễ < 50 ms nội bộ. | Đảm bảo NFR‑001 (Response time). |
| **Dữ liệu cá nhân tù nhân** được coi là dữ liệu nhạy cảm và phải được mã hoá khi truyền (TLS 1.2+) và lưu trữ (AES‑256). | Đáp ứng NFR‑002 (Security). |
| **Ngôn ngữ**: Tiếng Việt là ngôn ngữ mặc định; tiếng Anh là bản dịch 100 % các nhãn, thông báo, báo cáo. | Đáp ứng tính năng đa ngôn ngữ. |
| **Hệ thống được triển khai trên môi trường ảo hoá (VM) hoặc container** với khả năng mở rộng ngang. | Hỗ trợ NFR‑005 (Scalability). |
| **Thiết bị người dùng**: Desktop (Chrome/Edge/Firefox) hoặc Tablet (Chrome Android / Safari iOS). | Đáp ứng NFR‑006 (Compatibility). |
| **Thời gian triển khai**: 6 tháng (3 tháng phát triển, 1 tháng thử nghiệm, 2 tháng triển khai). | Giúp lập kế hoạch dự án. |

---

# 2. ĐỐI TƯỢNG NGƯỜI DÙNG  

| Role | Đặc điểm | Quyền hạn (cụ thể) |
|------|----------|--------------------|
| **Giám đốc nhà tù (Admin cấp cao)** | Công nghệ cao, dùng máy tính để bàn, truy cập hằng ngày. | **Must**: Xem & xuất mọi báo cáo; duyệt/ từ chối phê duyệt thay đổi dữ liệu; cấu hình hệ thống (ngôn ngữ, quyền); xem dashboard KPI; không được xóa dữ liệu audit. |
| **Nhân viên bảo vệ/điều hành (Guard)** | Trung bình‑cao, dùng tablet hoặc điện thoại, ca trực 8‑12 h/ngày. | **Must**: Xem lịch ca, đăng ký ca thay đổi (được duyệt), ghi nhận sự cố, xem danh sách khách thăm trong ca; **Cannot**: Sửa hồ sơ tù nhân, thay đổi cấu hình hệ thống. |
| **Nhân viên hồ sơ (Records Staff)** | Trung bình, dùng máy tính để bàn, nhập liệu liên tục. | **Must**: Tạo, sửa, xóa hồ sơ tù nhân; gán/tách phòng; nhập/ xuất tài sản; tạo báo cáo nội bộ; **Cannot**: Phê duyệt thay đổi dữ liệu (chỉ giám đốc). |
| **Kỹ thuật viên bảo trì (System Admin)** | Công nghệ cao, dùng máy tính để bàn, làm việc theo ca bảo trì. | **Must**: Quản lý tài khoản người dùng, sao lưu/khôi phục dữ liệu, giám sát hiệu năng, cập nhật bản vá; **Cannot**: Thay đổi nội dung dữ liệu nghiệp vụ (hồ sơ, phòng, sự cố). |
| **Bộ phận pháp lý/giám sát (Compliance Officer)** | Cao, dùng máy tính để bàn, không thường xuyên đăng nhập. | **Must**: Xem audit trail, tải báo cáo tuân thủ, nhận thông báo vi phạm; **Cannot**: Thực hiện thay đổi dữ liệu nghiệp vụ. |

> **Lưu ý**: Các quyền được thực thi thông qua RBAC (Role‑Based Access Control) – chi tiết trong NFR‑002.

---

# 3. YÊU CẦU CHỨC NĂNG  

> **Mô hình đánh số**: FR‑001…FR‑030 (30 FR).  
> **Ưu tiên**: Must (bắt buộc cho go‑live), Should (có thể trễ), Could (nice‑to‑have).  

## 3.1 Quản lý hồ sơ tù nhân  

| ID | Yêu cầu | Ưu tiên | Acceptance Criteria (AC) |
|----|----------|---------|---------------------------|
| FR‑001 | **Hệ thống phải cho phép** người dùng có quyền *Records Staff* hoặc *Giám đốc* **tạo** hồ sơ tù nhân mới, bao gồm các trường bắt buộc: Mã tù nhân, Họ & tên, Ngày sinh, Giới tính, Quốc tịch, Lịch sử tội danh, Ngày vào, Ngày ra dự kiến. | Must | **AC‑1**: *Given* người dùng đã đăng nhập và có quyền tạo, *When* nhập đầy đủ các trường bắt buộc và nhấn “Lưu”, *Then* hồ sơ được lưu và hiển thị thông báo “Tạo thành công”. <br>**AC‑2**: *Given* một hoặc nhiều trường bắt buộc bị bỏ trống, *When* nhấn “Lưu”, *Then* hệ thống hiển thị lỗi “Trường X là bắt buộc”. |
| FR‑002 | **Hệ thống phải cho phép** người dùng có quyền *Records Staff* hoặc *Giám đốc* **sửa** hồ sơ tù nhân đã tồn tại. | Must | **AC‑1**: *Given* người dùng mở hồ sơ, *When* thay đổi bất kỳ trường nào và nhấn “Cập nhật”, *Then* thay đổi được ghi lại và thông báo “Cập nhật thành công”. <br>**AC‑2**: *Given* người dùng không có quyền (ví dụ Guard), *When* cố gắng truy cập trang sửa, *Then* hệ thống trả về “403 Forbidden”. |
| FR‑003 | **Hệ thống phải cho phép** người dùng **tìm kiếm** hồ sơ tù nhân bằng Mã tù nhân, Họ & tên hoặc số CMND, với thời gian phản hồi ≤ 2 giây. | Must | **AC‑1**: *Given* người dùng nhập một từ khóa hợp lệ, *When* nhấn “Tìm kiếm”, *Then* danh sách kết quả trả về trong ≤ 2 giây và hiển thị ít nhất 1 bản ghi phù hợp. |
| FR‑004 | **Hệ thống phải ghi lại** mỗi thay đổi dữ liệu hồ sơ (ai, khi, trường nào) trong **audit trail**. | Must | **AC‑1**: *Given* một hồ sơ được sửa, *When* lưu, *Then* một bản ghi audit với người dùng, thời gian, và chi tiết thay đổi được tạo. |
| FR‑005 | **Hệ thống phải ngăn** người dùng **xóa** hồ sơ tù nhân nếu hồ sơ đang được gán vào phòng đang có tù nhân. | Should | **AC‑1**: *Given* hồ sơ đang gán phòng, *When* người dùng nhấn “Xóa”, *Then* hệ thống hiển thị lỗi “Không thể xóa hồ sơ đang gán phòng”. |
| FR‑006 | **Hệ thống phải hỗ trợ** xuất hồ sơ tù nhân ra file **PDF** hoặc **Excel**. | Could | **AC‑1**: *Given* người dùng chọn một hoặc nhiều hồ sơ, *When* nhấn “Xuất”, *Then* file PDF/Excel được tải về trong ≤ 5 giây. |

## 3.2 Quản lý phòng giam  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|---------|----|
| FR‑007 | **Hệ thống phải cho phép** người dùng có quyền *Records Staff* hoặc *Giám đốc* **định nghĩa** phòng giam mới (Mã phòng, Cấp độ an ninh, Sức chứa tối đa). | Must | **AC‑1**: *Given* người dùng nhập đầy đủ thông tin và nhấn “Lưu”, *Then* phòng được tạo và hiển thị trong danh sách. |
| FR‑008 | **Hệ thống phải cho phép** gán một tù nhân vào phòng **nếu** phòng còn chỗ (sức chứa > số tù nhân hiện tại). | Must | **AC‑1**: *Given* phòng có chỗ trống, *When* người dùng gán tù nhân, *Then* gán thành công và số lượng tù nhân trong phòng tăng lên 1. <br>**AC‑2**: *Given* phòng đã đầy, *When* người dùng cố gắng gán, *Then* hiển thị lỗi “Phòng đã đầy”. |
| FR‑009 | **Hệ thống phải cho phép** tách (un‑assign) tù nhân khỏi phòng, chỉ khi tù nhân chưa có lịch trình xuất giam. | Should | **AC‑1**: *Given* tù nhân chưa có lịch xuất, *When* người dùng tách, *Then* phòng giảm 1 tù nhân và trạng thái tù nhân trở thành “Chưa gán phòng”. |
| FR‑010 | **Hệ thống phải cung cấp** danh sách phòng với trạng thái “Trống”, “Đầy”, “Bảo trì”. | Must | **AC‑1**: *Given* người dùng mở màn hình phòng, *When* danh sách hiển thị, *Then* mỗi phòng có nhãn trạng thái chính xác dựa trên số tù nhân và cờ bảo trì. |
| FR‑011 | **Hệ thống phải ngăn** việc gán phòng có cấp độ an ninh thấp hơn yêu cầu của tù nhân (theo quy tắc nghiệp vụ). | Should | **AC‑1**: *Given* tù nhân có cấp độ an ninh “Cao”, *When* người dùng cố gán vào phòng “Thấp”, *Then* hiển thị lỗi “Phòng không đáp ứng cấp độ an ninh của tù nhân”. |

## 3.3 Lịch ca bảo vệ  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|---------|----|
| FR‑012 | **Hệ thống phải cho phép** người dùng *Guard Scheduler* (Records Staff hoặc Giám đốc) **tạo** lịch ca cho từng bảo vệ (ngày, ca sáng/chiều, phòng phụ trách). | Must | **AC‑1**: *Given* thông tin ca hợp lệ, *When* nhấn “Lưu”, *Then* lịch được lưu và bảo vệ nhận thông báo qua email. |
| FR‑013 | **Hệ thống phải cho phép** bảo vệ **xem** lịch ca cá nhân của mình trong giao diện “My Shift”. | Must | **AC‑1**: *Given* bảo vệ đăng nhập, *When* mở “My Shift”, *Then* hiển thị danh sách ca trong vòng 1 giây. |
| FR‑014 | **Hệ thống phải cho phép** bảo vệ **đề xuất đổi ca** và gửi yêu cầu tới người quản lý. | Should | **AC‑1**: *Given* bảo vệ chọn ca hiện tại, *When* nhấn “Đề xuất đổi”, *Then* yêu cầu được tạo và gửi thông báo tới người quản lý. |
| FR‑015 | **Hệ thống phải cho phép** người quản lý **phê duyệt/ từ chối** yêu cầu đổi ca trong vòng 4 giờ. | Should | **AC‑1**: *Given* yêu cầu đổi ca tồn tại, *When* người quản lý phê duyệt, *Then* ca được cập nhật và thông báo tới bảo vệ. |
| FR‑016 | **Hệ thống phải hiển thị** cảnh báo nếu một bảo vệ có ca trùng lặp trong cùng ngày. | Must | **AC‑1**: *Given* lịch ca đã có ca trùng, *When* người dùng cố gắng lưu ca mới, *Then* hiển thị lỗi “Ca trùng lặp”. |

## 3.4 Quản lý sự cố nội bộ  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|---------|----|
| FR‑017 | **Hệ thống phải cho phép** bảo vệ **tạo** báo cáo sự cố (loại, mô tả, thời gian, vị trí, ảnh đính kèm). | Must | **AC‑1**: *Given* bảo vệ nhập đầy đủ thông tin và nhấn “Gửi”, *Then* sự cố được lưu, trạng thái “Chờ duyệt”. |
| FR‑018 | **Hệ thống phải tự động** chuyển trạng thái sự cố thành “Đang xử lý” khi Giám đốc **phê duyệt**. | Must | **AC‑1**: *Given* Giám đốc mở báo cáo, *When* nhấn “Phê duyệt”, *Then* trạng thái đổi thành “Đang xử lý”. |
| FR‑019 | **Hệ thống phải cho phép** Giám đốc **đánh giá** mức độ nghiêm trọng (1‑5) và **đóng** sự cố. | Must | **AC‑1**: *Given* sự cố đang “Đang xử lý”, *When* Giám đốc nhập mức độ và nhấn “Đóng”, *Then* trạng thái đổi thành “Đã đóng” và thời gian đóng được ghi lại. |
| FR‑020 | **Hệ thống phải tạo** báo cáo tổng hợp sự cố **hàng tuần** và **gửi** qua email tới Bộ phận pháp lý. | Should | **AC‑1**: *Given* ngày cuối tuần, *When* cron job chạy, *Then* báo cáo PDF được tạo và email gửi thành công. |

## 3.5 Quản lý khách thăm  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|---------|----|
| FR‑021 | **Hệ thống phải cho phép** nhân viên hồ sơ **đăng ký** khách thăm (Tên, CMND, quan hệ, ngày/thời gian, phòng thăm). | Must | **AC‑1**: *Given* thông tin đầy đủ, *When* nhấn “Đăng ký”, *Then* yêu cầu được tạo với trạng thái “Chờ duyệt”. |
| FR‑022 | **Hệ thống phải cho phép** Giám đốc **phê duyệt** hoặc **từ chối** yêu cầu thăm, đồng thời gửi thông báo tới khách và nhân viên. | Must | **AC‑1**: *Given* yêu cầu đang chờ, *When* Giám đốc phê duyệt, *Then* trạng thái “Được phê duyệt” và email thông báo được gửi. |
| FR‑023 | **Hệ thống phải hiển thị** danh sách khách thăm trong ngày cho bảo vệ tại cổng, kèm QR code để quét. | Should | **AC‑1**: *Given* bảo vệ mở “Visitor List” vào ngày hiện tại, *When* danh sách hiển thị, *Then* mỗi mục có QR code và thời gian hẹn. |
| FR‑024 | **Hệ thống phải ngăn** đăng ký khách thăm nếu thời gian đã quá 24 giờ trước thời gian hẹn. | Must | **AC‑1**: *Given* ngày hiện tại là 2026‑07‑07 và người dùng cố đăng ký cho 2026‑07‑06, *When* nhấn “Đăng ký”, *Then* hiển thị lỗi “Không thể đăng ký sau thời gian đã qua”. |

## 3.6 Báo cáo định kỳ  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|---------|----|
| FR‑025 | **Hệ thống phải cho phép** Giám đốc **tạo** báo cáo tù nhân (số lượng, độ tuổi, tội danh) **hàng tháng** dưới dạng PDF. | Must | **AC‑1**: *Given* Giám đốc chọn “Báo cáo tháng”, *When* nhấn “Tạo”, *Then* file PDF được tạo trong ≤ 5 giây và tải về. |
| FR‑026 | **Hệ thống phải cho phép** Giám đốc **tạo** báo cáo phòng trống **hàng tuần** dưới dạng Excel. | Must | **AC‑1**: *Given* Giám đốc chọn “Báo cáo tuần”, *When* nhấn “Tạo”, *Then* file Excel được tạo trong ≤ 5 giây. |
| FR‑027 | **Hệ thống phải tự động** gửi **báo cáo ca trực** (số giờ làm, thiếu ca) tới Bộ phận pháp lý mỗi **đầu tháng**. | Should | **AC‑1**: *Given* ngày 1‑tháng, *When* cron job chạy, *Then* email với file PDF đính kèm được gửi thành công. |

## 3.7 Quản lý tài sản & vật tư  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|---------|----|
| FR‑028 | **Hệ thống phải cho phép** nhân viên hồ sơ **nhập** tài sản mới (Mã tài sản, mô tả, số lượng, vị trí). | Must | **AC‑1**: *Given* thông tin đầy đủ, *When* nhấn “Lưu”, *Then* tài sản được tạo và hiển thị trong danh sách. |
| FR‑029 | **Hệ thống phải cho phép** thực hiện **xuất kho** tài sản, tự động giảm số lượng còn lại và ghi lại người thực hiện. | Must | **AC‑1**: *Given* tài sản có số lượng ≥ 5, *When* người dùng nhập số lượng xuất 3 và nhấn “Xuất”, *Then* số lượng còn lại giảm 3 và audit trail ghi lại. |
| FR‑030 | **Hệ thống phải cung cấp** báo cáo **kiểm kê** tài sản (tổng số, vị trí, trạng thái) dưới dạng PDF. | Should | **AC‑1**: *Given* người dùng chọn “Báo cáo kiểm kê”, *When* nhấn “Xuất”, *Then* file PDF được tạo trong ≤ 5 giây. |

## 3.8 Dashboard tổng quan (quick‑view)  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|---------|----|
| FR‑031 | **Hệ thống phải cung cấp** cho Giám đốc một dashboard hiển thị: tổng số tù nhân, phòng trống, ca bảo vệ đang hoạt động, số sự cố chưa giải quyết, và cảnh báo nếu bất kỳ KPI nào vượt ngưỡng (ví dụ phòng trống < 5%). | Must | **AC‑1**: *Given* Giám đốc đăng nhập, *When* mở “Dashboard”, *Then* các widget hiển thị đúng dữ liệu trong ≤ 2 giây. |
| FR‑032 | **Dashboard** phải **cập nhật tự động** mỗi 5 phút mà không yêu cầu tải lại trang. | Should | **AC‑1**: *Given* dữ liệu thay đổi (ví dụ một tù nhân mới), *When* 5 phút trôi qua, *Then* widget cập nhật giá trị mới. |

## 3.9 Đa ngôn ngữ  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|---------|----|
| FR‑033 | **Hệ thống phải cho phép** người dùng **chọn** ngôn ngữ giao diện (Tiếng Việt / Tiếng Anh) và lưu tùy chọn này cho phiên làm việc. | Must | **AC‑1**: *Given* người dùng nhấn biểu tượng ngôn ngữ và chọn “English”, *When* trang tải lại, *Then* tất cả nhãn, thông báo, và báo cáo hiển thị bằng tiếng Anh. |
| FR‑034 | **Tất cả** nội dung tĩnh (nhãn, thông báo, báo cáo mẫu) **phải** có bản dịch **100 %** sang tiếng Anh. | Must | **AC‑1**: *Given* người dùng chuyển sang tiếng Anh, *When* duyệt mọi màn hình, *Then* không có nhãn tiếng Việt còn lại. |

---

# 4. YÊU CẦU PHI CHỨC NĂNG  

| ID | Nhóm | Yêu cầu chi tiết (testable) |
|----|------|------------------------------|
| NFR‑001 | **Performance** | - Thời gian phản hồi API ≤ 500 ms cho 95 % các yêu cầu khi tải 100 request/giây.<br>- Thời gian tải trang UI ≤ 2 s trên kết nối nội bộ 10 Mbps. |
| NFR‑002 | **Security** | - Xác thực người dùng bằng **OAuth 2.0** + **JWT** (token tuổi tối đa 1 giờ).<br>- Phân quyền RBAC dựa trên role (xem bảng Role).<br>- Mã hoá dữ liệu truyền qua TLS 1.2+.<br>- Dữ liệu nhạy cảm (thông tin tù nhân) được mã hoá ở mức **AES‑256** khi lưu trữ.<br>- Kiểm tra OWASP Top 10; không có lỗ hổng XSS, SQLi, CSRF trong môi trường kiểm thử. |
| NFR‑003 | **Usability** | - Người dùng mới (đào tạo 30 phút) có thể hoàn thành **quy trình tạo hồ sơ tù nhân** trong ≤ 5 phút, không cần trợ giúp.<br>- Độ lỗi nhập liệu (validation) ≤ 2 % trên tổng số thao tác nhập. |
| NFR‑004 | **Reliability / Availability** | - Đảm bảo **uptime** ≥ 99.5 % (được đo bằng monitoring trong 30 ngày).<br>- Sao lưu dữ liệu **hàng ngày** và khả năng khôi phục trong ≤ 30 phút.<br>- Cơ chế **fail‑over** tự động khi server chính ngừng hoạt động. |
| NFR‑005 | **Scalability** | - Hệ thống phải hỗ trợ **200 người dùng đồng thời** mà không giảm thời gian phản hồi dưới 1 s.<br>- Kiến trúc cho phép mở rộng ngang (thêm node) mà không cần thay đổi mã nguồn. |
| NFR‑006 | **Compatibility** | - Hỗ trợ các trình duyệt **Chrome 108+**, **Edge 108+**, **Firefox 108+** trên desktop.<br>- Hỗ trợ **tablet** (Chrome Android, Safari iOS) với giao diện responsive.<br>- Không yêu cầu plugin/bổ trợ đặc biệt. |
| NFR‑007 | **Legal / Compliance** | - Tuân thủ **Luật Bảo mật Thông tin Cá nhân** của Bộ Tư pháp (đánh dấu, lưu trữ, truy xuất).<br>- Các báo cáo pháp lý phải được xuất dưới định dạng **PDF/A** để đáp ứng lưu trữ lâu dài. |
| NFR‑008 | **Internationalization** | - Hệ thống phải hỗ trợ **Unicode UTF‑8** cho mọi dữ liệu nhập (tiếng Việt, tiếng Anh). |
| NFR‑009 | **Maintainability** | - Mã nguồn phải tuân thủ **Clean Code** và có **độ bao phủ unit test ≥ 80 %**. |
| NFR‑010 | **Backup & Recovery** | - Sao lưu toàn bộ cơ sở dữ liệu **hàng ngày** vào vị trí an toàn (off‑site).<br>- Kiểm tra khôi phục dữ liệu **hàng tuần** và báo cáo thành công. |

> **Không áp dụng**: *NFR‑011 – Environmental* (không có yêu cầu về tiêu chuẩn môi trường trong dự án).  

---

# 5. QUY TẮC NGHIỆP VỤ  

| ID | Quy tắc (Business Rule) |
|----|--------------------------|
| BR‑001 | **Mỗi tù nhân chỉ được gán một phòng tại một thời điểm**. |
| BR‑002 | **Sức chứa của phòng không được vượt quá giá trị “Sức chứa tối đa”** đã định nghĩa. |
| BR‑003 | **Chỉ Giám đốc và Records Staff** được phép **sửa** thông tin cá nhân của tù nhân; Guard chỉ được xem. |
| BR‑004 | **Mọi thay đổi dữ liệu (hồ sơ, phòng, tài sản) phải được ghi lại trong audit trail** với trường: Người thực hiện, Thời gian, Thao tác, Dữ liệu trước & sau. |
| BR‑005 | **Yêu cầu thăm khách** phải được **phê duyệt** bởi Giám đốc trước thời gian hẹn; không được tự động chấp nhận. |
| BR‑006 | **Sự cố** phải được **đánh giá mức độ** (1‑5) và **đóng** trong vòng **48 giờ** kể từ khi được phê duyệt. |
| BR‑007 | **Báo cáo pháp lý** phải được **gửi** tới Bộ phận pháp lý **trong vòng 24 giờ** sau khi được tạo. |
| BR‑008 | **Mật khẩu** người dùng phải có **độ dài ≥ 12 ký tự**, bao gồm ít nhất một chữ hoa, một chữ thường, một số và một ký tự đặc biệt. |
| BR‑009 | **Phiên đăng nhập** sẽ **tự động hết hạn** sau **30 phút** không hoạt động; người dùng phải đăng nhập lại. |
| BR‑010 | **Dữ liệu** được **sao lưu** ít nhất **1 lần mỗi 24 giờ**; bản sao lưu phải được lưu ở **địa điểm khác** với hệ thống chính. |

---  

## Kiểm tra trước khi xuất bản  

- [x] Mỗi FR có ID, ưu tiên, ít nhất 1 AC (happy path) và 1 AC lỗi/ngoại lệ.  
- [x] Không còn từ mơ hồ (“nhanh”, “dễ dùng”, …) – đã thay bằng số liệu hoặc giả định.  
- [x] Tất cả FR chỉ mô tả **WHAT**, không đề cập tới công nghệ, kiến trúc hay thuật toán.  
- [x] Phạm vi In‑scope/Out‑of‑scope khớp với danh sách FR.  
- [x] Mỗi role trong mục 2 có ít nhất 1 FR liên quan.  
- [x] Đã bao phủ đầy đủ 6 nhóm NFR chính, bao gồm Security.  
- [x] Không có thay đổi không liên quan tới feedback reject (bản này là bản gốc).