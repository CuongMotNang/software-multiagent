"""Artifact Store - Persist pipeline artifacts to disk."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

SANDBOX_ROOT = Path(__file__).resolve().parent.parent / "sandbox"

def _artifact_dir(thread_id: str) -> Path:
    d = SANDBOX_ROOT / "workspace" / thread_id / "artifacts"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def save_prd(thread_id: str, prd_v1: str) -> Path:
    """Lưu SRS theo timestamp (không ghi đè bản cũ).

    Mỗi lần gọi sinh file ``srs_{timestamp}.md`` mới, đồng thời cập nhật
    alias ``prd_v1.md`` để ``read_prd()`` luôn đọc bản mới nhất.
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    d = _artifact_dir(thread_id)
    p = d / f"srs_{ts}.md"
    p.write_text(prd_v1, encoding="utf-8")
    # alias — read_prd() vẫn hoạt động bình thường
    (d / "prd_v1.md").write_text(prd_v1, encoding="utf-8")
    return p

def read_prd(thread_id: str) -> str:
    p = _artifact_dir(thread_id) / "prd_v1.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""

def save_design(thread_id: str, design_doc: str) -> Path:
    """Lưu Design Document theo timestamp (không ghi đè bản cũ).

    Mỗi lần gọi sinh file ``design_doc_{timestamp}.md`` mới, đồng thời cập
    nhật alias ``design_doc.md`` để ``read_design()`` luôn đọc bản mới nhất.
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    d = _artifact_dir(thread_id)
    p = d / f"design_doc_{ts}.md"
    p.write_text(design_doc, encoding="utf-8")
    # alias — read_design() vẫn hoạt động bình thường
    (d / "design_doc.md").write_text(design_doc, encoding="utf-8")
    return p

def read_design(thread_id: str) -> str:
    p = _artifact_dir(thread_id) / "design_doc.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""

def _next_mockup_version(d: Path, is_dir: bool = False) -> int:
    """Xác định số version tiếp theo (v1, v2...) dựa trên thư mục hiện tại."""
    if not d.exists():
        return 1
    import re
    max_v = 0
    for item in d.iterdir():
        if is_dir and item.is_dir():
            match = re.match(r"^v(\d+)$", item.name)
            if match:
                max_v = max(max_v, int(match.group(1)))
        elif not is_dir and item.is_file():
            match = re.match(r"^mockup_v(\d+)\.html$", item.name)
            if match:
                max_v = max(max_v, int(match.group(1)))
    return max_v + 1

def save_mockup(thread_id: str, mockup_html: str) -> Path:
    """Lưu mockup HTML với tên có version (v1, v2...), không ghi đè bản cũ."""
    d = _artifact_dir(thread_id) / "mockup_versions"
    d.mkdir(parents=True, exist_ok=True)
    v = _next_mockup_version(d, is_dir=False)
    p = d / f"mockup_v{v}.html"
    p.write_text(mockup_html, encoding="utf-8")
    return p

def read_mockup(thread_id: str) -> str:
    """Đọc bản mockup mới nhất (version vX lớn nhất)."""
    d = _artifact_dir(thread_id) / "mockup_versions"
    if not d.exists():
        return ""
    import re
    files = []
    for item in d.glob("mockup_*.html"):
        match = re.match(r"^mockup_v(\d+)\.html$", item.name)
        if match:
            files.append((int(match.group(1)), item))
        else:
            # Tương thích ngược với file timestamp cũ (coi là version 0)
            files.append((0, item))
    if not files:
        return ""
    files.sort(key=lambda x: (x[0], x[1].name))
    return files[-1][1].read_text(encoding="utf-8")

def save_mockup_screens(thread_id: str, screens: list[dict]) -> list[Path]:
    """Lưu nhiều file HTML màn hình vào thư mục mockup_versions/v{N}/.
    
    Args:
        screens: list[{"filename": "01_login.html", "html": "<!DOCTYPE html>..."}]
    
    Returns:
        list Path của các file HTML đã lưu
    """
    base = _artifact_dir(thread_id) / "mockup_versions"
    v = _next_mockup_version(base, is_dir=True)
    d = base / f"v{v}"
    d.mkdir(parents=True, exist_ok=True)
    
    saved: list[Path] = []
    for screen in screens:
        filename = screen.get("filename", "screen.html")
        html = screen.get("html", "")
        p = d / filename
        p.write_text(html, encoding="utf-8")
        saved.append(p)
    
    return saved


def read_latest_mockup_screens(thread_id: str) -> list[Path]:
    """Trả về list Path HTML của bản mockup mới nhất (version vX lớn nhất)."""
    base = _artifact_dir(thread_id) / "mockup_versions"
    if not base.exists():
        return []
    import re
    folders = []
    for item in base.iterdir():
        if item.is_dir():
            match = re.match(r"^v(\d+)$", item.name)
            if match:
                folders.append((int(match.group(1)), item))
            else:
                # Tương thích ngược với timestamp folders (coi là version 0)
                folders.append((0, item))
    if not folders:
        return []
    folders.sort(key=lambda x: (x[0], x[1].name))
    latest = folders[-1][1]
    return sorted(latest.glob("*.html"))


def save_test_report(thread_id: str, report: Dict[str, Any]) -> Path:
    p = _artifact_dir(thread_id) / "test_report.json"
    p.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return p

def read_test_report(thread_id: str) -> Optional[Dict[str, Any]]:
    p = _artifact_dir(thread_id) / "test_report.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

def save_test_results(thread_id: str, results: str) -> Path:
    p = _artifact_dir(thread_id) / "test_results.txt"
    p.write_text(results, encoding="utf-8")
    return p

def read_test_results(thread_id: str) -> str:
    p = _artifact_dir(thread_id) / "test_results.txt"
    return p.read_text(encoding="utf-8") if p.exists() else ""

def save_engineer_log(thread_id: str, log: str) -> Path:
    p = _artifact_dir(thread_id) / "engineer_log.txt"
    p.write_text(log, encoding="utf-8")
    return p

def read_engineer_log(thread_id: str) -> str:
    p = _artifact_dir(thread_id) / "engineer_log.txt"
    return p.read_text(encoding="utf-8") if p.exists() else ""

def save_manifest(thread_id: str, manifest: Dict[str, Any]) -> Path:
    p = _artifact_dir(thread_id) / "manifest.json"
    p.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return p

def read_manifest(thread_id: str) -> Dict[str, Any]:
    p = _artifact_dir(thread_id) / "manifest.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def list_artifacts(thread_id: str) -> list:
    d = _artifact_dir(thread_id)
    return sorted([f.name for f in d.iterdir() if f.is_file()]) if d.exists() else []


def save_gate_feedback(thread_id: str, gate: str, feedback: str, decision: str) -> Path:
    """Lưu feedback từ gate vào file markdown, append (không ghi đè).

    Mỗi gate có 1 file riêng, ví dụ ``feedback_gate_prd.md``.
    Mỗi lần reject/edit ghi thêm 1 entry mới vào cuối file — lịch sử
    được giữ nguyên để LLM đọc lại ở lần chạy tiếp theo.

    Args:
        thread_id: ID của pipeline run.
        gate: Tên gate, ví dụ ``"gate_prd"``.
        feedback: Nội dung nhận xét từ reviewer.
        decision: ``"reject"`` hoặc ``"edit"``.

    Returns:
        Path tới file feedback đã ghi.
    """
    d = _artifact_dir(thread_id)
    p = d / f"feedback_{gate}.md"
    ts = _now()
    entry = f"\n## [{ts}] Decision: {decision}\n{feedback.strip()}\n"
    with p.open("a", encoding="utf-8") as f:
        f.write(entry)
    return p


def read_gate_feedback(thread_id: str, gate: str) -> str:
    """Đọc toàn bộ lịch sử feedback của 1 gate.

    Args:
        thread_id: ID của pipeline run.
        gate: Tên gate, ví dụ ``"gate_prd"``.

    Returns:
        Nội dung file feedback (chuỗi Markdown) hoặc ``""`` nếu chưa có.
    """
    p = _artifact_dir(thread_id) / f"feedback_{gate}.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""