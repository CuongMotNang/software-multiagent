import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";

interface TreeNode {
  name: string;
  type: "file" | "dir";
  path: string;
  size?: number | null;
  children?: TreeNode[];
}

interface Props {
  threadId: string | undefined;
}

const IMAGE_EXT = new Set(["png", "jpg", "jpeg", "gif", "webp", "svg"]);
const LANG_BY_EXT: Record<string, string> = {
  py: "python",
  ts: "typescript",
  tsx: "tsx",
  js: "javascript",
  jsx: "jsx",
  json: "json",
  css: "css",
  html: "markup",
  sql: "sql",
  sh: "bash",
  yml: "yaml",
  yaml: "yaml",
  toml: "toml",
  txt: "text",
};

function extOf(name: string): string {
  const i = name.lastIndexOf(".");
  return i === -1 ? "" : name.slice(i + 1).toLowerCase();
}

export function RepoBrowser({ threadId }: Props) {
  const [tree, setTree] = useState<TreeNode | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState<TreeNode | null>(null);
  const [content, setContent] = useState<string>("");
  const [loadingTree, setLoadingTree] = useState(false);
  const [loadingFile, setLoadingFile] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!threadId) return;
    setLoadingTree(true);
    setError(null);
    fetch(`/tree/${threadId}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: TreeNode) => {
        setTree(data);
        setExpanded(new Set([data.path])); // mở sẵn thư mục gốc
      })
      .catch((err) => setError(`Không tải được cây thư mục: ${err.message}`))
      .finally(() => setLoadingTree(false));
  }, [threadId]);

  const openFile = (node: TreeNode) => {
    if (!threadId) return;
    setSelected(node);
    if (IMAGE_EXT.has(extOf(node.name))) {
      setContent(""); // ảnh không cần fetch text, render trực tiếp bằng <img>
      return;
    }
    setLoadingFile(true);
    fetch(`/artifacts/${threadId}/${node.path}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.text();
      })
      .then(setContent)
      .catch((err) => setContent(`⚠️ Không đọc được file: ${err.message}`))
      .finally(() => setLoadingFile(false));
  };

  const toggleDir = (path: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  if (!threadId) {
    return <p style={{ color: "#999", fontSize: 13 }}>Chưa có thread nào được chọn.</p>;
  }

  return (
    <div style={{ display: "flex", height: "70vh", border: "1px solid #e5e7eb", borderRadius: 8, overflow: "hidden" }}>
      {/* Sidebar: cây thư mục */}
      <div
        style={{
          width: 280,
          borderRight: "1px solid #e5e7eb",
          overflowY: "auto",
          padding: 8,
          background: "#f6f8fa",
          fontFamily: "ui-monospace, monospace",
          fontSize: 13,
        }}
      >
        {loadingTree && <div style={{ color: "#999", padding: 8 }}>Đang tải...</div>}
        {error && <div style={{ color: "#d32f2f", padding: 8 }}>{error}</div>}
        {tree && (
          <TreeItem
            node={tree}
            depth={0}
            expanded={expanded}
            onToggleDir={toggleDir}
            onOpenFile={openFile}
            selectedPath={selected?.path}
          />
        )}
      </div>

      {/* Nội dung file */}
      <div style={{ flex: 1, overflowY: "auto", padding: 16, background: "#fff" }}>
        {!selected && <p style={{ color: "#999" }}>Chọn 1 file bên trái để xem nội dung.</p>}

        {selected && IMAGE_EXT.has(extOf(selected.name)) && (
          <img
            src={`/artifacts/${threadId}/${selected.path}`}
            alt={selected.name}
            style={{ maxWidth: "100%", border: "1px solid #eee", borderRadius: 4 }}
          />
        )}

        {selected && !IMAGE_EXT.has(extOf(selected.name)) && (
          <>
            <div style={{ fontSize: 13, color: "#666", marginBottom: 12, fontFamily: "ui-monospace, monospace" }}>
              {selected.path}
            </div>
            {loadingFile ? (
              <div style={{ color: "#999" }}>Đang tải...</div>
            ) : extOf(selected.name) === "md" ? (
              <div className="markdown-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
              </div>
            ) : (
              <SyntaxHighlighter
                language={LANG_BY_EXT[extOf(selected.name)] || "text"}
                style={oneLight}
                customStyle={{ fontSize: 13, borderRadius: 6 }}
                showLineNumbers
              >
                {content}
              </SyntaxHighlighter>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function TreeItem({
  node,
  depth,
  expanded,
  onToggleDir,
  onOpenFile,
  selectedPath,
}: {
  node: TreeNode;
  depth: number;
  expanded: Set<string>;
  onToggleDir: (path: string) => void;
  onOpenFile: (node: TreeNode) => void;
  selectedPath: string | undefined;
}) {
  const isDir = node.type === "dir";
  const isOpen = expanded.has(node.path);
  const isSelected = selectedPath === node.path;

  return (
    <div>
      <div
        onClick={() => (isDir ? onToggleDir(node.path) : onOpenFile(node))}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          padding: "3px 6px",
          paddingLeft: depth * 14 + 6,
          cursor: "pointer",
          borderRadius: 4,
          background: isSelected ? "#dbeafe" : "transparent",
          whiteSpace: "nowrap",
        }}
        onMouseEnter={(e) => {
          if (!isSelected) e.currentTarget.style.background = "#eef1f4";
        }}
        onMouseLeave={(e) => {
          if (!isSelected) e.currentTarget.style.background = "transparent";
        }}
      >
        <span>{isDir ? (isOpen ? "📂" : "📁") : fileIcon(node.name)}</span>
        <span>{node.name}</span>
      </div>
      {isDir && isOpen && node.children?.map((child) => (
        <TreeItem
          key={child.path}
          node={child}
          depth={depth + 1}
          expanded={expanded}
          onToggleDir={onToggleDir}
          onOpenFile={onOpenFile}
          selectedPath={selectedPath}
        />
      ))}
    </div>
  );
}

function fileIcon(name: string): string {
  const ext = extOf(name);
  if (IMAGE_EXT.has(ext)) return "🖼️";
  if (ext === "md") return "📝";
  if (ext === "py") return "🐍";
  if (["ts", "tsx", "js", "jsx"].includes(ext)) return "📜";
  if (ext === "json") return "🔧";
  return "📄";
}