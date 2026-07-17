"use client";

/**
 * The transmission network as an interactive star atlas.
 *
 * Canvas force-directed graph of confident person-level student→teacher
 * edges (GET /transmission-graph). Design notes:
 * - The plate is deliberately dark (a night-sky map inside the cream reading
 *   room). Imams are gold suns; narrators wear a validated 5-step blue
 *   ordinal ramp by ṭabaqa (early = luminous, late = deep azure); undated
 *   narrators recede to gray-green. Palette validated with the dataviz
 *   six-checks script against surface #121c17 (ordinal ramp: all PASS; gold
 *   vs ramp extremes: CVD ΔE 54.3, contrast ≥ 3:1).
 * - Node size = distinct hadiths; edge weight = distinct shared hadiths —
 *   the same semantics as /narrators/{id}/transmission-edges.
 * - Uncertainty honesty: only confident (resolved / via_collective) mentions
 *   are drawn at all, and ṭabaqa values are labeled as estimates.
 * - Two layouts: Constellation (free force) and Ṭabaqāt (time flows down
 *   from the earliest generations to the compilers).
 * - Everything hover shows is also reachable in the table view below.
 */

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { getTransmissionEdgeEvidence, getTransmissionGraph } from "@/lib/api/books";
import type {
  TransmissionEdgeEvidenceRead,
  TransmissionGraphEdge,
  TransmissionGraphNode,
  TransmissionGraphRead,
} from "@/lib/api/types";
import { formatArabicText } from "@/lib/arabic";
import { amiri } from "@/lib/fonts";

/* ------------------------------------------------------------------ */
/* Palette (validated — see component docblock)                        */
/* ------------------------------------------------------------------ */

const PLATE_BG = "#121c17";
const PLATE_BG_CENTER = "#17251e";
const IMAM_GOLD = "#c98500";
const IMAM_GOLD_BRIGHT = "#e8b54a";
const ERA_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf"];
const UNDATED = "#6f7d72";
const INK_PRIMARY = "#ece7d6";
const INK_SECONDARY = "#9aa695";
const EDGE_RGB = "214, 224, 210";
const HIGHLIGHT = "#e8b54a";

const ERA_LABELS = ["Ṭabaqa ≤ 4", "Ṭabaqa 5–6", "Ṭabaqa 7–8", "Ṭabaqa 9–10", "Ṭabaqa 11+"];
const MAX_GEN = 13;

// Evidence-quality colors (validated status hue on the dark plate).
const QUALITY_CONTRADICTED = "#d03b3b"; // critical — 3.62:1 on #121c17
const QUALITY_CORROBORATED = "#1baf7a"; // good — reads distinct from the blue ramp

function tabaqaBandY(generation: number, height: number): number {
  return height * 0.08 + (generation / MAX_GEN) * height * 0.84;
}

function eraIndex(generation: number | null): number | null {
  if (generation === null) return null;
  if (generation <= 4) return 0;
  if (generation <= 6) return 1;
  if (generation <= 8) return 2;
  if (generation <= 10) return 3;
  return 4;
}

function nodeColor(node: TransmissionGraphNode): string {
  if (node.kind === "imam") return IMAM_GOLD;
  const era = eraIndex(node.generation);
  return era === null ? UNDATED : ERA_RAMP[era];
}

/* ------------------------------------------------------------------ */
/* Arabic search normalisation (display strings stay untouched)        */
/* ------------------------------------------------------------------ */

function normaliseArabic(text: string): string {
  return text
    .replace(/[ً-ٰٟـ]/g, "")
    .replace(/[آأإ]/g, "ا")
    .replace(/[یى]/g, "ي")
    .replace(/ک/g, "ك")
    .replace(/\s+/g, " ")
    .trim();
}

/* ------------------------------------------------------------------ */
/* Simulation types                                                    */
/* ------------------------------------------------------------------ */

interface SimNode extends TransmissionGraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  color: string;
  visible: boolean;
}

interface SimEdge extends TransmissionGraphEdge {
  a: SimNode;
  b: SimNode;
  visible: boolean;
}

type LayoutMode = "constellation" | "tabaqat";

interface SimState {
  nodes: SimNode[];
  edges: SimEdge[];
  byId: Map<number, SimNode>;
  neighbors: Map<number, Set<number>>;
  alpha: number;
  tx: number;
  ty: number;
  scale: number;
  targetTx: number | null;
  targetTy: number | null;
  targetScale: number;
  width: number;
  height: number;
  fadeIn: number;
  reducedMotion: boolean;
  refitPending: boolean;
}

/** Deterministic pseudo-random from a node id, so reloads look the same. */
function hashUnit(id: number, salt: number): number {
  let h = (id * 2654435761 + salt * 40503) >>> 0;
  h ^= h >> 13;
  h = (h * 2246822519) >>> 0;
  return ((h >>> 8) % 100000) / 100000;
}

/* ------------------------------------------------------------------ */
/* Physics + visibility — plain mutable functions on the sim object.   */
/* Deliberately outside the component: this is a simulation engine,    */
/* not React state, and hooks must not mutate ref-reachable objects.   */
/* ------------------------------------------------------------------ */

function applyWeightFilter(sim: SimState, minWeight: number): void {
  const touched = new Set<number>();
  for (const e of sim.edges) {
    e.visible = e.count >= minWeight;
    if (e.visible) {
      touched.add(e.source);
      touched.add(e.target);
    }
  }
  for (const n of sim.nodes) n.visible = touched.has(n.id);
  sim.alpha = Math.max(sim.alpha, 0.6);
}

/** Merge quality verdicts from a freshly fetched graph into the live edges by
 * (source,target) — deliberately does NOT rebuild the sim, so the layout the
 * user is looking at is preserved. */
function applyEdgeQuality(sim: SimState, edges: TransmissionGraphEdge[]): void {
  const byKey = new Map<string, TransmissionGraphEdge>();
  for (const e of edges) byKey.set(`${e.source}->${e.target}`, e);
  for (const e of sim.edges) {
    const q = byKey.get(`${e.source}->${e.target}`);
    e.quality = q?.quality ?? null;
    e.gen_violation = q?.gen_violation ?? null;
  }
  sim.alpha = Math.max(sim.alpha, 0.05);
}

function clearEdgeQuality(sim: SimState): void {
  for (const e of sim.edges) {
    e.quality = null;
    e.gen_violation = null;
  }
  sim.alpha = Math.max(sim.alpha, 0.05);
}

function tickSim(sim: SimState, mode: LayoutMode, dragging: SimNode | null): void {
  const nodes = sim.nodes.filter((n) => n.visible);
  if (!nodes.length) return;
  const alpha = sim.alpha;
  const w = sim.width;
  const h = sim.height;

  // Repulsion (O(n²) with a cutoff — ≤500 visible nodes stays cheap).
  const cutoff = 320;
  const cutoffSq = cutoff * cutoff;
  for (let i = 0; i < nodes.length; i++) {
    const a = nodes[i];
    for (let j = i + 1; j < nodes.length; j++) {
      const b = nodes[j];
      const dx = a.x - b.x;
      const dy = a.y - b.y;
      let dSq = dx * dx + dy * dy;
      if (dSq > cutoffSq) continue;
      if (dSq < 4) dSq = 4;
      const d = Math.sqrt(dSq);
      const f = ((150 * (a.r + b.r)) / dSq) * alpha;
      const fx = (dx / d) * f;
      const fy = (dy / d) * f;
      a.vx += fx;
      a.vy += fy;
      b.vx -= fx;
      b.vy -= fy;
    }
  }

  // Edge springs — heavier edges pull harder and sit shorter.
  for (const e of sim.edges) {
    if (!e.visible) continue;
    const dx = e.b.x - e.a.x;
    const dy = e.b.y - e.a.y;
    const d = Math.max(1, Math.sqrt(dx * dx + dy * dy));
    const rest = Math.max(46, 96 - 9 * Math.log2(1 + e.count));
    const k = Math.min(0.07, 0.018 + 0.012 * Math.log2(1 + e.count));
    const f = (d - rest) * k * alpha;
    const fx = (dx / d) * f;
    const fy = (dy / d) * f;
    const ma = e.b.r / (e.a.r + e.b.r);
    const mb = 1 - ma;
    e.a.vx += fx * ma;
    e.a.vy += fy * ma;
    e.b.vx -= fx * mb;
    e.b.vy -= fy * mb;
  }

  // Gravity / ṭabaqāt bands.
  for (const n of nodes) {
    // In ṭabaqāt mode the bands should spread wide, so x-gravity is gentler.
    n.vx += (w / 2 - n.x) * (mode === "tabaqat" ? 0.004 : 0.009) * alpha;
    if (mode === "tabaqat") {
      const gen = n.generation ?? MAX_GEN; // undated sinks to the bottom band
      n.vy += (tabaqaBandY(gen, h) - n.y) * 0.14 * alpha;
    } else {
      n.vy += (h / 2 - n.y) * 0.011 * alpha;
    }
  }

  // Integrate with a hard speed limit — an unclamped spring/repulsion
  // feedback can overflow positions to Infinity/NaN, which then kills the
  // canvas render (createRadialGradient throws on non-finite coordinates).
  const maxV = 24;
  for (const n of nodes) {
    if (n === dragging) {
      n.vx = 0;
      n.vy = 0;
      continue;
    }
    n.vx *= 0.58;
    n.vy *= 0.58;
    if (!Number.isFinite(n.vx) || !Number.isFinite(n.vy)) {
      n.vx = 0;
      n.vy = 0;
    }
    if (n.vx > maxV) n.vx = maxV;
    else if (n.vx < -maxV) n.vx = -maxV;
    if (n.vy > maxV) n.vy = maxV;
    else if (n.vy < -maxV) n.vy = -maxV;
    n.x += n.vx;
    n.y += n.vy;
    if (!Number.isFinite(n.x) || !Number.isFinite(n.y)) {
      n.x = w / 2 + (hashUnit(n.id, 3) - 0.5) * 200;
      n.y = h / 2 + (hashUnit(n.id, 4) - 0.5) * 200;
      n.vx = 0;
      n.vy = 0;
    }
  }
  sim.alpha = Math.max(0, alpha * 0.985 - 0.0004);
}

/** One animation frame: physics, entrance fade, and camera easing. */
function advanceFrame(sim: SimState, mode: LayoutMode, dragging: SimNode | null): void {
  if (sim.reducedMotion && sim.alpha > 0.02) {
    // Settle instantly rather than animating the layout.
    let guard = 0;
    while (sim.alpha > 0.02 && guard++ < 400) tickSim(sim, mode, dragging);
  } else if (sim.alpha > 0.02) {
    tickSim(sim, mode, dragging);
  }
  if (!sim.reducedMotion) sim.fadeIn = Math.min(1, sim.fadeIn + 0.05);
  // After a layout morph settles, re-frame the camera on the result.
  if (sim.refitPending && sim.alpha < 0.1) {
    sim.refitPending = false;
    fitCamera(sim);
  }
  // Smooth fly-to when search picks a node.
  if (sim.targetTx !== null && sim.targetTy !== null) {
    sim.tx += (sim.targetTx - sim.tx) * 0.14;
    sim.ty += (sim.targetTy - sim.ty) * 0.14;
    sim.scale += (sim.targetScale - sim.scale) * 0.14;
    if (Math.abs(sim.targetTx - sim.tx) + Math.abs(sim.targetTy - sim.ty) < 1) {
      sim.targetTx = null;
      sim.targetTy = null;
    }
  }
}

function buildSim(sim: SimState, graph: TransmissionGraphRead, reducedMotion: boolean): void {
  sim.reducedMotion = reducedMotion;
  const maxCount = Math.max(1, ...graph.nodes.map((n) => n.hadith_count));
  const w = sim.width || 900;
  const h = sim.height || 640;
  sim.nodes = graph.nodes.map((n) => {
    const angle = hashUnit(n.id, 1) * Math.PI * 2;
    const radius = Math.sqrt(hashUnit(n.id, 2)) * Math.min(w, h) * 0.38;
    return {
      ...n,
      x: w / 2 + Math.cos(angle) * radius,
      y: h / 2 + Math.sin(angle) * radius,
      vx: 0,
      vy: 0,
      r: 3.2 + 13 * Math.sqrt(n.hadith_count / maxCount),
      color: nodeColor(n),
      visible: true,
    };
  });
  sim.byId = new Map(sim.nodes.map((n) => [n.id, n]));
  sim.edges = graph.edges
    .map((e) => ({
      ...e,
      a: sim.byId.get(e.source)!,
      b: sim.byId.get(e.target)!,
      visible: true,
    }))
    .filter((e) => e.a && e.b);
  sim.neighbors = new Map();
  for (const e of sim.edges) {
    if (!sim.neighbors.has(e.source)) sim.neighbors.set(e.source, new Set());
    if (!sim.neighbors.has(e.target)) sim.neighbors.set(e.target, new Set());
    sim.neighbors.get(e.source)!.add(e.target);
    sim.neighbors.get(e.target)!.add(e.source);
  }
  sim.alpha = 1;
  sim.fadeIn = 0.35; // first paint is already presentable even at 1 fps
  sim.scale = 1;
  sim.tx = 0;
  sim.ty = 0;
  sim.targetScale = 1;
  sim.refitPending = false;
}

function resizeSim(sim: SimState, width: number, height: number): void {
  sim.width = width;
  sim.height = height;
  sim.alpha = Math.max(sim.alpha, 0.2);
}

/** Frame the camera on the visible nodes, whatever the physics decided. */
function fitCamera(sim: SimState, padding = 70): void {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const n of sim.nodes) {
    if (!n.visible || !Number.isFinite(n.x) || !Number.isFinite(n.y)) continue;
    if (n.x < minX) minX = n.x;
    if (n.y < minY) minY = n.y;
    if (n.x > maxX) maxX = n.x;
    if (n.y > maxY) maxY = n.y;
  }
  if (!Number.isFinite(minX) || maxX - minX < 1 || maxY - minY < 1) return;
  const scale = Math.min(
    1.25,
    (sim.width - padding * 2) / (maxX - minX),
    (sim.height - padding * 2) / (maxY - minY)
  );
  sim.scale = scale;
  sim.targetScale = scale;
  sim.tx = sim.width / 2 - ((minX + maxX) / 2) * scale;
  sim.ty = sim.height / 2 - ((minY + maxY) / 2) * scale;
  sim.targetTx = null;
  sim.targetTy = null;
}

/** Settle the layout synchronously so the map appears already formed —
 * nobody should watch the physics wobble for its first three seconds. */
function warmupSim(sim: SimState, mode: LayoutMode, ticks: number): void {
  sim.alpha = 1;
  for (let i = 0; i < ticks && sim.alpha > 0.02; i++) tickSim(sim, mode, null);
  sim.alpha = 0.15; // a breath of residual motion, not a boil
  fitCamera(sim);
}

function panCamera(sim: SimState, dx: number, dy: number): void {
  sim.tx += dx;
  sim.ty += dy;
  sim.targetTx = null;
  sim.targetTy = null;
}

function zoomCamera(sim: SimState, mx: number, my: number, factor: number): void {
  const next = Math.min(6, Math.max(0.2, sim.scale * factor));
  // Zoom around the cursor.
  sim.tx = mx - ((mx - sim.tx) / sim.scale) * next;
  sim.ty = my - ((my - sim.ty) / sim.scale) * next;
  sim.scale = next;
  sim.targetScale = next;
  sim.targetTx = null;
  sim.targetTy = null;
}

function dragNodeTo(sim: SimState, node: SimNode, x: number, y: number): void {
  node.x = x;
  node.y = y;
  sim.alpha = Math.max(sim.alpha, 0.22);
}

function bumpAlpha(sim: SimState, value: number): void {
  sim.alpha = Math.max(sim.alpha, value);
}

function flyCameraTo(sim: SimState, node: SimNode): void {
  const targetScale = Math.max(sim.scale, 1.6);
  sim.targetScale = targetScale;
  sim.targetTx = sim.width / 2 - node.x * targetScale;
  sim.targetTy = sim.height / 2 - node.y * targetScale;
}

function resetCamera(sim: SimState): void {
  fitCamera(sim);
}

const numberFormat = new Intl.NumberFormat("en-US");

function formatComputedAt(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

export function TransmissionGraphClient() {
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);

  const [graph, setGraph] = useState<TransmissionGraphRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const searchParams = useSearchParams();
  const [minWeight, setMinWeight] = useState(3);
  // useSearchParams is SSR-consistent, so seeding state from it can't cause a
  // hydration mismatch the way window.location would.
  const [layout, setLayout] = useState<LayoutMode>(
    searchParams.get("layout") === "tabaqat" ? "tabaqat" : "constellation"
  );
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [qualityOn, setQualityOn] = useState(searchParams.get("quality") === "1");
  const [qualityLoading, setQualityLoading] = useState(false);
  const [evidence, setEvidence] = useState<{
    source: number;
    target: number;
    label: string;
    data: TransmissionEdgeEvidenceRead | null;
  } | null>(null);

  // Mutable sim state lives in refs — the render loop must never re-create
  // React state 60 times a second.
  const simRef = useRef<SimState>({
    nodes: [],
    edges: [],
    byId: new Map(),
    neighbors: new Map(),
    alpha: 0,
    tx: 0,
    ty: 0,
    scale: 1,
    targetTx: null,
    targetTy: null,
    targetScale: 1,
    width: 0,
    height: 0,
    fadeIn: 0,
    reducedMotion: false,
    refitPending: false,
  });
  const interactionRef = useRef<{
    dragging: SimNode | null;
    panning: boolean;
    moved: number;
    lastX: number;
    lastY: number;
  }>({ dragging: null, panning: false, moved: 0, lastX: 0, lastY: 0 });
  const hoveredRef = useRef<SimNode | null>(null);
  const selectedRef = useRef<SimNode | null>(null);
  const layoutRef = useRef<LayoutMode>("constellation");
  const qualityOnRef = useRef(false);

  /* ---------------------------- data ----------------------------- */

  useEffect(() => {
    let cancelled = false;
    getTransmissionGraph({ minCount: 2, maxNodes: 500 })
      .then((data) => {
        if (!cancelled) setGraph(data);
      })
      .catch(() => {
        if (!cancelled) setError("The graph API is not reachable. Is the backend running?");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  /* ------------------------- sim building ------------------------ */

  const builtGraphRef = useRef<TransmissionGraphRead | null>(null);
  const focusConsumedRef = useRef(false);
  useEffect(() => {
    if (!graph) return;
    const sim = simRef.current;
    const fresh = builtGraphRef.current !== graph;
    if (fresh) {
      const reducedMotion =
        typeof window !== "undefined" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      buildSim(sim, graph, reducedMotion);
      builtGraphRef.current = graph;
    }
    const layoutChanged = layoutRef.current !== layout;
    layoutRef.current = layout;
    applyWeightFilter(sim, minWeight);
    if (fresh) {
      // First paint shows a formed constellation, not a cold boil.
      warmupSim(sim, layout, 260);
      // Consume ?focus=<personId> / ?narrator=<narratorId> once — deep links
      // from narrator pages fly to and select the matching node.
      if (!focusConsumedRef.current) {
        focusConsumedRef.current = true;
        const focusPerson = Number(searchParams.get("focus"));
        const focusNarrator = Number(searchParams.get("narrator"));
        const target = sim.nodes.find(
          (n) =>
            (focusPerson && (n.id === focusPerson || n.merged_person_ids.includes(focusPerson))) ||
            (focusNarrator && n.narrator_id === focusNarrator)
        );
        if (target && target.visible) {
          selectedRef.current = target;
          setSelectedId(target.id);
          flyCameraTo(sim, target);
        }
      }
    } else if (layoutChanged) {
      // Let the morph play out, then re-frame on the new shape.
      sim.refitPending = true;
    }
  }, [minWeight, layout, graph, searchParams]);

  /* ------------------------ quality overlay ---------------------- */

  const qualityGraphRef = useRef<TransmissionGraphRead | null>(null);
  useEffect(() => {
    qualityOnRef.current = qualityOn;
    if (!qualityOn) {
      clearEdgeQuality(simRef.current);
      return;
    }
    // Reuse a cached quality fetch when the base graph is unchanged.
    if (qualityGraphRef.current && qualityGraphRef.current === graph) {
      return;
    }
    let cancelled = false;
    setQualityLoading(true);
    getTransmissionGraph({ minCount: 2, maxNodes: 500, quality: true })
      .then((data) => {
        if (cancelled) return;
        applyEdgeQuality(simRef.current, data.edges);
        qualityGraphRef.current = graph;
      })
      .finally(() => {
        if (!cancelled) setQualityLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [qualityOn, graph]);

  /* --------------------------- evidence -------------------------- */

  useEffect(() => {
    if (!evidence || evidence.data !== null) return;
    let cancelled = false;
    getTransmissionEdgeEvidence({
      sourcePersonId: evidence.source,
      targetPersonId: evidence.target,
      limit: 25,
    })
      .then((data) => {
        if (!cancelled) setEvidence((cur) => (cur ? { ...cur, data } : cur));
      })
      .catch(() => {
        if (!cancelled) setEvidence((cur) => (cur ? { ...cur, data: { source_person_id: cur.source, target_person_id: cur.target, source_book_id: "11005", total: 0, items: [] } } : cur));
      });
    return () => {
      cancelled = true;
    };
  }, [evidence]);

  /* -------------------------- rendering -------------------------- */

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const sim = simRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const { width: w, height: h } = sim;

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    // The plate: deep green-ink with a soft center vignette.
    const grad = ctx.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, Math.max(w, h) * 0.75);
    grad.addColorStop(0, PLATE_BG_CENTER);
    grad.addColorStop(1, PLATE_BG);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    ctx.translate(sim.tx, sim.ty);
    ctx.scale(sim.scale, sim.scale);

    // Ṭabaqāt mode: hairline generation rules under the data.
    if (layoutRef.current === "tabaqat") {
      ctx.strokeStyle = "rgba(236, 231, 214, 0.055)";
      ctx.lineWidth = 1 / sim.scale;
      for (let gen = 0; gen <= MAX_GEN; gen++) {
        const y = tabaqaBandY(gen, h);
        ctx.beginPath();
        ctx.moveTo(-20000, y);
        ctx.lineTo(20000, y);
        ctx.stroke();
      }
    }

    const hovered = hoveredRef.current;
    const selected = selectedRef.current;
    const focus = hovered ?? selected;
    const focusNeighbors = focus ? sim.neighbors.get(focus.id) ?? new Set() : null;
    const globalFade = sim.reducedMotion ? 1 : Math.min(1, sim.fadeIn);
    const qualityOn = qualityOnRef.current;

    const maxEdge = Math.max(1, ...sim.edges.map((e) => (e.visible ? e.count : 1)));

    /* edges */
    for (const e of sim.edges) {
      if (!e.visible) continue;
      if (
        !Number.isFinite(e.a.x) ||
        !Number.isFinite(e.a.y) ||
        !Number.isFinite(e.b.x) ||
        !Number.isFinite(e.b.y)
      ) {
        continue;
      }
      const t = Math.log(1 + e.count) / Math.log(1 + maxEdge);
      const isFocusEdge =
        focus !== null && (e.source === focus.id || e.target === focus.id);
      // Quality overlay tints edges by their Mu'jam verdict when enabled — but
      // the focus highlight always wins so hovering a node stays legible.
      // A generation-impossible edge is as strong a red flag as a contradicted one.
      const q = qualityOn ? (e.gen_violation ? "contradicted" : e.quality) : null;
      ctx.setLineDash([]);
      if (focus && !isFocusEdge) {
        ctx.strokeStyle = `rgba(${EDGE_RGB}, ${(0.025 + 0.1 * t) * globalFade})`;
        ctx.lineWidth = 0.5 + 1.6 * t;
      } else if (isFocusEdge) {
        ctx.strokeStyle = `rgba(232, 181, 74, ${(0.55 + 0.35 * t) * globalFade})`;
        ctx.lineWidth = 1 + 2 * t;
      } else if (q === "contradicted") {
        ctx.strokeStyle = `rgba(208, 59, 59, ${(0.6 + 0.3 * t) * globalFade})`;
        ctx.lineWidth = 1 + 2 * t;
      } else if (q === "corroborated") {
        ctx.strokeStyle = `rgba(27, 175, 122, ${(0.45 + 0.3 * t) * globalFade})`;
        ctx.lineWidth = 0.8 + 1.9 * t;
      } else if (qualityOn && (q === "under_documented" || q === "no_mujam")) {
        ctx.strokeStyle = `rgba(${EDGE_RGB}, ${(0.03 + 0.14 * t) * globalFade})`;
        ctx.lineWidth = 0.6 + 1.4 * t;
        ctx.setLineDash([4, 4]);
      } else {
        ctx.strokeStyle = `rgba(${EDGE_RGB}, ${(0.05 + 0.3 * t) * globalFade})`;
        ctx.lineWidth = 0.6 + 1.9 * t;
      }
      ctx.beginPath();
      ctx.moveTo(e.a.x, e.a.y);
      ctx.lineTo(e.b.x, e.b.y);
      ctx.stroke();
      ctx.setLineDash([]);
      // Direction chevron (student → teacher) on focused edges only.
      if (isFocusEdge && sim.scale > 0.5) {
        const mx = e.a.x + (e.b.x - e.a.x) * 0.58;
        const my = e.a.y + (e.b.y - e.a.y) * 0.58;
        const ang = Math.atan2(e.b.y - e.a.y, e.b.x - e.a.x);
        const s = 4.5 / Math.sqrt(sim.scale);
        ctx.fillStyle = `rgba(232, 181, 74, ${0.9 * globalFade})`;
        ctx.beginPath();
        ctx.moveTo(mx + Math.cos(ang) * s, my + Math.sin(ang) * s);
        ctx.lineTo(mx + Math.cos(ang + 2.5) * s, my + Math.sin(ang + 2.5) * s);
        ctx.lineTo(mx + Math.cos(ang - 2.5) * s, my + Math.sin(ang - 2.5) * s);
        ctx.closePath();
        ctx.fill();
      }
    }

    /* nodes */
    const labelIds = new Set<number>();
    const visibleSorted = sim.nodes.filter((n) => n.visible);
    visibleSorted
      .slice()
      .sort((a, b) => b.hadith_count - a.hadith_count)
      .slice(0, 8)
      .forEach((n) => labelIds.add(n.id));
    for (const n of visibleSorted) if (n.kind === "imam") labelIds.add(n.id);
    if (focus) {
      labelIds.add(focus.id);
      focusNeighbors?.forEach((id) => labelIds.add(id));
    }

    for (const n of visibleSorted) {
      if (!Number.isFinite(n.x) || !Number.isFinite(n.y)) continue;
      const dimmed = focus !== null && n.id !== focus.id && !focusNeighbors?.has(n.id);
      const alpha = (dimmed ? 0.18 : 1) * globalFade;
      ctx.globalAlpha = alpha;

      if (n.kind === "imam" && !dimmed) {
        const glow = ctx.createRadialGradient(n.x, n.y, n.r * 0.4, n.x, n.y, n.r * 3.2);
        glow.addColorStop(0, "rgba(232, 181, 74, 0.35)");
        glow.addColorStop(1, "rgba(232, 181, 74, 0)");
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r * 3.2, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.fillStyle = n.color;
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
      ctx.fill();
      // 1px plate-colored ring separates overlapping marks.
      ctx.strokeStyle = PLATE_BG;
      ctx.lineWidth = 1;
      ctx.stroke();
      if (n.kind === "imam") {
        ctx.fillStyle = IMAM_GOLD_BRIGHT;
        ctx.beginPath();
        ctx.arc(n.x, n.y, Math.max(1.5, n.r * 0.42), 0, Math.PI * 2);
        ctx.fill();
      }

      const isFocused = focus !== null && n.id === focus.id;
      if (isFocused || (selected && n.id === selected.id)) {
        ctx.strokeStyle = HIGHLIGHT;
        ctx.lineWidth = 2 / sim.scale;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r + 3.5 / sim.scale, 0, Math.PI * 2);
        ctx.stroke();
      }

      const showLabel = labelIds.has(n.id) || sim.scale > 1.9;
      if (showLabel && (!dimmed || isFocused)) {
        const fs = Math.max(11, Math.min(15, 10 + n.r * 0.35)) / Math.sqrt(sim.scale);
        ctx.font = `${n.kind === "imam" ? "700 " : ""}${fs}px ${amiri.style.fontFamily}, serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.lineWidth = 3 / sim.scale;
        ctx.strokeStyle = PLATE_BG;
        ctx.strokeText(n.label, n.x, n.y + n.r + 3 / sim.scale);
        ctx.fillStyle = n.kind === "imam" ? IMAM_GOLD_BRIGHT : INK_PRIMARY;
        ctx.fillText(n.label, n.x, n.y + n.r + 3 / sim.scale);
      }
      ctx.globalAlpha = 1;
    }

    // Ṭabaqāt tick labels, fixed to the left edge in screen space.
    if (layoutRef.current === "tabaqat") {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.font = "10px system-ui, sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillStyle = INK_SECONDARY;
      for (let gen = 0; gen <= MAX_GEN; gen++) {
        const y = tabaqaBandY(gen, h) * sim.scale + sim.ty;
        if (y < 14 || y > h - 8) continue;
        ctx.fillText(gen === MAX_GEN ? "undated" : `ṭabaqa ${gen}`, 10, y);
      }
    }
  }, []);

  /* --------------------------- rAF loop --------------------------- */

  useEffect(() => {
    let raf = 0;
    const sim = simRef.current;
    const loop = () => {
      if (sim.nodes.length) {
        advanceFrame(sim, layoutRef.current, interactionRef.current.dragging);
        draw();
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [draw]);

  /* ------------------------ canvas sizing ------------------------ */

  useEffect(() => {
    const wrap = wrapRef.current;
    const canvas = canvasRef.current;
    if (!wrap || !canvas) return;
    const sim = simRef.current;
    const resize = () => {
      const rect = wrap.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(rect.width * dpr);
      canvas.height = Math.round(rect.height * dpr);
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
      resizeSim(sim, rect.width, rect.height);
    };
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(wrap);
    return () => observer.disconnect();
  }, [graph]);

  /* ------------------------- interactions ------------------------ */

  const toWorld = useCallback((clientX: number, clientY: number) => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    const sim = simRef.current;
    return {
      x: (clientX - rect.left - sim.tx) / sim.scale,
      y: (clientY - rect.top - sim.ty) / sim.scale,
    };
  }, []);

  const hitTest = useCallback(
    (clientX: number, clientY: number): SimNode | null => {
      const sim = simRef.current;
      const p = toWorld(clientX, clientY);
      let best: SimNode | null = null;
      let bestD = Infinity;
      // ≥24px screen-space hit target per mark.
      const maxD = Math.max(24 / sim.scale, 6);
      for (const n of sim.nodes) {
        if (!n.visible) continue;
        const d = Math.hypot(n.x - p.x, n.y - p.y) - n.r;
        if (d < maxD && d < bestD) {
          bestD = d;
          best = n;
        }
      }
      return best;
    },
    [toWorld]
  );

  const syncTooltip = useCallback((node: SimNode | null, clientX = 0, clientY = 0) => {
    const tip = tooltipRef.current;
    const wrap = wrapRef.current;
    if (!tip || !wrap) return;
    if (!node) {
      tip.style.opacity = "0";
      return;
    }
    const rect = wrap.getBoundingClientRect();
    const x = Math.min(clientX - rect.left + 14, rect.width - 240);
    const y = Math.max(clientY - rect.top - 14, 10);
    tip.style.transform = `translate(${x}px, ${y}px)`;
    tip.style.opacity = "1";
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const sim = simRef.current;
    const inter = interactionRef.current;

    const onPointerDown = (ev: PointerEvent) => {
      canvas.setPointerCapture(ev.pointerId);
      const node = hitTest(ev.clientX, ev.clientY);
      inter.moved = 0;
      inter.lastX = ev.clientX;
      inter.lastY = ev.clientY;
      if (node) {
        inter.dragging = node;
        bumpAlpha(sim, 0.25);
      } else {
        inter.panning = true;
      }
    };

    const onPointerMove = (ev: PointerEvent) => {
      const dx = ev.clientX - inter.lastX;
      const dy = ev.clientY - inter.lastY;
      if (inter.dragging || inter.panning) inter.moved += Math.abs(dx) + Math.abs(dy);
      if (inter.dragging) {
        const p = toWorld(ev.clientX, ev.clientY);
        dragNodeTo(sim, inter.dragging, p.x, p.y);
        syncTooltip(null);
      } else if (inter.panning) {
        panCamera(sim, dx, dy);
      } else {
        const node = hitTest(ev.clientX, ev.clientY);
        hoveredRef.current = node;
        setHoveredId(node?.id ?? null);
        canvas.style.cursor = node ? "pointer" : "grab";
        syncTooltip(node, ev.clientX, ev.clientY);
      }
      inter.lastX = ev.clientX;
      inter.lastY = ev.clientY;
    };

    const onPointerUp = (ev: PointerEvent) => {
      if (inter.moved < 5) {
        const node = hitTest(ev.clientX, ev.clientY);
        selectedRef.current = node;
        setSelectedId(node?.id ?? null);
      }
      inter.dragging = null;
      inter.panning = false;
    };

    const onWheel = (ev: WheelEvent) => {
      ev.preventDefault();
      const rect = canvas.getBoundingClientRect();
      zoomCamera(
        sim,
        ev.clientX - rect.left,
        ev.clientY - rect.top,
        ev.deltaY < 0 ? 1.14 : 1 / 1.14
      );
    };

    const onLeave = () => {
      hoveredRef.current = null;
      setHoveredId(null);
      syncTooltip(null);
    };

    canvas.addEventListener("pointerdown", onPointerDown);
    canvas.addEventListener("pointermove", onPointerMove);
    canvas.addEventListener("pointerup", onPointerUp);
    canvas.addEventListener("pointerleave", onLeave);
    canvas.addEventListener("wheel", onWheel, { passive: false });
    return () => {
      canvas.removeEventListener("pointerdown", onPointerDown);
      canvas.removeEventListener("pointermove", onPointerMove);
      canvas.removeEventListener("pointerup", onPointerUp);
      canvas.removeEventListener("pointerleave", onLeave);
      canvas.removeEventListener("wheel", onWheel);
    };
  }, [hitTest, toWorld, syncTooltip, graph]);

  useEffect(() => {
    const onKey = (ev: KeyboardEvent) => {
      if (ev.key === "Escape") {
        selectedRef.current = null;
        setSelectedId(null);
        setSearchOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  /* --------------------------- search ---------------------------- */

  const searchResults = useMemo(() => {
    if (!graph || query.trim().length < 2) return [];
    const q = normaliseArabic(query);
    return graph.nodes
      .filter((n) => normaliseArabic(n.label).includes(q))
      .sort((a, b) => b.hadith_count - a.hadith_count)
      .slice(0, 8);
  }, [graph, query]);

  const flyToNode = useCallback((id: number) => {
    const sim = simRef.current;
    const node = sim.byId.get(id);
    if (!node) return;
    selectedRef.current = node;
    setSelectedId(id);
    setSearchOpen(false);
    flyCameraTo(sim, node);
  }, []);

  const resetView = useCallback(() => {
    resetCamera(simRef.current);
    selectedRef.current = null;
    setSelectedId(null);
  }, []);

  const openEvidence = useCallback((source: number, target: number, label: string) => {
    setEvidence({ source, target, label, data: null });
  }, []);

  /* ------------------------ derived detail ----------------------- */

  const selected = useMemo(
    () => (graph && selectedId !== null ? graph.nodes.find((n) => n.id === selectedId) ?? null : null),
    [graph, selectedId]
  );

  const selectedEdges = useMemo(() => {
    if (!graph || selectedId === null) return { teachers: [], students: [] };
    const byId = new Map(graph.nodes.map((n) => [n.id, n]));
    const teachers = graph.edges
      .filter((e) => e.source === selectedId && e.count >= minWeight)
      .map((e) => ({ node: byId.get(e.target)!, count: e.count }))
      .filter((r) => r.node)
      .sort((a, b) => b.count - a.count)
      .slice(0, 7);
    const students = graph.edges
      .filter((e) => e.target === selectedId && e.count >= minWeight)
      .map((e) => ({ node: byId.get(e.source)!, count: e.count }))
      .filter((r) => r.node)
      .sort((a, b) => b.count - a.count)
      .slice(0, 7);
    return { teachers, students };
  }, [graph, selectedId, minWeight]);

  const hoveredNode = useMemo(
    () => (graph && hoveredId !== null ? graph.nodes.find((n) => n.id === hoveredId) ?? null : null),
    [graph, hoveredId]
  );

  const visibleStats = useMemo(() => {
    if (!graph) return { nodes: 0, edges: 0 };
    const kept = graph.edges.filter((e) => e.count >= minWeight);
    const touched = new Set<number>();
    kept.forEach((e) => {
      touched.add(e.source);
      touched.add(e.target);
    });
    return { nodes: touched.size, edges: kept.length };
  }, [graph, minWeight]);

  const tableRows = useMemo(() => {
    if (!graph) return [];
    const byId = new Map(graph.nodes.map((n) => [n.id, n]));
    return graph.edges
      .filter((e) => e.count >= minWeight)
      .slice(0, 150)
      .map((e) => ({
        student: byId.get(e.source),
        teacher: byId.get(e.target),
        count: e.count,
      }))
      .filter((r) => r.student && r.teacher);
  }, [graph, minWeight]);

  /* ---------------------------- render ---------------------------- */

  if (error) {
    return (
      <div className="rounded-lg border border-border bg-surface p-10 text-center text-muted">
        {error}
      </div>
    );
  }

  return (
    <div>
      {/* Controls — one row above the plate */}
      <div className="mb-4 flex flex-wrap items-center gap-x-6 gap-y-3">
        <div className="relative">
          <input
            type="search"
            value={query}
            onChange={(ev) => {
              setQuery(ev.target.value);
              setSearchOpen(true);
            }}
            onFocus={() => setSearchOpen(true)}
            onKeyDown={(ev) => {
              if (ev.key === "Enter" && searchResults.length) flyToNode(searchResults[0].id);
            }}
            placeholder="Find a narrator…"
            aria-label="Find a narrator"
            className="min-h-11 w-64 rounded-md border border-border bg-surface px-4 py-2 text-sm outline-none focus:border-accent focus:ring-1 focus:ring-accent"
          />
          {searchOpen && searchResults.length > 0 && (
            <ul className="absolute z-30 mt-1 w-80 overflow-hidden rounded-md border border-border bg-surface shadow-lg">
              {searchResults.map((n) => (
                <li key={n.id}>
                  <button
                    type="button"
                    onClick={() => flyToNode(n.id)}
                    className="flex min-h-11 w-full items-center justify-between gap-3 px-4 py-2 text-right hover:bg-background"
                  >
                    <span className="text-xs text-muted">
                      {numberFormat.format(n.hadith_count)}
                    </span>
                    <span dir="rtl" lang="ar" className={`${amiri.className} text-[15px]`}>
                      {formatArabicText(n.label)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <label className="flex items-center gap-3 text-sm text-muted">
          Min. shared hadiths
          <input
            type="range"
            min={2}
            max={15}
            value={minWeight}
            onChange={(ev) => setMinWeight(Number(ev.target.value))}
            className="w-36 accent-[var(--accent)]"
          />
          <span className="w-5 font-medium text-foreground tabular-nums">{minWeight}</span>
        </label>

        <div className="flex overflow-hidden rounded-md border border-border text-sm" role="group" aria-label="Layout">
          {(
            [
              ["constellation", "Constellation"],
              ["tabaqat", "Ṭabaqāt"],
            ] as [LayoutMode, string][]
          ).map(([mode, label]) => (
            <button
              key={mode}
              type="button"
              onClick={() => setLayout(mode)}
              aria-pressed={layout === mode}
              className={`min-h-11 px-4 py-1.5 transition ${
                layout === mode
                  ? "bg-accent text-accent-foreground"
                  : "bg-surface text-foreground/70 hover:text-accent"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <button
          type="button"
          onClick={() => setQualityOn((on) => !on)}
          aria-pressed={qualityOn}
          className={`min-h-11 rounded-md border px-4 py-1.5 text-sm transition ${
            qualityOn
              ? "border-accent bg-accent text-accent-foreground"
              : "border-border bg-surface text-foreground/70 hover:text-accent"
          }`}
          title="Color each edge by whether al-Khoei's Mu'jam corroborates the transmission"
        >
          {qualityLoading ? "Scoring…" : "Evidence quality"}
        </button>

        <button
          type="button"
          onClick={resetView}
          className="min-h-11 rounded-md border border-border bg-surface px-4 py-1.5 text-sm text-foreground/70 transition hover:text-accent"
        >
          Reset view
        </button>

        <p className="ml-auto text-sm text-muted">
          {graph
            ? `${numberFormat.format(visibleStats.nodes)} narrators · ${numberFormat.format(visibleStats.edges)} transmission links`
            : "Charting the network…"}
          {graph && graph.decisions_applied > 0
            ? ` · ${numberFormat.format(graph.decisions_applied)} review corrections applied`
            : ""}
          {graph?.computed_at ? ` · as of ${formatComputedAt(graph.computed_at)}` : ""}
        </p>
      </div>

      {/* The plate */}
      <div
        ref={wrapRef}
        className="relative h-[72vh] min-h-[480px] w-full overflow-hidden rounded-lg border border-border shadow-[inset_0_0_48px_rgba(0,0,0,0.28)]"
        style={{ background: PLATE_BG }}
      >
        <canvas ref={canvasRef} className="block h-full w-full cursor-grab" aria-label="Narrator transmission network graph" role="img" />

        {!graph && !error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="animate-pulse text-sm" style={{ color: INK_SECONDARY }}>
              Charting the network…
            </p>
          </div>
        )}

        {/* Tooltip */}
        <div
          ref={tooltipRef}
          className="pointer-events-none absolute left-0 top-0 z-20 w-56 rounded-md p-3 opacity-0 transition-opacity duration-100"
          style={{
            background: "rgba(15, 24, 19, 0.95)",
            border: "1px solid rgba(236, 231, 214, 0.16)",
            backdropFilter: "blur(4px)",
          }}
        >
          {hoveredNode && (
            <>
              <p
                dir="rtl"
                lang="ar"
                className={`${amiri.className} text-[15px] leading-snug`}
                style={{ color: hoveredNode.kind === "imam" ? IMAM_GOLD_BRIGHT : INK_PRIMARY }}
              >
                {formatArabicText(hoveredNode.label)}
              </p>
              <p className="mt-1.5 text-xs" style={{ color: INK_SECONDARY }}>
                <span className="font-semibold" style={{ color: INK_PRIMARY }}>
                  {numberFormat.format(hoveredNode.hadith_count)}
                </span>{" "}
                hadiths in resolved chains
              </p>
              <p className="text-xs" style={{ color: INK_SECONDARY }}>
                {hoveredNode.kind === "imam"
                  ? "Maʿṣūm"
                  : hoveredNode.generation !== null
                    ? `Ṭabaqa ${hoveredNode.generation} (estimated)`
                    : "Ṭabaqa unknown"}
                {hoveredNode.merged_person_ids.length > 1
                  ? ` · ${hoveredNode.merged_person_ids.length} merged identities`
                  : ""}
              </p>
              <p className="mt-1 text-[11px]" style={{ color: INK_SECONDARY }}>
                Click for details
              </p>
            </>
          )}
        </div>

        {/* Legend */}
        <div
          className="absolute bottom-3 left-3 z-10 rounded-md px-3.5 py-3 text-[11px] leading-5"
          style={{
            background: "rgba(15, 24, 19, 0.88)",
            border: "1px solid rgba(236, 231, 214, 0.12)",
            color: INK_SECONDARY,
          }}
        >
          <p className="flex items-center gap-2">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ background: IMAM_GOLD, boxShadow: "0 0 6px rgba(232,181,74,0.8)" }}
            />
            <span style={{ color: INK_PRIMARY }}>The Imams</span>
          </p>
          {ERA_RAMP.map((hex, i) => (
            <p key={hex} className="flex items-center gap-2">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: hex }} />
              {ERA_LABELS[i]}
            </p>
          ))}
          <p className="flex items-center gap-2">
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: UNDATED }} />
            Undated
          </p>
          <p className="mt-1.5 border-t pt-1.5" style={{ borderColor: "rgba(236,231,214,0.12)" }}>
            size = hadiths · line = shared hadiths
          </p>
          {qualityOn && (
            <div className="mt-1.5 border-t pt-1.5" style={{ borderColor: "rgba(236,231,214,0.12)" }}>
              <p className="flex items-center gap-2">
                <span className="inline-block h-0.5 w-4" style={{ background: QUALITY_CORROBORATED }} />
                Mu&apos;jam corroborates
              </p>
              <p className="flex items-center gap-2">
                <span className="inline-block h-0.5 w-4" style={{ background: QUALITY_CONTRADICTED }} />
                Not attested (review)
              </p>
              <p className="flex items-center gap-2">
                <span
                  className="inline-block h-0 w-4"
                  style={{ borderTop: `2px dashed ${INK_SECONDARY}` }}
                />
                Under-documented
              </p>
            </div>
          )}
        </div>

        {/* Detail panel */}
        {selected && (
          <aside
            className="absolute right-3 top-3 z-10 w-80 max-w-[calc(100%-1.5rem)] rounded-md p-4"
            style={{
              background: "rgba(15, 24, 19, 0.94)",
              border: "1px solid rgba(236, 231, 214, 0.16)",
              backdropFilter: "blur(6px)",
            }}
          >
            <div className="flex items-start justify-between gap-3">
              <p
                dir="rtl"
                lang="ar"
                className={`${amiri.className} text-xl leading-snug`}
                style={{ color: selected.kind === "imam" ? IMAM_GOLD_BRIGHT : INK_PRIMARY }}
              >
                {formatArabicText(selected.label)}
              </p>
              <button
                type="button"
                onClick={() => {
                  selectedRef.current = null;
                  setSelectedId(null);
                }}
                aria-label="Close details"
                className="rounded-md px-2 text-lg leading-none transition hover:opacity-70"
                style={{ color: INK_SECONDARY }}
              >
                ×
              </button>
            </div>
            <p className="mt-1 text-xs" style={{ color: INK_SECONDARY }}>
              {selected.kind === "imam"
                ? "Maʿṣūm"
                : selected.generation !== null
                  ? `Ṭabaqa ${selected.generation} (estimated)`
                  : "Ṭabaqa unknown"}
              {" · "}
              <span className="font-semibold" style={{ color: INK_PRIMARY }}>
                {numberFormat.format(selected.hadith_count)}
              </span>{" "}
              hadiths
              {selected.merged_person_ids.length > 1
                ? ` · ${selected.merged_person_ids.length} identities merged`
                : ""}
            </p>

            {selectedEdges.teachers.length > 0 && (
              <div className="mt-3">
                <p className="text-[11px] font-semibold uppercase tracking-wide" style={{ color: INK_SECONDARY }}>
                  Narrates from
                </p>
                <ul className="mt-1 space-y-1">
                  {selectedEdges.teachers.map(({ node, count }) => (
                    <li key={node.id} className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => openEvidence(selected.id, node.id, `${selected.label} → ${node.label}`)}
                        title="Show the shared hadiths for this edge"
                        className="inline-flex min-h-6 min-w-6 items-center justify-center rounded-md px-1.5 py-1 text-xs tabular-nums transition hover:bg-[#f2ead9]/10"
                        style={{ color: INK_PRIMARY }}
                      >
                        {numberFormat.format(count)}
                      </button>
                      <button
                        type="button"
                        onClick={() => flyToNode(node.id)}
                        className="flex flex-1 items-center justify-end rounded-lg px-2 py-1 text-right transition hover:bg-[#f2ead9]/5"
                      >
                        <span
                          dir="rtl"
                          lang="ar"
                          className={`${amiri.className} truncate text-[14px]`}
                          style={{ color: node.kind === "imam" ? IMAM_GOLD_BRIGHT : INK_PRIMARY }}
                        >
                          {formatArabicText(node.label)}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {selectedEdges.students.length > 0 && (
              <div className="mt-3">
                <p className="text-[11px] font-semibold uppercase tracking-wide" style={{ color: INK_SECONDARY }}>
                  Narrated by
                </p>
                <ul className="mt-1 space-y-1">
                  {selectedEdges.students.map(({ node, count }) => (
                    <li key={node.id} className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => openEvidence(node.id, selected.id, `${node.label} → ${selected.label}`)}
                        title="Show the shared hadiths for this edge"
                        className="inline-flex min-h-6 min-w-6 items-center justify-center rounded-md px-1.5 py-1 text-xs tabular-nums transition hover:bg-[#f2ead9]/10"
                        style={{ color: INK_PRIMARY }}
                      >
                        {numberFormat.format(count)}
                      </button>
                      <button
                        type="button"
                        onClick={() => flyToNode(node.id)}
                        className="flex flex-1 items-center justify-end rounded-lg px-2 py-1 text-right transition hover:bg-[#f2ead9]/5"
                      >
                        <span
                          dir="rtl"
                          lang="ar"
                          className={`${amiri.className} truncate text-[14px]`}
                          style={{ color: node.kind === "imam" ? IMAM_GOLD_BRIGHT : INK_PRIMARY }}
                        >
                          {formatArabicText(node.label)}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {selected.narrator_id !== null && (
              <Link
                href={`/narrators/${selected.narrator_id}`}
                className="mt-4 flex min-h-11 items-center justify-center rounded-md px-4 py-2 text-center text-sm font-medium transition hover:opacity-90"
                style={{ background: IMAM_GOLD, color: "#171207" }}
              >
                Open narrator profile →
              </Link>
            )}
          </aside>
        )}

        {/* Edge evidence — the actual shared hadiths behind one transmission link */}
        {evidence && (
          <aside
            className="absolute bottom-3 right-3 z-20 flex max-h-[60%] w-96 max-w-[calc(100%-1.5rem)] flex-col rounded-md p-4"
            style={{
              background: "rgba(15, 24, 19, 0.96)",
              border: "1px solid rgba(236, 231, 214, 0.18)",
              backdropFilter: "blur(6px)",
            }}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wide" style={{ color: INK_SECONDARY }}>
                  Shared hadiths
                  {evidence.data ? ` · ${numberFormat.format(evidence.data.total)}` : ""}
                </p>
                <p
                  dir="rtl"
                  lang="ar"
                  className={`${amiri.className} mt-0.5 text-[15px] leading-snug`}
                  style={{ color: INK_PRIMARY }}
                >
                  {formatArabicText(evidence.label)}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setEvidence(null)}
                aria-label="Close evidence"
                className="rounded-md px-2 text-lg leading-none transition hover:opacity-70"
                style={{ color: INK_SECONDARY }}
              >
                ×
              </button>
            </div>

            <div className="mt-2 overflow-y-auto">
              {evidence.data === null ? (
                <p className="py-4 text-center text-xs" style={{ color: INK_SECONDARY }}>
                  Loading…
                </p>
              ) : evidence.data.items.length === 0 ? (
                <p className="py-4 text-center text-xs" style={{ color: INK_SECONDARY }}>
                  No shared hadiths.
                </p>
              ) : (
                <ul className="space-y-2">
                  {evidence.data.items.map((item) => (
                    <li key={item.public_id}>
                      <Link
                        href={`/hadith/${item.public_id}`}
                        className="flex min-h-11 items-center rounded-lg px-2 py-1.5 transition hover:bg-[#f2ead9]/5"
                      >
                        <span className="text-[11px]" style={{ color: INK_SECONDARY }}>
                          #{item.sequence_in_book}
                          {item.volume_start ? ` · vol. ${item.volume_start}` : ""}
                          {item.page_start ? `, p. ${item.page_start}` : ""}
                        </span>
                        {item.isnad_excerpt && (
                          <span
                            dir="rtl"
                            lang="ar"
                            className={`${amiri.className} mt-0.5 block truncate text-[13px]`}
                            style={{ color: INK_PRIMARY }}
                          >
                            {formatArabicText(item.isnad_excerpt)}
                          </span>
                        )}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </aside>
        )}
      </div>

      {/* Table view — the non-visual path to the same data */}
      <details className="mt-6 rounded-lg border border-border bg-surface">
        <summary className="cursor-pointer px-5 py-3 text-sm font-medium text-foreground/80 transition hover:text-accent">
          View as table — strongest transmission links
        </summary>
        <div className="max-h-96 overflow-auto border-t border-border">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-surface text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="px-5 py-2">Student</th>
                <th className="px-5 py-2">Teacher</th>
                <th className="px-5 py-2 text-right">Shared hadiths</th>
              </tr>
            </thead>
            <tbody>
              {tableRows.map((row) => (
                <tr key={`${row.student!.id}-${row.teacher!.id}`} className="border-t border-border/60">
                  <td dir="rtl" lang="ar" className={`${amiri.className} px-5 py-1.5 text-right`}>
                    {formatArabicText(row.student!.label)}
                  </td>
                  <td dir="rtl" lang="ar" className={`${amiri.className} px-5 py-1.5 text-right`}>
                    {formatArabicText(row.teacher!.label)}
                  </td>
                  <td className="px-5 py-1.5 text-right tabular-nums">{numberFormat.format(row.count)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
