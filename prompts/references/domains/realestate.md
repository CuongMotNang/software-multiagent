# Domain: Bất Động Sản (Real Estate)

## 1. Thuật Ngữ Chuyên Ngành

| Thuật ngữ | Tiếng Anh | Giải thích |
|-----------|-----------|------------|
| Sổ đỏ / Sổ hồng | Land Use Right Certificate | Giấy chứng nhận quyền sử dụng đất / sở hữu nhà |
| Chủ đầu tư (CĐT) | Developer / Investor | Tổ chức/cá nhân phát triển dự án BĐS |
| Booking / Đặt chỗ | Reservation | Đặt cọc giữ chỗ trước khi ký HĐMB |
| HĐMB | Sale & Purchase Agreement (SPA) | Hợp đồng mua bán |
| Bàn giao | Handover | Giao nhà/căn hộ cho khách hàng |
| Phí bảo trì | Maintenance Fee | 2% giá trị căn hộ, nộp khi bàn giao |
| Phí quản lý | Management Fee | Phí quản lý tòa nhà hàng tháng (VND/m²/tháng) |
| NOM | Net Operating Margin | Biên lợi nhuận hoạt động |
| GFA / NFA | Gross/Net Floor Area | Diện tích sàn thô / thực tế sử dụng |
| CĐT / Sàn GD | Developer / Trading Floor | Chủ đầu tư / Sàn giao dịch BĐS |
| Pháp lý dự án | Project Legal Status | Giấy phép xây dựng, quy hoạch 1/500, EIA |
| Thanh toán theo tiến độ | Progress Payment | Thanh toán theo % hoàn thành xây dựng |
| Mở bán | Sales Launch | Sự kiện mở bán chính thức |
| Commission | Hoa hồng môi giới | % giá trị giao dịch trả cho broker |

## 2. Compliance & Quy Định

| Quy định | Phạm vi | Yêu cầu chính cho BA |
|----------|---------|----------------------|
| **Luật Kinh doanh BĐS 2023** | Toàn ngành | Điều kiện bán, thanh toán, bảo lãnh ngân hàng |
| **Luật Nhà ở 2023** | Nhà ở | Sở hữu chung cư có thời hạn, quản lý tòa nhà |
| **Nghị định 99/2015/NĐ-CP** | Sở hữu nhà cho người nước ngoài | Tối đa 30% căn hộ/tòa nhà, sở hữu 50 năm |
| **Thông tư 19/2016/TT-BXD** | Bảo lãnh nhà ở hình thành tương lai | Ngân hàng bảo lãnh nghĩa vụ CĐT |
| **Luật Đất đai 2024** | Sử dụng đất | Quyền sử dụng đất, bồi thường, giải phóng mặt bằng |

## 3. Entities Chính

```mermaid
erDiagram
    PROJECT ||--|{ BUILDING : has
    PROJECT {
        string project_id PK
        string project_name
        string developer_id FK
        string address
        string district
        string city
        enum type "Apartment/Villa/Townhouse/Commercial/Mixed"
        enum legal_status "Planning/Approved/Under_Construction/Completed"
        int total_units
        date expected_handover
    }
    BUILDING ||--|{ UNIT : contains
    BUILDING {
        string building_id PK
        string project_id FK
        string building_name
        int total_floors
        int units_per_floor
        enum construction_status "Foundation/Structure/MEP/Finishing/Completed"
    }
    UNIT ||--o| BOOKING : reserved_by
    UNIT ||--o| CONTRACT : sold_via
    UNIT {
        string unit_id PK
        string building_id FK
        string unit_code "VD: A-1205"
        int floor
        decimal gfa_m2
        decimal nfa_m2
        enum type "Studio/1BR/2BR/3BR/Penthouse/Shophouse"
        decimal base_price
        decimal price_per_m2
        enum direction "East/West/South/North/SE/NE/SW/NW"
        enum view "Pool/Garden/River/City/Internal"
        enum status "Available/Booked/Deposited/Sold/Handed_Over/Cancelled"
    }
    CUSTOMER ||--o{ BOOKING : makes
    CUSTOMER ||--o{ CONTRACT : signs
    CUSTOMER {
        string customer_id PK
        string full_name
        string id_number
        string phone
        string email
        enum nationality "Vietnamese/Foreign"
        string referral_source "VD: Broker/Online/Event"
        string broker_id FK
    }
    BOOKING {
        string booking_id PK
        string unit_id FK
        string customer_id FK
        decimal booking_amount
        datetime booking_date
        datetime expiry_date
        enum status "Active/Converted_to_Contract/Expired/Cancelled/Refunded"
    }
    CONTRACT ||--|{ PAYMENT_SCHEDULE : has
    CONTRACT {
        string contract_id PK
        string unit_id FK
        string customer_id FK
        decimal contract_value
        decimal discount_percent
        decimal final_price
        date signed_date
        enum payment_method "Full/Progress/Bank_Loan"
        enum status "Draft/Signed/In_Payment/Completed/Handed_Over/Terminated"
    }
    PAYMENT_SCHEDULE {
        string payment_id PK
        string contract_id FK
        int installment_number
        string milestone "VD: Ký HĐ / Cất nóc / Bàn giao"
        decimal amount
        decimal percentage
        date due_date
        enum status "Upcoming/Due/Paid/Overdue"
    }
    BROKER {
        string broker_id PK
        string full_name
        string company
        string phone
        decimal commission_rate
        enum status "Active/Inactive"
    }
```

## 4. State Diagrams

### 4.1 Unit Sales Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Available: Unit listed for sale
    Available --> Booked: Customer pays booking fee
    Booked --> Deposited: Customer pays deposit (within booking window)
    Booked --> Available: Booking expired / Cancelled → refund
    Deposited --> Contract_Signed: SPA signed
    Deposited --> Available: Customer withdraws → forfeit deposit
    Contract_Signed --> In_Payment: Progress payments ongoing
    In_Payment --> Payment_Completed: All installments paid
    Payment_Completed --> Handover_Scheduled: Construction complete
    Handover_Scheduled --> Handed_Over: Customer accepts unit + POD
    Handed_Over --> Certificate_Issued: Sổ hồng issued
    Certificate_Issued --> [*]
    
    Contract_Signed --> Terminated: Contract breach
    Terminated --> Available: Unit returned to inventory
```

### 4.2 Payment Schedule

```mermaid
stateDiagram-v2
    [*] --> Upcoming: Future installment
    Upcoming --> Due: Due date reached
    Due --> Paid: Customer pays within grace period
    Due --> Overdue: Grace period (15 days) expired
    Overdue --> Paid: Late payment received (+ penalty)
    Overdue --> Escalated: > 30 days overdue
    Escalated --> Paid: Payment received after escalation
    Escalated --> Contract_Termination: > 90 days, no payment
    Paid --> [*]
```

## 5. Events

| Event | Trigger | System Action | Notification |
|-------|---------|---------------|-------------|
| Sales Launch | CĐT opens sales | Update units to Available, enable booking | Email/SMS to registered leads |
| Booking Created | Customer pays booking fee | Reserve unit, start countdown timer | SMS confirmation + booking receipt |
| Booking Expiry Warning | 3 days before booking expires | Alert sales team | SMS to customer + Email to sales |
| Contract Signed | Both parties sign SPA | Generate payment schedule, lock unit price | Email with contract + schedule |
| Payment Due | 7 days before installment due | Generate payment reminder | SMS + Email reminder |
| Payment Overdue | Due date + grace period passed | Calculate penalty interest, alert finance | SMS warning + Email to customer |
| Construction Milestone | Builder reports progress (VD: cất nóc) | Update building status, trigger next payment | SMS "Dự án đã cất nóc, đợt TT tiếp theo..." |
| Handover Invitation | Unit ready for handover | Schedule handover appointment | Letter + SMS + Email to customer |
| Commission Due | Contract signed OR handover (per policy) | Calculate broker commission | Notify broker + finance |
| Price Adjustment | CĐT updates price list | Update unit prices, log change history | Internal alert to sales team |

## 6. User Roles

| Role | Tiếng Việt | Permissions | Typical Actions |
|------|-----------|-------------|-----------------|
| **Customer** | Khách hàng | View units, book, track payments | Xem căn hộ, đặt chỗ, theo dõi thanh toán |
| **Sales Consultant** | Tư vấn viên | CRUD bookings, view units, manage leads | Tư vấn, tạo booking, chăm sóc khách |
| **Sales Manager** | Quản lý kinh doanh | Approve discounts, view reports, manage team | Duyệt giảm giá, xem doanh số |
| **Broker** | Môi giới | View available units, refer customers | Giới thiệu khách, theo dõi hoa hồng |
| **Finance** | Kế toán | Manage payments, reconcile, generate invoices | Xác nhận thanh toán, xuất hóa đơn |
| **Legal** | Pháp chế | Manage contracts, verify documents | Soạn HĐ, kiểm tra pháp lý |
| **Construction PM** | Quản lý xây dựng | Update construction progress | Cập nhật tiến độ xây dựng |
| **Customer Service** | CSKH | Handle complaints, manage handover scheduling | Xử lý khiếu nại, lên lịch bàn giao |
| **Admin** | Quản trị | System config, user management, master data | Cấu hình dự án, phân quyền |

## 7. Common Business Rules

| Rule ID | Mô tả | Điều kiện | Hành động |
|---------|-------|-----------|-----------|
| BR-RE-001 | Foreign ownership cap | Foreign buyers > 30% units in building | Block booking for foreigners |
| BR-RE-002 | Booking validity | Booking not converted within 15 days | Auto-expire + refund |
| BR-RE-003 | Discount authority | Discount ≤ 3%: Sales Mgr; > 3%: Director | Route for approval |
| BR-RE-004 | Maintenance fee collection | At handover | Collect 2% of contract value |
| BR-RE-005 | Late payment penalty | Payment overdue > grace period | 0.05%/day on overdue amount |
| BR-RE-006 | One unit per booking | 1 customer can book max 1 unit per transaction | Validate at booking |

## 8. Mẫu Requirement

**User Story:**
```
As a Sales Consultant,
I want to view real-time unit availability on an interactive floor plan,
So that I can quickly show customers which units are available during a sales event.

AC1: Given Building A has 200 units,
     When I open the floor plan for Floor 12,
     Then each unit is color-coded: Green=Available, Yellow=Booked, Red=Sold, Grey=Unavailable.

AC2: Given a unit is Booked and booking expires in < 24h,
     When I view the floor plan,
     Then the unit shows a blinking Yellow indicator with countdown timer.
```
