import { Component, useEffect, useRef, useState } from "react";
import { Client } from "@langchain/langgraph-sdk";
import { useStream } from "@langchain/langgraph-sdk/react";
import "./App.css";
import { ThreadDashboard } from "./components/ThreadDashboard";
import { PipelineGraph } from "./components/PipelineGraph";
import { MockupVersionHistory } from "./components/MockupVersionHistory";
import { RepoBrowser } from "./components/RepoBrowser";
import { MockupPuckEditor } from "./components/MockupPuckEditor";
const LANGGRAPH_API_URL = import.meta.env.VITE_LANGGRAPH_API_URL ?? "http://localhost:8123";
const client = new Client({ apiUrl: LANGGRAPH_API_URL });
const GRAPH_ID = "SoftwareFactory";
type ActiveTab = "prd" | "design" | "mockup" | "files";

class ErrorBoundary extends Component<
  { children: React.ReactNode },
  { error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 40, fontFamily: "monospace", color: "red" }}>
          <h2>❌ React Error Boundary</h2>
          <pre style={{ whiteSpace: "pre-wrap", fontSize: 13 }}>
            {this.state.error?.stack || this.state.error?.message}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}

function ReviewApp() {
  const [mockupEditMode, setMockupEditMode] = useState(false);
  const [editingSlug, setEditingSlug] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>("prd");
  const [feedback, setFeedback] = useState("");
  const [rawRequirements, setRawRequirements] = useState("Todo app");
  const [threadId, setThreadId] = useState<string | undefined>(undefined);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [currentNode, setCurrentNode] = useState<string>("");
  const submittingRef = useRef(false);
  const [nextNodes, setNextNodes] = useState<string[]>([]);
  const [interrupted, setInterrupted] = useState(false);

  // NEW: nguồn dữ liệu thật cho state, được nạp từ client.threads.getState()
  // (thread?.values từ useStream không đáng tin vì các lần chạy pipeline
  // đều dùng client.runs.stream() gọi tay, không đi qua cơ chế nội bộ của hook)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [snapshotState, setSnapshotState] = useState<Record<string, any>>({});

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const stream: any = useStream({
    client,
    apiUrl: LANGGRAPH_API_URL,
    threadId,
    assistantId: GRAPH_ID,
    onThreadId: setThreadId,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onCustomEvent: (event: any) => console.log("[customEvent]", event),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onError: (err: any) => {
      console.error("[useStream error]", err);
      setSubmitError(typeof err === "string" ? err : JSON.stringify(err));
    },
  });

  const { error } = stream;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const state: Record<string, any> = snapshotState;

  // DEBUG: log mockup data để kiểm tra format thật
  console.log("[debug] mockup_screenshots:", state.mockup_screenshots);
  console.log("[debug] mockup_html length:", state.mockup_html?.length);
  console.log("[debug] mockup_screens:", state.mockup_screens);
  console.log("[debug] mockup_screens keys:", state.mockup_screens ? Object.keys(state.mockup_screens) : []);

  // Detect interrupt from thread state
  useEffect(() => {
    const checkInterrupt = async () => {
      if (!threadId) return;
      try {
        const s = await client.threads.getState(threadId);
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        setSnapshotState((s.values as Record<string, any>) ?? {});
        const next = s.next || [];
        setNextNodes(next);
        const isAtGate = next.some((n: string) => n.startsWith("gate_"));
        setInterrupted(isAtGate);
        if (isAtGate) {
          console.log("[interrupt] Pipeline paused at:", next);
          setIsRunning(false);
        }
      } catch {
        /* ignore */
      }
    };
    if (!isRunning && threadId) {
      checkInterrupt();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [threadId, isRunning]);

  const currentGate: string =
  state.current_gate ||
  nextNodes.find((n) => n.startsWith("gate_")) ||
  "";
  const pendingRole: string =
  state.pending_gate_role ||
  (currentGate === "gate_prd" || currentGate === "gate_mockup"
    ? "ba"
    : currentGate === "gate_design"
    ? "dev"
    : "");
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const gateHistory: Array<Record<string, any>> = state.gate_history ?? [];
  const hasStarted = !!threadId;

  // Auto-switch tab when gate is detected
  useEffect(() => {
    if (currentGate === "gate_prd") setActiveTab("prd");
    else if (currentGate === "gate_design") setActiveTab("design");
    else if (currentGate === "gate_mockup") setActiveTab("mockup");
  }, [currentGate]);

  const fetchLatestState = async (tid: string) => {
    try {
      const s = await client.threads.getState(tid);
      const next = s.next || [];
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setSnapshotState((s.values as Record<string, any>) ?? {});
      setNextNodes(next);
      const isAtGate = next.some((n: string) => n.startsWith("gate_"));
      setInterrupted(isAtGate);
      console.log("[state]", {
        next: s.next,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        current_gate: (s.values as any)?.current_gate,
      });
      return s;
    } catch (e) {
      console.error("[state] error", e);
      return null;
    }
  };

  const handleStart = async () => {
    if (submittingRef.current) return;
    submittingRef.current = true;
    setSubmitError(null);
    setIsRunning(true);
    setInterrupted(false);
    setNextNodes([]);
    setCurrentNode("creating_thread");
    try {
      const newThread = await client.threads.create({
        metadata: { project_name: rawRequirements.slice(0, 30) },
      });
      const tid = newThread.thread_id;
      console.log("[pipeline] thread created:", tid);
      setThreadId(tid);
      await new Promise((r) => setTimeout(r, 500));
      setCurrentNode("running");

      const runStream = client.runs.stream(tid, GRAPH_ID, {
        input: { raw_requirements: rawRequirements || "Todo app" },
        streamMode: ["values", "updates", "custom"],
      });

      for await (const event of runStream) {
        if (event.event === "updates") {
          const nodeName = event.data ? Object.keys(event.data)[0] : "?";
          setCurrentNode(nodeName);
        } else if (event.event === "values") {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const next = (event.data as any)?.next;
          if (next && Array.isArray(next)) {
            setNextNodes(next);
            const isAtGate = next.some((n: string) => n.startsWith("gate_"));
            if (isAtGate) {
              setInterrupted(true);
              setIsRunning(false);
              console.log("[pipeline] Interrupted at gate:", next);
            }
          }
        }
      }

      console.log("[pipeline] stream ended, fetching final state");
      await fetchLatestState(tid);
      setIsRunning(false);
      setCurrentNode("");
    } catch (err: unknown) {
      console.error("[pipeline] error", err);
      const msg = err instanceof Error ? err.message : String(err);
      setSubmitError(msg);
      setIsRunning(false);
      setCurrentNode("");
    } finally {
      submittingRef.current = false;
    }
  };

  const handleGateSubmit = async (decision: "approve" | "reject" | "approve_with_edit") => {
    if (!threadId) return;
    setSubmitError(null);
    setIsRunning(true);
    setInterrupted(false);
    setCurrentNode("resuming");
    try {
      // dùng "action" thay vì "decision" — backend đọc field "action"
      const resumeData = { action: decision, feedback: feedback.trim() };

      console.log("[gate] Submitting:", resumeData);
      const runStream = client.runs.stream(threadId, GRAPH_ID, {
        command: { resume: resumeData },
        streamMode: ["values", "updates", "custom"],
      });

      for await (const event of runStream) {
        if (event.event === "updates") {
          const nodeName = event.data ? Object.keys(event.data)[0] : "?";
          setCurrentNode(nodeName);
        } else if (event.event === "values") {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const next = (event.data as any)?.next;
          if (next && Array.isArray(next)) {
            setNextNodes(next);
            const isAtGate = next.some((n: string) => n.startsWith("gate_"));
            if (isAtGate) {
              setInterrupted(true);
              setIsRunning(false);
              console.log("[gate] Interrupted at next gate:", next);
            }
          }
        }
      }

      console.log("[gate] stream ended, fetching final state");
      await fetchLatestState(threadId);
      setIsRunning(false);
      setCurrentNode("");
      setFeedback("");
    } catch (err: unknown) {
      console.error("[gate] error", err);
      const msg = err instanceof Error ? err.message : String(err);
      setSubmitError(msg);
      setIsRunning(false);
      setCurrentNode("");
    }
  };

  const renderGateHistory = () => {
    if (gateHistory.length === 0) return null;
    return (
      <div style={{ marginTop: 24, borderTop: "1px solid #eee", paddingTop: 16 }}>
        <h4 style={{ fontSize: 15, fontWeight: 600, marginBottom: 10 }}>
          📋 Gate History
        </h4>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: "2px solid #eee", textAlign: "left" }}>
              <th style={{ padding: "6px 8px" }}>Gate</th>
              <th style={{ padding: "6px 8px" }}>Decision</th>
              <th style={{ padding: "6px 8px" }}>Feedback</th>
              <th style={{ padding: "6px 8px" }}>Time</th>
            </tr>
          </thead>
          <tbody>
            {gateHistory.map((entry, i) => (
              <tr key={i} style={{ borderBottom: "1px solid #f0f0f0" }}>
                <td style={{ padding: "6px 8px" }}>{entry.gate_name ?? "—"}</td>
                <td style={{ padding: "6px 8px" }}>
                  <span
                    style={{
                      color: entry.decision === "approve" ? "#52c41a" : "#ff4d4f",
                      fontWeight: 600,
                    }}
                  >
                    {entry.decision === "approve" ? "✅ Approve" : "❌ Reject"}
                  </span>
                </td>
                <td
                  style={{
                    padding: "6px 8px",
                    maxWidth: 300,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {entry.feedback || "—"}
                </td>
                <td style={{ padding: "6px 8px", color: "#999", fontSize: 12 }}>
                  {entry.timestamp
                    ? new Date(entry.timestamp).toLocaleString("vi-VN")
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderTabs = () => {
    if (!hasStarted) return null;
    const gateLabel: Record<string, string> = {
      gate_prd: "Gate PRD",
      gate_design: "Gate Design",
      gate_mockup: "Gate Mockup",
    };
    const gateDescription: Record<string, string> = {
      gate_prd: "Review the PRD document before proceeding to Design phase.",
      gate_design: "Review the Design document before proceeding to UI phase.",
      gate_mockup: "Review the Mockup HTML before proceeding to Engineer phase.",
    };

    return (
      <>
        {interrupted && currentGate && (
          <div
            style={{
              background: "#fffbe6",
              border: "2px solid #faad14",
              borderRadius: 8,
              padding: 20,
              marginBottom: 20,
            }}
          >
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>
              ⏸ {gateLabel[currentGate] ?? currentGate} — Awaiting Review
            </h3>
            <p style={{ fontSize: 13, color: "#666", marginBottom: 16 }}>
              {gateDescription[currentGate] ?? "Review the output before continuing."}
            </p>

            {pendingRole && (
              <p style={{ fontSize: 12, color: "#854d0e", marginBottom: 12 }}>
                👤 Role required:{" "}
                <strong>{pendingRole === "ba" ? "BA" : "Dev"}</strong>
              </p>
            )}
          </div>
        )}

        <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
          {(["prd", "design", "mockup", "files"] as ActiveTab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: "6px 14px",
                borderRadius: 4,
                border: "1px solid #d9d9d9",
                background: activeTab === tab ? "#1677ff" : "#fff",
                color: activeTab === tab ? "#fff" : "#333",
                cursor: "pointer",
                fontWeight: activeTab === tab ? 600 : 400,
              }}
            >
              {tab === "prd" ? "📄 PRD" : tab === "design" ? "🎨 Design" : tab === "mockup" ? "🖥 Mockup" : "📁 Files"}
            </button>
          ))}
        </div>

        {activeTab === "files" && (
          <div style={{ marginBottom: 16 }}>
            <RepoBrowser threadId={threadId} />
          </div>
        )}

        {activeTab !== "files" && (
          <div
            style={{
              background: "#fff",
              borderRadius: 6,
              border: "1px solid #e8e8e8",
              padding: 16,
              marginBottom: 16,
              maxHeight: 400,
              overflow: "auto",
            }}
          >
            {activeTab === "prd" && (
              <pre style={{ whiteSpace: "pre-wrap", fontSize: 13, margin: 0 }}>
                {state.prd_markdown ?? state.prd ?? "PRD content not available yet."}
              </pre>
            )}
            {activeTab === "design" && (
              <pre style={{ whiteSpace: "pre-wrap", fontSize: 13, margin: 0 }}>
                {state.design_markdown ?? state.design ?? "Design content not available yet."}
              </pre>
            )}
            {activeTab === "mockup" && (
              <div style={{ marginBottom: 12 }}>
                <button onClick={() => setMockupEditMode((v) => !v)}>
                  {mockupEditMode ? "🖼 Xem ảnh" : "✏️ Sửa tay (Puck)"}
                </button>
              </div>
            )}
            {activeTab === "mockup" && mockupEditMode && threadId && (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {(state.mockup_screenshots ?? []).map((imgPath: string, i: number) => {
                  const slug = imgPath.split("/").pop()!.replace(/(\.preview)?\.png$/, "");
                  return (
                    <div key={i}>
                      <button onClick={() => setEditingSlug(slug)}>{slug}</button>
                      {editingSlug === slug && (
                        <MockupPuckEditor
                          projectId={threadId}
                          slug={slug}
                          onSaved={() => fetchLatestState(threadId)}
                        />
                      )}
                    </div>
                  );
                })}
              </div>
            )}
            {activeTab === "mockup" && !mockupEditMode && (
              (state.mockup_screenshots && state.mockup_screenshots.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                  {state.mockup_screenshots.map((imgPath: string, i: number) => (
                    <div key={i}>
                      <p style={{ fontSize: 12, color: "#999", marginBottom: 4 }}>
                        📸 Màn hình {i + 1}: {imgPath.split("/").pop()}
                      </p>
                      <img
                        src={`/artifacts/${imgPath}`}
                        alt={`Screenshot ${i + 1}`}
                        style={{
                          width: "100%",
                          border: "1px solid #e8e8e8",
                          borderRadius: 6,
                          display: "block",
                        }}
                      />
                    </div>
                  ))}
                </div>
              ) : state.mockup_html ? (
                <iframe
                  sandbox="allow-scripts"
                  srcDoc={state.mockup_html}
                  style={{ width: "100%", height: 350, border: "none", display: "block" }}
                  title="Mockup Preview"
                />
              ) : (
                <p style={{ color: "#999", fontSize: 13 }}>Mockup not available yet.</p>
              )
            ))}
          </div>
        )}



        {activeTab === "mockup" && (
          <MockupVersionHistory
            client={client}
            threadId={threadId}
            currentHtml={state.mockup_html ?? ""}
          />
        )}

        {interrupted && currentGate && (
          <div style={{ marginTop: 16 }}>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Optional feedback..."
              style={{
                width: "100%",
                minHeight: 60,
                padding: 8,
                borderRadius: 4,
                border: "1px solid #d9d9d9",
                fontSize: 13,
                resize: "vertical",
                marginBottom: 12,
                boxSizing: "border-box",
              }}
            />
            <div style={{ display: "flex", gap: 10 }}>
              <button
                onClick={() => handleGateSubmit("approve")}
                disabled={isRunning}
                style={{
                  padding: "8px 20px",
                  borderRadius: 4,
                  border: "none",
                  background: isRunning ? "#d9d9d9" : "#52c41a",
                  color: "#fff",
                  cursor: isRunning ? "not-allowed" : "pointer",
                  fontWeight: 600,
                  fontSize: 14,
                }}
              >
                ✅ Approve
              </button>
              <button
                onClick={() => handleGateSubmit("reject")}
                disabled={isRunning}
                style={{
                  padding: "8px 20px",
                  borderRadius: 4,
                  border: "none",
                  background: isRunning ? "#d9d9d9" : "#ff4d4f",
                  color: "#fff",
                  cursor: isRunning ? "not-allowed" : "pointer",
                  fontWeight: 600,
                  fontSize: 14,
                }}
              >
                ❌ Reject
              </button>
              <button onClick={() => handleGateSubmit("approve_with_edit")}>
                ✅ Approve kèm sửa tay
              </button>
            </div>
          </div>
        )}
      </>
    );
  };

  const renderStartPanel = () => {
    if (hasStarted) return null;
    return (
      <div
        style={{
          background: "#fff",
          borderRadius: 8,
          border: "1px solid #e8e8e8",
          padding: 24,
          marginBottom: 20,
        }}
      >
        <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>
          🚀 Start New Pipeline
        </h3>
        <textarea
          value={rawRequirements}
          onChange={(e) => setRawRequirements(e.target.value)}
          placeholder="Enter your project requirements..."
          style={{
            width: "100%",
            minHeight: 80,
            padding: 10,
            borderRadius: 4,
            border: "1px solid #d9d9d9",
            fontSize: 14,
            resize: "vertical",
            marginBottom: 12,
            boxSizing: "border-box",
          }}
        />
        <button
          onClick={handleStart}
          disabled={isRunning || !rawRequirements.trim()}
          style={{
            padding: "10px 24px",
            borderRadius: 4,
            border: "none",
            background: isRunning ? "#d9d9d9" : "#1677ff",
            color: "#fff",
            cursor: isRunning ? "not-allowed" : "pointer",
            fontWeight: 600,
            fontSize: 14,
          }}
        >
          {isRunning ? "⏳ Running..." : "▶ Start"}
        </button>
      </div>
    );
  };

  const renderRunningIndicator = () => {
    if (!isRunning) return null;
    return (
      <div
        style={{
          background: "#e6f4ff",
          border: "1px solid #91caff",
          borderRadius: 6,
          padding: "12px 16px",
          marginBottom: 20,
          fontSize: 13,
          color: "#003eb3",
        }}
      >
        ⏳ Pipeline is running...{" "}
        {currentNode && (
          <span>
            Current node: <strong>{currentNode}</strong>
          </span>
        )}
      </div>
    );
  };

  const renderError = () => {
    if (!submitError && !error) return null;
    const errMsg =
      submitError || (typeof error === "string" ? error : JSON.stringify(error));
    return (
      <div
        style={{
          background: "#fff2f0",
          border: "1px solid #ffccc7",
          borderRadius: 6,
          padding: "12px 16px",
          marginBottom: 20,
          fontSize: 13,
          color: "#a8071a",
        }}
      >
        ❌ Error: {errMsg}
      </div>
    );
  };

  const renderDebugState = () => {
    if (!hasStarted) return null;
    return (
      <details style={{ marginTop: 24 }}>
        <summary style={{ fontSize: 13, color: "#999", cursor: "pointer" }}>
          🔧 Debug: Raw State
        </summary>
        <pre
          style={{
            background: "#f5f5f5",
            padding: 12,
            borderRadius: 6,
            fontSize: 12,
            overflow: "auto",
            maxHeight: 300,
            whiteSpace: "pre-wrap",
          }}
        >
          {JSON.stringify(state, null, 2)}
        </pre>
      </details>
    );
  };

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      {/* Left column: Thread list */}
      <ThreadDashboard
        client={client}
        activeThreadId={threadId}
        onSelect={(tid) => {
          setThreadId(tid);
          setIsRunning(false);
          setCurrentNode("");
          setInterrupted(false);
          setSnapshotState({});
        }}
        onCreateNew={() => {
          setThreadId(undefined);
          setIsRunning(false);
          setCurrentNode("");
          setInterrupted(false);
          setFeedback("");
          setSnapshotState({});
        }}
      />

      {/* Middle column: Pipeline graph */}
      <div
        style={{
          width: 340,
          borderRight: "1px solid #e8e8e8",
          overflowY: "auto",
          background: "#fff",
        }}
      >
        <PipelineGraph
          currentGate={currentGate}
          nextNodes={nextNodes}
          isRunning={isRunning}
          currentNode={currentNode}
          nodeStats={state.node_stats}
        />
      </div>

      {/* Right column: Review content */}
      <div style={{ flex: 1, overflowY: "auto", padding: 24 }}>
        <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 20 }}>
          🏭 Software Factory
        </h2>
        {renderError()}
        {renderStartPanel()}
        {renderRunningIndicator()}
        {renderTabs()}
        {renderGateHistory()}
        {renderDebugState()}
      </div>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ReviewApp />
    </ErrorBoundary>
  );
}

export default App;