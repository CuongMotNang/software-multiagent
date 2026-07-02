# Domain: Viễn Thông (Telecommunications)

## 1. Thuật Ngữ Chuyên Ngành

| Thuật ngữ | Tiếng Anh | Giải thích |
|-----------|-----------|------------|
| MSISDN | Mobile Station International Subscriber Directory Number | Số thuê bao di động (VD: 0912345678) |
| IMSI | International Mobile Subscriber Identity | Mã định danh thuê bao trên SIM |
| HLR/HSS | Home Location Register / Home Subscriber Server | Cơ sở dữ liệu thuê bao chính |
| OCS | Online Charging System | Hệ thống tính cước thời gian thực (trả trước) |
| OFCS | Offline Charging System | Hệ thống tính cước hậu kỳ (trả sau) |
| PCRF | Policy & Charging Rules Function | Điều khiển chính sách QoS và cước |
| CDR | Call Detail Record | Bản ghi chi tiết cuộc gọi/data/SMS |
| VAS | Value Added Services | Dịch vụ giá trị gia tăng (nhạc chờ, SMS banking...) |
| MNP | Mobile Number Portability | Chuyển mạng giữ số |
| ARPU | Average Revenue Per User | Doanh thu trung bình/thuê bao |
| Churn Rate | Tỷ lệ rời mạng | % thuê bao ngừng sử dụng/chuyển mạng |
| Provisioning | Cung cấp dịch vụ | Kích hoạt/thay đổi gói cước trên hệ thống |
| Top-up | Nạp tiền | Nạp tiền vào tài khoản trả trước |
| Bundle | Gói combo | Gói kết hợp (data + voice + SMS) |
| FTTx | Fiber to the x | Internet cáp quang (FTTH = Fiber to Home) |

## 2. Compliance & Quy Định

| Quy định | Phạm vi | Yêu cầu chính cho BA |
|----------|---------|----------------------|
| **Nghị định 49/2017/NĐ-CP** | Đăng ký thuê bao | Xác thực danh tính, 1 CMND tối đa 3 SIM/nhà mạng |
| **Thông tư 47/2017/TT-BTTTT** | Quản lý thuê bao trả trước | Thu hồi SIM không chính chủ, xác minh qua OTP |
| **Luật Viễn thông 2023** | Toàn ngành | Chia sẻ hạ tầng, bảo vệ thông tin thuê bao |
| **QoS Standards (VNPT/Viettel)** | Chất lượng dịch vụ | Tỷ lệ cuộc gọi thành công ≥ 92%, data latency < 100ms |
| **Nghị định 13/2023/NĐ-CP** | Bảo vệ dữ liệu cá nhân | Consent, quyền truy cập/xóa dữ liệu cá nhân |

## 3. Entities Chính

```mermaid
erDiagram
    SUBSCRIBER ||--o{ SUBSCRIPTION : has
    SUBSCRIBER ||--o{ CDR : generates
    SUBSCRIBER {
        string subscriber_id PK
        string msisdn
        string imsi
        string id_card_number
        string full_name
        enum sub_type "Prepaid/Postpaid"
        enum status "Active/Suspended/Deactivated/PortedOut"
        decimal main_balance
        decimal data_balance_mb
        datetime activated_date
    }
    SUBSCRIPTION ||--|| PLAN : subscribes_to
    SUBSCRIPTION {
        string subscription_id PK
        string subscriber_id FK
        string plan_id FK
        datetime start_date
        datetime end_date
        enum auto_renew "Yes/No"
        enum status "Active/Expired/Cancelled"
    }
    PLAN ||--o{ PLAN_COMPONENT : includes
    PLAN {
        string plan_id PK
        string plan_name
        enum type "Voice/Data/Bundle/VAS"
        decimal price
        int validity_days
        enum billing_type "Prepaid/Postpaid"
    }
    PLAN_COMPONENT {
        string component_id PK
        string plan_id FK
        enum type "Voice_Minutes/SMS/Data_MB/Data_GB"
        decimal quota
        string description
    }
    CDR {
        string cdr_id PK
        string subscriber_id FK
        enum type "Voice/SMS/Data/VAS"
        datetime start_time
        int duration_seconds
        decimal data_usage_mb
        string destination
        decimal charge_amount
        enum rating_status "Rated/Unrated/Error"
    }
    TOP_UP {
        string topup_id PK
        string subscriber_id FK
        decimal amount
        enum channel "Scratch_Card/E_Wallet/Bank/Agent"
        datetime topup_time
        enum status "Success/Failed"
    }
```

## 4. State Diagrams

### 4.1 Subscriber Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Registered: SIM sold + identity verified
    Registered --> Active: First top-up / First call
    Active --> Suspended_Grace: No activity > 90 days (prepaid) OR No payment > 30 days (postpaid)
    Suspended_Grace --> Active: Top-up / Payment received
    Suspended_Grace --> Suspended_Lock: Grace period expired (30 days)
    Suspended_Lock --> Active: Top-up / Payment + reactivation fee
    Suspended_Lock --> Deactivated: Lock period expired (60 days)
    Active --> Ported_Out: MNP request completed
    Active --> Voluntarily_Deactivated: Customer requests deactivation
    Deactivated --> Number_Recycled: After quarantine period (12 months)
    Number_Recycled --> [*]
    Ported_Out --> [*]
```

### 4.2 Plan Subscription Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Pending: Customer registers plan
    Pending --> Active: Payment success / Balance deducted
    Pending --> Failed: Insufficient balance
    Active --> Quota_Exhausted: Data/Voice quota used up
    Quota_Exhausted --> Active: Top-up add-on package
    Active --> Expired: Validity period ends
    Expired --> Renewed: Auto-renew success
    Expired --> Lapsed: Auto-renew failed (no balance)
    Renewed --> Active
    Lapsed --> [*]
    Active --> Cancelled: Customer cancels
    Cancelled --> [*]
```

## 5. Events

| Event | Trigger | System Action | Notification |
|-------|---------|---------------|-------------|
| SIM Activated | First top-up or call | Provision on HLR, create subscriber record | Welcome SMS |
| Top-up Received | Payment confirmed | Update main_balance, extend validity | SMS balance confirmation |
| Plan Subscribed | Customer registers via USSD/App | Deduct fee, provision quota on OCS/PCRF | SMS plan activation details |
| Quota Exhausted | Data/voice usage reaches limit | Throttle speed (data) or block (voice) | SMS "Bạn đã hết data, mua thêm gói..." |
| CDR Generated | Call ends / Data session closes | Rate CDR, deduct from balance/quota | None (background) |
| Auto-Renew Triggered | Plan expiry date reached | Attempt balance deduction, renew if success | SMS success/failure |
| MNP Request | Customer applies to port | Validate eligibility, coordinate with new carrier | SMS confirmation + timeline |
| Suspension Warning | 60 days no activity (prepaid) | Send warning before suspension | SMS "Thuê bao sắp bị tạm ngưng..." |
| Fraud Detection | Abnormal usage pattern (VD: 100 SMS/min) | Auto-block, flag for review | SMS to subscriber + Alert to fraud team |
| Network Outage | BTS/Node failure detected | Reroute traffic, create incident ticket | Internal alert to NOC |

## 6. User Roles

| Role | Tiếng Việt | Permissions | Typical Actions |
|------|-----------|-------------|-----------------|
| **Subscriber** | Thuê bao | View balance, buy plan, top-up, check usage | Đăng ký gói, nạp tiền, kiểm tra tài khoản |
| **Call Center Agent** | Tổng đài viên | View subscriber info, troubleshoot, change plan | Hỗ trợ thuê bao, đổi gói, khóa/mở SIM |
| **Shop Agent** | Nhân viên cửa hàng | Activate SIM, sell plans, verify identity | Kích hoạt SIM, bán gói, xác minh giấy tờ |
| **Product Manager** | Quản lý sản phẩm | CRUD plans, set pricing, configure promotions | Thiết kế gói cước, cấu hình khuyến mãi |
| **Revenue Assurance** | Đảm bảo doanh thu | View CDR, reconcile billing, detect leakage | Đối soát cước, phát hiện thất thoát doanh thu |
| **NOC Engineer** | Kỹ sư vận hành mạng | Monitor network, manage incidents | Giám sát mạng, xử lý sự cố |
| **Fraud Analyst** | Phân tích gian lận | View flagged accounts, investigate, block | Điều tra thuê bao bất thường |
| **System Admin** | Quản trị hệ thống | Configure OCS/PCRF, user management | Cấu hình hệ thống tính cước |

## 7. Common Business Rules

| Rule ID | Mô tả | Điều kiện | Hành động |
|---------|-------|-----------|-----------|
| BR-TEL-001 | Giới hạn SIM/CMND | 1 CMND ≤ 3 SIM cùng nhà mạng | Block activation nếu vượt |
| BR-TEL-002 | Tính cước theo block | Voice: block 6s (6+1), Data: block 10KB | Round up to nearest block |
| BR-TEL-003 | Ưu tiên trừ cước | Quota gói → Tài khoản khuyến mãi → Tài khoản chính | Sequential deduction |
| BR-TEL-004 | Auto-renew retry | Nếu không đủ tiền, retry sau 24h, max 3 lần | Retry then expire |
| BR-TEL-005 | MNP eligibility | Thuê bao active ≥ 90 ngày, không nợ cước | Allow/deny port request |
| BR-TEL-006 | Data throttle | Hết data tốc độ cao → giảm xuống 128kbps | Apply PCRF policy |

## 8. Mẫu Requirement Đặc Thù

**User Story:**
```
As a Prepaid Subscriber,
I want to register a data plan via USSD code *098#,
So that I can get 2GB/day for 30 days.

AC1: Given my main balance ≥ plan price (VD: 77K),
     When I dial *098# and confirm,
     Then deduct 77K, provision 2GB/day quota, send SMS confirmation.

AC2: Given my balance < 77K,
     When I dial *098#,
     Then show "Tài khoản không đủ. Vui lòng nạp thêm" and do not subscribe.

AC3: Given I already have an active data plan,
     When I register a new one,
     Then stack the new plan (quotas are cumulative, validity = max of two).
```
