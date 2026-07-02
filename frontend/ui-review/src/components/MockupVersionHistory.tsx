import { useEffect, useState } from "react";
import { Client } from "@langchain/langgraph-sdk";
import { getMockupVersions, type MockupVersion } from "../lib/mockupHistory";

interface Props {
  client: Client;
  threadId: string | undefined;
  currentHtml: string; // bản đang hiển thị ở tab Mockup
}

export function MockupVersionHistory({ client, threadId, currentHtml }: Props) {
  const [versions, setVersions] = useState<MockupVersion[]>([]);
  const [selected, setSelected] = useState<MockupVersion | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!threadId) return;
    setLoading(true);
    getMockupVersions(client, threadId)
      .then(setVersions)
      .catch((err) => console.error("[mockup history] load error", err))
      .finally(() => setLoading(false));
  }, [client, threadId, currentHtml]);

  if (!threadId) return null;

  return (
    <div style={{ marginTop: 20, borderTop: "1px solid #eee", paddingTop: 16 }}>
      <h4 style={{ fontSize: 15, fontWeight: 600, marginBottom: 10 }}>
        📜 Lịch sử phiên bản Mockup {loading && <span style={{ color: "#999", fontWeight: 400, fontSize: 13 }}>(đang tải...)</span>}
      </h4>

      {versions.length === 0 && !loading && (
        <p style={{ color: "#999", fontSize: 13 }}>Chưa có phiên bản nào.</p>
      )}

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        {versions.map((v, i) => (
          <button
            key={v.checkpointId}
            onClick={() => setSelected(selected?.checkpointId === v.checkpointId ? null : v)}
            style={{
              padding: "6px 14px",
              border: selected?.checkpointId === v.checkpointId ? "2px solid #1677ff" : "1px solid #ddd",
              borderRadius: 6,
              background: selected?.checkpointId === v.checkpointId ? "#e6f4ff" : "#fff",
              cursor: "pointer",
              fontSize: 13,
              fontWeight: selected?.checkpointId === v.checkpointId ? 600 : 400,
              color: "#333",
            }}
          >
            #{i + 1} — {new Date(v.timestamp).toLocaleString("vi-VN")}
            {v.gateDecision && ` (${v.gateDecision})`}
          </button>
        ))}
      </div>

      {selected && (
        <div style={{ border: "1px solid #ddd", borderRadius: 8, overflow: "hidden" }}>
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "8px 14px",
            background: "#fafafa",
            borderBottom: "1px solid #eee",
            fontSize: 13,
            fontWeight: 600,
          }}>
            <span>Xem lại phiên bản #{versions.indexOf(selected) + 1}</span>
            <button
              onClick={() => setSelected(null)}
              style={{
                border: "none",
                background: "transparent",
                cursor: "pointer",
                color: "#999",
                fontSize: 16,
              }}
            >
              ✕ Đóng
            </button>
          </div>
          <iframe
            sandbox="allow-scripts"
            srcDoc={selected.html}
            style={{ width: "100%", height: 500, border: "none", display: "block" }}
            title={`Mockup version ${versions.indexOf(selected) + 1}`}
          />
        </div>
      )}
    </div>
  );
}