/**
 * Giai đoạn 3.5 — Puck editor cho gate_mockup.
 *
 * Load UI JSON mới nhất của 1 màn hình từ /repo/project/{projectId}/mockup/screens/{slug}.json
 * (static, đọc qua repo_store.py), cho sửa tay trên canvas Puck, lưu lại
 * qua POST /repo/project/{projectId}/mockup/screens/{slug} (commit git mới,
 * xem server/static_server.py).
 *
 * LƯU Ý project_id hiện = thread_id đầu tiên của project (quyết định tạm
 * ở Giai đoạn 0.2) — component này nhận thẳng `projectId` từ ngoài truyền
 * vào, không tự suy luận.
 */
import { useEffect, useState } from "react";
import { Puck } from "@measured/puck";
import "@measured/puck/puck.css";
import { puckConfig } from "../lib/puckConfig";
import { uiScreenToPuckData, puckDataToUIScreen } from "../lib/puckAdapter";
import type { UIScreen } from "../lib/puckAdapter";
import type { Data } from "@measured/puck";

interface Props {
  projectId: string;
  slug: string; // vd: "01_login" (không có đuôi .json)
  onSaved?: () => void;
}

export function MockupPuckEditor({ projectId, slug, onSaved }: Props) {
  const [screenMeta, setScreenMeta] = useState<{ screen: string; label: string } | null>(null);
  const [data, setData] = useState<Data | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveWarning, setSaveWarning] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setLoadError(null);
    fetch(`/repo/${projectId}/mockup/screens/${slug}.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((screen: UIScreen) => {
        if (cancelled) return;
        setScreenMeta({ screen: screen.screen, label: screen.label });
        setData(uiScreenToPuckData(screen));
      })
      .catch((e) => !cancelled && setLoadError(String(e)));
    return () => {
      cancelled = true;
    };
  }, [projectId, slug]);

  const handlePublish = async (newData: Data) => {
    if (!screenMeta) return;
    setSaving(true);
    setSaveWarning(null);
    try {
      const screen = puckDataToUIScreen(newData, screenMeta);
      const res = await fetch(`/repo/${projectId}/mockup/screens/${slug}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(screen),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ? String(body.detail) : `Lưu thất bại: HTTP ${res.status}`);
      }
      const result = await res.json();
      if (result?.preview_regenerated === false) {
        // JSON đã lưu thành công (git commit OK) nhưng ảnh preview PNG
        // chưa render lại được — vẫn coi là lưu thành công, chỉ cảnh báo.
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
  if (!data) return <p style={{ color: "#999" }}>Đang tải UI JSON…</p>;

  return (
    <div style={{ height: 600, border: "1px solid #e8e8e8", borderRadius: 6, position: "relative" }}>
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
      <Puck config={puckConfig} data={data} onPublish={handlePublish} />
    </div>
  );
}