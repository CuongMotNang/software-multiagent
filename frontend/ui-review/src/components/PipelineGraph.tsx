interface Props {
  currentGate: string;   // gate đang interrupt (vd "gate_prd")
  nextNodes: string[];   // từ thread state .next
  isRunning: boolean;
  currentNode: string;   // node đang chạy (từ stream updates)
}

const NODES = [
  { id: "ba",           label: "BA",           y: 1 },
  { id: "prd",          label: "PRD",          y: 2 },
  { id: "gate_prd",     label: "Gate PRD",     y: 3, isGate: true },
  { id: "design",       label: "Design",       y: 4 },
  { id: "gate_design",  label: "Gate Design",  y: 5, isGate: true },
  { id: "ui",           label: "UI",           y: 6 },
  { id: "gate_mockup",  label: "Gate Mockup",  y: 7, isGate: true },
  { id: "engineer",     label: "Engineer",     y: 8 },
];

const ROW_H = 64;
const NODE_W = 140;
const NODE_H = 36;
const CX = 160; // center x của cột chính
const SVG_W = 340;
const SVG_H = NODES.length * ROW_H + 20;

export function PipelineGraph({ currentGate, nextNodes, isRunning, currentNode }: Props) {
  const getNodeY = (y: number) => y * ROW_H - ROW_H / 2 + 10;

  const nodeState = (id: string): "active" | "waiting" | "running" | "idle" => {
    if (nextNodes.includes(id)) return "active";           // gate dừng tại đây
    if (isRunning && currentNode === id) return "running"; // đang chạy qua
    return "idle";
  };

  const nodeColor = (state: ReturnType<typeof nodeState>, isGate?: boolean) => {
    if (state === "active") return { fill: "#fffbe6", stroke: "#faad14", text: "#854d0e" };
    if (state === "running") return { fill: "#e6f4ff", stroke: "#1677ff", text: "#003eb3" };
    if (isGate) return { fill: "#f9f0ff", stroke: "#d3adf7", text: "#531dab" };
    return { fill: "#f6ffed", stroke: "#b7eb8f", text: "#237804" };
  };

  return (
    <div style={{ padding: "16px 8px" }}>
      <h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: "#555" }}>📊 Pipeline Graph</h4>
      <svg width={SVG_W} height={SVG_H} style={{ display: "block", margin: "0 auto" }}>
        {/* Edges chính (tuyến tính) */}
        {NODES.slice(0, -1).map((n, i) => {
          const y1 = getNodeY(n.y) + NODE_H;
          const y2 = getNodeY(NODES[i + 1].y);
          return <line key={`e-${n.id}`} x1={CX} y1={y1} x2={CX} y2={y2} stroke="#ccc" strokeWidth={2} />;
        })}

        {/* Reject loop: gate_prd → ba */}
        <path d={`M ${CX - NODE_W / 2} ${getNodeY(3) + NODE_H / 2} 
                   C ${CX - NODE_W} ${getNodeY(3) + NODE_H / 2}, 
                     ${CX - NODE_W} ${getNodeY(1) + NODE_H / 2}, 
                     ${CX - NODE_W / 2} ${getNodeY(1) + NODE_H / 2}`}
          fill="none" stroke="#ff9f9f" strokeWidth={1.5} strokeDasharray="4,3" />
        <text x={CX - NODE_W - 4} y={getNodeY(2) + 4} fontSize={10} fill="#ff7875" textAnchor="middle">↺ reject</text>

        {/* Reject loop: gate_design → design */}
        <path d={`M ${CX + NODE_W / 2} ${getNodeY(5) + NODE_H / 2}
                   C ${CX + NODE_W} ${getNodeY(5) + NODE_H / 2},
                     ${CX + NODE_W} ${getNodeY(4) + NODE_H / 2},
                     ${CX + NODE_W / 2} ${getNodeY(4) + NODE_H / 2}`}
          fill="none" stroke="#ff9f9f" strokeWidth={1.5} strokeDasharray="4,3" />
        <text x={CX + NODE_W + 4} y={getNodeY(4) + 14} fontSize={10} fill="#ff7875" textAnchor="middle">↺ reject</text>

        {/* Reject loop: gate_mockup → ui */}
        <path d={`M ${CX - NODE_W / 2} ${getNodeY(7) + NODE_H / 2}
                   C ${CX - NODE_W - 20} ${getNodeY(7) + NODE_H / 2},
                     ${CX - NODE_W - 20} ${getNodeY(6) + NODE_H / 2},
                     ${CX - NODE_W / 2} ${getNodeY(6) + NODE_H / 2}`}
          fill="none" stroke="#ff9f9f" strokeWidth={1.5} strokeDasharray="4,3" />
        <text x={CX - NODE_W - 24} y={getNodeY(6) + 14} fontSize={10} fill="#ff7875" textAnchor="middle">↺ reject</text>

        {/* Nodes */}
        {NODES.map((n) => {
          const state = nodeState(n.id);
          const color = nodeColor(state, (n as any).isGate);
          const y = getNodeY(n.y);
          return (
            <g key={n.id}>
              <rect x={CX - NODE_W / 2} y={y} width={NODE_W} height={NODE_H}
                rx={6} fill={color.fill} stroke={color.stroke} strokeWidth={state === "active" ? 2.5 : 1.5} />
              {state === "active" && (
                <rect x={CX - NODE_W / 2 - 2} y={y - 2} width={NODE_W + 4} height={NODE_H + 4}
                  rx={8} fill="none" stroke={color.stroke} strokeWidth={1} strokeDasharray="4,2" opacity={0.5} />
              )}
              <text x={CX} y={y + NODE_H / 2 + 4} textAnchor="middle"
                fontSize={12} fontWeight={(n as any).isGate ? 500 : 600} fill={color.text}>
                {(n as any).isGate ? "⏸ " : ""}{n.label}
              </text>
            </g>
          );
        })}

        {/* Legend */}
        <g transform={`translate(10, ${SVG_H - 52})`}>
          <rect width={8} height={8} rx={2} fill="#e6f4ff" stroke="#1677ff" />
          <text x={12} y={7} fontSize={10} fill="#555">Đang chạy</text>
          <rect y={14} width={8} height={8} rx={2} fill="#fffbe6" stroke="#faad14" />
          <text x={12} y={21} fontSize={10} fill="#555">Chờ duyệt</text>
          <rect y={28} width={8} height={8} rx={2} fill="#f9f0ff" stroke="#d3adf7" />
          <text x={12} y={35} fontSize={10} fill="#555">Gate node</text>
        </g>
      </svg>
    </div>
  );
}