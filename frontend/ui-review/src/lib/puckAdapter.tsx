/**
 * @deprecated Bước 1 (2026-07-11) — Puck editor bị thay thế bởi GrapesJS.
 * File này được giữ lại để tham khảo, sẽ bị xóa ở Bước 2.
 *
 * Chuyển đổi 2 chiều giữa UIScreen (JSON lưu trên git, khớp
 * `graph/schemas.py`) và Puck `Data` (định dạng editor dùng để render/sửa).
 *
 * Khác biệt cốt lõi:
 * - UIScreen: mỗi node có field `children: UIComponentNode[]` (mảng con trực tiếp).
 * - Puck Data: mỗi component cần `props.id` (string duy nhất, Puck dùng để
 *   track selection/drag). Với container (Card/Modal/Container), field
 *   `children` trong props chính là "slot" — về hình dạng JSON nó vẫn là
 *   1 mảng {type, props} giống hệt content gốc, nên có thể map gần như
 *   1-1, chỉ cần thêm/bớt `id`.
 */
import type { Data } from "@measured/puck";

export interface UIComponentNode {
  type: string;
  props: Record<string, unknown>;
  children: UIComponentNode[];
}

export interface UIScreen {
  screen: string;
  label: string;
  root: UIComponentNode[];
}

const CONTAINER_TYPES = new Set(["Card", "Modal", "Container"]);

let _idCounter = 0;
function genId(type: string): string {
  _idCounter += 1;
  return `${type}-${Date.now()}-${_idCounter}`;
}

/** UIScreen (git) → Puck Data (editor). */
export function uiScreenToPuckData(screen: UIScreen): Data {
  function convert(node: UIComponentNode): { type: string; props: Record<string, unknown> } {
    const props: Record<string, unknown> = { ...node.props, id: genId(node.type) };
    if (CONTAINER_TYPES.has(node.type)) {
      props.children = node.children.map(convert);
    }
    return { type: node.type, props };
  }

  return {
    content: screen.root.map(convert),
    root: { props: {} },
  };
}

/** Puck Data (editor) → UIScreen (git). Bỏ hết `id` — schema Python không cần. */
export function puckDataToUIScreen(data: Data, meta: { screen: string; label: string }): UIScreen {
  function convert(item: { type: string; props: Record<string, unknown> }): UIComponentNode {
    const { id, children, ...rest } = item.props as Record<string, unknown> & { id?: string; children?: unknown };
    const childArray = CONTAINER_TYPES.has(item.type) && Array.isArray(children) ? children : [];
    return {
      type: item.type,
      props: rest,
      children: (childArray as Array<{ type: string; props: Record<string, unknown> }>).map(convert),
    };
  }

  return {
    screen: meta.screen,
    label: meta.label,
    root: (data.content as Array<{ type: string; props: Record<string, unknown> }>).map(convert),
  };
}