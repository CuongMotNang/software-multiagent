"""Artifact Store — Persist pipeline artifacts to disk.

Mỗi node trong pipeline ghi output ra file để các node sau có thể đọc.
Các artifacts được lưu trong sandbox/workspace/{thread_id}/artifacts/.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Root của sandbox folder (cùng cấp với graph/ folder)
SANDBOX_ROOT = Path(__file__).resolve().parent.parent / "sandbox"

# === Helpers ===

def _artifact_dir(thread_id: str) -> Path:
    """Trả về đường dẫn artifact của một thread."""
    d = SANDBOX_ROOT / "workspace" / thread_id / "artifacts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# === PRD ===

def save_prd(thread_id: str, prd_v1: str) -> Path:
    """Ghi PRD v1 ra file, trả về đường dẫn file."""
    p = _artifact_dir(thread_id) / "prd_v1.md"
    p.write_text(prd_v1, encoding="utf-8")
    return p

def read_prd(thread_id: str) -> str:
    """Đọc PRD v1 từ file."""
    p = _artifact_dir(thread_id) / "prd_v1.md"
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


# === Design Document ===

def save_design(thread_id: str, design_doc: str) -> Path:
    p = _artifact_dir(thread_id) / "design_doc.md"
    p.write_text(design_doc, encoding="utf-8")
    return p

def read_design(thread_id: str) -> str:
    p = _artifact_dir(thread_id) / "design_doc.md"
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


# === Mockup HTML ===

def save_mockup(thread_id: str, mockup_html: str) -> Path:
    p = _artifact_dir(thread_id) / "mockup.html"
    p.write_text(mockup_html, encoding="utf-8")
    return p

def read_mockup(thread_id: str) -> str:
    p = _artifact_dir(thread_id) / "mockup.html"
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


# === Mockup Screens (nhiều màn hình) ===

def save_mockup_screens(thread_id: str, screens: list[dict]) -> list[Path]:
    """Lưu nhiều file HTML mockup, mỗi màn hình 1 file.
    
    Args:
        thread_id: ID của thread
        screens: list[dict] với keys "filename" và "html"
        
    Returns:
        list[Path] danh sách đường dẫn các file đã lưu
    """
    artifact_dir = _artifact_dir(thread_id)
    paths: list[Path] = []
    for screen in screens:
        filename = screen.get("filename", "screen.html")
        html = screen.get("html", "")
        p = artifact_dir / filename
        p.write_text(html, encoding="utf-8")
        paths.append(p)
    return paths

def read_mockup_screens(thread_id: str) -> dict[str, str]:
    """Đọc tất cả các file HTML mockup trong thư mục artifact.
    
    Returns:
        dict[str, str] với key = tên file, value = nội dung HTML
    """
    artifact_dir = _artifact_dir(thread_id)
    screens: dict[str, str] = {}
    for f in sorted(artifact_dir.glob("*.html")):
        if f.name == "mockup.html":
            continue  # bỏ qua file alias
        screens[f.name] = f.read_text(encoding="utf-8")
    return screens


# === Test Report ===

def save_test_report(thread_id: str, report: Dict[str, Any]) -> Path:
    """Ghi test report ra file JSON."""
    p = _artifact_dir(thread_id) / "test_report.json"
    p.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return p

def read_test_report(thread_id: str) -> Optional[Dict[str, Any]]:
    p = _artifact_dir(thread_id) / "test_report.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


# === Test Results (raw log) ===

def save_test_results(thread_id: str, results: str) -> Path:
    p = _artifact_dir(thread_id) / "test_results.txt"
    p.write_text(results, encoding="utf-8")
    return p

def read_test_results(thread_id: str) -> str:
    p = _artifact_dir(thread_id) / "test_results.txt"
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


# === Engineer Log ===

def save_engineer_log(thread_id: str, log: str) -> Path:
    p = _artifact_dir(thread_id) / "engineer_log.txt"
    p.write_text(log, encoding="utf-8")
    return p

def read_engineer_log(thread_id: str) -> str:
    p = _artifact_dir(thread_id) / "engineer_log.txt"
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


# === Manifest (index của toàn bộ artifacts) ===

def save_manifest(thread_id: str, manifest: Dict[str, Any]) -> Path:
    p = _artifact_dir(thread_id) / "manifest.json"
    p.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return p

def read_manifest(thread_id: str) -> Dict[str, Any]:
    p = _artifact_dir(thread_id) / "manifest.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


# === List all artifacts ===

def list_artifacts(thread_id: str) -> list[str]:
    """Trả về danh sách tên file artifacts."""
    d = _artifact_dir(thread_id)
    if not d.exists():
        return []
    return sorted([f.name for f in d.iterdir() if f.is_file()])
