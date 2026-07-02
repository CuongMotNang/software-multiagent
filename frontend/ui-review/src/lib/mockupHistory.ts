import { Client } from "@langchain/langgraph-sdk";

export interface MockupVersion {
  checkpointId: string;
  html: string;
  timestamp: string;
  gateDecision: string | null;
}

export async function getMockupVersions(
  client: Client,
  threadId: string
): Promise<MockupVersion[]> {
  const history = await client.threads.getHistory(threadId);

  const versions: MockupVersion[] = [];
  let lastHtml: string | null = null;

  // history mới nhất đứng đầu — duyệt ngược để lấy thứ tự tăng dần thời gian
  for (const snapshot of [...history].reverse()) {
    const html = (snapshot.values as any)?.mockup_html;
    if (!html || html === lastHtml) continue; // bỏ qua nếu trùng bản trước
    lastHtml = html;
    const checkpointId = snapshot.checkpoint?.checkpoint_id;
    const timestamp = snapshot.created_at;
    if (!checkpointId || !timestamp) continue; // skip nếu thiếu metadata
    versions.push({
      checkpointId,
      html,
      timestamp,
      gateDecision: (snapshot.values as any)?.gate_decision ?? null,
    });
  }

  return versions; // thứ tự tăng dần: version đầu tiên -> mới nhất
}
