// The manuscript layer of the shareable folio.
//
// Everything here is constructed, not traced: an eight-fold girih tessellation,
// the multi-rule frame (*jadwal*) a manuscript page is ruled with, corner
// pieces, a rosette to part the chain from the words, and paper grain. Drawing
// the geometry rather than shipping decorative assets keeps it crisp at any
// size, recolours it with the reader's theme for free, and means no clip-art
// arabesque — the ornament this tradition actually uses is mathematical, and
// the honest way to render it is to compute it.

/** Regular {8/3} star — the *khatim*. Its inner radius is √2−1 of the outer,
 *  which is what gives the eight points their characteristic sharpness. */
const STAR_INNER_RATIO = Math.SQRT2 - 1;

function starPath(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number,
  points = 8,
  rotation = 0
): void {
  const inner = radius * STAR_INNER_RATIO;
  ctx.beginPath();
  for (let i = 0; i < points * 2; i += 1) {
    const angle = rotation + (i * Math.PI) / points;
    const r = i % 2 === 0 ? radius : inner;
    const x = cx + Math.cos(angle) * r;
    const y = cy + Math.sin(angle) * r;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.closePath();
}

function diamondPath(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number
): void {
  ctx.beginPath();
  for (let i = 0; i < 4; i += 1) {
    const angle = (i * Math.PI) / 2;
    const x = cx + Math.cos(angle) * radius;
    const y = cy + Math.sin(angle) * radius;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.closePath();
}

/**
 * Fill a region with the star-and-cross girih field.
 *
 * Stars sit on a square lattice with diamonds at the interstices; the negative
 * space between them resolves into the crosses the pattern is named for. Kept
 * at a whisper of opacity — this is the ground the folio sits on, and the
 * moment it competes with the narration it has failed.
 */
export function drawGirihField(
  ctx: CanvasRenderingContext2D,
  region: { x: number; y: number; width: number; height: number },
  options: { color: string; alpha: number; cell: number; lineWidth?: number }
): void {
  const { color, alpha, cell, lineWidth = 1.4 } = options;
  ctx.save();
  ctx.beginPath();
  ctx.rect(region.x, region.y, region.width, region.height);
  ctx.clip();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.lineJoin = "round";

  const radius = cell * 0.46;
  const startX = region.x - cell;
  const startY = region.y - cell;
  const endX = region.x + region.width + cell;
  const endY = region.y + region.height + cell;

  for (let y = startY; y <= endY; y += cell) {
    for (let x = startX; x <= endX; x += cell) {
      starPath(ctx, x, y, radius, 8, Math.PI / 8);
      ctx.stroke();
      diamondPath(ctx, x + cell / 2, y + cell / 2, cell * 0.2);
      ctx.stroke();
    }
  }
  ctx.restore();
}

/**
 * The ruled frame of a manuscript page.
 *
 * Real *jadwal* is never one line: a hairline, a gap, a weighted rule in the
 * bibliographic colour, a gap, another hairline. The rhythm is what reads as
 * "ruled by hand" rather than "bordered by CSS".
 */
export function drawManuscriptFrame(
  ctx: CanvasRenderingContext2D,
  frame: { x: number; y: number; width: number; height: number },
  colors: { line: string; accent: string }
): void {
  const { x, y, width, height } = frame;
  ctx.save();

  ctx.strokeStyle = colors.line;
  ctx.lineWidth = 1.5;
  ctx.strokeRect(x + 0.75, y + 0.75, width - 1.5, height - 1.5);

  ctx.strokeStyle = colors.accent;
  ctx.lineWidth = 2.5;
  ctx.globalAlpha = 0.85;
  ctx.strokeRect(x + 11, y + 11, width - 22, height - 22);

  ctx.globalAlpha = 0.5;
  ctx.strokeStyle = colors.line;
  ctx.lineWidth = 1;
  ctx.strokeRect(x + 19, y + 19, width - 38, height - 38);

  ctx.restore();
}

/**
 * Corner pieces on the weighted rule.
 *
 * A short bracket stepped inward on each corner, which is how a ruled page
 * resolves its frame without a full illuminated cartouche.
 */
export function drawCornerPieces(
  ctx: CanvasRenderingContext2D,
  frame: { x: number; y: number; width: number; height: number },
  color: string,
  arm = 34
): void {
  const inset = 11;
  const { x, y, width, height } = frame;
  const corners: [number, number, number, number][] = [
    [x + inset, y + inset, 1, 1],
    [x + width - inset, y + inset, -1, 1],
    [x + inset, y + height - inset, 1, -1],
    [x + width - inset, y + height - inset, -1, -1],
  ];

  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = 2.5;
  ctx.lineCap = "round";
  for (const [cx, cy, sx, sy] of corners) {
    // Step in, run along, step back — a small squared spiral, the plainest
    // corner motif in the repertoire and the one that never looks fussy.
    ctx.beginPath();
    ctx.moveTo(cx + sx * arm, cy);
    ctx.lineTo(cx + sx * 12, cy);
    ctx.lineTo(cx + sx * 12, cy + sy * 12);
    ctx.lineTo(cx, cy + sy * 12);
    ctx.lineTo(cx, cy + sy * arm);
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(cx + sx * 20, cy + sy * 20, 3, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
  }
  ctx.restore();
}

/**
 * A rosette flanked by rules — the divider between the chain and the words.
 *
 * This is the one ornamental moment inside the text panel, and it earns its
 * place: it marks exactly where provenance ends and the narration begins.
 */
export function drawRosetteDivider(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  colors: { line: string; accent: string }
): void {
  const cx = x + width / 2;
  const radius = 11;
  const gap = radius + 16;

  ctx.save();
  ctx.strokeStyle = colors.line;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(x, y + 0.5);
  ctx.lineTo(cx - gap, y + 0.5);
  ctx.moveTo(cx + gap, y + 0.5);
  ctx.lineTo(x + width, y + 0.5);
  ctx.stroke();

  ctx.strokeStyle = colors.accent;
  ctx.lineWidth = 1.6;
  ctx.lineJoin = "round";
  starPath(ctx, cx, y + 0.5, radius, 8, Math.PI / 8);
  ctx.stroke();
  starPath(ctx, cx, y + 0.5, radius * 0.44, 8, 0);
  ctx.stroke();

  // Two small dots outboard of the rosette, so the rules end deliberately
  // rather than just stopping.
  ctx.fillStyle = colors.accent;
  for (const dx of [-gap + 7, gap - 7]) {
    ctx.beginPath();
    ctx.arc(cx + dx, y + 0.5, 2, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

/**
 * A bare rosette, used as a footer mark.
 *
 * Deliberately ornamental and nothing else. Anything resembling a badge — a
 * seal, a tick, a shield — would be read as a verdict on the narration, and
 * this project grades nothing on a shared image.
 */
export function drawStarMark(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number,
  color: string
): void {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  ctx.lineJoin = "round";
  starPath(ctx, cx, cy, radius, 8, Math.PI / 8);
  ctx.stroke();
  ctx.restore();
}

/**
 * Paper grain.
 *
 * A flat fill reads as a colour swatch; a little tooth reads as a sheet. Built
 * once as a small tile and repeated, rather than perturbing two million pixels.
 */
export function drawGrain(
  ctx: CanvasRenderingContext2D,
  region: { x: number; y: number; width: number; height: number },
  alpha: number,
  seedTile = 96
): void {
  const tile = document.createElement("canvas");
  tile.width = seedTile;
  tile.height = seedTile;
  const tileCtx = tile.getContext("2d");
  if (!tileCtx) return;
  const image = tileCtx.createImageData(seedTile, seedTile);
  for (let i = 0; i < image.data.length; i += 4) {
    const value = 110 + Math.random() * 145;
    image.data[i] = value;
    image.data[i + 1] = value;
    image.data[i + 2] = value;
    image.data[i + 3] = 255;
  }
  tileCtx.putImageData(image, 0, 0);

  const pattern = ctx.createPattern(tile, "repeat");
  if (!pattern) return;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.globalCompositeOperation = "overlay";
  ctx.fillStyle = pattern;
  ctx.fillRect(region.x, region.y, region.width, region.height);
  ctx.restore();
}
