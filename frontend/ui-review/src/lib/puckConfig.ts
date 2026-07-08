/**
 * Bộ component chuẩn dùng cho UI JSON (Giai đoạn 3.2).
 *
 * QUAN TRỌNG — ĐỒNG BỘ TAY: danh sách tên component ở đây PHẢI khớp với
 * `STANDARD_COMPONENTS` trong `graph/schemas.py` (phía Python). LLM sinh
 * design_tokens.json chỉ được chọn tên trong danh sách đó — nếu 2 bên
 * lệch nhau, JSON tham chiếu 1 component không có config ở đây sẽ vỡ lúc
 * render trong Puck editor (Giai đoạn 3.5).
 *
 * Cố tình viết dạng object thuần (chưa import `Config` từ `@measured/puck`)
 * vì package đó CHƯA được cài — việc cài + nhúng Puck editor thật để dành
 * Giai đoạn 3.5. File này chỉ định nghĩa "hợp đồng" (tên field, kiểu dữ
 * liệu) mà LLM (ui_node) và Puck editor sau này phải cùng tuân theo.
 * Khi cài Puck ở 3.5, đổi khai báo `PuckComponentConfig` bên dưới thành
 * đúng `Config<...>` của package, cấu trúc field/props giữ nguyên logic.
 */

export type PuckFieldType = "text" | "textarea" | "number" | "select" | "boolean" | "array";

export interface PuckFieldDef {
  type: PuckFieldType;
  label: string;
  /** Chỉ dùng khi type === "select" */
  options?: { label: string; value: string }[];
  /** Giá trị mặc định khi kéo component mới vào canvas */
  defaultValue?: unknown;
}

export interface PuckComponentDef {
  /** Tên hiển thị trong panel chọn component của Puck editor */
  label: string;
  fields: Record<string, PuckFieldDef>;
}

/**
 * Danh sách tên component chuẩn — nguồn thật để đối chiếu với
 * `STANDARD_COMPONENTS` phía graph/schemas.py.
 */
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

export const puckComponentConfig: Record<StandardComponentName, PuckComponentDef> = {
  Button: {
    label: "Button",
    fields: {
      label: { type: "text", label: "Nhãn nút", defaultValue: "Button" },
      variant: {
        type: "select",
        label: "Kiểu",
        options: [
          { label: "Primary", value: "primary" },
          { label: "Danger", value: "danger" },
          { label: "Ghost", value: "ghost" },
        ],
        defaultValue: "primary",
      },
      onClickAction: { type: "text", label: "Hành động (mô tả, vd: 'submit form')" },
    },
  },

  Input: {
    label: "Input",
    fields: {
      name: { type: "text", label: "Tên field", defaultValue: "field_name" },
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
        defaultValue: "text",
      },
      required: { type: "boolean", label: "Bắt buộc", defaultValue: false },
    },
  },

  Select: {
    label: "Select",
    fields: {
      name: { type: "text", label: "Tên field" },
      label: { type: "text", label: "Nhãn hiển thị" },
      options: { type: "array", label: "Danh sách lựa chọn" },
      required: { type: "boolean", label: "Bắt buộc", defaultValue: false },
    },
  },

  Checkbox: {
    label: "Checkbox",
    fields: {
      name: { type: "text", label: "Tên field" },
      label: { type: "text", label: "Nhãn hiển thị" },
      defaultChecked: { type: "boolean", label: "Mặc định chọn", defaultValue: false },
    },
  },

  Card: {
    label: "Card",
    fields: {
      title: { type: "text", label: "Tiêu đề" },
      // Card chứa các component khác — trong Puck thật sẽ dùng `slot`,
      // ở đây chỉ khai báo field mô tả để LLM/JSON biết field nào hợp lệ.
    },
  },

  Table: {
    label: "Table",
    fields: {
      columns: { type: "array", label: "Danh sách cột (tên cột)" },
      dataSource: { type: "text", label: "Nguồn dữ liệu (mô tả, vd: 'danh sách sản phẩm')" },
    },
  },

  Modal: {
    label: "Modal",
    fields: {
      title: { type: "text", label: "Tiêu đề modal" },
      triggerLabel: { type: "text", label: "Nhãn nút mở modal" },
    },
  },

  Text: {
    label: "Text",
    fields: {
      content: { type: "textarea", label: "Nội dung" },
      variant: {
        type: "select",
        label: "Kiểu chữ",
        options: [
          { label: "Heading", value: "heading" },
          { label: "Body", value: "body" },
          { label: "Caption", value: "caption" },
        ],
        defaultValue: "body",
      },
    },
  },

  Container: {
    label: "Container",
    fields: {
      direction: {
        type: "select",
        label: "Hướng sắp xếp",
        options: [
          { label: "Dọc (column)", value: "column" },
          { label: "Ngang (row)", value: "row" },
        ],
        defaultValue: "column",
      },
      gap: { type: "number", label: "Khoảng cách giữa các phần tử (px)", defaultValue: 16 },
    },
  },
};
