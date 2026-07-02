# Design Specification Guide

Template for writing Detailed Design documents, abstracted from real-world Vietnamese IT project standards.

## Document Structure

```
I.   NGUỒN GỐC THAY ĐỔI (Change Origin)
II.  NỘI DUNG THAY ĐỔI (Change Summary)
     1. Mô tả chung về yêu cầu thay đổi
     2. Mô tả thay đổi về luồng nghiệp vụ
     3. Mô tả thay đổi về CSDL
III. CHI TIẾT CÁC CHỨC NĂNG (Function Details)
     Per function:
       X.1. [Function Name]
            - Đối tượng bị tác động (Affected Objects)
            - Thay đổi về giao diện (UI Changes) → Control Spec Table
            - Thay đổi về nghiệp vụ (Business Logic Changes)
            - Xử lý sự kiện tương tác (Event Handling) → Processing Steps Table
IV.  CHI TIẾT NGHIỆP VỤ ẢNH HƯỞNG (Impact Assessment)
     1. Các nghiệp vụ trong cùng hệ thống
     2. Chức năng của hệ thống khác
```

## Change Log Table (Bảng ghi nhận thay đổi)

Place at the top of document:

| Ngày thay đổi | Vị trí thay đổi | A/M/D* | Nguồn gốc | Đầu mối KH | Mô tả thay đổi | Version |
|----------------|------------------|--------|------------|-------------|-----------------|---------|
| [Date] | [Section] | A | [Source] | [Contact] | [Description] | 1.0 |

*A = Add new, M = Modify, D = Delete

## Control Specification Table (Bảng mô tả control)

For EVERY screen/form, provide:

| STT | Tên (Field Name) | Loại Control | Bắt buộc | Độ dài tối đa | Read Only | Mô tả |
|-----|-------------------|-------------|----------|---------------|-----------|-------|
| 1 | [field_name] | Text box / Select box / Date picker / Button / Text area / Checkbox / Radio | X or blank | [number] | X or blank | [Business description + validation rules + error messages] |

### Mô tả field must include:
- **Purpose**: What this field is for
- **Data source**: Where values come from (static list, DB query, API)
- **Validation**: Rules applied on input
- **Error messages**: Exact message for each validation failure
  - Format: `Error message: [Field Name]: [Message text]`
- **Default value**: If any

### Example:
```
| 1 | URL | Text box | X | 500 | | Nhập URL của API endpoint.
Nếu để trống: Error message: URL: Dữ liệu chưa được tạo
Nếu sai format: Error message: URL: Đường dẫn sai định dạng
Format: phải bắt đầu bằng http:// hoặc https:// |
```

## Processing Steps Table (Bảng xử lý sự kiện)

For EVERY user interaction or system process:

| Step | Description |
|------|-------------|
| 1 | [Trigger: what user does] |
| 2 | [System validation: check input fields] |
| 3 | [Processing: business logic, DB operations] |
| 4 | [Output: what system returns/displays] |
| 5 | [Error handling: what happens if step 3 fails] |

### Rules for Processing Steps:
- Each step must be atomic (one action)
- Include exact SQL/API calls if known (use parameterized queries with :parameter_name)
- Include conditional logic clearly (Nếu... thì... Nếu không...)
- Include error messages for failure scenarios
- Reference Control Spec table field names

## Section III Detail Pattern

For each function/feature being specified:

```markdown
### X.1. [Function Name]

#### Đối tượng bị tác động
- [List affected entities, tables, or system components]
- Write "N/A" if none

#### Thay đổi về giao diện
[Insert screenshot or wireframe reference]
[Insert Control Specification Table]

#### Thay đổi về nghiệp vụ
- [Describe business rule changes in bullet points]
- [Reference BR-xxx IDs if available]

#### Xử lý sự kiện tương tác
[Insert Processing Steps Table]
```

## Section IV Pattern

```markdown
### 1. Các nghiệp vụ trong cùng hệ thống
- [List functions in same system affected by this change]

### 2. Chức năng của hệ thống khác
- [List external system functions affected]
- Write "Không có hệ thống ngoài ảnh hưởng" if none
```

## Quality Checks for Design (run Checklist 3)

Before finalizing, verify every function section has:
- [ ] Complete Control Spec table (no missing fields)
- [ ] All input fields have validation rules + error messages
- [ ] Processing Steps cover happy path + error paths
- [ ] Boundary conditions addressed (empty, max length, special chars)
- [ ] Affected objects listed
- [ ] Impact assessment completed
