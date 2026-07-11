import { useState } from "react";
import GjsEditor from "@grapesjs/react";
import grapesjs from "grapesjs";
import "grapesjs/dist/css/grapes.min.css";
// Trong Vite (ESM), import preset-webpage theo default export (function plugin)
// rồi truyền trực tiếp vào options.plugins — an toàn hơn tên string vì
// grapesjs-preset-webpage là CommonJS, side-effect import chưa chắc đã đăng ký name.
import presetWebpage from "grapesjs-preset-webpage";

/**
 * SPIKE — Bước 0 (KHÔNG động vào MockupPuckEditor.tsx hay App.tsx của Puck).
 *
 * Mục đích: xác nhận GrapesJS + preset-webpage hoạt động đúng trong chính
 * stack Vite/React của project, trước khi xoá bất cứ thứ gì của Puck.
 *
 * Cách mở: chạy `npm run dev` rồi vào http://localhost:5173/?spike=1
 * (xem main.tsx — query param này mount SpikeApp thay vì App của Puck,
 *  App.tsx mặc định không bị ảnh hưởng).
 *
 * Checklist xác nhận (kéo xuống phần UI "Spike Checklist" trong trang):
 *  1) Giao diện hiện đúng như grapesjs.com/demo.html
 *     (panel block trái, Style Manager, Layer Manager, toolbar trên component)
 *  2) Kéo-thả block vào canvas hoạt động
 *  3) Chỉnh style qua Style Manager (đổi màu, spacing) phản ánh đúng trên canvas
 *  4) Lấy được HTML/CSS ra ngoài (nút "Xuất HTML/CSS" -> in console + textareas)
 *  5) Load được 1 chuỗi HTML/CSS có sẵn vào editor
 *     (nút "Load mẫu LLM" -> components + style truyền tay)
 */

// Editor instance — dùng any cho gọn spike (chỉ cần getHtml/getCss/setComponents/setStyle).
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type EditorAny = any;

// QUAN TRỌNG: KHÔNG dùng <Canvas /> con bên trong <GjsEditor> ở spike này.
// Theo README @grapesjs/react, khi có <Canvas/> con thì GrapesJS DISABLE default UI
// (panel block, style manager, layer manager...) — mà checklist bước 0 lại yêu cầu
// confirm default UI hiện đúng như grapesjs.com/demo.html. Nên dùng "Default UI"
// mode (không child <Canvas/>) để GrapesJS render toàn bộ panel mặc định.

// Mẫu HTML/CSS giống cái LLM sẽ sinh ra (một section hero đơn giản).
const SAMPLE_HTML = `
<section class="hero" data-gjs-type="section">
  <div class="hero__inner">
    <h1 class="hero__title">Build software, faster.</h1>
    <p class="hero__subtitle">Agentic pipeline tạo PRD, design, mockup và code.</p>
    <a class="hero__cta" href="#">Bắt đầu</a>
  </div>
</section>
`.trim();

const SAMPLE_CSS = `
.hero {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  padding: 80px 24px;
  text-align: center;
  font-family: system-ui, sans-serif;
}
.hero__inner { max-width: 720px; margin: 0 auto; }
.hero__title { font-size: 40px; font-weight: 700; margin: 0 0 12px; }
.hero__subtitle { font-size: 18px; opacity: 0.9; margin: 0 0 24px; }
.hero__cta {
  display: inline-block;
  background: #fff;
  color: #4338ca;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
}
`.trim();

const CHECKLIST = [
  "Giao diện hiện đúng như grapesjs.com/demo.html (panel block trái, Style Manager, Layer Manager, toolbar trên component)",
  "Kéo-thả block vào canvas hoạt động",
  "Chỉnh style qua Style Manager (đổi màu, spacing) phản ánh đúng trên canvas",
  "Lấy được HTML/CSS ra ngoài: editor.getHtml() / editor.getCss()",
  "Load được 1 chuỗi HTML/CSS có sẵn vào editor (nút 'Load mẫu LLM')",
];

export function GrapesSpike() {
  const [editorRef, setEditorRef] = useState<EditorAny>(null);
  const [exportedHtml, setExportedHtml] = useState("");
  const [exportedCss, setExportedCss] = useState("");
  const [checked, setChecked] = useState<boolean[]>(CHECKLIST.map(() => false));
  const [loadCount, setLoadCount] = useState(0);

  const handleExport = () => {
    if (!editorRef) return;
    const html = editorRef.getHtml();
    const css = editorRef.getCss();
    setExportedHtml(html);
    setExportedCss(css);
    // In ra console để dễ kiểm tra bằng DevTools.
    console.log("[spike] getHtml():\n", html);
    console.log("[spike] getCss():\n", css);
  };

  const handleLoadSample = () => {
    if (!editorRef) return;
    // Load HTML/CSS có sẵn vào editor — test case "LLM sinh ra rồi load lại".
    // setComponents + setStyle (alias của setCss) sẽ thay toàn bộ canvas.
    editorRef.setComponents(SAMPLE_HTML);
    editorRef.setStyle(SAMPLE_CSS);
    setLoadCount((c) => c + 1);
    console.log("[spike] Loaded sample HTML/CSS into editor");
  };

  const handleReset = () => {
    if (!editorRef) return;
    editorRef.setComponents("<h1>Test</h1><p>Xin chào từ GrapesJS</p>");
    editorRef.setStyle("");
    setExportedHtml("");
    setExportedCss("");
    console.log("[spike] Editor reset");
  };

  const allChecked = checked.every(Boolean);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden" }}>
      {/* Top bar: tiêu đề + dev controls */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "8px 16px",
          borderBottom: "1px solid #e8e8e8",
          background: "#fafafa",
          flexShrink: 0,
        }}
      >
        <strong style={{ fontSize: 14 }}>🍇 GrapesJS Spike (Bước 0)</strong>
        <span style={{ fontSize: 12, color: "#999" }}>
          Khong dong vao Puck — mo {`http://localhost:5173/?spike=1`}
        </span>
        <div style={{ flex: 1 }} />
        <button onClick={handleLoadSample} style={btnStyle}>
          Load mẫu LLM (HTML/CSS)
        </button>
        <button onClick={handleReset} style={btnStyle}>
          Reset editor
        </button>
        <button
          onClick={handleExport}
          style={{ ...btnStyle, background: "#1677ff", color: "#fff", borderColor: "#1677ff" }}
        >
          Xuất HTML/CSS
        </button>
        <span
          style={{
            fontSize: 12,
            fontWeight: 600,
            padding: "2px 8px",
            borderRadius: 4,
            background: allChecked ? "#f6ffed" : "#fff7e6",
            color: allChecked ? "#389e0d" : "#d48806",
            border: `1px solid ${allChecked ? "#b7eb8f" : "#ffd591"}`,
          }}
        >
          {allChecked ? "✅ Spike OK" : `${checked.filter(Boolean).length}/${CHECKLIST.length} đạt`}
        </span>
      </div>

      {/* Editor area — Default UI mode (không có <Canvas/> con) */}
      <div style={{ flex: 1, minHeight: 0, display: "flex", borderTop: "1px solid #e8e8e8" }}>
        <GjsEditor
          grapesjs={grapesjs}
          options={{
            height: "100%",
            storageManager: false,
            plugins: [presetWebpage],
            components: "<h1>Test</h1><p>Xin chào từ GrapesJS</p>",
          }}
          onEditor={(editor: EditorAny) => {
            setEditorRef(editor);
            console.log("[spike] Editor ready:", editor);
          }}
        />
      </div>

      {/* Bottom: exported HTML/CSS + checklist */}
      <div
        style={{
          height: 240,
          flexShrink: 0,
          borderTop: "1px solid #e8e8e8",
          background: "#fff",
          padding: 12,
          overflow: "auto",
          boxSizing: "border-box",
        }}
      >
        <details open style={{ marginBottom: 8 }}>
          <summary style={{ fontWeight: 600, fontSize: 13, cursor: "pointer" }}>
            Spike Checklist (đánh dấu sau khi test thủ công)
          </summary>
          <ol style={{ margin: "8px 0 0", paddingLeft: 20, fontSize: 13, lineHeight: 1.8 }}>
            {CHECKLIST.map((item, i) => (
              <li
                key={i}
                style={{
                  cursor: "pointer",
                  userSelect: "none",
                  color: checked[i] ? "#389e0d" : "#333",
                }}
                onClick={() => setChecked((arr) => arr.map((v, j) => (j === i ? !v : v)))}
              >
                {checked[i] ? "✅" : "⬜"} {item}
              </li>
            ))}
          </ol>
        </details>

        <div style={{ display: "flex", gap: 12 }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>
              Exported HTML (editor.getHtml()){" "}
              {loadCount > 0 && <span style={{ color: "#999" }}>— load #{loadCount}</span>}
            </div>
            <textarea
              value={exportedHtml}
              readOnly
              placeholder="Bam 'Xuat HTML/CSS' de lay ket qua..."
              style={{
                width: "100%",
                height: 130,
                fontSize: 11,
                fontFamily: "monospace",
                padding: 6,
                boxSizing: "border-box",
              }}
            />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>
              Exported CSS (editor.getCss())
            </div>
            <textarea
              value={exportedCss}
              readOnly
              placeholder="Bam 'Xuat HTML/CSS' de lay ket qua..."
              style={{
                width: "100%",
                height: 130,
                fontSize: 11,
                fontFamily: "monospace",
                padding: 6,
                boxSizing: "border-box",
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

const btnStyle: React.CSSProperties = {
  padding: "5px 12px",
  borderRadius: 4,
  border: "1px solid #d9d9d9",
  background: "#fff",
  cursor: "pointer",
  fontSize: 12,
};