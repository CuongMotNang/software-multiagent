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
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from loguru import logger
    logger.enable("softwarefactory")
except ImportError:  # pragma: no cover
    import logging
    logger = logging.getLogger("softwarefactory")

PROJECTS_ROOT = Path(__file__).resolve().parent.parent / "projects"

# Dùng cho các file KHÔNG track git (screenshot PNG, build output...) —
# giữ nguyên đường dẫn cũ để không phá vỡ mockup_renderer.py / static_server.py
# (route /artifacts vẫn mount đúng sandbox/workspace như trước, không đổi).
SANDBOX_ROOT = Path(__file__).resolve().parent.parent / "projects_data"

# ── AGENT_WORKSPACE_ROOT ──
# Đường dẫn gốc cho workspace của agent nodes (ba, prd, design, ...).
# Giống logic static_server.py: ưu tiên env PROJECTS_ROOT_OVERRIDE >
# projects (Docker mount) > projects_data (host fallback).
_env_override = os.environ.get("PROJECTS_ROOT_OVERRIDE", "")
if _env_override:
    AGENT_WORKSPACE_ROOT = Path(_env_override)
elif (Path(__file__).resolve().parent.parent / "projects").exists() and any(
    (Path(__file__).resolve().parent.parent / "projects").iterdir()
):
    # Docker container: volume được mount vào projects/
    AGENT_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent / "projects"
else:
    # Host fallback
    AGENT_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent / "projects_data"


def screenshot_dir(thread_id: str) -> Path:
    """Thư mục lưu PNG screenshot của mockup — dùng AGENT_WORKSPACE_ROOT
    thay vì hardcode projects_data.

    Path: AGENT_WORKSPACE_ROOT/<thread_id>/mockup_screenshots/
    """
    d = AGENT_WORKSPACE_ROOT / thread_id / "mockup_screenshots"
    d.mkdir(parents=True, exist_ok=True)
    return d

# Không track vào git — binary/log lớn, không cần diff
_GITIGNORE_CONTENT = """\
*.png
*.jpg
*.jpeg
engineer/build/
# Workspace tạm của các nhánh agentic/bmad-skill (ba_work/, prd_work_bmad/,
# ux_work_bmad/, design_work_bmad/, engineer_work_bmad/...) — chứa file
# agent tự sinh ra để pipeline đọc lại, không phải artifact chính thức của
# project (những cái đó đã được save_*() commit riêng vào đúng thư mục
# prd/, design/, ux/... rồi). Bỏ qua để tránh untracked-files clutter.
*_work/
*_work_bmad/
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


def _clear_stale_git_lock(project_dir: Path, max_age_s: float = 30.0) -> bool:
    """Xoá .git/index.lock NẾU nó đã cũ (max_age_s) — dấu hiệu process trước
    bị kill giữa chừng (rất hay gặp khi debug/dừng đột ngột trên Windows),
    không phải 1 git process khác đang thực sự chạy. KHÔNG xoá lock mới
    (an toàn hơn — tránh phá 1 commit đang thực sự diễn ra).

    Trả True nếu đã xoá (nên retry ngay), False nếu không có gì để xoá
    (lock không tồn tại, hoặc còn quá mới nên không đụng vào)."""
    lock_path = project_dir / ".git" / "index.lock"
    if not lock_path.exists():
        return False
    try:
        age_s = time.time() - lock_path.stat().st_mtime
    except OSError:
        return False
    if age_s < max_age_s:
        return False
    try:
        lock_path.unlink()
        logger.warning(f"Đã xoá .git/index.lock cũ ({age_s:.0f}s) tại {project_dir}")
        return True
    except OSError as e:
        logger.warning(f"Không xoá được .git/index.lock cũ: {e}")
        return False


def _run_git_with_retry(
    project_dir: Path, *args: str, max_retries: int = 3, backoff_s: float = 0.5
) -> subprocess.CompletedProcess:
    """Chạy git, tự retry khi gặp lỗi liên quan .git/index.lock (dù là do
    lock cũ sót lại, hay do 1 process khác thật sự đang giữ lock ngắn hạn).
    KHÔNG retry với lỗi khác (VD lỗi cú pháp lệnh) — chỉ retry khi output có
    dấu hiệu index.lock, để không che giấu lỗi git thật sự khác."""
    last_result: Optional[subprocess.CompletedProcess] = None
    for attempt in range(max_retries):
        result = _run_git(project_dir, *args)
        if result.returncode == 0:
            return result
        combined = (result.stdout or "") + (result.stderr or "")
        if "index.lock" not in combined and combined.strip():
            # Lỗi git thật sự khác (không phải lock) — không retry, trả ngay
            # để _commit_file() báo lỗi chính xác, không giấu lỗi thật.
            return result
        last_result = result
        _clear_stale_git_lock(project_dir)
        time.sleep(backoff_s * (attempt + 1))
    return last_result if last_result is not None else _run_git(project_dir, *args)


def _is_nothing_to_commit(output: str) -> bool:
    """Git có ít nhất 2 câu thông báo khác nhau cho cùng 1 tình huống 'không
    có gì để commit' — tuỳ repo có untracked file khác hay không:
      - "nothing to commit, working tree clean" (repo sạch hoàn toàn)
      - "nothing added to commit but untracked files present" (có untracked
        file khác, VD *_work_bmad/ do pilot Phase 3 tạo ra trong cùng repo)
    Trước đây chỉ check đúng cụm "nothing to commit" — KHÔNG khớp biến thể
    thứ 2, khiến bị raise RuntimeError oan dù nội dung file không đổi gì."""
    return "nothing to commit" in output or "nothing added to commit" in output


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

    _run_git_with_retry(d, "add", relpath)

    trailers = []
    if gate:
        trailers.append(f"Gate: {gate}")
    if decision:
        trailers.append(f"Decision: {decision}")
    if checkpoint_id:
        trailers.append(f"Checkpoint-Id: {checkpoint_id}")
    full_message = message if not trailers else message + "\n\n" + "\n".join(trailers)

    result = _run_git_with_retry(d, "commit", "-q", "-m", full_message)
    if result.returncode != 0:
        # Không có gì thay đổi so với version trước — không phải lỗi, xem
        # _is_nothing_to_commit() để biết vì sao check theo 2 cụm khác nhau
        if _is_nothing_to_commit(result.stdout + result.stderr):
            head = _run_git(d, "rev-parse", "HEAD")
            return head.stdout.strip()
        # Lấy cả stdout lẫn stderr — trên 1 số phiên bản git Windows, lỗi
        # index.lock có thể xuất hiện ở stdout thay vì stderr, hoặc stderr
        # bị nuốt bởi subprocess buffering. Không để thông báo lỗi rỗng.
        detail = (result.stderr or "").strip() or (result.stdout or "").strip() or "(không có output từ git)"
        raise RuntimeError(f"git commit thất bại (relpath={relpath}, returncode={result.returncode}): {detail}")

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


def save_ux_spec(thread_id: str, ux_spec: str) -> str:
    return _commit_file(
        thread_id, "ux/ux_spec.md", ux_spec, message="ux: cập nhật UX Spec"
    )


def read_ux_spec(thread_id: str) -> str:
    return _read_file(thread_id, "ux/ux_spec.md")


def save_tech_docs(thread_id: str, tech_docs: str) -> str:
    return _commit_file(
        thread_id, "docs/README.md", tech_docs, message="docs: cập nhật tài liệu handoff"
    )


def read_tech_docs(thread_id: str) -> str:
    return _read_file(thread_id, "docs/README.md")


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
    """Lưu nhiều màn hình, mỗi lần gọi = 1 commit (có thể chứa nhiều file)."""
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
    if result.returncode != 0 and not _is_nothing_to_commit(result.stdout + result.stderr):
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
    return _commit_file(
        thread_id,
        "design/design_tokens.json",
        tokens_json,
        message="design: cập nhật design tokens",
    )


def read_design_tokens(thread_id: str) -> str:
    return _read_file(thread_id, "design/design_tokens.json")


def save_debate_transcript(thread_id: str, node_name: str, transcript_md: str) -> str:
    """Ghi toàn bộ transcript debate ra 1 file, commit riêng.

    Context isolation: orchestrator (debate node) không giữ transcript đầy đủ
    trong state — chỉ giữ bản synthesis do lead viết. Muốn xem lại chi tiết
    ai nói gì thì đọc file này.
    """
    return _commit_file(
        thread_id,
        f"debate/{node_name}/transcript.md",
        transcript_md,
        message=f"debate({node_name}): transcript",
    )


def read_debate_transcript(thread_id: str, node_name: str) -> str:
    return _read_file(thread_id, f"debate/{node_name}/transcript.md")


def save_critic_report(
    thread_id: str, node_name: str, lens_id: str, report_md: str
) -> str:
    """Ghi full report của 1 critic lens ra file riêng + commit riêng.

    Đây là phần "context isolation" — parent (node điều phối) không giữ
    toàn văn report trong state/context, chỉ giữ summary ngắn. Muốn đọc lại
    chi tiết thì gọi read_critic_reports() hoặc mở thẳng file này.
    """
    return _commit_file(
        thread_id,
        f"critic/{node_name}/{lens_id}.md",
        report_md,
        message=f"critic({node_name}): {lens_id}",
    )


def read_critic_reports(thread_id: str, node_name: str) -> Dict[str, str]:
    """Đọc full report (không phải summary) của mọi lens đã chạy cho node_name."""
    d = _project_dir(thread_id) / "critic" / node_name
    if not d.exists():
        return {}
    return {
        p.stem: p.read_text(encoding="utf-8")
        for p in d.glob("*.md")
    }


def save_gate_feedback(thread_id: str, gate: str, feedback: str, decision: str) -> str:
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