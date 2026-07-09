"""Render UI JSON (Giai đoạn 3.3) sang HTML tĩnh — dùng để Playwright chụp
PNG preview (Giai đoạn 3.4).

QUAN TRỌNG — đây KHÔNG phải Puck thật: package ``@measured/puck`` chưa được
cài (để dành Giai đoạn 3.5, lúc đó mới nhúng Puck editor thật cho phép sửa
tay). Renderer này tự viết bằng Python, chỉ nhằm mục đích tạo ra 1 bản
preview tĩnh đủ giống để reviewer xem hình dáng màn hình qua PNG — KHÔNG
tương tác được, KHÔNG dùng để sửa tay.

Chỉ hỗ trợ đúng 9 component trong STANDARD_COMPONENTS (khớp
frontend/ui-review/src/lib/puckConfig.ts) — component nào không có
trong đây sẽ không lọt qua được validate ở graph/schemas.py trước khi tới
renderer này.
"""

import html as html_lib

from graph.schemas import DesignTokens, UIComponentNode, UIScreen


def _esc(s: object) -> str:
    return html_lib.escape(str(s)) if s is not None else ""


def _render_button(props: dict, tokens: DesignTokens) -> str:
    variant = props.get("variant", "primary")
    color = {
        "primary": tokens.colors.primary,
        "danger": tokens.colors.danger,
        "ghost": "transparent",
    }.get(variant, tokens.colors.primary)
    text_color = tokens.colors.text if variant == "ghost" else "#ffffff"
    border = f"1px solid {tokens.colors.text}" if variant == "ghost" else "none"
    label = _esc(props.get("label", "Button"))
    return (
        f'<button style="background:{color};color:{text_color};border:{border};'
        f'padding:8px 16px;border-radius:6px;font-family:inherit;cursor:pointer;">{label}</button>'
    )


def _render_input(props: dict, tokens: DesignTokens) -> str:
    label = _esc(props.get("label", ""))
    placeholder = _esc(props.get("placeholder", ""))
    input_type = _esc(props.get("inputType", "text"))
    required = " *" if props.get("required") else ""
    sm = tokens.typography.sizes.get("sm", 12)
    gap0 = tokens.spacing_scale[0] if tokens.spacing_scale else 8
    label_html = f'<label style="display:block;margin-bottom:4px;font-size:{sm}px;">{label}{required}</label>' if label else ""
    return (
        f'<div style="margin-bottom:{gap0}px;">'
        f"{label_html}"
        f'<input type="{input_type}" placeholder="{placeholder}" '
        f'style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px;font-family:inherit;box-sizing:border-box;" />'
        f"</div>"
    )


def _render_select(props: dict, tokens: DesignTokens) -> str:
    label = _esc(props.get("label", ""))
    options = props.get("options", []) or []
    opts_html = "".join(f"<option>{_esc(o)}</option>" for o in options)
    label_html = f'<label style="display:block;margin-bottom:4px;">{label}</label>' if label else ""
    return (
        f'<div style="margin-bottom:8px;">{label_html}'
        f'<select style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px;">{opts_html}</select></div>'
    )


def _render_checkbox(props: dict, tokens: DesignTokens) -> str:
    label = _esc(props.get("label", ""))
    checked = "checked" if props.get("defaultChecked") else ""
    return (
        f'<label style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
        f'<input type="checkbox" {checked} />{label}</label>'
    )


def _render_table(props: dict, tokens: DesignTokens) -> str:
    columns = props.get("columns", []) or []
    source = _esc(props.get("dataSource", ""))
    headers = "".join(
        f'<th style="text-align:left;padding:8px;border-bottom:2px solid {tokens.colors.text};">{_esc(c)}</th>'
        for c in columns
    )
    placeholder_row = (
        f'<tr><td colspan="{max(len(columns), 1)}" style="padding:8px;color:#999;font-style:italic;">'
        f"(dữ liệu: {source})</td></tr>" if source else ""
    )
    return (
        f'<table style="width:100%;border-collapse:collapse;margin-bottom:16px;">'
        f"<thead><tr>{headers}</tr></thead><tbody>{placeholder_row}</tbody></table>"
    )


def _render_modal(props: dict, tokens: DesignTokens) -> str:
    title = _esc(props.get("title", ""))
    trigger = _esc(props.get("triggerLabel", "Open"))
    sm = tokens.typography.sizes.get("sm", 12)
    return (
        f'<div style="border:1px dashed #999;padding:16px;border-radius:8px;margin-bottom:8px;">'
        f'<div style="font-size:{sm}px;color:#999;">[Modal preview]</div>'
        f'<div style="font-weight:bold;">{title}</div>'
        f'<button style="margin-top:8px;">{trigger}</button></div>'
    )


def _render_text(props: dict, tokens: DesignTokens) -> str:
    content = _esc(props.get("content", ""))
    variant = props.get("variant", "body")
    size = {
        "heading": tokens.typography.sizes.get("xl", 24),
        "body": tokens.typography.sizes.get("base", 14),
        "caption": tokens.typography.sizes.get("sm", 12),
    }.get(variant, tokens.typography.sizes.get("base", 14))
    weight = "bold" if variant == "heading" else "normal"
    return f'<div style="font-size:{size}px;font-weight:{weight};margin-bottom:8px;">{content}</div>'


def _render_card(props: dict, children_html: str, tokens: DesignTokens) -> str:
    title = _esc(props.get("title", ""))
    title_html = f'<div style="font-weight:bold;margin-bottom:8px;">{title}</div>' if title else ""
    return (
        f'<div style="border:1px solid #e8e8e8;border-radius:8px;padding:16px;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.08);margin-bottom:16px;">{title_html}{children_html}</div>'
    )


def _render_container(props: dict, children_html: str, tokens: DesignTokens) -> str:
    direction = props.get("direction", "column")
    gap = props.get("gap", tokens.spacing_scale[1] if len(tokens.spacing_scale) > 1 else 16)
    flex_dir = "row" if direction == "row" else "column"
    return f'<div style="display:flex;flex-direction:{flex_dir};gap:{gap}px;">{children_html}</div>'


def _render_node(node: UIComponentNode, tokens: DesignTokens) -> str:
    children_html = "".join(_render_node(c, tokens) for c in node.children)
    if node.type == "Button":
        return _render_button(node.props, tokens)
    if node.type == "Input":
        return _render_input(node.props, tokens)
    if node.type == "Select":
        return _render_select(node.props, tokens)
    if node.type == "Checkbox":
        return _render_checkbox(node.props, tokens)
    if node.type == "Table":
        return _render_table(node.props, tokens)
    if node.type == "Modal":
        return _render_modal(node.props, tokens)
    if node.type == "Text":
        return _render_text(node.props, tokens)
    if node.type == "Card":
        return _render_card(node.props, children_html, tokens)
    if node.type == "Container":
        return _render_container(node.props, children_html, tokens)
    # Không nên tới đây — schema đã validate type ở graph/schemas.py rồi.
    return f"<!-- component không xác định: {_esc(node.type)} -->"


def render_screen_to_html(screen: UIScreen, tokens: DesignTokens) -> str:
    """UIScreen + DesignTokens -> 1 file HTML hoàn chỉnh, độc lập (đủ để
    Playwright mở trực tiếp và chụp full-page screenshot)."""
    body = "".join(_render_node(node, tokens) for node in screen.root)
    base_size = tokens.typography.sizes.get("base", 14)
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8" />
<title>{_esc(screen.label)}</title>
<style>
  body {{
    margin: 0;
    padding: 32px;
    background: {tokens.colors.background};
    color: {tokens.colors.text};
    font-family: {tokens.typography.font};
    font-size: {base_size}px;
  }}
</style>
</head>
<body>
{body}
</body>
</html>"""
