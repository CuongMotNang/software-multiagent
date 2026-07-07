# STAKEHOLDER REGISTER

| Role | Quyền lực (H/L) | Quan tâm (H/L) | Chiến lược tiếp cận |
|------|------------------|-----------------|----------------------|
| Developer (người dùng cuối) | L | H | Thu thập phản hồi qua khảo sát định kỳ, beta testing; ưu tiên UX phù hợp workflow coding |
| Product Owner/Quản lý sản phẩm | H | H | Họp định kỳ tuần/sprint, cần sign-off trước mỗi giai đoạn phát hành |
| Team Lead/Technical Lead | H | L | Cập nhật tiến độ qua báo cáo ngắn gọn, đảm bảo công cụ không gây friction cho team |
| Nhà đầu tư/Chủ sở hữu sản phẩm (nếu có) | H | L | Báo cáo KPI định kỳ, tập trung vào metrics adoption và retention |

---

# ELICITATION SUMMARY

## Mục tiêu nghiệp vụ
- Giải quyết nhu cầu quản lý công việc cá nhân của developer trong quá trình lập trình
- Mục tiêu định lượng: **Không đề cập** → cần làm rõ (VD: giảm context switching, tăng năng suất focus time)
- Mục tiêu định tính: Cung cấp công cụ todo phù hợp với workflow đặc thù của developer (khác biệt với todo app chung chung)

## Đối tượng người dùng
| Nhóm | Đặc điểm |
|------|----------|
| Developer cá nhân/freelancer | 1 người, am hiểu công nghệ cao, sử dụng desktop chính (VS Code/IDE), có thể dùng mobile phụ |
| Developer trong team | Nhiều người, cần đồng bộ với công cụ team hiện có (Jira, GitHub, Slack...) |
| *Suy luận*: Có thể có cả 2 nhóm trên, hoặc tập trung 1 nhóm — cần làm rõ | |

## Tính năng cốt lõi
*(Ước lượng độ ưu tiên dựa trên "developer" và "todo app")*

1. **Tạo và quản lý task cá nhân** — nền tảng của mọi todo app
2. **Tích hợp với workflow development** *(suy luận: đặc thù "cho developer")* — VD: liên kết task với branch, commit, PR; hoặc tích hợp IDE
3. **Phân loại/đánh tag task theo context kỹ thuật** — VD: bug, feature, refactor, tech debt
4. **Đặt deadline/priority cho task** — cơ bản nhưng cần thiết
5. **Theo dõi trạng thái task** — todo, in-progress, done; có thể mở rộng thêm trạng thái dev-specific
6. **Lưu trữ lịch sử/task archive** — developer thường cần tra lại task cũ

## Ràng buộc

| Nhóm | Chi tiết |
|------|----------|
| **Thời gian** | Không đề cập |
| **Công nghệ** | Không đề cập — nhưng *suy luận*: nền tảng desktop (Windows/Mac/Linux) hoặc web là phù hợp; có thể cần xem xét extension cho IDE |
| **Ngân sách** | Không đề cập |
| **Pháp lý/Tuân thủ** | Không đề cập — *suy luận*: nếu tích hợp với GitHub/GitLab, cần tuân thủ OAuth/API terms của bên thứ ba |

## Câu hỏi còn mở

| Câu hỏi | Tại sao cần làm rõ | Ảnh hưởng nếu không trả lời |
|---------|-------------------|------------------------------|
| "Developer" ở đây là nhóm nhỏ cá nhân hay tổ chức/enterprise? | Quyết định scope: cá nhân (single player) hay team collaboration | Thiết kế sai architecture, thiếu/t thừa tính năng multi-user |
| Có cần tích hợp với công cụ cụ thể nào không? (GitHub, Jira, VS Code, Notion...) | Đặc thù "cho developer" chưa rõ | Không biết prioritise tích hợp nào; risk làm app generic |
| Mục tiêu định lượng là gì? (VD: giảm 20% task bị bỏ quên, tăng 30% focus time) | Đo lường thành công của sản phẩm | Không có KPI để đánh giá, dễ scope creep |
| Nền tảng ưu tiên: web, desktop app, mobile, hay IDE extension? | Developer workflow khác nhau về thiết bị | UX thiếu tối ưu cho context thực tế |
| Có cần đồng bộ đa thiết bị không? | Developer thường dùng nhiều máy | Ảnh hưởng đến yêu cầu về real-time sync, offline support |
| Mô hình kinh doanh dự kiến? (miễn phí, freemium, subscription) | Ảnh hưởng đến giới hạn tính năng và NFR về scalability | Không biết giới hạn ngầm về chi phí vận hành |