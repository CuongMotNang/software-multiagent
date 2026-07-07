# 1. TỔNG QUAN  

## Mục đích  
Hệ thống **Quản lý kỳ thi trực tuyến** cung cấp cho **Quản trị viên**, **Giáo viên/Người tạo đề thi** và **Thí sinh (sinh viên)** một công cụ web duy nhất để lên kế hoạch, tổ chức, thực hiện và tổng hợp kết quả các kỳ thi, thay thế quy trình thủ công hiện tại.  

## Phạm vi (In‑scope)  
| Module / Chức năng | Mô tả ngắn gọn |
|---------------------|----------------|
| Quản lý tài khoản & phân quyền | Đăng nhập, tạo, sửa, xóa tài khoản; gán vai trò Admin, Teacher, Student |
| Ngân hàng câu hỏi | Thêm, sửa, xóa, phân loại câu hỏi (trắc nghiệm, đúng/sai, tự luận) |
| Tạo kỳ thi | Lựa chọn câu hỏi, cấu hình thời gian, điểm, trọng số |
| Lên lịch thi | Xác định ngày/giờ, phòng thi hoặc đường link môi trường trực tuyến |
| Đăng ký tham gia | Sinh viên đăng ký/ký tên vào kỳ thi trong thời gian cho phép |
| Thực hiện thi trực tuyến | Hiển thị câu hỏi, ghi nhận câu trả lời, thời gian làm bài |
| Chấm điểm tự động | Tự động tính điểm cho câu hỏi có thể chấm tự động |
| Quản lý kết quả | Xem, xuất bảng điểm cá nhân, lớp, báo cáo tổng hợp |
| Thông báo | Gửi email / tin nhắn về lịch thi, nhắc nhở, công bố kết quả |
| Lưu trữ lịch sử | Lưu trữ toàn bộ dữ liệu kỳ thi ít nhất 5 năm, hỗ trợ tra cứu và in báo cáo |

## Phạm vi (Out‑of‑scope)  
| Nội dung | Lý do |
|----------|-------|
| Tích hợp AI để chấm câu hỏi tự luận | Không được yêu cầu trong phiên bản này; sẽ xem xét trong các phiên bản sau. |
| Tích hợp trực tiếp với hệ thống LMS hoặc cơ sở dữ liệu sinh viên hiện có | Chưa có yêu cầu chi tiết; sẽ được đánh giá trong giai đoạn mở rộng. |
| Quản lý phòng thi vật lý (đặt phòng, thiết bị) | Hệ thống chỉ lưu trữ thông tin phòng; việc quản lý thực tế thuộc trách nhiệm của bộ phận hành chính. |
| Hỗ trợ đa ngôn ngữ | Phiên bản đầu chỉ hỗ trợ tiếng Việt; đa ngôn ngữ sẽ là tính năng tương lai. |
| Xác thực hai‑yếu tố (2FA) | Không yêu cầu trong phiên bản hiện tại; sẽ được xem xét khi có yêu cầu bảo mật bổ sung. |

## Giả định  
| Giả định | Nội dung |
|----------|----------|
| **Giảm thời gian chuẩn bị kỳ thi**: hệ thống phải giúp giảm ít nhất **30 %** thời gian so với quy trình thủ công hiện tại (theo tiêu chuẩn ngành). |
| **Số lượng người dùng đồng thời**: tối đa **200** người dùng (giảng viên, sinh viên) đồng thời truy cập trong giờ cao điểm. |
| **Thời gian phản hồi API**: ≤ 500 ms cho các yêu cầu chuẩn (truy vấn danh sách, đăng ký, nộp bài). |
| **Thời gian tải trang UI**: ≤ 2 s trên kết nối băng thông 5 Mbps (desktop) và ≤ 3 s trên 3 Mbps (mobile). |
| **Thời gian chấm tự động**: kết quả hiển thị cho sinh viên trong vòng **5 giây** sau khi nộp bài. |
| **Bảo mật dữ liệu**: mọi dữ liệu cá nhân và kết quả thi được lưu trữ mã hoá AES‑256; truyền tải qua TLS 1.2+. |
| **Thời gian lưu trữ lịch sử**: dữ liệu kỳ thi được lưu ít nhất **5 năm**. |
| **Thiết bị hỗ trợ**: trình duyệt Chrome, Edge, Firefox, Safari (phiên bản mới nhất) trên desktop và mobile. |
| **Môi trường triển khai**: hệ thống chạy trên môi trường cloud (IaaS) có khả năng mở rộng tự động. |

---

# 2. ĐỐI TƯỢNG NGƯỜI DÙNG  

| Role | Đặc điểm | Quyền hạn |
|------|----------|-----------|
| **Quản trị viên (Admin)** | Thành thạo máy tính, hiểu quy trình quản lý, dùng desktop (web). | **Có**: tạo/sửa/xóa tài khoản, gán vai trò, cấu hình hệ thống, xem/ xuất toàn bộ báo cáo, hủy/kích hoạt kỳ thi. **Không có**: tham gia làm bài thi. |
| **Giáo viên / Người tạo đề thi (Teacher)** | Trình độ công nghệ trung‑cao, dùng PC (desktop web). | **Có**: tạo/sửa/xóa câu hỏi, tạo kỳ thi, lên lịch, cấu hình điểm, duyệt kết quả tự luận, xuất báo cáo lớp, gửi thông báo. **Không có**: quản lý tài khoản người dùng khác, thay đổi quyền admin. |
| **Thí sinh (Student)** | Đa dạng, ít hoặc không có kinh nghiệm, dùng mobile & desktop (web). | **Có**: đăng ký kỳ thi, thực hiện thi, xem kết quả cá nhân, nhận thông báo. **Không có**: tạo/ sửa câu hỏi, tạo kỳ thi, truy cập báo cáo lớp. |

---

# 3. YÊU CẦU CHỨC NĂNG  

## 3.1 Quản lý tài khoản & phân quyền  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|----------|----|
| **FR-001** | Hệ thống **phải** cho phép người dùng **đăng nhập** bằng địa chỉ email và mật khẩu. | Must | **AC1**: *Given* người dùng đã đăng ký tài khoản, *When* nhập đúng email + mật khẩu, *Then* hệ thống cho phép truy cập và trả về token hợp lệ.<br>**AC2**: *Given* email không tồn tại hoặc mật khẩu sai, *When* người dùng nhấn “Đăng nhập”, *Then* hệ thống hiển thị thông báo “Email hoặc mật khẩu không đúng” và không cấp token. |
| **FR-002** | Hệ thống **phải** cho phép **Admin** **tạo** tài khoản người dùng mới và **gán** một trong các vai trò: Admin, Teacher, Student. | Must | **AC1**: *Given* Admin đang ở trang “Quản lý người dùng”, *When* nhập email, họ tên, mật khẩu và chọn vai trò, *Then* tài khoản mới được tạo, người dùng nhận email kích hoạt.<br>**AC2**: *Given* một trường bắt buộc (email) bị bỏ trống, *When* Admin nhấn “Lưu”, *Then* hệ thống hiển thị lỗi “Email không được để trống”. |
| **FR-003** | Hệ thống **phải** cho phép **Admin** **khóa** hoặc **hủy kích hoạt** tài khoản người dùng. | Must | **AC1**: *Given* Admin trên danh sách người dùng, *When* chọn “Khóa” cho một tài khoản, *Then* tài khoản không thể đăng nhập và hiển thị trạng thái “Khóa”.<br>**AC2**: *Given* tài khoản đã bị khóa, *When* người dùng cố gắng đăng nhập, *Then* hệ thống trả về thông báo “Tài khoản bị khóa, vui lòng liên hệ quản trị viên”. |
| **FR-004** | Hệ thống **phải** cho phép **Admin** **đặt lại mật khẩu** cho bất kỳ tài khoản nào. | Must | **AC1**: *Given* Admin chọn “Đặt lại mật khẩu” cho một tài khoản, *When* nhập mật khẩu mới và xác nhận, *Then* mật khẩu được cập nhật và người dùng nhận email xác nhận.<br>**AC2**: *Given* mật khẩu mới không đáp ứng chính sách (ít nhất 8 ký tự, có chữ và số), *When* Admin lưu, *Then* hệ thống hiển thị lỗi “Mật khẩu không đáp ứng yêu cầu bảo mật”. |

## 3.2 Ngân hàng câu hỏi  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|----------|----|
| **FR-005** | Hệ thống **phải** cho phép **Teacher** **thêm** câu hỏi mới, bao gồm tiêu đề, nội dung, loại (trắc nghiệm, đúng/sai, tự luận), mức độ khó, và các lựa chọn (nếu có). | Must | **AC1**: *Given* Teacher ở trang “Thêm câu hỏi”, *When* nhập đầy đủ thông tin và nhấn “Lưu”, *Then* câu hỏi được lưu và hiển thị trong danh sách.<br>**AC2**: *Given* thiếu nội dung câu hỏi, *When* Teacher lưu, *Then* hệ thống hiển thị lỗi “Nội dung câu hỏi không được để trống”. |
| **FR-006** | Hệ thống **phải** cho phép **Teacher** **sửa** câu hỏi đã tồn tại. | Must | **AC1**: *Given* Teacher mở câu hỏi trong chế độ “Sửa”, *When* thay đổi nội dung và lưu, *Then* thay đổi được ghi nhận và hiển thị trong danh sách.<br>**AC2**: *Given* Teacher cố gắng lưu câu hỏi với loại “Trắc nghiệm” nhưng không có ít nhất 2 lựa chọn, *When* nhấn “Lưu”, *Then* hệ thống trả về lỗi “Câu hỏi trắc nghiệm phải có ít nhất 2 lựa chọn”. |
| **FR-007** | Hệ thống **phải** cho phép **Teacher** **xóa** câu hỏi đã lưu. | Must | **AC1**: *Given* Teacher chọn “Xóa” trên một câu hỏi, *When* xác nhận “Có”, *Then* câu hỏi bị xóa vĩnh viễn và không còn xuất hiện trong danh sách.<br>**AC2**: *Given* câu hỏi đã được gắn vào một kỳ thi đang hoạt động, *When* Teacher nhấn “Xóa”, *Then* hệ thống hiển thị lỗi “Câu hỏi đang được sử dụng trong kỳ thi, không thể xóa”. |
| **FR-008** | Hệ thống **phải** cho phép **Teacher** **phân loại** câu hỏi theo môn học, chủ đề và mức độ khó (Dễ, Trung bình, Khó). | Must | **AC1**: *Given* Teacher tạo hoặc sửa câu hỏi, *When* chọn môn học, chủ đề, mức độ khó, *Then* thông tin được lưu và có thể lọc trong danh sách câu hỏi.<br>**AC2**: *Given* không chọn môn học, *When* lưu, *Then* hệ thống trả về lỗi “Môn học là bắt buộc”. |

## 3.3 Tạo và cấu hình kỳ thi  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|----------|----|
| **FR-009** | Hệ thống **phải** cho phép **Teacher** **tạo kỳ thi** bằng cách **chọn** một tập hợp câu hỏi từ ngân hàng. | Must | **AC1**: *Given* Teacher ở trang “Tạo kỳ thi”, *When* chọn ít nhất 1 câu hỏi và nhấn “Tạo”, *Then* kỳ thi mới được tạo với danh sách câu hỏi đã chọn.<br>**AC2**: *Given* không chọn câu hỏi nào, *When* nhấn “Tạo”, *Then* hệ thống hiển thị lỗi “Cần chọn ít nhất một câu hỏi”. |
| **FR-010** | Hệ thống **phải** cho phép **Teacher** **đặt thời gian bắt đầu** và **kết thúc** cho kỳ thi (định dạng ngày‑giờ, múi giờ). | Must | **AC1**: *Given* Teacher nhập ngày‑giờ bắt đầu và kết thúc, *When* lưu, *Then* hệ thống lưu thời gian và hiển thị trên chi tiết kỳ thi.<br>**AC2**: *Given* thời gian kết thúc sớm hơn thời gian bắt đầu, *When* lưu, *Then* hệ thống trả về lỗi “Thời gian kết thúc phải sau thời gian bắt đầu”. |
| **FR-011** | Hệ thống **phải** cho phép **Teacher** **cấu hình điểm** cho mỗi loại câu hỏi (ví dụ: 1 điểm cho trắc nghiệm, 2 điểm cho tự luận). | Must | **AC1**: *Given* Teacher thiết lập “Điểm mỗi câu hỏi” và nhấn “Lưu”, *Then* cấu hình được áp dụng khi tính điểm.<br>**AC2**: *Given* nhập giá trị âm, *When* lưu, *Then* hệ thống hiển thị lỗi “Điểm phải là số nguyên dương”. |
| **FR-012** | Hệ thống **phải** cho phép **Teacher** **đặt thời gian làm bài** (thời lượng) cho kỳ thi, tối đa 3 giờ. | Must | **AC1**: *Given* Teacher nhập thời lượng 90 phút, *When* lưu, *Then* thời lượng được lưu và hiển thị.<br>**AC2**: *Given* thời lượng > 180 phút, *When* lưu, *Then* hệ thống trả về lỗi “Thời lượng tối đa cho phép là 180 phút”. |

## 3.4 Lên lịch thi  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|----------|----|
| **FR-013** | Hệ thống **phải** cho phép **Teacher** **chỉ định phòng thi** (hoặc đường link phòng trực tuyến) khi lên lịch. | Must | **AC1**: *Given* Teacher nhập “Phòng 101” hoặc URL Zoom, *When* lưu, *Then* thông tin được lưu và hiển thị trong chi tiết kỳ thi.<br>**AC2**: *Given* URL không hợp lệ, *When* lưu, *Then* hệ thống trả về lỗi “Định dạng URL không hợp lệ”. |
| **FR-014** | Hệ thống **phải** cho phép **Admin** **hủy** một kỳ thi **trước** thời gian bắt đầu. | Must | **AC1**: *Given* Admin trên trang chi tiết kỳ thi, *When* nhấn “Hủy” và xác nhận, *Then* trạng thái kỳ thi chuyển thành “Đã hủy” và sinh viên nhận thông báo hủy.<br>**AC2**: *Given* thời gian hiện tại đã vượt qua thời gian bắt đầu, *When* Admin nhấn “Hủy”, *Then* hệ thống trả về lỗi “Kỳ thi đã bắt đầu, không thể hủy”. |

## 3.5 Đăng ký tham gia kỳ thi  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|----------|----|
| **FR-015** | Hệ thống **phải** cho phép **Student** **đăng ký** vào kỳ thi **khi** kỳ thi đang ở trạng thái “Mở đăng ký”. | Must | **AC1**: *Given* Student đăng nhập và xem danh sách kỳ thi mở, *When* nhấn “Đăng ký” cho một kỳ thi, *Then* đăng ký thành công và hiển thị trạng thái “Đã đăng ký”.<br>**AC2**: *Given* kỳ thi đã đóng đăng ký, *When* Student nhấn “Đăng ký”, *Then* hệ thống trả về lỗi “Đăng ký đã kết thúc”. |
| **FR-016** | Hệ thống **phải** ngăn **Student** **đăng ký** cùng một kỳ thi **nhiều lần**. | Must | **AC1**: *Given* Student đã đăng ký kỳ thi X, *When* nhấn “Đăng ký” lại, *Then* hệ thống hiển thị thông báo “Bạn đã đăng ký kỳ thi này”. |
| **FR-017** | Hệ thống **phải** cho phép **Admin** **xác nhận** hoặc **từ chối** đăng ký của sinh viên (trong trường hợp đăng ký thủ công). | Should | **AC1**: *Given* Admin xem danh sách đăng ký, *When* chọn “Xác nhận” cho một sinh viên, *Then* trạng thái thay đổi thành “Được chấp nhận”.<br>**AC2**: *Given* Admin chọn “Từ chối”, *When* lưu, *Then* sinh viên nhận email thông báo “Đăng ký của bạn đã bị từ chối”. |

## 3.6 Thực hiện thi trực tuyến  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|----------|----|
| **FR-018** | Hệ thống **phải** hiển thị **giao diện thi** cho **Student** đúng thời gian bắt đầu đã định, và **khóa** khi hết thời gian. | Must | **AC1**: *Given* thời gian hiện tại = thời gian bắt đầu kỳ thi, *When* Student truy cập đường link, *Then* giao diện thi được mở.<br>**AC2**: *Given* thời gian hiện tại > thời gian kết thúc, *When* Student cố gắng truy cập, *Then* hệ thống hiển thị “Kỳ thi đã kết thúc”. |
| **FR-019** | Hệ thống **phải** **ghi nhận** câu trả lời của Student **theo thời gian thực** và lưu tạm trên server mỗi khi câu trả lời được thay đổi. | Must | **AC1**: *Given* Student trả lời câu hỏi 5, *When* nhấn “Lưu câu trả lời”, *Then* câu trả lời được lưu và có thể xem lại khi chuyển sang câu hỏi khác.<br>**AC2**: *Given* mất kết nối mạng, *When* Student trả lời, *Then* hệ thống lưu tạm trên client và đồng bộ khi kết nối phục hồi, thông báo “Đã lưu tạm, sẽ đồng bộ khi có mạng”. |
| **FR-020** | Hệ thống **phải** ngăn **Student** **điều hướng ra ngoài** giao diện thi (tab, cửa sổ) **nhiều hơn 2 lần** trong cùng một kỳ thi. | Should | **AC1**: *Given* Student rời giao diện thi và quay lại, *When* số lần rời > 2, *Then* hệ thống hiển thị cảnh báo “Bạn đã rời giao diện quá nhiều lần, thời gian còn lại sẽ bị giảm 5 phút”. |
| **FR-021** | Hệ thống **phải** tự động **nộp bài** khi thời gian làm bài hết. | Must | **AC1**: *Given* thời gian còn 00:00, *When* đồng hồ đếm ngược kết thúc, *Then* hệ thống tự động lưu câu trả lời cuối cùng và chuyển trạng thái “Đã nộp”. |

## 3.7 Chấm điểm tự động  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|----------|----|
| **FR-022** | Hệ thống **phải** **tự động chấm** các câu hỏi **trắc nghiệm** và **đúng/sai** ngay khi Student nộp bài. | Must | **AC1**: *Given* Student đã nộp kỳ thi, *When* hệ thống tính điểm, *Then* điểm cho các câu hỏi tự động được tính và lưu.<br>**AC2**: *Given* câu hỏi không có đáp án chuẩn (được nhập sai), *When* hệ thống chấm, *Then* ghi log lỗi “Không có đáp án chuẩn cho câu hỏi ID‑xxx”. |
| **FR-023** | Hệ thống **phải** **đánh dấu** các câu hỏi **tự luận** để Teacher thực hiện chấm thủ công. | Must | **AC1**: *Given* kỳ thi có câu hỏi tự luận, *When* Student nộp, *Then* câu hỏi được gắn trạng thái “Chờ chấm” và hiển thị trong danh sách chấm của Teacher.<br>**AC2**: *Given* Teacher mở câu hỏi tự luận, *When* nhập điểm và lưu, *Then* điểm được cập nhật và trạng thái chuyển thành “Đã chấm”. |

## 3.8 Xem và xuất kết quả  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|----------|----|
| **FR-024** | Hệ thống **phải** cho phép **Student** **xem điểm cá nhân** ngay sau khi kỳ thi được công bố. | Must | **AC1**: *Given* Student đăng nhập, *When* truy cập “Kết quả” và chọn kỳ thi đã công bố, *Then* hiển thị điểm tổng và chi tiết từng câu hỏi.<br>**AC2**: *Given* kỳ thi chưa được công bố, *When* Student cố gắng xem, *Then* hệ thống hiển thị “Kết quả chưa có”. |
| **FR-025** | Hệ thống **phải** cho phép **Teacher** **xem bảng điểm lớp** và **xuất file CSV**. | Must | **AC1**: *Given* Teacher mở “Bảng điểm lớp” cho kỳ thi X, *When* nhấn “Xuất CSV”, *Then* file CSV chứa các cột: Mã sinh viên, Họ tên, Điểm, Trạng thái (đạt/không đạt).<br>**AC2**: *Given* không có dữ liệu (không có sinh viên đăng ký), *When* nhấn “Xuất CSV”, *Then* hệ thống trả về thông báo “Không có dữ liệu để xuất”. |
| **FR-026** | Hệ thống **phải** cho phép **Admin** **xem báo cáo tổng hợp** (số lượng kỳ thi, tỷ lệ hoàn thành, trung bình điểm) và **xuất PDF**. | Should | **AC1**: *Given* Admin vào “Báo cáo tổng hợp”, *When* chọn khoảng thời gian và nhấn “Xuất PDF”, *Then* file PDF được tải về với các biểu đồ và bảng thống kê.<br>**AC2**: *Given* khoảng thời gian không có kỳ thi, *When* nhấn “Xuất PDF”, *Then* hệ thống hiển thị “Không có dữ liệu trong khoảng thời gian đã chọn”. |

## 3.9 Thông báo  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|----------|----|
| **FR-027** | Hệ thống **phải** **gửi email** tới **Student** khi kỳ thi **được lên lịch** (ngày lập lịch). | Must | **AC1**: *Given* Teacher lưu lịch thi, *When* hệ thống tạo lịch, *Then* email “Kỳ thi X đã được lên lịch vào ngày Y” được gửi tới tất cả sinh viên đăng ký.<br>**AC2**: *Given* địa chỉ email không hợp lệ, *When* gửi, *Then* hệ thống ghi log lỗi “Email không hợp lệ: …”. |
| **FR-028** | Hệ thống **phải** **gửi email nhắc nhở** 24 giờ trước ngày thi. | Must | **AC1**: *Given* ngày thi còn 24 giờ, *When* hệ thống chạy công việc định kỳ, *Then* email “Kỳ thi X sẽ diễn ra vào ngày Y, vui lòng chuẩn bị” được gửi tới sinh viên đã đăng ký.<br>**AC2**: *Given* sinh viên đã hủy đăng ký, *When* công việc chạy, *Then* không gửi email cho sinh viên đó. |
| **FR-029** | Hệ thống **phải** **gửi email** khi **kết quả** của kỳ thi **được công bố**. | Must | **AC1**: *Given* Teacher công bố kết quả, *When* hệ thống kích hoạt, *Then* email “Kết quả kỳ thi X đã có sẵn, vui lòng đăng nhập để xem” được gửi tới tất cả sinh viên đã tham gia.<br>**AC2**: *Given* email server trả về lỗi 550, *When* gửi, *Then* hệ thống ghi log và thử lại 3 lần, sau đó thông báo cho Admin “Gửi email thất bại cho 5 sinh viên”. |

## 3.10 Lưu trữ lịch sử  

| ID | Yêu cầu | Ưu tiên | AC |
|----|----------|----------|----|
| **FR-030** | Hệ thống **phải** **lưu trữ** toàn bộ dữ liệu kỳ thi (câu hỏi, đáp án, kết quả, log hoạt động) **ít nhất 5 năm**. | Must | **AC1**: *Given* kỳ thi đã kết thúc, *When* hệ thống lưu trữ, *Then* dữ liệu được gắn nhãn “archived” và không thể bị xóa bởi người dùng.<br>**AC2**: *Given* yêu cầu xóa dữ liệu trước 5 năm, *When* Admin thực hiện, *Then* hệ thống trả về lỗi “Dữ liệu chưa đủ thời gian lưu trữ, không thể xóa”. |
| **FR-031** | Hệ thống **phải** cho phép **Admin** **tra cứu** lịch sử kỳ thi theo ngày, môn học, hoặc giáo viên. | Should | **AC1**: *Given* Admin nhập tiêu chí tìm kiếm, *When* nhấn “Tìm”, *Then* danh sách kỳ thi phù hợp được hiển thị.<br>**AC2**: *Given* không có kỳ thi nào khớp, *When* tìm, *Then* hiển thị “Không tìm thấy kết quả”. |

---

# 4. YÊU CẦU PHI CHỨC NĂNG  

| ID | Nhóm | Yêu cầu chi tiết |
|----|------|-------------------|
| **NFR-001** | **Performance** | - Thời gian phản hồi API cho các thao tác CRUD ≤ 500 ms khi tải 200 request/giây.<br>- Thời gian tải trang UI ≤ 2 s trên desktop (kết nối 5 Mbps) và ≤ 3 s trên mobile (3 Mbps). |
| **NFR-002** | **Security** | - Xác thực người dùng bằng **OAuth 2.0** (password grant) và **JWT** có thời hạn 1 giờ.<br>- Mật khẩu được lưu bằng **bcrypt** (cost factor ≥ 12).<br>- Tất cả dữ liệu truyền qua HTTPS TLS 1.2+.<br>- **Role‑Based Access Control (RBAC)**: mỗi API chỉ cho phép các vai trò được phép (Admin, Teacher, Student).<br>- Dữ liệu cá nhân (họ tên, email, điểm) được mã hoá AES‑256 khi lưu trữ.<br>- Tuân thủ **GDPR** và quy định bảo vệ thông tin sinh viên của Việt Nam. |
| **NFR-003** | **Usability** | - Người dùng mới (Student) có thể **đăng ký** và **đăng nhập** trong **≤ 3 bước**.<br>- Thực hiện **đăng ký kỳ thi** trong **≤ 2 click** sau khi danh sách kỳ thi mở được hiển thị.<br>- Hệ thống cung cấp hướng dẫn ngắn gọn (tooltip) cho mỗi trường nhập liệu. |
| **NFR-004** | **Reliability / Availability** | - Đảm bảo **uptime** ≥ 99.5 % (điều kiện thời gian bảo trì không quá 4 giờ/tháng).<br>- Cơ chế **backup** dữ liệu hàng ngày, lưu trữ tại ít nhất 2 vùng địa lý.<br>- Khôi phục dữ liệu trong vòng **30 phút** sau sự cố. |
| **NFR-005** | **Scalability** | - Hệ thống phải hỗ trợ **tối thiểu 500** người dùng đồng thời (khi có 2 kỳ thi diễn ra đồng thời).<br>- Kiến trúc phải cho phép **scale‑out** (thêm node) mà không cần downtime. |
| **NFR-006** | **Compatibility** | - Hỗ trợ các trình duyệt: Chrome ≥ 90, Edge ≥ 90, Firefox ≥ 88, Safari ≥ 14.<br>- Giao diện đáp ứng (responsive) cho màn hình **≥ 320 px** (mobile) và **≥ 1024 px** (desktop). |
| **NFR-007** | **Maintainability** | - Mã nguồn phải tuân thủ **ESLint** (cho JavaScript) hoặc **Pylint** (cho Python) với mức độ lỗi ≤ 5 %.<br>- Tài liệu API (OpenAPI 3.0) phải luôn cập nhật. |
| **NFR-008** | **Legal / Compliance** | - Tuân thủ **Luật An toàn thông tin mạng** và **Quy định về bảo vệ dữ liệu cá nhân** (đối tượng sinh viên).<br>- Lưu trữ log truy cập người dùng ít nhất 180 ngày để phục vụ kiểm toán. |

---

# 5. QUY TẮC NGHIỆP VỤ  

| ID | Quy tắc |
|----|----------|
| **BR-001** | Một **câu hỏi** chỉ có thể được **xóa** khi không được gắn vào bất kỳ **kỳ thi nào** đang ở trạng thái “Mở đăng ký” hoặc “Đang diễn ra”. |
| **BR-002** | **Sinh viên** chỉ được **đăng ký** tối đa **3** kỳ thi trong một học kỳ. |
| **BR-003** | **Kỳ thi** chỉ có thể **được công bố kết quả** sau khi **tất cả** câu hỏi tự luận đã được **chấm thủ công**. |
| **BR-004** | **Thời gian làm bài** của sinh viên **không được vượt quá** thời lượng đã cấu hình cho kỳ thi (tối đa 180 phút). |
| **BR-005** | **Admin** có thể **hủy** kỳ thi **trước** thời gian bắt đầu, nhưng **không** được hủy khi kỳ thi đã **bắt đầu** hoặc **đã kết thúc**. |
| **BR-006** | **Email thông báo** phải được gửi **đúng thời gian** (lập lịch, nhắc nhở 24 h, công bố kết quả) và **đảm bảo không trùng lặp** (một sinh viên nhận tối đa 1 email mỗi loại). |
| **BR-007** | **Mật khẩu** phải đáp ứng: ít nhất 8 ký tự, bao gồm ít nhất 1 chữ cái in hoa, 1 chữ cái thường, 1 số và 1 ký tự đặc biệt. |
| **BR-008** | **Dữ liệu lịch sử** không được **xóa** hoặc **sửa** sau khi đã được gắn nhãn “archived”. |

---

# Kiểm tra tự động (Checklist)  

- [ ] Mỗi FR có ID, ưu tiên, ít nhất 1 AC (Given/When/Then) và có AC lỗi/exception.  
- [ ] Không còn từ mơ hồ; mọi tiêu chí đều có số liệu hoặc giả định được ghi rõ.  
- [ ] FR chỉ mô tả **WHAT**, không đề cập tới công nghệ cụ thể.  
- [ ] In‑scope/Out‑of‑scope phù hợp với danh sách FR.  
- [ ] Mỗi role trong mục 2 có ít nhất 1 FR liên quan.  
- [ ] Đã bao phủ đầy đủ 6 nhóm NFR chính, trong đó **Security** (NFR‑002) được chi tiết.  
- [ ] Không có thay đổi không liên quan nếu đây là bản sửa dựa trên feedback reject (không có feedback reject trong yêu cầu hiện tại).