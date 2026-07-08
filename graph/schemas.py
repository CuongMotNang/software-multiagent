"""Schema dùng chung cho pipeline — hiện chỉ có DesignTokens (Giai đoạn 3.1).

LƯU Ý ĐỒNG BỘ TAY: ``STANDARD_COMPONENTS`` ở đây phải khớp với danh sách
component thật sự có config trong ``frontend/ui-review/src/lib/puckConfig.ts``
(Giai đoạn 3.2). Đây là bộ component CỐ ĐỊNH, viết tay — LLM chỉ được chọn
tên trong danh sách này khi liệt kê ``components`` trong design_tokens.json,
không tự "phát minh" component mới (tránh JSON tham chiếu component không
tồn tại trong Puck config, sẽ vỡ lúc render).
"""

from pydantic import BaseModel, Field, field_validator

STANDARD_COMPONENTS: list[str] = [
    "Button",
    "Input",
    "Select",
    "Checkbox",
    "Card",
    "Table",
    "Modal",
    "Text",
    "Container",
]


class DesignTokensColors(BaseModel):
    primary: str
    danger: str
    background: str
    text: str


class DesignTokensTypography(BaseModel):
    font: str
    sizes: dict[str, int]


class DesignTokens(BaseModel):
    """Schema cho design_tokens.json — sinh 1 lần sau design_node, dùng làm
    ngữ cảnh bắt buộc cho mọi lần ui_node sinh screen (Giai đoạn 3.1-3.2).
    """

    colors: DesignTokensColors
    spacing_scale: list[int] = Field(min_length=1)
    typography: DesignTokensTypography
    components: list[str] = Field(min_length=1)

    @field_validator("components")
    @classmethod
    def _components_must_be_standard(cls, v: list[str]) -> list[str]:
        unknown = [c for c in v if c not in STANDARD_COMPONENTS]
        if unknown:
            raise ValueError(
                f"Component không hợp lệ: {unknown}. "
                f"Chỉ được chọn trong: {STANDARD_COMPONENTS}"
            )
        return v
