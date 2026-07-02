import { useEffect, useState } from "react";
import { Client } from "@langchain/langgraph-sdk";

interface ThreadInfo {
  thread_id: string;
  status: string;
  created_at?: string;
  metadata?: Record<string, any> | null;
}

interface Props {
  client: Client;
  activeThreadId: string | undefined;
  onSelect: (threadId: string) => void;
  onCreateNew: () => void;
}

export function ThreadDashboard({ client, activeThreadId, onSelect, onCreateNew }: Props) {
  const [threads, setThreads] = useState<ThreadInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [showIdle, setShowIdle] = useState(false);

  const loadThreads = async () => {
    setLoading(true);
    try {
      const threadsClient = client.threads;
      const [interruptedResult, busyResult] = await Promise.all([
        threadsClient.search({ status: "interrupted", limit: 50 }),
        threadsClient.search({ status: "busy", limit: 50 }),
      ]);

      let result: ThreadInfo[] = [...interruptedResult, ...busyResult];

      if (showIdle) {
        const idleResult = await threadsClient.search({ status: "idle", limit: 50 });
        result = [...result, ...idleResult];
      }

      const seen = new Set<string>();
      const filtered: ThreadInfo[] = [];
      for (const t of result) {
        if (!seen.has(t.thread_id)) {
          seen.add(t.thread_id);
          filtered.push(t);
        }
      }

      filtered.sort((a, b) => new Date(b.created_at ?? 0).getTime() - new Date(a.created_at ?? 0).getTime());
      setThreads(filtered);
    } catch (e) {
      console.error("[ThreadDashboard] load error", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadThreads();
    if (showIdle) return;
    const iv = setInterval(loadThreads, 10_000);
    return () => clearInterval(iv);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showIdle]);

  const statusIcon = (t: ThreadInfo) => {
    if (t.status === "interrupted") return "⏸️";
    if (t.status === "busy") return "⏳";
    if (t.status === "error") return "❌";
    return "✅";
  };

  const statusLabel = (t: ThreadInfo) => {
    if (t.status === "interrupted") return "Chờ duyệt";
    if (t.status === "busy") return "Đang chạy";
    if (t.status === "error") return "Lỗi";
    return "Idle";
  };

  return (
    <div style={{ width: 280, borderRight: "1px solid #e8e8e8", padding: "16px 12px", overflowY: "auto", background: "#fafafa", flexShrink: 0 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, margin: 0 }}>🗂️ Threads</h3>
        <button onClick={() => { onCreateNew(); loadThreads(); }}
          style={{ fontSize: 12, padding: "4px 10px", background: "#1677ff", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>
          + Mới
        </button>
      </div>

      <div style={{ marginBottom: 10 }}>
        <label style={{ fontSize: 12, color: "#555", cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}>
          <input
            type="checkbox"
            checked={showIdle}
            onChange={(e) => setShowIdle(e.target.checked)}
            style={{ cursor: "pointer" }}
          />
          Hiện thread đã dừng
        </label>
      </div>

      {loading && threads.length === 0 && <p style={{ color: "#999", fontSize: 12 }}>Đang tải...</p>}
      {threads.map((t) => (
        <div key={t.thread_id}
          onClick={() => onSelect(t.thread_id)}
          style={{
            padding: "10px 12px", borderRadius: 6, marginBottom: 6, cursor: "pointer",
            background: activeThreadId === t.thread_id ? "#e6f4ff" : "#fff",
            border: `1px solid ${activeThreadId === t.thread_id ? "#1677ff" : "#e8e8e8"}`,
          }}>
          <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 2 }}>
            {statusIcon(t)} {t.metadata?.project_name ?? t.thread_id.slice(0, 8) + "..."}
          </div>
          <div style={{ fontSize: 11, color: "#666" }}>{statusLabel(t)}</div>
          <div style={{ fontSize: 10, color: "#999", marginTop: 2 }}>
            {new Date(t.created_at ?? Date.now()).toLocaleString("vi-VN")}
          </div>
        </div>
      ))}
    </div>
  );
}
