/**
 * Bước 2 — GrapesJS editor thay thế MockupPuckEditor.
 *
 * Load HTML preview hiện có của 1 screen từ
 *   GET /artifacts/{project_id}/mockup_screenshots/{slug}.preview.html
 * (sandbox/workspace, đã có cho cả project cũ lẫn mới — xem screenshot_dir()
 * trong repo_store.py). File preview là HTML đầy đủ (<!DOCTYPE>+<head>+<style>
 * inline+body) nên GrapesJS parse được luôn, không cần fetch .css riêng.
 *
 * Cho sửa trên canvas GrapesJS (preset-webpage: panel block, Style Manager,
 * Layer Manager, toolbar), rồi nút Save gọi:
 *   POST /repo/{project_id}/mockup/screens/{slug}/html
 * với body { html: string, css: string } — route trong static_server.py
 * lưu .html + .css vào git (projects_data) + regenerate .preview.html + PNG
 * ngay (route POST ghi preview vào sandbox qua screenshot_dir()).
 *
 * Rủi ro đã xử lý:
 * - editor.destroy() gọi khi unmount (canvas iframe leak listener nếu quên).
 * - storageManager: false (không để GrapesJS tự lưu localStorage).
 */
import { useEffect, useRef, useState } from "react";
import GjsEditor from "@grapesjs/react";
import grapesjs from "grapesjs";
import "grapesjs/dist/css/grapes.min.css";
import presetWebpage from "grapesjs-preset-webpage";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type EditorAny = any;

interface Props {
  projectId: string;
  slug: string; // vd: "01_login" (không có đuôi .html)
  onSaved?: () => void;
}

export function MockupGrapesEditor({ projectId, slug, onSaved }: Props) {
  const [editorRef, setEditorRef] = useState<EditorAny>(null);
  const [htmlContent, setHtmlContent] = useState<string | null>(null);
  const [cssContent, setCssContent] = useState<string>("");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveWarning, setSaveWarning] = useState<string | null>(null);
  const editorRefStable = useRef<EditorAny>(null);

  // Load HTML preview hiện có của screen.
  // Pipeline (cũ + mới) đều ghi {slug}.preview.html vào sandbox/workspace
  // (xem graph/repo_store.py screenshot_dir() → SANDBOX_ROOT/workspace/{id}/mockup_screenshots/).
  // static_server.py mount sandbox/workspace dưới /artifacts, nên load qua:
  //   GET /artifacts/{projectId}/mockup_screenshots/{slug}.preview.html
  // File preview này là HTML đầy đủ (<!DOCTYPE>+<head>+<style> inline+body) —
  // GrapesJS parse được luôn, không cần fetch .css riêng.
  useEffect(() => {
    let cancelled = false;
    setHtmlContent(null);
    setLoadError(null);
    setCssContent("");

    fetch(`/artifacts/${projectId}/mockup_screenshots/${slug}.preview.html`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.text();
      })
      .then((html) => {
        if (cancelled) return;
        setHtmlContent(html);
      })
      .catch((e) => {
        if (cancelled) return;
        // Nếu preview chưa có (màn chưa từng render), dùng template rỗng
        if (String(e).includes("404")) {
          setHtmlContent("<div><!-- Chưa có HTML cho màn hình này — bắt đầu soạn thảo --></div>");
        } else {
          setLoadError(String(e));
        }
      });

    return () => {
      cancelled = true;
    };
  }, [projectId, slug]);

  // Cleanup editor khi unmount / đổi slug
  useEffect(() => {
    return () => {
      if (editorRefStable.current) {
        try {
          editorRefStable.current.destroy();
        } catch {
          /* ignore */
        }
        editorRefStable.current = null;
      }
    };
  }, [projectId, slug]);

  const handleSave = async () => {
    if (!editorRef) return;
    setSaving(true);
    setSaveWarning(null);
    try {
      const html = editorRef.getHtml();
      const css = editorRef.getCss();

      const res = await fetch(`/repo/${projectId}/mockup/screens/${slug}/html`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ html, css }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ? String(body.detail) : `Lưu thất bại: HTTP ${res.status}`);
      }
      const result = await res.json();
      if (result?.preview_regenerated === false) {
        setSaveWarning(
          `Đã lưu, nhưng chưa render lại được ảnh preview: ${result.preview_warning ?? "không rõ lý do"}`
        );
      }
      onSaved?.();
    } catch (e) {
      setLoadError(String(e));
    } finally {
      setSaving(false);
    }
  };

  if (loadError) return <p style={{ color: "#ff4d4f" }}>Lỗi tải màn hình: {loadError}</p>;
  if (htmlContent === null) return <p style={{ color: "#999" }}>Đang tải HTML…</p>;

  // Gộp HTML + CSS thành 1 chuỗi components truyền vào GrapesJS.
  // Nếu HTML đã chứa <style>, GrapesJS sẽ parse CSS từ đó. Nếu CSS riêng,
  // truyền qua options.style để editor apply.
  const initialStyle = cssContent || "";

  return (
    <div style={{ height: 600, border: "1px solid #e8e8e8", borderRadius: 6, position: "relative", overflow: "hidden" }}>
      {saveWarning && (
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, background: "#fffbe6", border: "1px solid #faad14", padding: "6px 10px", fontSize: 12, zIndex: 20 }}>
          ⚠️ {saveWarning}
        </div>
      )}
      {saving && (
        <div style={{ position: "absolute", inset: 0, background: "rgba(255,255,255,0.6)", zIndex: 10, display: "flex", alignItems: "center", justifyContent: "center" }}>
          Đang lưu…
        </div>
      )}

      {/* Top bar: nút Save */}
      <div style={{ display: "flex", justifyContent: "flex-end", padding: "4px 8px", borderBottom: "1px solid #f0f0f0", background: "#fafafa" }}>
        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            padding: "5px 16px",
            borderRadius: 4,
            border: "1px solid #1677ff",
            background: saving ? "#d9d9d9" : "#1677ff",
            color: "#fff",
            cursor: saving ? "not-allowed" : "pointer",
            fontWeight: 600,
            fontSize: 12,
          }}
        >
          💾 Lưu HTML/CSS
        </button>
      </div>

      {/* Editor area — Default UI mode (không có <Canvas/> con) */}
      <div style={{ height: "calc(100% - 36px)", display: "flex", borderTop: "1px solid #e8e8e8" }}>
        <GjsEditor
          grapesjs={grapesjs}
          options={{
            height: "100%",
            storageManager: false,
            plugins: [presetWebpage],
            components: htmlContent,
            style: initialStyle,
            dragMode: "absolute",
          }}
          onEditor={(editor: EditorAny) => {
            editorRefStable.current = editor;
            setEditorRef(editor);
            console.log("[grapes] Editor ready for slug:", slug);
          }}
        />
      </div>
    </div>
  );
}