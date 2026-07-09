"""Repo Store — Persist pipeline artifacts vào git repo theo project.

Thay thế artifact_store.py: thay vì tự đặt tên file v{N}/timestamp tay,
mỗi lần lưu là 1 git commit. Lịch sử version = ``git log``, không cần tự
duy trì version_index.json riêng (dễ lệch dữ liệu).

Quy ước hiện tại (theo quyết định đã chốt khi làm 0.2):
    project_id = thread_id đầu tiên của project (1-1 tạm thời, sẽ mở
    rộng thành nhiều thread/project ở Giai đoạn 0.4).

Cấu trúc:
    projects/{project_id}/           <- git repo root
        prd/prd.md
        design/design_doc.md
        mockup/screens/{filename}.html
        feedback/feedback_{gate}.md
        engineer/engineer_log.txt
        manifest.json
        test_report.json
        test_results.txt
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

PROJECTS_ROOT = Path(__file__).resolve().parent.parent / "projects"

# Dùng cho các file KHÔNG track git (screenshot PNG, build output...) —
# giữ nguyên đường dẫn cũ để không phá vỡ mockup_renderer.py / static_server.py
# (route /artifacts vẫn mount đúng sandbox/workspace như trước, không đổi).
SANDBOX_ROOT = Path(__file__).resolve().parent.parent / "sandbox"


def screenshot_dir(thread_id: str) -> Path:
    """Thư mục lưu PNG screenshot của mockup — luôn là bản MỚI NHẤT, không
    versioned (khác với HTML — HTML lưu trong git repo, xem lịch sử qua
    ``list_versions()``; PNG chỉ cần hiển thị bản hiện tại nên không cần).
    """
    d = SANDBOX_ROOT / "workspace" / thread_id / "mockup_screenshots"
    d.mkdir(parents=True, exist_ok=True)
    return d

# Không track vào git — binary/log lớn, không cần diff
_GITIGNORE_CONTENT = """\
*.png
*.jpg
*.jpeg
engineer/build/
"""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_git(project_dir: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        check=False,
    )


def _project_dir(project_id: str) -> Path:
    """Đảm bảo repo git đã tồn tại cho project_id, trả về path root."""
    d = PROJECTS_ROOT / project_id
    if not (d / ".git").exists():
        d.mkdir(parents=True, exist_ok=True)
        result = _run_git(d, "init", "-q")
        if result.returncode != 0:
            raise RuntimeError(f"git init thất bại cho {project_id}: {result.stderr}")
        _run_git(d, "config", "user.email", "pipeline@softwarefactory.local")
        _run_git(d, "config", "user.name", "SoftwareFactory Pipeline")
        (d / ".gitignore").write_text(_GITIGNORE_CONTENT, encoding="utf-8")
        _run_git(d, "add", ".gitignore")
        _run_git(d, "commit", "-q", "-m", "chore: khởi tạo project repo")
    return d


def _commit_file(
    project_id: str,
    relpath: str,
    content: str,
    *,
    message: str,
    gate: Optional[str] = None,
    decision: Optional[str] = None,
    checkpoint_id: Optional[str] = None,
) -> str:
    """Ghi file + commit. Trả về commit sha (rỗng nếu không có gì đổi)."""
    d = _project_dir(project_id)
    p = d / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

    _run_git(d, "add", relpath)

    trailers = []
    if gate:
        trailers.append(f"Gate: {gate}")
    if decision:
        trailers.append(f"Decision: {decision}")
    if checkpoint_id:
        trailers.append(f"Checkpoint-Id: {checkpoint_id}")
    full_message = message if not trailers else message + "\n\n" + "\n".join(trailers)

    result = _run_git(d, "commit", "-q", "-m", full_message)
    if result.returncode != 0:
        # "nothing to commit" — nội dung giống hệt bản trước, không phải lỗi
        if "nothing to commit" in (result.stdout + result.stderr):
            head = _run_git(d, "rev-parse", "HEAD")
            return head.stdout.strip()
        raise RuntimeError(f"git commit thất bại: {result.stderr}")

    sha = _run_git(d, "rev-parse", "HEAD")
    return sha.stdout.strip()


def _read_file(project_id: str, relpath: str) -> str:
    p = _project_dir(project_id) / relpath
    return p.read_text(encoding="utf-8") if p.exists() else ""


def list_versions(project_id: str, relpath: str) -> list[Dict[str, str]]:
    """Lịch sử commit của 1 file, mới nhất trước.

    Trả về [{"commit": sha, "date": iso, "subject": str, "body": str}, ...]
    """
    d = _project_dir(project_id)
    if not (d / relpath).exists() and not _run_git(
        d, "log", "--all", "--", relpath
    ).stdout.strip():
        return []
    sep = "\x1f"  # field separator hiếm gặp trong text thường
    result = _run_git(
        d, "log", f"--pretty=format:%H{sep}%aI{sep}%s{sep}%b\x1e", "--", relpath
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    versions = []
    for entry in result.stdout.split("\x1e"):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split(sep)
        if len(parts) < 3:
            continue
        sha, date, subject = parts[0], parts[1], parts[2]
        body = parts[3] if len(parts) > 3 else ""
        versions.append({"commit": sha, "date": date, "subject": subject, "body": body.strip()})
    return versions


def read_version(project_id: str, relpath: str, commit_sha: Optional[str] = None) -> str:
    """Đọc nội dung file — bản mới nhất nếu commit_sha=None, hoặc bản cũ cụ thể."""
    if commit_sha is None:
        return _read_file(project_id, relpath)
    d = _project_dir(project_id)
    result = _run_git(d, "show", f"{commit_sha}:{relpath}")
    return result.stdout if result.returncode == 0 else ""


# ─── API tương thích với artifact_store.py cũ (drop-in cho các node) ───

def save_prd(thread_id: str, prd_v1: str) -> str:
    return _commit_file(
        thread_id, "prd/prd.md", prd_v1, message="prd: cập nhật PRD", gate="gate_prd"
    )


def read_prd(thread_id: str) -> str:
    return _read_file(thread_id, "prd/prd.md")


def save_design(thread_id: str, design_doc: str) -> str:
    return _commit_file(
        thread_id,
        "design/design_doc.md",
        design_doc,
        message="design: cập nhật Design Document",
        gate="gate_design",
    )


def read_design(thread_id: str) -> str:
    return _read_file(thread_id, "design/design_doc.md")


def save_mockup_screens(thread_id: str, screens: list[dict]) -> list[Path]:
    """Lưu nhiều màn hình, mỗi lần gọi = 1 commit (có thể chứa nhiều file).

    Không còn thư mục v{N} riêng — mỗi màn hình ghi đè đúng 1 file cố định
    (``mockup/screens/{filename}``), lịch sử version xem qua ``list_versions()``
    (git log), không qua tên thư mục nữa.

    Từ Giai đoạn 3.3: ``filename`` thường là ``.json`` (UI JSON), không còn
    ``.html`` — hàm này không quan tâm định dạng, ``content`` là gì thì ghi
    y nguyên, caller (ui_node) tự quyết định phần mở rộng.

    Args:
        screens: list[{"filename": "01_login.json", "content": "..."}]
                 (chấp nhận cả key "html" cũ để không phá code gọi cũ)
    """
    d = _project_dir(thread_id)
    paths: list[Path] = []
    for screen in screens:
        filename = screen.get("filename", "screen.json")
        content = screen.get("content", screen.get("html", ""))
        relpath = f"mockup/screens/{filename}"
        p = d / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        _run_git(d, "add", relpath)
        paths.append(p)

    result = _run_git(
        d, "commit", "-q", "-m", f"mockup: cập nhật {len(screens)} màn hình\n\nGate: gate_mockup"
    )
    if result.returncode != 0 and "nothing to commit" not in (result.stdout + result.stderr):
        raise RuntimeError(f"git commit thất bại: {result.stderr}")
    return paths


def read_latest_mockup_screens(thread_id: str, pattern: str = "*.json") -> list[Path]:
    d = _project_dir(thread_id) / "mockup" / "screens"
    if not d.exists():
        return []
    return sorted(d.glob(pattern))


def save_test_report(thread_id: str, report: Dict[str, Any]) -> str:
    return _commit_file(
        thread_id,
        "test_report.json",
        json.dumps(report, indent=2, ensure_ascii=False),
        message="test: cập nhật test report",
    )


def read_test_report(thread_id: str) -> Optional[Dict[str, Any]]:
    content = _read_file(thread_id, "test_report.json")
    return json.loads(content) if content else None


def save_test_results(thread_id: str, results: str) -> str:
    return _commit_file(thread_id, "test_results.txt", results, message="test: cập nhật kết quả test")


def read_test_results(thread_id: str) -> str:
    return _read_file(thread_id, "test_results.txt")


def save_engineer_log(thread_id: str, log: str) -> str:
    return _commit_file(thread_id, "engineer/engineer_log.txt", log, message="engineer: cập nhật log")


def read_engineer_log(thread_id: str) -> str:
    return _read_file(thread_id, "engineer/engineer_log.txt")


def save_manifest(thread_id: str, manifest: Dict[str, Any]) -> str:
    return _commit_file(
        thread_id,
        "manifest.json",
        json.dumps(manifest, indent=2, ensure_ascii=False),
        message="chore: cập nhật manifest",
    )


def read_manifest(thread_id: str) -> Dict[str, Any]:
    content = _read_file(thread_id, "manifest.json")
    return json.loads(content) if content else {}


def list_artifacts(thread_id: str) -> list:
    d = _project_dir(thread_id)
    files = [
        str(f.relative_to(d))
        for f in d.rglob("*")
        if f.is_file() and ".git" not in f.parts
    ]
    return sorted(files)


def save_design_tokens(thread_id: str, tokens_json: str) -> str:
    """Lưu design_tokens.json — KHÔNG qua gate riêng (không có decision),
    nhưng vẫn track git để xem lịch sử thay đổi (Giai đoạn 3.1)."""
    return _commit_file(
        thread_id,
        "design/design_tokens.json",
        tokens_json,
        message="design: cập nhật design tokens",
    )


def read_design_tokens(thread_id: str) -> str:
    return _read_file(thread_id, "design/design_tokens.json")


def save_gate_feedback(thread_id: str, gate: str, feedback: str, decision: str) -> str:
    """Giữ format markdown-append như cũ (đổi sang JSON có cấu trúc ở Giai đoạn 2)."""
    relpath = f"feedback/feedback_{gate}.md"
    existing = _read_file(thread_id, relpath)
    ts = _now()
    entry = f"\n## [{ts}] Decision: {decision}\n{feedback.strip()}\n"
    return _commit_file(
        thread_id,
        relpath,
        existing + entry,
        message=f"feedback: {gate} — {decision}",
        gate=gate,
        decision=decision,
    )


def read_gate_feedback(thread_id: str, gate: str) -> str:
    return _read_file(thread_id, f"feedback/feedback_{gate}.md")


def _artifact_dir(thread_id: str) -> Path:
    """Tương thích ngược — trả về root của project repo (trước đây là sandbox dir)."""
    return _project_dir(thread_id)
