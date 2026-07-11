/**
 * @deprecated Bước 1 (2026-07-11) — Puck editor bị thay thế bởi GrapesJS.
 * File này được giữ lại để tham khảo, sẽ bị xóa ở Bước 2.
 *
 * Bộ component chuẩn dùng cho UI JSON (Giai đoạn 3.2 → 3.5).
 *
 * QUAN TRỌNG — ĐỒNG BỘ TAY: danh sách tên component ở đây PHẢI khớp với
 * `STANDARD_COMPONENTS` trong `graph/schemas.py` (phía Python).
 *
 * Giai đoạn 3.5: đã cài `@measured/puck` thật. Container (Card, Container,
 * Modal) dùng field kiểu `slot` để chứa component con — đây là cách Puck
 * biểu diễn cây lồng, KHÁC với field `children: UIComponentNode[]` mà
 * `graph/schemas.py` (Python) dùng để lưu trên git. Hai định dạng này
 * không giống nhau — xem `puckAdapter.ts` cho hàm chuyển đổi 2 chiều.
 */
import type { Config } from "@measured/puck";

export const STANDARD_COMPONENT_NAMES = [
  "Button",
  "Input",
  "Select",
  "Checkbox",
  "Card",
  "Table",
  "Modal",
  "Text",
  "Container",
] as const;

export type StandardComponentName = (typeof STANDARD_COMPONENT_NAMES)[number];

// ── Props types — 1 interface cho mỗi component, khớp field trong graph/schemas.py ──
type ButtonProps = { label: string; variant: "primary" | "danger" | "ghost"; onClickAction?: string };
type InputProps = { name: string; label?: string; placeholder?: string; inputType: "text" | "email" | "password" | "number"; required: boolean };
type SelectProps = { name: string; label?: string; options: { option: string }[]; required: boolean };
type CheckboxProps = { name: string; label?: string; defaultChecked: boolean };
type CardProps = { title?: string; children: any }; // "children" ở đây là slot, không phải mảng UIComponentNode
type TableProps = { columns: { column: string }[]; dataSource?: string };
type ModalProps = { title?: string; triggerLabel?: string; children: any };
type TextProps = { content: string; variant: "heading" | "body" | "caption" };
type ContainerProps = { direction: "column" | "row"; gap: number; children: any };

export type PuckComponentProps = {
  Button: ButtonProps;
  Input: InputProps;
  Select: SelectProps;
  Checkbox: CheckboxProps;
  Card: CardProps;
  Table: TableProps;
  Modal: ModalProps;
  Text: TextProps;
  Container: ContainerProps;
};

export const puckConfig: Config<PuckComponentProps> = {
  components: {
    Button: {
      label: "Button",
      fields: {
        label: { type: "text", label: "Nhãn nút" },
        variant: {
          type: "select",
          label: "Kiểu",
          options: [
            { label: "Primary", value: "primary" },
            { label: "Danger", value: "danger" },
            { label: "Ghost", value: "ghost" },
          ],
        },
        onClickAction: { type: "text", label: "Hành động (mô tả, vd: 'submit form')" },
      },
      defaultProps: { label: "Button", variant: "primary" },
      render: ({ label, variant }) => {
        const bg = variant === "primary" ? "#1677ff" : variant === "danger" ? "#ff4d4f" : "transparent";
        const color = variant === "ghost" ? "#1a1a1a" : "#ffffff";
        return (
          <button style={{ background: bg, color, border: variant === "ghost" ? "1px solid #1a1a1a" : "none", padding: "8px 16px", borderRadius: 6 }}>
            {label}
          </button>
        );
      },
    },

    Input: {
      label: "Input",
      fields: {
        name: { type: "text", label: "Tên field" },
        label: { type: "text", label: "Nhãn hiển thị" },
        placeholder: { type: "text", label: "Placeholder" },
        inputType: {
          type: "select",
          label: "Loại input",
          options: [
            { label: "Text", value: "text" },
            { label: "Email", value: "email" },
            { label: "Password", value: "password" },
            { label: "Number", value: "number" },
          ],
        },
        required: { type: "radio", label: "Bắt buộc", options: [{ label: "Có", value: true }, { label: "Không", value: false }] },
      },
      defaultProps: { name: "field_name", inputType: "text", required: false },
      render: ({ label, placeholder, inputType, required }) => (
        <div style={{ marginBottom: 8 }}>
          {label && <label style={{ display: "block", marginBottom: 4, fontSize: 12 }}>{label}{required ? " *" : ""}</label>}
          <input type={inputType} placeholder={placeholder} style={{ width: "100%", padding: 8, border: "1px solid #d9d9d9", borderRadius: 4 }} readOnly />
        </div>
      ),
    },

    Select: {
      label: "Select",
      fields: {
        name: { type: "text", label: "Tên field" },
        label: { type: "text", label: "Nhãn hiển thị" },
        options: { type: "array", label: "Danh sách lựa chọn", arrayFields: { option: { type: "text", label: "Giá trị" } } },
        required: { type: "radio", label: "Bắt buộc", options: [{ label: "Có", value: true }, { label: "Không", value: false }] },
      },
      defaultProps: { name: "field_name", options: [], required: false },
      render: ({ label, options }) => (
        <div style={{ marginBottom: 8 }}>
          {label && <label style={{ display: "block", marginBottom: 4 }}>{label}</label>}
          <select style={{ width: "100%", padding: 8, border: "1px solid #d9d9d9", borderRadius: 4 }}>
            {options.map((o, i) => <option key={i}>{o.option}</option>)}
          </select>
        </div>
      ),
    },

    Checkbox: {
      label: "Checkbox",
      fields: {
        name: { type: "text", label: "Tên field" },
        label: { type: "text", label: "Nhãn hiển thị" },
        defaultChecked: { type: "radio", label: "Mặc định chọn", options: [{ label: "Có", value: true }, { label: "Không", value: false }] },
      },
      defaultProps: { name: "field_name", defaultChecked: false },
      render: ({ label, defaultChecked }) => (
        <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <input type="checkbox" defaultChecked={defaultChecked} readOnly />{label}
        </label>
      ),
    },

    // ── Container components — dùng field kiểu "slot" để chứa component con ──
    Card: {
      label: "Card",
      fields: {
        title: { type: "text", label: "Tiêu đề" },
        children: { type: "slot" },
      },
      defaultProps: { title: "" },
      render: ({ title, children: Children }) => (
        <div style={{ border: "1px solid #eee", borderRadius: 8, padding: 16 }}>
          {title && <h3 style={{ marginTop: 0 }}>{title}</h3>}
          <Children />
        </div>
      ),
    },

    Modal: {
      label: "Modal",
      fields: {
        title: { type: "text", label: "Tiêu đề modal" },
        triggerLabel: { type: "text", label: "Nhãn nút mở modal" },
        children: { type: "slot" },
      },
      defaultProps: { triggerLabel: "Open" },
      render: ({ title, triggerLabel, children: Children }) => (
        <div style={{ border: "2px dashed #999", borderRadius: 8, padding: 16 }}>
          <em>[Modal: {triggerLabel}]</em>
          {title && <h4>{title}</h4>}
          <Children />
        </div>
      ),
    },

    Container: {
      label: "Container",
      fields: {
        direction: {
          type: "select",
          label: "Hướng sắp xếp",
          options: [{ label: "Dọc (column)", value: "column" }, { label: "Ngang (row)", value: "row" }],
        },
        gap: { type: "number", label: "Khoảng cách (px)" },
        children: { type: "slot" },
      },
      defaultProps: { direction: "column", gap: 16 },
      render: ({ direction, gap, children: Children }) => (
        <div style={{ display: "flex", flexDirection: direction, gap }}>
          <Children />
        </div>
      ),
    },

    Table: {
      label: "Table",
      fields: {
        columns: { type: "array", label: "Danh sách cột", arrayFields: { column: { type: "text", label: "Tên cột" } } },
        dataSource: { type: "text", label: "Nguồn dữ liệu (mô tả)" },
      },
      defaultProps: { columns: [] },
      render: ({ columns }) => (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead><tr>{columns.map((c, i) => <th key={i} style={{ border: "1px solid #eee", padding: 8, textAlign: "left" }}>{c.column}</th>)}</tr></thead>
        </table>
      ),
    },

    Text: {
      label: "Text",
      fields: {
        content: { type: "textarea", label: "Nội dung" },
        variant: {
          type: "select",
          label: "Kiểu chữ",
          options: [{ label: "Heading", value: "heading" }, { label: "Body", value: "body" }, { label: "Caption", value: "caption" }],
        },
      },
      defaultProps: { content: "", variant: "body" },
      render: ({ content, variant }) => {
        const Tag = variant === "heading" ? "h2" : variant === "caption" ? "small" : "p";
        return <Tag>{content}</Tag>;
      },
    },
  },
  root: { render: ({ children }) => <div>{children}</div> },
};