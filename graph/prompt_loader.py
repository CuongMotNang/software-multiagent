"""Prompt Loader — đọc system prompt theo version từ biến môi trường.

Cấu trúc thư mục prompts/:
    prompts/
    ├── system/
    │   ├── ba_system.txt           ← file active (fallback)
    │   ├── prd_system.txt
    │   ├── design_system.txt
    │   └── ui_system.txt
    └── versions/
        ├── ba_v1.txt               ← version cụ thể
        ├── ba_v2.txt
        ├── prd_v1.txt
        ├── prd_v2.txt
        └── ...

Biến môi trường điều khiển version (.env):
    BA_PROMPT_VERSION=v2
    PRD_PROMPT_VERSION=v2
    DESIGN_PROMPT_VERSION=v2
    UI_PROMPT_VERSION=v1
"""

import os
from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"

# Map tên prompt → tên biến env tương ứng
_ENV_KEY_MAP = {
    "ba_system":     "BA_PROMPT_VERSION",
    "prd_system":    "PRD_PROMPT_VERSION",
    "design_system": "DESIGN_PROMPT_VERSION",
    "ui_system":     "UI_PROMPT_VERSION",
}

# Map tên prompt → prefix của file versioned
_PREFIX_MAP = {
    "ba_system":     "ba",
    "prd_system":    "prd",
    "design_system": "design",
    "ui_system":     "ui",
}


def load_prompt(name: str) -> str:
    """Load system prompt theo version được chỉ định trong môi trường.

    Args:
        name: Tên prompt, một trong:
              ``"ba_system"`` | ``"prd_system"`` |
              ``"design_system"`` | ``"ui_system"``

    Returns:
        Nội dung prompt (str). Không bao giờ raise exception — nếu không
        tìm thấy file nào trả về chuỗi cảnh báo.

    Ví dụ:
        >>> prompt = load_prompt("prd_system")
        # Nếu PRD_PROMPT_VERSION=v2, đọc prompts/versions/prd_v2.txt
        # Nếu file không tồn tại, fallback sang prompts/system/prd_system.txt
    """
    env_key = _ENV_KEY_MAP.get(name, f"{name.upper().replace('_', '_')}_VERSION")
    version = os.getenv(env_key, "").strip()

    # Thử đọc file versioned trước (ví dụ: versions/prd_v2.txt)
    if version:
        prefix = _PREFIX_MAP.get(name, name)
        versioned = PROMPT_DIR / "versions" / f"{prefix}_{version}.txt"
        if versioned.exists():
            return versioned.read_text(encoding="utf-8")

    # Fallback về file gốc trong system/ (ví dụ: system/prd_system.txt)
    fallback = PROMPT_DIR / "system" / f"{name}.txt"
    if fallback.exists():
        return fallback.read_text(encoding="utf-8")

    return (
        f"[WARN] Prompt file not found: {name} "
        f"(version={version!r}, looked in {PROMPT_DIR})"
    )
