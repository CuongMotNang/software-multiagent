"""Node UX — Sally, UX Designer: tạo UX Spec (user flows + danh sách màn
hình + edge case) từ PRD đã duyệt, TRƯỚC khi Architect vào việc.

3 nhánh: simple (mặc định, prompt tự viết ux_system.txt) / bmad-skill thật
(UX_USE_BMAD_SKILL=true, gọi skill bmad-ux qua OpenCode headless — có
headless.md + schema riêng, trả về DESIGN.md + EXPERIENCE.md, khác bmad-prd
chỉ trả 1 file). Chưa có nhánh agentic custom-prompt (khác ba/prd/design).
"""
import os
from pathlib import Path
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig

from graph.state import (
    SoftwareFactoryState,
    update_node_stats,
    push_content_history,
)
from graph.llm import llm_factory
from graph.repo_store import save_ux_spec, read_ux_spec, AGENT_WORKSPACE_ROOT
from graph.prompt_loader import load_prompt


def _get_feedback(state: SoftwareFactoryState) -> str:
    """Lấy phản hồi chỉnh sửa gần nhất cho UX Spec, gộp 2 nguồn:
    1. gate_history của gate_design — không có gate riêng cho ux_node, nên
       mượn lại gate_design để không mất phản hồi khi người reject/edit vì
       lý do liên quan UX.
    2. upstream_feedback['ux'] — critic_design phát hiện Design Document
       không khớp UX Spec (bad_spec) và tự quay lại 'ux', KHÔNG cần người
       bấm reject thủ công. Backward-loop thật, khác nguồn (1)."""
    parts = []

    if state.gate_history:
        design_gates = [h for h in state.gate_history if h.get("gate") == "gate_design"]
        if design_gates:
            last_gate = design_gates[-1]
            if last_gate.get("decision") in ["edit", "reject"]:
                note = last_gate.get("note", "")
                if note:
                    parts.append(f"[Từ người duyệt gate_design]\n{note}")

    critic_fb = state.upstream_feedback.get("ux", "")
    if critic_fb:
        parts.append(f"[Từ critic pass ở bước Design]\n{critic_fb}")

    return "\n\n".join(parts)


def _ux_node_simple(
    state: SoftwareFactoryState, thread_id: str, prd: str, feedback: str,
) -> Dict[str, Any]:
    """Cách cũ: 1 lệnh gọi LLM, prompt tự viết (ux_system.txt), không tool."""
    provider_name = os.getenv("UX_PROVIDER", None)
    llm = llm_factory(provider_name)

    system_prompt = load_prompt("ux_system")
    user_prompt = f"## PRD ĐÃ DUYỆT\n\n{prd}\n\n"
    if feedback:
        user_prompt += (
            f"## LỊCH SỬ NHẬN XÉT TỪ REVIEWER (gate_design)\n"
            f"\"{feedback}\"\n\n"
            f"Lưu ý nhận xét trên khi cập nhật lại UX Spec — có thể nhận xét "
            f"nhắm vào phần thiết kế kỹ thuật chứ không phải UX, chỉ sửa nếu "
            f"thực sự liên quan tới UX."
        )
    else:
        user_prompt += "Hãy thiết kế UX Spec chi tiết dựa trên PRD trên."

    llm_response = llm.call(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.4,
        max_tokens=12000,
    )
    result = llm_response.content

    if result is None:
        return {
            "ux_spec": "## LỖI: LLM không trả về UX Spec.",
            "status": "failed",
            "error": "LLM returned None",
        }

    save_ux_spec(thread_id, result)

    node_stats = update_node_stats(
        state.node_stats, "ux",
        reject_count=0,
        tokens_used=llm_response.total_tokens,
        model=llm_response.model,
    )
    content_history = push_content_history(state.content_history, "ux", result)

    return {
        "ux_spec": result,
        "status": "running",
        "node_stats": node_stats,
        "content_history": content_history,
    }


def _ux_node_bmad(
    state: SoftwareFactoryState, thread_id: str, prd: str, feedback: str,
) -> Dict[str, Any]:
    """Gọi skill `bmad-ux` THẬT qua OpenCode headless (có headless.md +
    assets/headless-schemas.md riêng, đã verify). Khác `bmad-prd`: schema
    trả về 2 field `design` (DESIGN.md) + `experience` (EXPERIENCE.md), không
    phải 1 field `prd` duy nhất — ghép lại thành 1 chuỗi cho state.ux_spec
    (schema state hiện tại chỉ có 1 field, chưa tách 2 file riêng).

    Bật qua UX_USE_BMAD_SKILL=true, độc lập UX_USE_AGENT.
    """
    from graph.agent_runtime import run_agent
    from graph.bmad_headless import (
        ensure_bmad_installed, build_real_headless_prompt, parse_generic_json_tail,
    )

    workspace_path = AGENT_WORKSPACE_ROOT / thread_id / "ux_work_bmad"
    workspace_path.mkdir(parents=True, exist_ok=True)

    ok, msg = ensure_bmad_installed(workspace_path, tools="opencode")
    if not ok:
        return {
            "ux_spec": f"## LỖI: không cài được _bmad/ ({msg}) — dùng UX_USE_AGENT=true để fallback nhánh agentic custom-prompt.",
            "status": "failed",
            "error": msg,
        }

    if feedback:
        intent_type = "update"
        payload_lines = (
            "- DESIGN.md + EXPERIENCE.md đã tồn tại trong workspace hiện tại "
            "(nếu chưa từng chạy create trước đó ở workspace này, coi đây là "
            "create thay vì update)\n"
            f"- change signal (điều cần sửa và lý do):\n{feedback}\n"
        )
    else:
        intent_type = "create"
        payload_lines = f"- source spec (PRD đã duyệt):\n{prd}\n"

    instructions = build_real_headless_prompt(
        skill_name="bmad-ux",
        intent_type=intent_type,
        payload_lines=payload_lines,
        extra_rule="Creative tools (color themes, mockup phác thảo...) để mặc định TẮT trong headless — chỉ cần DESIGN.md + EXPERIENCE.md.",
    )

    cfg = {
        "model": os.getenv("UX_LLM_MODEL", os.getenv("NVIDIA_MODEL", "openai/gpt-oss-120b")),
        "api_key": os.getenv("UX_LLM_API_KEY", os.getenv("NVIDIA_API_KEY", "")),
        "base_url": os.getenv("UX_LLM_BASE_URL", os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")),
    }

    result = run_agent(
        "opencode",
        {"instructions": instructions, "workspace_path": workspace_path, "output_file": None},
        cfg,
    )

    if result["status"] != "completed":
        return {
            "ux_spec": f"## LỖI: bmad-ux headless thất bại — {result['log']}",
            "status": "failed",
            "error": result["log"],
        }

    headless = parse_generic_json_tail(result.get("output", ""))

    def _read_field(field_name: str, fallback_filename: str) -> str:
        path_str = headless.get(field_name)
        if path_str:
            p = Path(path_str)
            if not p.is_absolute():
                p = workspace_path / path_str
            if p.exists():
                return p.read_text(encoding="utf-8")
        candidates = list(workspace_path.rglob(fallback_filename))
        return candidates[0].read_text(encoding="utf-8") if candidates else ""

    design_md = _read_field("design", "DESIGN.md")
    experience_md = _read_field("experience", "EXPERIENCE.md")

    if not design_md and not experience_md:
        return {
            "ux_spec": (
                f"## LỖI: bmad-ux headless không tạo được DESIGN.md/EXPERIENCE.md "
                f"đọc được (status={headless.get('status', 'unknown')}).\nRaw "
                f"output (500 ký tự cuối): {result.get('output', '')[-500:]}"
            ),
            "status": "failed",
            "error": "DESIGN.md/EXPERIENCE.md not found after bmad-ux headless run",
        }

    ux_spec = (
        f"# DESIGN.md\n\n{design_md}\n\n---\n\n# EXPERIENCE.md\n\n{experience_md}"
    )

    save_ux_spec(thread_id, ux_spec)

    pipeline_status = "running" if headless.get("status") == "complete" else "failed"

    node_stats = update_node_stats(
        state.node_stats, "ux",
        reject_count=0,
        tokens_used=result["prompt_tokens"] + result["completion_tokens"],
        model=result["model"],
    )
    content_history = push_content_history(state.content_history, "ux", ux_spec)

    updates: Dict[str, Any] = {
        "ux_spec": ux_spec,
        "status": pipeline_status,
        "node_stats": node_stats,
        "content_history": content_history,
    }

    open_questions = headless.get("open_questions") or []
    if open_questions:
        updates["pending_escalation_questions"] = "\n".join(f"- {q}" for q in open_questions)

    return updates


def ux_node(state: SoftwareFactoryState, config: RunnableConfig | None = None) -> Dict[str, Any]:
    """Node UX: prd_v1 (đã duyệt) -> ux_spec.

    Đứng giữa gate_prd (approve) và design trong graph — Winston (Architect)
    ở design_node sẽ đọc lại ux_spec.

    3 nhánh (ưu tiên theo thứ tự): bmad-skill thật (UX_USE_BMAD_SKILL=true)
    / agentic custom-prompt hiện CHƯA implement (UX_USE_AGENT chưa có tác
    dụng, giữ chỗ cho tương lai) / simple (mặc định, giữ nguyên hành vi cũ).
    """
    thread_id = "default"
    if config:
        configurable = config.get("configurable", {}) or {}
        thread_id = configurable.get("thread_id", "default")

    prd = state.prd_approved.strip() or state.prd_v1.strip()
    if not prd:
        return {
            "ux_spec": "## LỖI: Không có PRD đã duyệt để thiết kế UX.",
            "status": "failed",
            "error": "prd_v1/prd_approved rỗng khi vào ux_node",
        }

    feedback = _get_feedback(state)

    use_bmad_skill = os.getenv("UX_USE_BMAD_SKILL", "false").strip().lower() in ("1", "true", "yes")
    if use_bmad_skill:
        return _ux_node_bmad(state, thread_id, prd, feedback)

    return _ux_node_simple(state, thread_id, prd, feedback)


# Alias để GraphBuilder dùng
UX_NODE = ux_node
