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

  const [loadError, setLoadError] = useState<string | null>(null);

  const loadThreads = async () => {
    setLoading(true);
    setLoadError(null);
    let result: ThreadInfo[] = [];
    try {
      const threadsClient = client.threads;
      const [interruptedResult, busyResult] = await Promise.all([
        threadsClient.search({ status: "interrupted", limit: 50 }),
        threadsClient.search({ status: "busy", limit: 50 }),
      ]);
      result = [...interruptedResult, ...busyResult];
    } catch (e) {
      console.error("[ThreadDashboard] load interrupted/busy error", e);
      setLoadError(`Không tải được danh sách thread: ${String(e)}`);
      setLoading(false);
      return;
    }

    // Tách riêng fetch "idle" (thread đã dừng) khỏi try/catch ở trên: nếu
    // request này lỗi, KHÔNG được để nó xoá mất kết quả interrupted/busy đã
    // fetch thành công — trước đây cả 2 nhóm request nằm chung 1 try/catch,
    // nên hễ request idle lỗi (timeout, backend tạm trục trặc...) là
    // setThreads() không bao giờ được gọi, danh sách trông như trống trơn dù
    // interrupted/busy đã có kết quả.
    if (showIdle) {
      try {
        const idleResult = await client.threads.search({ status: "idle", limit: 50 });
        result = [...result, ...idleResult];
      } catch (e) {
        console.error("[ThreadDashboard] load idle error", e);
        setLoadError(`Không tải được thread đã dừng: ${String(e)}`);
        // Vẫn tiếp tục hiển thị interrupted/busy đã có, không return sớm.
      }
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
    setLoading(false);
  };

  useEffect(() => {
    loadThreads();
    // Trước đây tắt hẳn auto-refresh khi showIdle=true — nghĩa là nếu lần
    // load đầu tiên gặp lỗi tạm thời (mạng, backend), danh sách sẽ đứng yên
    // mãi cho tới khi tự tick/untick lại checkbox. Giữ interval chạy trong
    // mọi trường hợp để tự phục hồi.
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

      {loadError && (
        <p style={{ color: "#ff4d4f", fontSize: 11, background: "#fff1f0", padding: "6px 8px", borderRadius: 4, marginBottom: 8 }}>
          ⚠️ {loadError}
        </p>
      )}
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
