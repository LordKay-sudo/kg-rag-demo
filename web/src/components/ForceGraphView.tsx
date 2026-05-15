import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D, { type ForceGraphMethods } from "react-force-graph-2d";
import type { SubgraphLink, SubgraphNode } from "../api/client";

const LABEL_COLORS: Record<string, string> = {
  Gene: "#34d399",
  Disease: "#f472b6",
  Drug: "#38bdf8",
  Document: "#a78bfa",
  Chunk: "#94a3b8",
};

interface GraphNode {
  id: string;
  label: string;
  name: string;
  x?: number;
  y?: number;
  fx?: number;
  fy?: number;
}

interface GraphLink {
  source: string;
  target: string;
  type: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

interface Props {
  centerId: string;
  nodes: SubgraphNode[];
  links: SubgraphLink[];
}

function layoutRing(nodeList: GraphNode[], centerId: string): GraphNode[] {
  const center = nodeList.find((n) => n.id === centerId);
  const others = nodeList.filter((n) => n.id !== centerId);
  const radius = Math.max(80, 36 * others.length);
  const laid: GraphNode[] = [];

  if (center) {
    laid.push({ ...center, x: 0, y: 0, fx: 0, fy: 0 });
  }

  others.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / others.length - Math.PI / 2;
    const x = radius * Math.cos(angle);
    const y = radius * Math.sin(angle);
    laid.push({ ...n, x, y, fx: x, fy: y });
  });

  return laid;
}

export default function ForceGraphView({ centerId, nodes, links }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<ForceGraphMethods | undefined>(undefined);
  const [dimensions, setDimensions] = useState({ width: 900, height: 420 });

  const data: GraphData = useMemo(() => {
    const graphNodes = layoutRing(
      nodes.map((n) => ({
        id: n.id,
        label: n.label,
        name: n.name ?? n.id,
      })),
      centerId
    );
    return {
      nodes: graphNodes,
      links: links.map((l) => ({
        source: l.source,
        target: l.target,
        type: l.type,
      })),
    };
  }, [nodes, links, centerId]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const update = () => setDimensions({ width: el.clientWidth, height: el.clientHeight });
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const fitGraph = () => graphRef.current?.zoomToFit(350, 60);

  useEffect(() => {
    const timers = [100, 400, 900].map((ms) => setTimeout(fitGraph, ms));
    return () => timers.forEach(clearTimeout);
  }, [data, dimensions]);

  if (data.nodes.length === 0) {
    return <div className="state-box">No graph data to display.</div>;
  }

  return (
    <div ref={containerRef} className="graph-panel">
      <ForceGraph2D
        ref={graphRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={data}
        enableNodeDrag={false}
        enableZoomInteraction
        nodeLabel={(n) => `${(n as GraphNode).label}: ${(n as GraphNode).name}`}
        linkLabel={(l) => (l as GraphLink).type.replace(/_/g, " ")}
        linkDirectionalArrowLength={5}
        linkDirectionalArrowRelPos={1}
        linkColor={() => "rgba(148, 163, 184, 0.55)"}
        linkWidth={1.4}
        backgroundColor="#121c2e"
        warmupTicks={0}
        cooldownTicks={0}
        onEngineStop={fitGraph}
        nodeCanvasObject={(node, ctx, globalScale) => {
          const n = node as GraphNode & { x?: number; y?: number };
          const isCenter = n.id === centerId;
          const r = isCenter ? 10 : 8;
          const fontSize = Math.max(11, 14 / globalScale);

          ctx.beginPath();
          ctx.arc(n.x ?? 0, n.y ?? 0, r, 0, 2 * Math.PI);
          ctx.fillStyle = LABEL_COLORS[n.label] ?? "#94a3b8";
          ctx.fill();
          if (isCenter) {
            ctx.strokeStyle = "#38bdf8";
            ctx.lineWidth = 2.5 / globalScale;
            ctx.stroke();
          }

          ctx.font = `600 ${fontSize}px DM Sans, sans-serif`;
          ctx.textAlign = "center";
          ctx.textBaseline = "top";
          ctx.fillStyle = "#e8edf5";
          ctx.fillText(n.name, n.x ?? 0, (n.y ?? 0) + r + 4);
        }}
      />
    </div>
  );
}
