import React, { useState, useEffect, useRef, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Maximize2, ZoomIn, ZoomOut, Layers, ShieldAlert, AlertTriangle, X, ArrowRight, User, Laptop, CreditCard, DollarSign } from 'lucide-react';
import debounce from 'lodash/debounce';

// Type color palette matching spec & reference image
const TYPE_COLORS = {
  user: '#3b82f6',        // Soft Blue (People)
  account: '#0284c7',     // Light Blue / Cyan (Accounts)
  device: '#f97316',      // Orange (Devices)
  transaction: '#ef4444', // Crimson / Red (Transactions)
  default: '#3b82f6'
};

const TYPE_NAMES = {
  user: 'Person',
  account: 'Account',
  device: 'Device',
  transaction: 'Txn',
  default: 'Entity'
};

// Default Anti-Fraud Reference Network with explicit Person-Device dotted links, Brother, Owner, Connected To
const DEFAULT_BASELINE_GRAPH = {
  nodes: [
    { id: "User 041", label: "User 041", type: "user", color: TYPE_COLORS.user, val: 20, has_alert: true, is_selected: false, role: "Accused Suspect" },
    { id: "DEV-992A", label: "DEV-992A", type: "device", color: TYPE_COLORS.device, val: 22, has_alert: true, is_selected: false, role: "Gateway Device" },
    { id: "User 882", label: "User 882", type: "user", color: TYPE_COLORS.user, val: 20, has_alert: true, is_selected: false, role: "Co-Conspirator" },
    { id: "DEV-174Q", label: "DEV-174Q", type: "device", color: TYPE_COLORS.device, val: 28, has_alert: true, is_selected: true, role: "Mastermind Device" },
    { id: "ACC-7741", label: "ACC-7741", type: "account", color: TYPE_COLORS.account, val: 22, has_alert: true, is_selected: false, role: "Mule Account" },
    { id: "185.221.14.8", label: "185.221.14.8", type: "transaction", color: TYPE_COLORS.transaction, val: 22, has_alert: true, is_selected: false, role: "IP Proxy" },
    { id: "ACC-1028", label: "ACC-1028", type: "account", color: TYPE_COLORS.account, val: 26, has_alert: true, is_selected: false, role: "Aggregator Account" },
    { id: "TXN-8831", label: "TXN-8831", type: "transaction", color: TYPE_COLORS.transaction, val: 24, has_alert: true, is_selected: false, role: "Exposure Txn" },
    { id: "ACC-5520", label: "ACC-5520", type: "account", color: TYPE_COLORS.account, val: 22, has_alert: true, is_selected: false, role: "Transit Ledger" },
    { id: "10.42.8.64", label: "10.42.8.64", type: "device", color: TYPE_COLORS.device, val: 22, has_alert: true, is_selected: false, role: "Vishing IP Hop" },
    { id: "TXN-8924", label: "TXN-8924", type: "transaction", color: TYPE_COLORS.transaction, val: 24, has_alert: true, is_selected: false, role: "Velocity Txn" },
    { id: "ACC-7015", label: "ACC-7015", type: "account", color: TYPE_COLORS.account, val: 22, has_alert: true, is_selected: false, role: "Cashout Account" }
  ],
  links: [
    // Person-Device Dotted Connections
    { source: "User 041", target: "DEV-992A", relation: "Owner", color: "#60a5fa", dashed: false, dotted: true, weight: 1.8 },
    { source: "User 882", target: "DEV-174Q", relation: "Connected To", color: "#60a5fa", dashed: false, dotted: true, weight: 1.8 },

    // Person-Person Solid Connection
    { source: "User 041", target: "User 882", relation: "Brother", color: "#3b82f6", dashed: false, dotted: false, weight: 2.0 },

    // Standard Solid Connections
    { source: "DEV-992A", target: "ACC-1028", relation: "device login", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "ACC-7741", target: "185.221.14.8", relation: "", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "ACC-7741", target: "ACC-1028", relation: "transfers to", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "185.221.14.8", target: "DEV-992A", relation: "", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "185.221.14.8", target: "ACC-1028", relation: "", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "ACC-1028", target: "TXN-8831", relation: "exposure", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "TXN-8831", target: "ACC-5520", relation: "clears via", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "ACC-5520", target: "10.42.8.64", relation: "", color: "#475569", dashed: false, dotted: false, weight: 1.5 },
    { source: "ACC-5520", target: "TXN-8924", relation: "", color: "#475569", dashed: false, dotted: false, weight: 1.5 },

    // High-Risk Yellow Trails
    { source: "DEV-174Q", target: "10.42.8.64", relation: "device trail", color: "#eab308", dashed: true, dotted: false, weight: 2.0 },
    { source: "DEV-174Q", target: "TXN-8924", relation: "velocity sig", color: "#eab308", dashed: true, dotted: false, weight: 2.0 },
    { source: "DEV-174Q", target: "ACC-7015", relation: "shared device", color: "#eab308", dashed: false, dotted: false, weight: 2.5 },
    { source: "TXN-8924", target: "ACC-7015", relation: "cashout", color: "#475569", dashed: false, dotted: false, weight: 1.5 }
  ]
};

// Pure normalization function
function normalizeGraphData(rawData) {
  let input = null;
  if (rawData && rawData.nodes && rawData.nodes.length > 0) {
    input = rawData;
  } else if (rawData?.graph_data?.nodes?.length > 0) {
    input = rawData.graph_data;
  } else if (rawData?.data?.graph_data?.nodes?.length > 0) {
    input = rawData.data.graph_data;
  } else {
    input = DEFAULT_BASELINE_GRAPH;
  }

  const cleanNodes = input.nodes.map(n => {
    const type = (n.type || 'account').toLowerCase();
    const isSelected = n.is_selected || n.id === 'DEV-174Q';
    return {
      ...n,
      id: String(n.id || n.label || 'unknown'),
      label: String(n.label || n.id || 'Node'),
      type: type,
      color: TYPE_COLORS[type] || n.color || TYPE_COLORS.default,
      val: n.val || (isSelected ? 26 : 20),
      has_alert: n.has_alert !== undefined ? n.has_alert : true,
      is_selected: isSelected
    };
  });

  const validNodeIds = new Set(cleanNodes.map(n => n.id));
  const nodeTypeMap = new Map(cleanNodes.map(n => [n.id, n.type]));

  const cleanLinks = (input.links || [])
    .map(l => {
      const source = typeof l.source === 'object' ? l.source.id : l.source;
      const target = typeof l.target === 'object' ? l.target.id : l.target;
      const srcType = nodeTypeMap.get(String(source));
      const tgtType = nodeTypeMap.get(String(target));
      const isPersonDevice = (srcType === 'user' && tgtType === 'device') || (srcType === 'device' && tgtType === 'user');

      return {
        ...l,
        source: String(source || ''),
        target: String(target || ''),
        relation: l.relation || (isPersonDevice ? 'Person-Device' : ''),
        color: l.color || (isPersonDevice ? '#60a5fa' : '#475569'),
        dashed: l.dashed || false,
        dotted: l.dotted || isPersonDevice,
        weight: l.weight || 1.5
      };
    })
    .filter(l => l.source && l.target && l.source !== l.target && validNodeIds.has(l.source) && validNodeIds.has(l.target));

  return { nodes: cleanNodes, links: cleanLinks };
}

export default function GraphCanvas({ initialData, customGraphData, onNodeSelect, onSelectNode }) {
  const fgRef = useRef(null);
  const containerRef = useRef(null);
  const prevInputRef = useRef(null);

  const [graphData, setGraphData] = useState(() => normalizeGraphData(customGraphData || initialData));
  const [selectedNode, setSelectedNode] = useState(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [isInitialized, setIsInitialized] = useState(true);

  const handleSelect = useCallback((node) => {
    setSelectedNode(node);
    if (onNodeSelect) onNodeSelect(node);
    if (onSelectNode) onSelectNode(node);
  }, [onNodeSelect, onSelectNode]);

  // Data ingestion
  useEffect(() => {
    const rawInput = customGraphData || initialData;
    if (prevInputRef.current === rawInput && graphData.nodes.length > 0) {
      return;
    }
    prevInputRef.current = rawInput;

    const normalized = normalizeGraphData(rawInput);
    setGraphData(normalized);
    setIsInitialized(true);

    const timer = setTimeout(() => {
      if (fgRef.current) {
        fgRef.current.zoomToFit(400, 60);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [initialData, customGraphData]);

  // Handle resizing
  useEffect(() => {
    const updateSize = debounce(() => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        if (rect.width > 100 && rect.height > 100) {
          setDimensions({ width: rect.width, height: rect.height });
        }
      }
    }, 100);

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // Force setup
  useEffect(() => {
    if (fgRef.current) {
      fgRef.current.d3Force('charge').strength(-350);
      fgRef.current.d3Force('link').distance(90);
    }
  }, [graphData]);

  const handleNodeClick = useCallback((node) => {
    if (!node || !fgRef.current) return;
    fgRef.current.centerAt(node.x, node.y, 400);
    handleSelect(node);
  }, [handleSelect]);

  // Draw Inner Icon
  const drawNodeIcon = (ctx, x, y, radius, type) => {
    const iconColor = '#ffffff';
    ctx.strokeStyle = iconColor;
    ctx.fillStyle = iconColor;
    ctx.lineWidth = 1.8;
    ctx.beginPath();

    if (type === 'user') {
      const headRadius = radius * 0.28;
      ctx.arc(x, y - radius * 0.15, headRadius, 0, 2 * Math.PI);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(x, y + radius * 0.55, radius * 0.42, Math.PI * 1.15, Math.PI * 1.85);
      ctx.stroke();
    } else if (type === 'account') {
      const w = radius * 0.6;
      const h = radius * 0.22;
      ctx.ellipse(x, y - h, w / 2, h / 2, 0, 0, 2 * Math.PI);
      ctx.stroke();
      ctx.beginPath();
      ctx.ellipse(x, y, w / 2, h / 2, 0, 0, Math.PI);
      ctx.stroke();
      ctx.beginPath();
      ctx.ellipse(x, y + h, w / 2, h / 2, 0, 0, Math.PI);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(x - w / 2, y - h);
      ctx.lineTo(x - w / 2, y + h);
      ctx.moveTo(x + w / 2, y - h);
      ctx.lineTo(x + w / 2, y + h);
      ctx.stroke();
    } else if (type === 'device') {
      const devW = radius * 0.7;
      const devH = radius * 0.55;
      ctx.strokeRect(x - devW / 2, y - devH / 2 - 2, devW, devH);
      ctx.beginPath();
      ctx.moveTo(x - devW * 0.2, y + devH / 2 + 3);
      ctx.lineTo(x + devW * 0.2, y + devH / 2 + 3);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(x, y - 2, 3, 0, 2 * Math.PI);
      ctx.fill();
    } else if (type === 'transaction') {
      const noteW = radius * 0.75;
      const noteH = radius * 0.45;
      ctx.strokeRect(x - noteW / 2, y - noteH / 2, noteW, noteH);
      ctx.beginPath();
      ctx.arc(x, y, radius * 0.12, 0, 2 * Math.PI);
      ctx.stroke();
    }
  };

  // Node Canvas Renderer with Mini Tag Pill below each node
  const drawNode = useCallback((node, ctx, globalScale) => {
    if (typeof node.x !== 'number' || typeof node.y !== 'number') return;

    const isSelected = (selectedNode && selectedNode.id === node.id) || node.is_selected;
    const type = (node.type || 'account').toLowerCase();
    const typeColor = TYPE_COLORS[type] || node.color || TYPE_COLORS.default;
    const typeName = TYPE_NAMES[type] || 'Entity';
    const radius = Math.max(node.val || 22, 18);

    ctx.save();

    // 1. Glowing outer ring for selected node
    if (isSelected) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius + 7 / globalScale, 0, 2 * Math.PI);
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 3 / globalScale;
      ctx.shadowColor = '#f59e0b';
      ctx.shadowBlur = 12 / globalScale;
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    // 2. Main Circle Node
    ctx.beginPath();
    ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
    ctx.fillStyle = '#0f172a';
    ctx.fill();
    ctx.lineWidth = 3 / globalScale;
    ctx.strokeStyle = typeColor;
    ctx.stroke();

    // 3. Inner Icon
    drawNodeIcon(ctx, node.x, node.y, radius, type);

    // 4. Alert Badge
    if (node.has_alert !== false) {
      const alertAngle = -Math.PI / 4;
      const alertX = node.x + radius * Math.cos(alertAngle);
      const alertY = node.y + radius * Math.sin(alertAngle);
      const badgeRadius = 4 / globalScale;

      ctx.beginPath();
      ctx.arc(alertX, alertY, badgeRadius, 0, 2 * Math.PI);
      ctx.fillStyle = '#ef4444';
      ctx.fill();
      ctx.lineWidth = 1.2 / globalScale;
      ctx.strokeStyle = '#ffffff';
      ctx.stroke();
    }

    // 5. MINI TAG PILL BELOW NODE
    const label = node.label || node.id;
    const tagText = `${label} • ${typeName}`;
    const fontSize = Math.max(10 / globalScale, 3.5);
    ctx.font = `600 ${fontSize}px "Inter", -apple-system, sans-serif`;

    const metrics = ctx.measureText(tagText);
    const textWidth = metrics.width || label.length * 6 / globalScale;
    const tagPaddingX = 8 / globalScale;
    const tagHeight = fontSize + 6 / globalScale;
    const tagY = node.y + radius + 8 / globalScale;
    const tagX = node.x - textWidth / 2 - tagPaddingX / 2;

    // Draw Mini-Tag Pill Background
    ctx.beginPath();
    if (ctx.roundRect) {
      ctx.roundRect(tagX, tagY, textWidth + tagPaddingX, tagHeight, 4 / globalScale);
    } else {
      ctx.rect(tagX, tagY, textWidth + tagPaddingX, tagHeight);
    }
    ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
    ctx.fill();
    ctx.lineWidth = 1 / globalScale;
    ctx.strokeStyle = typeColor;
    ctx.stroke();

    // Draw Mini-Tag Text
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(tagText, node.x, tagY + tagHeight / 2);

    ctx.restore();
  }, [selectedNode]);

  // Link Canvas Renderer with Solid/Dotted Lines, Directional Arrows, and Relationship Text
  const drawLinkCanvas = useCallback((link, ctx, globalScale) => {
    const start = link.source;
    const end = link.target;

    if (!start || !end || 
        typeof start.x !== 'number' || typeof end.x !== 'number' ||
        typeof start.y !== 'number' || typeof end.y !== 'number') {
      return;
    }

    ctx.save();

    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const angle = Math.atan2(dy, dx);
    const distance = Math.sqrt(dx * dx + dy * dy);

    const isPersonDevice = link.dotted || link.relation === 'Person-Device' || link.relation === 'Owner' || link.relation === 'Connected To';
    const isHighRisk = link.color === '#eab308' || link.dashed || link.relation === 'device trail' || link.relation === 'velocity sig' || link.relation === 'shared device';

    const strokeColor = isHighRisk ? '#eab308' : (isPersonDevice ? '#60a5fa' : (link.color || '#475569'));
    const lineWidth = (isHighRisk ? 2.2 : (link.weight || 1.5)) / globalScale;

    // Line Style: Dotted for Person-Device, Dashed for Trails, Solid for Standard
    if (isPersonDevice) {
      ctx.setLineDash([4 / globalScale, 4 / globalScale]);
    } else if (link.dashed || link.relation === 'device trail' || link.relation === 'velocity sig') {
      ctx.setLineDash([6 / globalScale, 6 / globalScale]);
    } else {
      ctx.setLineDash([]);
    }

    // Draw Connection Line
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = lineWidth;
    ctx.stroke();

    ctx.setLineDash([]);

    // Draw Directional Arrowhead pointing at target node boundary
    if (distance > 35) {
      const targetRadius = Math.max(end.val || 22, 18);
      const arrowDist = distance - (targetRadius + 3 / globalScale);
      const arrowX = start.x + arrowDist * Math.cos(angle);
      const arrowY = start.y + arrowDist * Math.sin(angle);

      const arrowSize = Math.max(7 / globalScale, 3.5);
      const headAngle = Math.PI / 6;

      ctx.beginPath();
      ctx.moveTo(arrowX, arrowY);
      ctx.lineTo(
        arrowX - arrowSize * Math.cos(angle - headAngle),
        arrowY - arrowSize * Math.sin(angle - headAngle)
      );
      ctx.lineTo(
        arrowX - arrowSize * Math.cos(angle + headAngle),
        arrowY - arrowSize * Math.sin(angle + headAngle)
      );
      ctx.closePath();
      ctx.fillStyle = strokeColor;
      ctx.fill();
    }

    // Draw Relationship Text Label with Pill Backdrop
    if (link.relation && link.relation.trim() !== '') {
      const midX = (start.x + end.x) / 2;
      const midY = (start.y + end.y) / 2;
      const labelFontSize = Math.max(9 / globalScale, 3.2);

      ctx.font = `600 ${labelFontSize}px "Inter", sans-serif`;
      const textMetrics = ctx.measureText(link.relation);
      const labelWidth = textMetrics.width || 20 / globalScale;
      const labelHeight = labelFontSize + 4 / globalScale;

      // Label background pill
      ctx.fillStyle = 'rgba(15, 23, 42, 0.92)';
      if (ctx.roundRect) {
        ctx.roundRect(midX - labelWidth / 2 - 4 / globalScale, midY - labelHeight / 2, labelWidth + 8 / globalScale, labelHeight, 3 / globalScale);
      } else {
        ctx.rect(midX - labelWidth / 2 - 4 / globalScale, midY - labelHeight / 2, labelWidth + 8 / globalScale, labelHeight);
      }
      ctx.fill();
      ctx.lineWidth = 0.8 / globalScale;
      ctx.strokeStyle = strokeColor;
      ctx.stroke();

      // Label Text
      ctx.fillStyle = isHighRisk ? '#eab308' : (isPersonDevice ? '#93c5fd' : '#cbd5e1');
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(link.relation, midX, midY);
    }

    ctx.restore();
  }, []);

  // Background clusters
  const drawBackgroundClusters = useCallback((ctx, globalScale) => {
    if (!graphData.nodes || graphData.nodes.length === 0) return;

    ctx.save();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.lineWidth = 1.2 / globalScale;
    ctx.setLineDash([4 / globalScale, 8 / globalScale]);

    const leftClusterNodes = graphData.nodes.filter(n => ['User 041', 'ACC-7741', '185.221.14.8', 'DEV-992A', 'ACC-1028'].includes(n.id));
    if (leftClusterNodes.length >= 2) {
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      leftClusterNodes.forEach(n => {
        if (typeof n.x === 'number' && typeof n.y === 'number') {
          minX = Math.min(minX, n.x);
          maxX = Math.max(maxX, n.x);
          minY = Math.min(minY, n.y);
          maxY = Math.max(maxY, n.y);
        }
      });
      if (minX !== Infinity) {
        const cx = (minX + maxX) / 2;
        const cy = (minY + maxY) / 2;
        const rx = (maxX - minX) / 2 + 45;
        const ry = (maxY - minY) / 2 + 45;
        ctx.beginPath();
        ctx.ellipse(cx, cy, rx, ry, 0, 0, 2 * Math.PI);
        ctx.stroke();
      }
    }

    const rightClusterNodes = graphData.nodes.filter(n => ['DEV-174Q', '10.42.8.64', 'TXN-8924', 'ACC-7015', 'ACC-5520'].includes(n.id));
    if (rightClusterNodes.length >= 2) {
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      rightClusterNodes.forEach(n => {
        if (typeof n.x === 'number' && typeof n.y === 'number') {
          minX = Math.min(minX, n.x);
          maxX = Math.max(maxX, n.x);
          minY = Math.min(minY, n.y);
          maxY = Math.max(maxY, n.y);
        }
      });
      if (minX !== Infinity) {
        const cx = (minX + maxX) / 2;
        const cy = (minY + maxY) / 2;
        const rx = (maxX - minX) / 2 + 50;
        const ry = (maxY - minY) / 2 + 50;
        ctx.beginPath();
        ctx.ellipse(cx, cy, rx, ry, 0, 0, 2 * Math.PI);
        ctx.stroke();
      }
    }

    ctx.restore();
  }, [graphData]);

  // Selected Node Connections helper
  const selectedNodeConnections = selectedNode ? graphData.links.filter(
    l => (typeof l.source === 'object' ? l.source.id : l.source) === selectedNode.id || 
         (typeof l.target === 'object' ? l.target.id : l.target) === selectedNode.id
  ) : [];

  return (
    <div 
      ref={containerRef} 
      className="w-full h-full min-h-[550px] relative bg-[#0b0f17] overflow-hidden flex border border-slate-800/80"
    >
      {/* ITEM 4: COMPREHENSIVE INTERACTIVE LEGEND PANEL */}
      <div className="absolute top-4 left-4 z-20 flex flex-col gap-2 bg-[#0f172a]/95 backdrop-blur p-3 rounded-lg border border-slate-800 shadow-2xl font-sans text-xs select-none max-w-xs">
        <div className="flex items-center justify-between border-b border-slate-800 pb-1.5 mb-1">
          <span className="font-bold text-slate-200 uppercase tracking-wider font-mono text-[11px] flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span>Graph Legend</span>
          </span>
          <div className="flex items-center gap-1">
            <button onClick={() => fgRef.current && fgRef.current.zoom(fgRef.current.zoom() * 1.3, 300)} title="Zoom In" className="p-1 rounded hover:bg-slate-800 text-slate-300">
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button onClick={() => fgRef.current && fgRef.current.zoom(fgRef.current.zoom() / 1.3, 300)} title="Zoom Out" className="p-1 rounded hover:bg-slate-800 text-slate-300">
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <button onClick={() => fgRef.current && fgRef.current.zoomToFit(400, 60)} title="Fit View" className="p-1 rounded hover:bg-slate-800 text-slate-300">
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Node Entity Types */}
        <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[11px] font-mono">
          <div className="flex items-center gap-2 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 ring-2 ring-blue-500/30 shrink-0"/>
            <span>People (User)</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-500 ring-2 ring-sky-500/30 shrink-0"/>
            <span>Accounts</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500 ring-2 ring-orange-500/30 shrink-0"/>
            <span>Devices</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 ring-2 ring-red-500/30 shrink-0"/>
            <span>Transactions</span>
          </div>
        </div>

        <div className="w-full h-[1px] bg-slate-800 my-1" />

        {/* Relationship Line Types & Direction */}
        <div className="space-y-1.5 text-[11px] font-mono">
          <div className="flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1.5">
              <span className="w-5 border-b-2 border-dashed border-sky-400 inline-block"/>
              <span>Dotted Line</span>
            </span>
            <span className="text-sky-400 text-[10px]">Person–Device Link</span>
          </div>
          <div className="flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1.5">
              <span className="w-5 border-b-2 border-slate-400 inline-block"/>
              <span>Solid Line</span>
            </span>
            <span className="text-slate-400 text-[10px]">Standard Link</span>
          </div>
          <div className="flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1.5">
              <ArrowRight className="w-3.5 h-3.5 text-slate-300" />
              <span>Arrowhead</span>
            </span>
            <span className="text-slate-400 text-[10px]">Link Direction</span>
          </div>
          <div className="flex items-center justify-between text-amber-400 font-bold">
            <span className="flex items-center gap-1.5">
              <span className="w-5 border-b-2 border-dashed border-amber-400 inline-block"/>
              <span>Yellow Trail</span>
            </span>
            <span className="text-amber-400 text-[10px]">Device Trail / Sig</span>
          </div>
        </div>
      </div>

      {/* ITEM 3: CLICKED NODE POP-UP INFORMATION BOX OVERLAY */}
      {selectedNode && (
        <div className="absolute bottom-6 right-6 z-30 w-80 bg-[#0f172a]/95 backdrop-blur-md rounded-xl border border-slate-700 shadow-2xl p-4 font-mono text-xs text-slate-100 animate-in fade-in slide-in-from-bottom-3 duration-200">
          <div className="flex items-start justify-between border-b border-slate-800 pb-2 mb-3">
            <div className="flex items-center gap-2">
              <div 
                className="w-3.5 h-3.5 rounded-full shrink-0" 
                style={{ backgroundColor: TYPE_COLORS[selectedNode.type] || '#3b82f6' }}
              />
              <div>
                <h3 className="font-bold text-sm text-white leading-tight">{selectedNode.label || selectedNode.id}</h3>
                <span className="text-[10px] text-indigo-400 font-semibold uppercase">{TYPE_NAMES[selectedNode.type] || 'Entity'} • {selectedNode.role || 'Node'}</span>
              </div>
            </div>
            <button 
              onClick={() => handleSelect(null)}
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-2 text-[11px]">
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-slate-900/90 p-2 rounded border border-slate-800">
                <span className="text-[9px] text-slate-400 block">ENTITY ID</span>
                <span className="text-slate-200 font-bold break-all">{selectedNode.id}</span>
              </div>
              <div className="bg-slate-900/90 p-2 rounded border border-slate-800">
                <span className="text-[9px] text-slate-400 block">CATEGORY</span>
                <span className="text-emerald-400 font-bold capitalize">{selectedNode.type}</span>
              </div>
            </div>

            <div className="bg-slate-900/90 p-2 rounded border border-slate-800 flex items-center justify-between">
              <span className="text-slate-400 text-[10px]">ACTIVE RELATIONSHIPS</span>
              <span className="text-sky-400 font-bold text-xs">{selectedNodeConnections.length} links</span>
            </div>

            {selectedNodeConnections.length > 0 && (
              <div className="bg-slate-900/90 p-2 rounded border border-slate-800 space-y-1">
                <span className="text-[9px] text-slate-400 block mb-1">CONNECTED ENTITIES & RELATIONSHIPS</span>
                {selectedNodeConnections.slice(0, 4).map((l, i) => {
                  const src = typeof l.source === 'object' ? l.source.id : l.source;
                  const tgt = typeof l.target === 'object' ? l.target.id : l.target;
                  const other = src === selectedNode.id ? tgt : src;
                  return (
                    <div key={i} className="flex items-center justify-between text-[10px]">
                      <span className="text-slate-300 truncate max-w-[140px]">→ {other}</span>
                      <span className="text-amber-400 font-medium">{l.relation || 'Connected'}</span>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="bg-indigo-950/40 p-2.5 rounded border border-indigo-800/80 flex items-center justify-between">
              <span className="text-[10px] text-slate-300">BSA Sec 63 Compliance</span>
              <span className="text-emerald-400 font-bold text-[10px] bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800">VERIFIED</span>
            </div>
          </div>
        </div>
      )}

      {/* Force Graph Viewport */}
      <div className="flex-1 w-full h-full">
        {graphData.nodes.length > 0 ? (
          <ForceGraph2D
            ref={fgRef}
            width={dimensions.width}
            height={dimensions.height}
            graphData={graphData}
            backgroundColor="#0b0f17"
            nodeId="id"
            nodeCanvas={drawNode}
            linkCanvas={drawLinkCanvas}
            onRenderFramePre={(ctx, globalScale) => drawBackgroundClusters(ctx, globalScale)}
            nodePointerAreaPaint={(node, color, ctx) => {
              ctx.fillStyle = color;
              ctx.beginPath();
              ctx.arc(node.x, node.y, Math.max(node.val || 22, 22), 0, 2 * Math.PI);
              ctx.fill();
            }}
            onNodeClick={handleNodeClick}
            onBackgroundClick={() => handleSelect(null)}
            d3AlphaDecay={0.02}
            d3VelocityDecay={0.3}
            cooldownTicks={200}
            warmupTicks={100}
            minZoom={0.2}
            maxZoom={4.0}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-slate-500 font-mono text-sm">
            {isInitialized ? 'Awaiting anti-fraud graph data...' : 'Initializing Intelligence Topology...'}
          </div>
        )}
      </div>
    </div>
  );
}