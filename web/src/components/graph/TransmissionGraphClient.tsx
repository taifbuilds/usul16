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
import {
  getNarratorDirectory,
  getTransmissionEdgeEvidence,
  getTransmissionGraph,
  getTransmissionPaths,
} from "@/lib/api/books";
import type {
  NarratorDirectoryEntry,
  TransmissionEdgeEvidenceRead,
  TransmissionGraphEdge,
  TransmissionGraphNode,
  TransmissionGraphRead,
  TransmissionPathsRead,
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
// Provisional narrators (ambiguous best-guess) read as a muted, desaturated
// clay — clearly "not confirmed" regardless of ṭabaqa.
const UNCERTAIN = "#9a8f79";
// Book compilers (al-Kulayni) — a mauve that is unmistakably neither the Imams'
// gold nor the narrators' blue ramp. Also drawn with a ring, so the distinction
// never depends on colour alone.
const COMPILER = "#b58bd6";
const INK_PRIMARY = "#ece7d6";
const INK_SECONDARY = "#9aa695";
const EDGE_RGB = "214, 224, 210";
const HIGHLIGHT = "#e8b54a";

const ERA_LABELS = ["Ṭabaqa ≤ 4", "Ṭabaqa 5–6", "Ṭabaqa 7–8", "Ṭabaqa 9–10", "Ṭabaqa 11+"];
const MAX_GEN = 13;
// Undated narrators get their own band *below* the timeline, separated by a
// rule — merging them into the last generation implied they were the latest,
// which is a claim the data does not make.
const UNDATED_BAND = MAX_GEN + 1;

// Each generation is anchored by the Maʿṣūm who lived in it, which is what makes
// the ṭabaqāt axis legible as time rather than as bare numbers.
const GENERATION_ANCHOR: Record<number, string> = {
  0: "the Prophet",
  1: "Imam ʿAlī",
  2: "al-Ḥasan · al-Ḥusayn",
  3: "al-Sajjād",
  4: "al-Bāqir",
  5: "al-Ṣādiq",
  6: "al-Kāẓim",
  7: "al-Riḍā",
  8: "al-Jawād",
  9: "al-Hādī",
  10: "al-ʿAskarī",
  11: "al-Mahdī",
  12: "the compilers",
  13: "later",
};

const ROLE_LABEL: Record<string, string> = {
  prophet: "The Prophet ﷺ",
  imam: "Maʿṣūm (Imam)",
  compiler: "Compiler of the book",
  narrator: "Narrator",
};

// Evidence-quality colors (validated status hue on the dark plate).
const QUALITY_CONTRADICTED = "#d03b3b"; // critical — 3.62:1 on #121c17
const QUALITY_CORROBORATED = "#1baf7a"; // good — reads distinct from the blue ramp

function tabaqaBandY(generation: number, height: number): number {
  return height * 0.08 + (generation / UNDATED_BAND) * height * 0.84;
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
  if (node.kind === "imam" || node.role === "prophet") return IMAM_GOLD;
  if (node.role === "compiler") return COMPILER;
  // A propagated generation is an estimate, not a date. Keep it out of the
  // colour encoding so a guessed layer cannot look like established chronology.
  const era = eraIndex(node.generation_anchored ? node.generation : null);
  return era === null ? UNDATED : ERA_RAMP[era];
}

function datedGeneration(node: TransmissionGraphNode): number | null {
  return node.generation_anchored ? node.generation : null;
}

/** Diacritic/variant-insensitive Arabic match for the in-graph path pickers,
 * which search the already-loaded node labels (strips harakat, folds
 * alef/yeh/kaf variants). */
function normArabic(text: string): string {
  return text
    .replace(/[ً-ْٰـ]/g, "") // harakat + tatweel
    .replace(/[آأإ]/g, "ا") // alef variants -> alef
    .replace(/[یى]/g, "ي") // farsi yeh / alef maksura -> yeh
    .replace(/ک/g, "ك") // farsi kaf -> kaf
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

/* ------------------------------------------------------------------ */
/* Barnes–Hut quadtree repulsion — O(n log n) so the whole al-Kāfī     */
/* network (~2,000 narrators) renders at 60fps. Small graphs keep the  */
/* exact O(n²) loop; only large ones use the approximation.            */
/* ------------------------------------------------------------------ */

interface QuadNode {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  cx: number; // centre of mass (radius-weighted)
  cy: number;
  n: number; // body count in this quad
  sumR: number; // Σ radius — the "mass"
  body: SimNode | null; // set only for a single-body leaf
  children: (QuadNode | null)[] | null;
  bucket: SimNode[] | null; // coincident bodies below the min quad size
}

const BH_THETA = 0.8; // quad accepted as one mass when size/distance < theta
const BH_MIN_QUAD = 1; // don't subdivide below ~1px — bucket instead

function makeQuad(x0: number, y0: number, x1: number, y1: number): QuadNode {
  return { x0, y0, x1, y1, cx: 0, cy: 0, n: 0, sumR: 0, body: null, children: null, bucket: null };
}

function quadInsertChild(q: QuadNode, node: SimNode): void {
  const mx = (q.x0 + q.x1) / 2;
  const my = (q.y0 + q.y1) / 2;
  const right = node.x >= mx ? 1 : 0;
  const bottom = node.y >= my ? 1 : 0;
  const idx = bottom * 2 + right;
  if (!q.children) q.children = [null, null, null, null];
  if (!q.children[idx]) {
    q.children[idx] = makeQuad(
      right ? mx : q.x0,
      bottom ? my : q.y0,
      right ? q.x1 : mx,
      bottom ? q.y1 : my
    );
  }
  quadInsert(q.children[idx]!, node);
}

function quadInsert(q: QuadNode, node: SimNode): void {
  if (q.n === 0) {
    q.body = node;
    q.cx = node.x;
    q.cy = node.y;
    q.n = 1;
    q.sumR = node.r;
    return;
  }
  // Below the minimum quad size, bucket bodies rather than subdivide forever
  // (identical coordinates would otherwise recurse without end).
  if (q.x1 - q.x0 <= BH_MIN_QUAD) {
    if (!q.bucket) q.bucket = q.body ? [q.body] : [];
    q.bucket.push(node);
    q.body = null;
  } else {
    if (q.body !== null) {
      const old = q.body;
      q.body = null;
      quadInsertChild(q, old);
    }
    quadInsertChild(q, node);
  }
  q.cx = (q.cx * q.sumR + node.x * node.r) / (q.sumR + node.r);
  q.cy = (q.cy * q.sumR + node.y * node.r) / (q.sumR + node.r);
  q.n += 1;
  q.sumR += node.r;
}

function buildQuadtree(nodes: SimNode[]): QuadNode | null {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const n of nodes) {
    if (!Number.isFinite(n.x) || !Number.isFinite(n.y)) continue;
    if (n.x < minX) minX = n.x;
    if (n.y < minY) minY = n.y;
    if (n.x > maxX) maxX = n.x;
    if (n.y > maxY) maxY = n.y;
  }
  if (!Number.isFinite(minX)) return null;
  const size = Math.max(maxX - minX, maxY - minY, 1) + 1;
  const root = makeQuad(minX, minY, minX + size, minY + size);
  for (const n of nodes) {
    if (Number.isFinite(n.x) && Number.isFinite(n.y)) quadInsert(root, n);
  }
  return root;
}

/** Accumulate repulsion on one node from the whole tree (same force law as the
 * exact loop: 150·(r_node + r_other)/d², summed via centre-of-mass). */
function bhApply(node: SimNode, cx: number, cy: number, n: number, sumR: number, alpha: number): void {
  let dx = node.x - cx;
  const dy = node.y - cy;
  let dSq = dx * dx + dy * dy;
  if (dSq < 4) {
    if (dx === 0 && dy === 0) dx = 0.5; // nudge coincident bodies apart
    dSq = 4;
  }
  const d = Math.sqrt(dSq);
  const f = ((150 * (node.r * n + sumR)) / dSq) * alpha;
  node.vx += (dx / d) * f;
  node.vy += (dy / d) * f;
}

function bhRepel(q: QuadNode | null, node: SimNode, alpha: number, cutoffSq: number): void {
  if (!q || q.n === 0) return;
  // Prune whole quads whose nearest point is beyond the interaction cutoff —
  // preserves the original local-repulsion character while staying fast.
  const nx = node.x < q.x0 ? q.x0 : node.x > q.x1 ? q.x1 : node.x;
  const ny = node.y < q.y0 ? q.y0 : node.y > q.y1 ? q.y1 : node.y;
  const gapX = node.x - nx;
  const gapY = node.y - ny;
  if (gapX * gapX + gapY * gapY > cutoffSq) return;

  if (q.bucket) {
    for (const b of q.bucket) if (b !== node) bhApply(node, b.x, b.y, 1, b.r, alpha);
    return;
  }
  if (q.body) {
    if (q.body !== node) bhApply(node, q.body.x, q.body.y, 1, q.body.r, alpha);
    return;
  }
  const dx = node.x - q.cx;
  const dy = node.y - q.cy;
  const dSq = dx * dx + dy * dy;
  const size = q.x1 - q.x0;
  if (size * size < BH_THETA * BH_THETA * dSq) {
    bhApply(node, q.cx, q.cy, q.n, q.sumR, alpha);
  } else if (q.children) {
    for (const c of q.children) bhRepel(c, node, alpha, cutoffSq);
  }
}

function tickSim(sim: SimState, mode: LayoutMode, dragging: SimNode | null): void {
  const nodes = sim.nodes.filter((n) => n.visible);
  if (!nodes.length) return;
  const alpha = sim.alpha;
  const w = sim.width;
  const h = sim.height;

  // Repulsion. Small graphs keep the exact O(n²) loop (tuned, unchanged);
  // large ones — the raised caps now surface the whole ~2,000-narrator al-Kāfī
  // network — use a Barnes–Hut quadtree so it still runs at 60fps.
  const cutoff = 320;
  const cutoffSq = cutoff * cutoff;
  if (nodes.length <= 600) {
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
  } else {
    const tree = buildQuadtree(nodes);
    for (const node of nodes) bhRepel(tree, node, alpha, cutoffSq);
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
      // Undated sits in its own band below the timeline, not at "latest".
      const gen = datedGeneration(n) ?? UNDATED_BAND;
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
      color: n.uncertain ? UNCERTAIN : nodeColor(n),
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

/** Smoothly frame the camera on a set of nodes (used to fit a traced path). */
function fitCameraToNodes(sim: SimState, nodes: SimNode[], padding = 130): void {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const n of nodes) {
    if (!Number.isFinite(n.x) || !Number.isFinite(n.y)) continue;
    if (n.x < minX) minX = n.x;
    if (n.y < minY) minY = n.y;
    if (n.x > maxX) maxX = n.x;
    if (n.y > maxY) maxY = n.y;
  }
  if (!Number.isFinite(minX)) return;
  const scale = Math.min(
    2.2,
    (sim.width - padding * 2) / Math.max(40, maxX - minX),
    (sim.height - padding * 2) / Math.max(40, maxY - minY)
  );
  sim.targetScale = scale;
  sim.targetTx = sim.width / 2 - ((minX + maxX) / 2) * scale;
  sim.targetTy = sim.height / 2 - ((minY + maxY) / 2) * scale;
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

/** A narrator picker that searches the drawn graph nodes (path-finding only
 * works between charted narrators), returning the cluster-root person id. */
function GraphNodePicker({
  nodes,
  placeholder,
  value,
  onChange,
}: {
  nodes: TransmissionGraphNode[];
  placeholder: string;
  value: { id: number; label: string } | null;
  onChange: (v: { id: number; label: string } | null) => void;
}) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const results = useMemo(() => {
    const qq = normArabic(q);
    if (qq.length < 1) return [];
    return nodes
      .filter((n) =>
        [n.label, ...(n.merged_labels ?? [])].some((label) => normArabic(label).includes(qq))
      )
      .sort((a, b) => b.hadith_count - a.hadith_count)
      .slice(0, 8);
  }, [nodes, q]);

  if (value) {
    return (
      <div
        className="flex items-center justify-between gap-2 rounded-md px-3 py-2"
        style={{ background: "rgba(236,231,214,0.06)", border: "1px solid rgba(236,231,214,0.16)" }}
      >
        <button
          type="button"
          onClick={() => {
            onChange(null);
            setQ("");
          }}
          aria-label="Clear"
          className="text-lg leading-none transition hover:opacity-70"
          style={{ color: INK_SECONDARY }}
        >
          ×
        </button>
        <span dir="rtl" lang="ar" className={`${amiri.className} truncate text-[15px]`} style={{ color: INK_PRIMARY }}>
          {formatArabicText(value.label)}
        </span>
      </div>
    );
  }

  return (
    <div className="relative">
      <input
        type="search"
        value={q}
        onChange={(e) => {
          setQ(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => window.setTimeout(() => setOpen(false), 120)}
        placeholder={placeholder}
        className="min-h-10 w-full rounded-md px-3 py-1.5 text-sm outline-none"
        style={{ background: "rgba(236,231,214,0.05)", border: "1px solid rgba(236,231,214,0.16)", color: INK_PRIMARY }}
      />
      {open && results.length > 0 && (
        <ul
          className="absolute z-40 mt-1 max-h-56 w-full overflow-auto rounded-md"
          style={{ background: "rgba(15,24,19,0.98)", border: "1px solid rgba(236,231,214,0.18)" }}
        >
          {results.map((n) => (
            <li key={n.id}>
              <button
                type="button"
                onClick={() => {
                  onChange({ id: n.id, label: n.label });
                  setQ("");
                  setOpen(false);
                }}
                className="flex min-h-10 w-full items-center justify-between gap-3 px-3 py-1.5 text-right transition hover:bg-[#f2ead9]/5"
              >
                <span className="shrink-0 text-[11px]" style={{ color: INK_SECONDARY }}>
                  {numberFormat.format(n.hadith_count)}
                </span>
                <span
                  dir="rtl"
                  lang="ar"
                  className={`${amiri.className} truncate text-[14px]`}
                  style={{ color: n.kind === "imam" ? IMAM_GOLD_BRIGHT : INK_PRIMARY }}
                >
                  {formatArabicText(n.label)}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function TransmissionGraphClient() {
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const tooltipRef = useRef<HTMLDivElement | null>(null);

  const [graph, setGraph] = useState<TransmissionGraphRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const searchParams = useSearchParams();
  // Default 1 shows the whole confident al-Kāfī network (~2,000 narrators);
  // raise the slider to thin it toward the busiest hubs.
  const [minWeight, setMinWeight] = useState(1);
  // useSearchParams is SSR-consistent, so seeding state from it can't cause a
  // hydration mismatch the way window.location would.
  const [layout, setLayout] = useState<LayoutMode>(
    searchParams.get("layout") === "tabaqat" ? "tabaqat" : "constellation"
  );
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [dirResults, setDirResults] = useState<NarratorDirectoryEntry[]>([]);
  const [dirLoading, setDirLoading] = useState(false);
  const [qualityOn, setQualityOn] = useState(searchParams.get("quality") === "1");
  const [qualityLoading, setQualityLoading] = useState(false);
  const [includeUncertain, setIncludeUncertain] = useState(searchParams.get("uncertain") === "1");
  const [legendOpen, setLegendOpen] = useState(true);
  const [evidence, setEvidence] = useState<{
    source: number;
    target: number;
    label: string;
    data: TransmissionEdgeEvidenceRead | null;
  } | null>(null);

  // Path-finding: pick two charted narrators, light up the isnad path(s).
  const [pathOpen, setPathOpen] = useState(false);
  const [pathFrom, setPathFrom] = useState<{ id: number; label: string } | null>(null);
  const [pathTo, setPathTo] = useState<{ id: number; label: string } | null>(null);
  const [pathResult, setPathResult] = useState<TransmissionPathsRead | null>(null);
  const [pathLoading, setPathLoading] = useState(false);
  const [pathError, setPathError] = useState<string | null>(null);
  const [activePathIdx, setActivePathIdx] = useState(0);
  const pathHighlightRef = useRef<{ nodes: Set<number>; edges: Set<string> } | null>(null);

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
    // Pull the whole confident al-Kāfī network (~2,000 narrators, not the old
    // ~500). min_count=1 keeps every co-transmission; the client-side weight
    // slider trims from there without a refetch. With uncertain on, also pull
    // the resolver's ambiguous best-guesses (~2,600 total) — marked, never fact.
    getTransmissionGraph({ minCount: 1, maxNodes: includeUncertain ? 3000 : 2000, includeUncertain })
      .then((data) => {
        if (!cancelled) setGraph(data);
      })
      .catch(() => {
        if (!cancelled) setError("The graph API is not reachable. Is the backend running?");
      });
    return () => {
      cancelled = true;
    };
  }, [includeUncertain]);

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
    getTransmissionGraph({ minCount: 1, maxNodes: 2000, quality: true })
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

    // Ṭabaqāt mode: hairline generation rules under the data, plus a stronger
    // dashed rule marking where dated history ends and "unknown" begins.
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
      const dividerY = (tabaqaBandY(MAX_GEN, h) + tabaqaBandY(UNDATED_BAND, h)) / 2;
      ctx.setLineDash([6 / sim.scale, 6 / sim.scale]);
      ctx.strokeStyle = "rgba(236, 231, 214, 0.16)";
      ctx.beginPath();
      ctx.moveTo(-20000, dividerY);
      ctx.lineTo(20000, dividerY);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    const hovered = hoveredRef.current;
    const selected = selectedRef.current;
    const focus = hovered ?? selected;
    const focusNeighbors = focus ? sim.neighbors.get(focus.id) ?? new Set() : null;
    const globalFade = sim.reducedMotion ? 1 : Math.min(1, sim.fadeIn);
    const qualityOn = qualityOnRef.current;
    // A traced path takes over the plate: its edges/nodes blaze gold, the rest
    // recedes so the isnad reads as a single bright thread.
    const pathHl = pathHighlightRef.current;
    const pathActive = pathHl !== null;

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
      const onPathEdge = pathActive && pathHl!.edges.has(`${e.source}->${e.target}`);
      // Quality overlay tints edges by their Mu'jam verdict when enabled — but
      // the focus highlight always wins so hovering a node stays legible.
      // A generation-impossible edge is as strong a red flag as a contradicted one.
      const q = qualityOn ? (e.gen_violation ? "contradicted" : e.quality) : null;
      ctx.setLineDash([]);
      if (pathActive) {
        if (onPathEdge) {
          ctx.strokeStyle = `rgba(232, 181, 74, ${(0.75 + 0.25 * t) * globalFade})`;
          ctx.lineWidth = 2.4 + 2.4 * t;
        } else {
          ctx.strokeStyle = `rgba(${EDGE_RGB}, ${0.028 * globalFade})`;
          ctx.lineWidth = 0.5;
        }
      } else if (focus && !isFocusEdge) {
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
      } else if (e.uncertain) {
        // Provisional edge (an endpoint was a best guess) — dashed and faint.
        ctx.strokeStyle = `rgba(${EDGE_RGB}, ${(0.02 + 0.1 * t) * globalFade})`;
        ctx.lineWidth = 0.5 + 1.2 * t;
        ctx.setLineDash([2, 4]);
      } else {
        ctx.strokeStyle = `rgba(${EDGE_RGB}, ${(0.05 + 0.3 * t) * globalFade})`;
        ctx.lineWidth = 0.6 + 1.9 * t;
      }
      ctx.beginPath();
      ctx.moveTo(e.a.x, e.a.y);
      ctx.lineTo(e.b.x, e.b.y);
      ctx.stroke();
      ctx.setLineDash([]);
      // Direction chevron (student → teacher) on focused / path edges.
      if ((isFocusEdge || onPathEdge) && sim.scale > 0.5) {
        const mx = e.a.x + (e.b.x - e.a.x) * 0.58;
        const my = e.a.y + (e.b.y - e.a.y) * 0.58;
        const ang = Math.atan2(e.b.y - e.a.y, e.b.x - e.a.x);
        const s = (onPathEdge ? 6 : 4.5) / Math.sqrt(sim.scale);
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
    // Imams and compilers are always named — they are the landmarks of the map.
    for (const n of visibleSorted) {
      if (n.kind === "imam" || n.role === "compiler" || n.role === "prophet") labelIds.add(n.id);
    }
    if (focus) {
      labelIds.add(focus.id);
      focusNeighbors?.forEach((id) => labelIds.add(id));
    }
    if (pathActive) pathHl!.nodes.forEach((id) => labelIds.add(id));

    for (const n of visibleSorted) {
      if (!Number.isFinite(n.x) || !Number.isFinite(n.y)) continue;
      const onPathNode = pathActive && pathHl!.nodes.has(n.id);
      const dimmed = pathActive
        ? !onPathNode
        : focus !== null && n.id !== focus.id && !focusNeighbors?.has(n.id);
      // In the ṭabaqāt layout the y-position IS a chronology claim, so a merely
      // inferred generation must not look as solid as an anchored one.
      const inferredGen =
        layoutRef.current === "tabaqat" && n.generation !== null && !n.generation_anchored;
      const alpha =
        (dimmed
          ? pathActive
            ? 0.09
            : 0.18
          : n.uncertain
            ? 0.6
            : inferredGen
              ? 0.45
              : 1) * globalFade;
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
      } else if (n.role === "compiler") {
        // A ring, so "compiler" is legible without relying on colour alone.
        ctx.strokeStyle = COMPILER;
        ctx.lineWidth = 1.5 / sim.scale;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r + 2.5 / sim.scale, 0, Math.PI * 2);
        ctx.stroke();
      }

      const isFocused = focus !== null && n.id === focus.id;
      if (isFocused || onPathNode || (selected && n.id === selected.id)) {
        ctx.strokeStyle = HIGHLIGHT;
        ctx.lineWidth = (onPathNode ? 2.5 : 2) / sim.scale;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r + 3.5 / sim.scale, 0, Math.PI * 2);
        ctx.stroke();
      }

      const showLabel = labelIds.has(n.id) || sim.scale > 1.9 || onPathNode;
      if (showLabel && (!dimmed || isFocused || onPathNode)) {
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

    // Ṭabaqāt tick labels, fixed to the left edge in screen space. Each band is
    // named for the Maʿṣūm who lived in it, so the axis reads as time.
    if (layoutRef.current === "tabaqat") {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      // "Earlier ↑ / later ↓" orientation cue at the top of the axis.
      ctx.font = "600 10px system-ui, sans-serif";
      ctx.fillStyle = INK_SECONDARY;
      ctx.fillText("EARLIER ↑", 10, 14);
      for (let gen = 0; gen <= UNDATED_BAND; gen++) {
        const y = tabaqaBandY(gen, h) * sim.scale + sim.ty;
        if (y < 26 || y > h - 8) continue;
        const undated = gen === UNDATED_BAND;
        ctx.font = `${undated ? "italic " : ""}10px system-ui, sans-serif`;
        ctx.fillStyle = INK_SECONDARY;
        const anchor = GENERATION_ANCHOR[gen];
        ctx.fillText(
          undated ? "generation unknown" : anchor ? `${gen} · ${anchor}` : `${gen}`,
          10,
          y
        );
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
      // Generous screen-space hit target per mark — fingers are far less precise
      // than a cursor, and the marks are only a few pixels wide when zoomed out.
      const touchLike = typeof window !== "undefined" && window.matchMedia("(pointer: coarse)").matches;
      const maxD = Math.max((touchLike ? 44 : 24) / sim.scale, 6);
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

    // Active touch points, so two fingers can pinch-zoom. Without this the only
    // zoom is the mouse wheel, which no phone has.
    const points = new Map<number, { x: number; y: number }>();
    let pinchDist = 0;

    const pinchGeometry = () => {
      const [a, b] = [...points.values()];
      const rect = canvas.getBoundingClientRect();
      return {
        dist: Math.hypot(a.x - b.x, a.y - b.y),
        cx: (a.x + b.x) / 2 - rect.left,
        cy: (a.y + b.y) / 2 - rect.top,
      };
    };

    const onPointerDown = (ev: PointerEvent) => {
      canvas.setPointerCapture(ev.pointerId);
      points.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
      if (points.size === 2) {
        // Second finger down: abandon drag/pan and start pinching.
        inter.dragging = null;
        inter.panning = false;
        pinchDist = pinchGeometry().dist;
        syncTooltip(null);
        return;
      }
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
      if (points.has(ev.pointerId)) {
        points.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
      }
      if (points.size >= 2) {
        const { dist, cx, cy } = pinchGeometry();
        if (pinchDist > 0 && dist > 0) zoomCamera(sim, cx, cy, dist / pinchDist);
        pinchDist = dist;
        return;
      }
      const dx = ev.clientX - inter.lastX;
      const dy = ev.clientY - inter.lastY;
      if (inter.dragging || inter.panning) inter.moved += Math.abs(dx) + Math.abs(dy);
      if (inter.dragging) {
        const p = toWorld(ev.clientX, ev.clientY);
        dragNodeTo(sim, inter.dragging, p.x, p.y);
        syncTooltip(null);
      } else if (inter.panning) {
        panCamera(sim, dx, dy);
      } else if (ev.pointerType === "mouse") {
        // Hover preview is a mouse affordance; on touch it would stick open.
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
      const wasPinching = points.size >= 2;
      points.delete(ev.pointerId);
      if (points.size < 2) pinchDist = 0;
      if (wasPinching) {
        inter.dragging = null;
        inter.panning = false;
        return;
      }
      if (inter.moved < 5) {
        const node = hitTest(ev.clientX, ev.clientY);
        selectedRef.current = node;
        setSelectedId(node?.id ?? null);
        // Touch has no hover, so a tap must dismiss the tooltip itself.
        if (ev.pointerType !== "mouse") syncTooltip(null);
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
    canvas.addEventListener("pointercancel", onPointerUp);
    canvas.addEventListener("pointerleave", onLeave);
    canvas.addEventListener("wheel", onWheel, { passive: false });
    return () => {
      canvas.removeEventListener("pointerdown", onPointerDown);
      canvas.removeEventListener("pointermove", onPointerMove);
      canvas.removeEventListener("pointerup", onPointerUp);
      canvas.removeEventListener("pointercancel", onPointerUp);
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
        setPathResult(null);
        pathHighlightRef.current = null;
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  /* --------------------------- search ---------------------------- */

  // Every narrator is findable — search the full Mu'jam directory (~15.6k),
  // not just the ~500 drawn nodes. Charted narrators fly into view on the plate;
  // the rest open their biography.
  const nodeIdByNarrator = useMemo(() => {
    const map = new Map<number, number>();
    if (graph) {
      for (const n of graph.nodes) if (n.narrator_id !== null) map.set(n.narrator_id, n.id);
    }
    return map;
  }, [graph]);

  useEffect(() => {
    const q = query.trim();
    let cancelled = false;
    // All setState runs inside the async timer/promise, never synchronously in
    // the effect body (avoids react-hooks/set-state-in-effect cascading renders).
    if (q.length < 2) {
      const clear = setTimeout(() => {
        if (!cancelled) {
          setDirResults([]);
          setDirLoading(false);
        }
      }, 0);
      return () => {
        cancelled = true;
        clearTimeout(clear);
      };
    }
    const timer = setTimeout(() => {
      if (cancelled) return;
      setDirLoading(true);
      getNarratorDirectory({ query: q, limit: 12 })
        .then((page) => {
          if (!cancelled) setDirResults(page.entries);
        })
        .catch(() => {
          if (!cancelled) setDirResults([]);
        })
        .finally(() => {
          if (!cancelled) setDirLoading(false);
        });
    }, 180);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query]);

  const flyToNode = useCallback((id: number) => {
    const sim = simRef.current;
    const node = sim.byId.get(id);
    if (!node) return;
    selectedRef.current = node;
    setSelectedId(id);
    setSearchOpen(false);
    flyCameraTo(sim, node);
  }, []);

  const openDirectoryEntry = useCallback(
    (entry: NarratorDirectoryEntry) => {
      const nodeId =
        entry.narrator_id !== null ? nodeIdByNarrator.get(entry.narrator_id) : undefined;
      if (nodeId !== undefined) {
        flyToNode(nodeId);
      } else {
        // Findable but not on the charted plate — go to the full biography.
        setSearchOpen(false);
        window.location.assign(`/narrators/${entry.narrator_id}`);
      }
    },
    [nodeIdByNarrator, flyToNode]
  );

  const resetView = useCallback(() => {
    resetCamera(simRef.current);
    selectedRef.current = null;
    setSelectedId(null);
  }, []);

  const openEvidence = useCallback((source: number, target: number, label: string) => {
    setEvidence({ source, target, label, data: null });
  }, []);

  /* --------------------------- path-finding ----------------------- */

  // Recompute the highlight set + frame the camera when the active path changes.
  // Only refs/sim are mutated here (no setState), so no cascading renders.
  useEffect(() => {
    const active = pathResult?.found ? pathResult.paths[activePathIdx] : null;
    if (!active) {
      pathHighlightRef.current = null;
      return;
    }
    pathHighlightRef.current = {
      nodes: new Set(active.nodes.map((n) => n.id)),
      edges: new Set(active.hops.map((h) => `${h.source}->${h.target}`)),
    };
    const sim = simRef.current;
    const pts = active.nodes
      .map((n) => sim.byId.get(n.id))
      .filter((n): n is SimNode => Boolean(n));
    if (pts.length) fitCameraToNodes(sim, pts);
  }, [pathResult, activePathIdx]);

  const findPath = useCallback(() => {
    if (!pathFrom || !pathTo) return;
    setPathLoading(true);
    setPathError(null);
    setPathResult(null);
    setActivePathIdx(0);
    getTransmissionPaths({ fromPerson: pathFrom.id, toPerson: pathTo.id, k: 5 })
      .then((res) => setPathResult(res))
      .catch(() => setPathError("Could not compute a path."))
      .finally(() => setPathLoading(false));
  }, [pathFrom, pathTo]);

  const clearPath = useCallback(() => {
    setPathResult(null);
    setPathError(null);
    pathHighlightRef.current = null;
  }, []);

  const closePathFinder = useCallback(() => {
    setPathOpen(false);
    setPathFrom(null);
    setPathTo(null);
    clearPath();
  }, [clearPath]);

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

  const legendPosition =
    layout === "tabaqat"
      ? selected || evidence
        ? "bottom-3 left-3"
        : "right-3 top-3"
      : "bottom-3 left-3";

  const visibleStats = useMemo(() => {
    if (!graph) return { nodes: 0, edges: 0, uncertain: 0, anchoredGen: 0 };
    const kept = graph.edges.filter((e) => e.count >= minWeight);
    const touched = new Set<number>();
    kept.forEach((e) => {
      touched.add(e.source);
      touched.add(e.target);
    });
    const byId = new Map(graph.nodes.map((n) => [n.id, n]));
    let uncertain = 0;
    let anchoredGen = 0;
    touched.forEach((id) => {
      const n = byId.get(id);
      if (n?.uncertain) uncertain += 1;
      if (n?.generation_anchored) anchoredGen += 1;
    });
    return { nodes: touched.size, edges: kept.length, uncertain, anchoredGen };
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
      <div className="mb-4 grid items-center gap-3 sm:grid-cols-2 lg:grid-cols-[minmax(13rem,1fr)_auto_auto_auto_auto_auto]">
        <div className="relative min-w-0">
          <input
            type="search"
            value={query}
            onChange={(ev) => {
              setQuery(ev.target.value);
              setSearchOpen(true);
            }}
            onFocus={() => setSearchOpen(true)}
            onKeyDown={(ev) => {
              if (ev.key === "Enter" && dirResults.length) openDirectoryEntry(dirResults[0]);
            }}
            placeholder="Find any narrator…"
            aria-label="Find any narrator in the Muʿjam"
            className="min-h-11 w-full rounded-md border border-border bg-surface px-4 py-2 text-sm outline-none focus:border-accent focus:ring-1 focus:ring-accent"
          />
          {searchOpen && query.trim().length >= 2 && (
            <ul className="absolute z-30 mt-1 max-h-80 w-full min-w-0 overflow-auto rounded-md border border-border bg-surface shadow-lg sm:w-96">
              {dirResults.length === 0 ? (
                <li className="px-4 py-3 text-xs text-muted">
                  {dirLoading ? "Searching the narrator directory…" : "No narrator found."}
                </li>
              ) : (
                dirResults.map((entry) => {
                  const charted = entry.charted_hadith_count > 0;
                  return (
                    <li key={entry.narrator_id}>
                      <button
                        type="button"
                        onClick={() => openDirectoryEntry(entry)}
                        className="flex min-h-11 w-full items-center justify-between gap-3 px-4 py-2 text-right hover:bg-background"
                      >
                        <span className="shrink-0 text-[11px] text-muted">
                          {charted
                            ? `${numberFormat.format(entry.charted_hadith_count)} in al-Kāfī`
                            : "profile ↗"}
                        </span>
                        <span
                          dir="rtl"
                          lang="ar"
                          className={`${amiri.className} truncate text-[15px] ${
                            charted ? "" : "text-muted"
                          }`}
                        >
                          {formatArabicText(entry.canonical_name_ar)}
                        </span>
                      </button>
                    </li>
                  );
                })
              )}
            </ul>
          )}
        </div>

        <label className="flex min-w-0 items-center gap-3 text-sm text-muted sm:justify-self-start">
          Min. shared hadiths
          <input
            type="range"
            min={1}
            max={15}
            value={minWeight}
            onChange={(ev) => setMinWeight(Number(ev.target.value))}
            className="min-w-20 flex-1 accent-[var(--accent)] sm:w-28 sm:flex-none"
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
          onClick={() => setIncludeUncertain((on) => !on)}
          aria-pressed={includeUncertain}
          className={`min-h-11 rounded-md border px-4 py-1.5 text-sm transition ${
            includeUncertain
              ? "border-accent bg-accent text-accent-foreground"
              : "border-border bg-surface text-foreground/70 hover:text-accent"
          }`}
          title="Also show narrators the resolver could only guess (ambiguous), clearly marked as provisional"
        >
          Show uncertain
        </button>

        <button
          type="button"
          onClick={resetView}
          className="min-h-11 rounded-md border border-border bg-surface px-4 py-1.5 text-sm text-foreground/70 transition hover:text-accent"
        >
          Reset view
        </button>

        <p className="border-t border-border pt-3 text-sm leading-6 text-muted sm:col-span-2 lg:col-span-6">
          {graph
            ? `${numberFormat.format(visibleStats.nodes)} narrators · ${numberFormat.format(visibleStats.edges)} transmission links`
            : "Charting the network…"}
          {graph && includeUncertain && visibleStats.uncertain > 0
            ? ` · ${numberFormat.format(visibleStats.uncertain)} provisional`
            : ""}
          {graph && graph.decisions_applied > 0
            ? ` · ${numberFormat.format(graph.decisions_applied)} review corrections applied`
            : ""}
          {graph?.computed_at ? ` · as of ${formatComputedAt(graph.computed_at)}` : ""}
        </p>

        {/* The ṭabaqāt axis is a chronology claim, and most of it is inferred.
            Say so plainly rather than letting the layout imply certainty. */}
        {layout === "tabaqat" && graph ? (
            <p className="rounded-md border border-dashed border-border px-3 py-2 text-xs leading-5 text-muted sm:col-span-2 lg:col-span-6">
            Only{" "}
            <span className="font-semibold text-foreground">
              {numberFormat.format(visibleStats.anchoredGen)}
            </span>{" "}
            of {numberFormat.format(visibleStats.nodes)} narrators here have a generation fixed by a
            companionship record. The rest stay in the unknown band; propagated estimates are
            shown only in their details and do not set a dated position.
          </p>
        ) : null}

        {/* Book coverage — honest about what is charted vs. still coming. */}
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5 text-xs text-muted sm:col-span-2 lg:col-span-6">
          <span className="uppercase tracking-wide text-[11px] text-foreground/60">Charted</span>
          <span className="inline-flex items-center rounded-full border border-accent/40 bg-badge-verified px-2.5 py-0.5 text-accent">
            al-Kāfī
          </span>
          <span aria-hidden className="opacity-50">·</span>
          <span className="uppercase tracking-wide text-[11px] text-foreground/60">Coming</span>
          {["Faqīh", "Tahdhīb", "Istibṣār"].map((b) => (
            <span
              key={b}
              className="inline-flex items-center rounded-full border border-dashed border-border px-2.5 py-0.5"
              title="Chains being resolved — will join the network when polished"
            >
              {b}
            </span>
          ))}
          <span className="text-muted/80">— yet every narrator in the Muʿjam is searchable above.</span>
        </div>
      </div>

      {/* The plate */}
      <div
        ref={wrapRef}
        className="relative h-[68svh] min-h-[430px] w-full overflow-hidden rounded-md border border-border shadow-[inset_0_0_48px_rgba(0,0,0,0.28)] sm:h-[72vh] sm:min-h-[480px]"
        style={{ background: PLATE_BG }}
      >
        {/* touch-none is essential on mobile: without it the browser claims the
            drag for page-scrolling and the graph can barely be panned at all. */}
        <canvas
          ref={canvasRef}
          className="block h-full w-full touch-none cursor-grab"
          aria-label="Narrator transmission network graph"
          role="img"
        />

        {!graph && !error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="animate-pulse text-sm" style={{ color: INK_SECONDARY }}>
              Charting the network…
            </p>
          </div>
        )}

        {/* Path finder — top left */}
        {graph && !pathOpen && (
          <button
            type="button"
            onClick={() => setPathOpen(true)}
            className="absolute left-3 top-3 z-10 rounded-md px-3 py-2 text-xs font-medium transition hover:opacity-90"
            style={{
              background: "rgba(15,24,19,0.9)",
              border: "1px solid rgba(236,231,214,0.16)",
              color: INK_PRIMARY,
            }}
          >
            Trace a path ↝
          </button>
        )}
        {graph && pathOpen && (
          <aside
            className="absolute inset-x-2 bottom-2 z-30 flex max-h-[72%] flex-col overflow-y-auto rounded-md p-4 sm:inset-x-auto sm:bottom-auto sm:left-3 sm:top-3 sm:max-h-[calc(100%-1.5rem)] sm:w-80 sm:max-w-[calc(100%-1.5rem)]"
            style={{
              background: "rgba(15,24,19,0.96)",
              border: "1px solid rgba(236,231,214,0.18)",
              backdropFilter: "blur(6px)",
            }}
          >
            <div className="flex items-start justify-between gap-3">
              <p className="text-[11px] font-semibold uppercase tracking-wide" style={{ color: INK_SECONDARY }}>
                Trace a transmission path
              </p>
              <button
                type="button"
                onClick={closePathFinder}
                aria-label="Close path finder"
                className="rounded-md px-2 text-lg leading-none transition hover:opacity-70"
                style={{ color: INK_SECONDARY }}
              >
                ×
              </button>
            </div>
            <p className="mt-1 text-[11px]" style={{ color: INK_SECONDARY }}>
              From a narrator, following who taught whom, to an Imam or another narrator.
            </p>

            <div className="mt-3 space-y-1.5">
              <GraphNodePicker nodes={graph.nodes} placeholder="From (student)…" value={pathFrom} onChange={setPathFrom} />
              <p className="text-center text-[10px] uppercase tracking-wide" style={{ color: INK_SECONDARY }}>
                ↓ narrates from
              </p>
              <GraphNodePicker nodes={graph.nodes} placeholder="To (teacher / Imam)…" value={pathTo} onChange={setPathTo} />
            </div>

            <button
              type="button"
              onClick={findPath}
              disabled={!pathFrom || !pathTo || pathLoading}
              className="mt-3 min-h-10 rounded-md px-4 py-2 text-sm font-medium transition disabled:opacity-40"
              style={{ background: IMAM_GOLD, color: "#171207" }}
            >
              {pathLoading ? "Searching…" : "Find path"}
            </button>

            <div className="mt-3 overflow-y-auto">
              {pathError && (
                <p className="py-2 text-xs" style={{ color: QUALITY_CONTRADICTED }}>{pathError}</p>
              )}
              {pathResult && !pathResult.found && (
                <p className="py-2 text-xs" style={{ color: INK_SECONDARY }}>
                  No confident transmission path between these two in al-Kāfī. Try a closer pair.
                </p>
              )}
              {pathResult && pathResult.found && (
                <>
                  {pathResult.reversed && (
                    <p className="mb-1 text-[11px]" style={{ color: INK_SECONDARY }}>
                      Oriented in transmission order (your picks were reversed).
                    </p>
                  )}
                  {pathResult.paths.length > 1 && (
                    <div className="mb-2 flex flex-wrap gap-1">
                      {pathResult.paths.map((p, i) => (
                        <button
                          key={i}
                          type="button"
                          onClick={() => setActivePathIdx(i)}
                          aria-pressed={i === activePathIdx}
                          className={`rounded px-2 py-0.5 text-[11px] transition ${
                            i === activePathIdx ? "bg-accent text-accent-foreground" : ""
                          }`}
                          style={i === activePathIdx ? {} : { border: "1px solid rgba(236,231,214,0.2)", color: INK_SECONDARY }}
                        >
                          {p.length} hops
                        </button>
                      ))}
                    </div>
                  )}
                  <ol>
                    {pathResult.paths[activePathIdx].nodes.map((node, i, arr) => (
                      <li key={`${node.id}-${i}`}>
                        <button
                          type="button"
                          onClick={() => flyToNode(node.id)}
                          className="flex w-full items-center justify-end rounded px-2 py-1 text-right transition hover:bg-[#f2ead9]/5"
                        >
                          <span
                            dir="rtl"
                            lang="ar"
                            className={`${amiri.className} truncate text-[15px]`}
                            style={{ color: node.kind === "imam" ? IMAM_GOLD_BRIGHT : INK_PRIMARY }}
                          >
                            {formatArabicText(node.label)}
                          </span>
                        </button>
                        {i < arr.length - 1 && (
                          <p className="pr-3 text-[10px]" style={{ color: INK_SECONDARY }}>
                            ↓ {numberFormat.format(pathResult.paths[activePathIdx].hops[i].count)} shared hadiths
                          </p>
                        )}
                      </li>
                    ))}
                  </ol>
                </>
              )}
            </div>
          </aside>
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
              <p
                className="text-xs font-medium"
                style={{
                  color:
                    hoveredNode.role === "compiler"
                      ? COMPILER
                      : hoveredNode.kind === "imam"
                        ? IMAM_GOLD_BRIGHT
                        : INK_SECONDARY,
                }}
              >
                {ROLE_LABEL[hoveredNode.role] ?? "Narrator"}
              </p>
              <p className="text-xs" style={{ color: INK_SECONDARY }}>
                {hoveredNode.generation !== null
                  ? `${hoveredNode.generation_anchored ? "Generation" : "Estimated generation"} ${hoveredNode.generation}${
                      GENERATION_ANCHOR[hoveredNode.generation]
                        ? ` · ${GENERATION_ANCHOR[hoveredNode.generation]}`
                        : ""
                    }`
                  : "Generation unknown"}
                {hoveredNode.merged_person_ids.length > 1
                  ? ` · ${hoveredNode.merged_person_ids.length} merged identities`
                  : ""}
              </p>
              {hoveredNode.generation !== null && (
                <p
                  className="text-[11px]"
                  style={{ color: hoveredNode.generation_anchored ? INK_SECONDARY : UNCERTAIN }}
                >
                  {hoveredNode.generation_anchored
                    ? "Dated from a companionship record"
                    : "Date inferred from transmission — may be unreliable"}
                </p>
              )}
              {hoveredNode.uncertain && (
                <p className="text-xs font-medium" style={{ color: UNCERTAIN }}>
                  Best guess — not confirmed
                </p>
              )}
              <p className="mt-1 text-[11px]" style={{ color: INK_SECONDARY }}>
                Click for details
              </p>
            </>
          )}
        </div>

        {/* Legend. Collapsible, and it moves to the right in ṭabaqāt mode so it
            never sits on top of the generation axis labels down the left edge. */}
        <details
          open={legendOpen}
          onToggle={(ev) => setLegendOpen((ev.currentTarget as HTMLDetailsElement).open)}
          className={`absolute z-50 max-w-[min(15rem,calc(100%-1.5rem))] rounded-md px-3.5 py-2.5 text-[11px] leading-5 ${legendPosition}`}
          style={{
            background: "rgba(15, 24, 19, 0.92)",
            border: "1px solid rgba(236, 231, 214, 0.12)",
            color: INK_SECONDARY,
          }}
        >
          <summary className="cursor-pointer list-none select-none font-medium" style={{ color: INK_PRIMARY }}>
            Legend <span className="opacity-60">{legendOpen ? "▾" : "▸"}</span>
          </summary>
          <div className="mt-2">
          <p className="flex items-center gap-2">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ background: IMAM_GOLD, boxShadow: "0 0 6px rgba(232,181,74,0.8)" }}
            />
            <span style={{ color: INK_PRIMARY }}>The Imams</span>
          </p>
          <p className="flex items-center gap-2">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ background: COMPILER, boxShadow: `0 0 0 1.5px ${COMPILER}40` }}
            />
            <span style={{ color: INK_PRIMARY }}>Compiler of the book</span>
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
          {includeUncertain && (
            <p className="flex items-center gap-2">
              <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: UNCERTAIN }} />
              Best guess (unconfirmed)
            </p>
          )}
          {layout === "tabaqat" && (
            <p className="flex items-center gap-2">
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ background: ERA_RAMP[2], opacity: 0.45 }}
              />
              Faded = estimate only
            </p>
          )}
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
        </details>

        {/* Detail panel */}
        {selected && (
          <aside
            // Phone: a bottom sheet inside the plate. Desktop: a floating card
            // that scrolls rather than overflowing the plate — a narrator with
            // many teachers/students used to run off the bottom edge.
            className="absolute inset-x-2 bottom-2 z-30 max-h-[60%] overflow-y-auto overscroll-contain rounded-md p-4 sm:inset-x-auto sm:bottom-3 sm:right-3 sm:top-3 sm:w-80 sm:max-w-[calc(100%-1.5rem)]"
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
              <span
                className="font-medium"
                style={{
                  color:
                    selected.role === "compiler"
                      ? COMPILER
                      : selected.kind === "imam"
                        ? IMAM_GOLD_BRIGHT
                        : INK_PRIMARY,
                }}
              >
                {ROLE_LABEL[selected.role] ?? "Narrator"}
              </span>
              {" · "}
              {selected.generation !== null ? (
                <span style={{ color: selected.generation_anchored ? undefined : UNCERTAIN }}>
                  {`Gen ${selected.generation}${
                    GENERATION_ANCHOR[selected.generation]
                      ? ` (${GENERATION_ANCHOR[selected.generation]})`
                      : ""
                  }`}
                  {selected.generation_anchored ? "" : " — inferred"}
                </span>
              ) : (
                "Generation unknown"
              )}
              {" · "}
              <span className="font-semibold" style={{ color: INK_PRIMARY }}>
                {numberFormat.format(selected.hadith_count)}
              </span>{" "}
              hadiths
              {selected.merged_person_ids.length > 1
                ? ` · ${selected.merged_person_ids.length} identities merged`
                : ""}
            </p>
            {selected.merged_person_ids.length > 1 && (
              <p className="mt-1 text-[11px] leading-5" style={{ color: UNCERTAIN }}>
                This dot is an identity cluster. The line evidence below is the actual
                chain order; the shorter display name may represent a longer name variant.
              </p>
            )}
            {selected.merged_labels && selected.merged_labels.length > 1 && (
              <p dir="rtl" lang="ar" className={`${amiri.className} mt-1 text-right text-[13px] leading-6`} style={{ color: INK_SECONDARY }}>
                {selected.merged_labels.map(formatArabicText).join(" / ")}
              </p>
            )}

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

            <button
              type="button"
              onClick={() => {
                setPathFrom({ id: selected.id, label: selected.label });
                setPathTo(null);
                clearPath();
                setPathOpen(true);
              }}
              className="mt-3 flex min-h-10 w-full items-center justify-center rounded-md px-4 py-2 text-center text-sm transition hover:bg-[#f2ead9]/5"
              style={{ border: "1px solid rgba(236,231,214,0.2)", color: INK_PRIMARY }}
            >
              Trace a path from here ↝
            </button>

            {selected.narrator_id !== null && (
              <Link
                href={`/narrators/${selected.narrator_id}`}
                className="mt-2 flex min-h-11 items-center justify-center rounded-md px-4 py-2 text-center text-sm font-medium transition hover:opacity-90"
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
            className="absolute inset-x-2 bottom-2 z-40 flex max-h-[60%] flex-col rounded-md p-4 sm:inset-x-auto sm:right-3 sm:w-96 sm:max-w-[calc(100%-1.5rem)]"
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
            <th className="px-5 py-2">Student → teacher</th>
            <th className="px-5 py-2">Resolved teacher</th>
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
