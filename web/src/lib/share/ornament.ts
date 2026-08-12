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
 * The illuminated headpiece — the *ʿunwān* that opens a manuscript page.
 *
 * A short narration leaves the folio with more page than words, and the
 * tradition's answer to that has never been to pad the margins: it is to
 * illuminate. A ruled band, a star medallion held at its centre, and an
 * interlace of alternating arcs running out to the edges — the guilloche a
 * scribe rules with a compass, drawn here with the same eight-fold geometry as
 * the rest of the folio so it reads as one hand.
 *
 * Sized by the caller from whatever space the narration did not want, so a full
 * page of text is never given one.
 */
export function drawIlluminatedBand(
  ctx: CanvasRenderingContext2D,
  region: { x: number; y: number; width: number; height: number },
  colors: { line: string; accent: string; reserve: string }
): void {
  const { x, y, width, height } = region;
  const cy = y + height / 2;
  const radius = Math.min(height * 0.46, 40);

  ctx.save();

  // The band is ruled top and bottom, which is what makes it read as a band
  // rather than as ornament floating loose on the page.
  ctx.strokeStyle = colors.line;
  ctx.lineWidth = 1.5;
  ctx.globalAlpha = 0.75;
  for (const edge of [y, y + height]) {
    ctx.beginPath();
    ctx.moveTo(x, edge + 0.5);
    ctx.lineTo(x + width, edge + 0.5);
    ctx.stroke();
  }

  // A star-and-cross frieze filling the band, clipped to it so the run is cut
  // by the rules at either end the way a ruled border actually terminates.
  // The same lattice as the ground field, at a cell sized to the band.
  const cx = x + width / 2;
  // The cell runs wider than the band is tall, and the star sits well inside
  // it: packed edge to edge the run reads as a sawtooth strip, and a star cut
  // off at its points by the rule above reads as an accident rather than as a
  // border running on. Ground between the motifs is what makes it a frieze.
  const cell = Math.max(38, height * 1.2);
  const starR = Math.min(height * 0.3, cell * 0.26);
  ctx.save();
  ctx.beginPath();
  ctx.rect(x, y, width, height);
  ctx.clip();
  ctx.globalAlpha = 0.55;
  ctx.strokeStyle = colors.accent;
  ctx.lineWidth = 1.3;
  ctx.lineJoin = "round";
  // Only whole motifs. The run is centred on the medallion and stops at the
  // last star that fits inside the rules, so the frieze ends on a complete
  // figure rather than on a star sliced down the middle.
  const margin = 12;
  const half = width / 2 - margin;
  const reach = Math.max(0, Math.floor((half - starR) / cell));
  const diamondR = cell * 0.1;
  for (let i = -reach; i <= reach; i += 1) {
    const px = cx + i * cell;
    // Leave the middle clear for the medallion.
    if (Math.abs(px - cx) > radius + cell * 0.4) {
      starPath(ctx, px, cy, starR, 8, Math.PI / 8);
      ctx.stroke();
    }
    for (const dx of [px - cell / 2, px + cell / 2]) {
      if (Math.abs(dx - cx) <= radius + cell * 0.3) continue;
      if (Math.abs(dx - cx) + diamondR > half) continue;
      diamondPath(ctx, dx, cy, diamondR);
      ctx.stroke();
    }
  }
  ctx.restore();

  // The medallion, set into a reserve so the frieze reads as running behind it
  // rather than colliding with it.
  ctx.globalAlpha = 1;
  ctx.fillStyle = colors.reserve;
  ctx.beginPath();
  ctx.arc(cx, cy, radius + 9, 0, Math.PI * 2);
  ctx.fill();

  ctx.globalAlpha = 0.95;
  ctx.strokeStyle = colors.accent;
  ctx.lineWidth = 1.8;
  ctx.lineJoin = "round";
  starPath(ctx, cx, cy, radius, 8, Math.PI / 8);
  ctx.stroke();
  ctx.lineWidth = 1.1;
  starPath(ctx, cx, cy, radius * 0.54, 8, 0);
  ctx.stroke();

  ctx.restore();
}

/**
 * The closing pendant, set above the colophon.
 *
 * Where the headpiece opens the page, this ends it: a rosette with a short
 * pair of rules either side, then two dots and a final one, tapering to a
 * point. A scribe closes a text this way so the last line reads as finished
 * rather than merely stopped.
 */
export function drawTailpiece(
  ctx: CanvasRenderingContext2D,
  cx: number,
  y: number,
  width: number,
  height: number,
  colors: { line: string; accent: string }
): void {
  const radius = Math.max(8, Math.min(height * 0.32, 15));

  ctx.save();
  ctx.lineJoin = "round";

  // Short rules either side of the rosette, kept well inside the measure so
  // this never competes with the footer rule below it.
  const reach = Math.min(width * 0.22, 150);
  ctx.strokeStyle = colors.line;
  ctx.lineWidth = 1.5;
  ctx.globalAlpha = 0.85;
  for (const direction of [-1, 1]) {
    ctx.beginPath();
    ctx.moveTo(cx + direction * (radius + 16), y + 0.5);
    ctx.lineTo(cx + direction * reach, y + 0.5);
    ctx.stroke();
  }

  ctx.strokeStyle = colors.accent;
  ctx.globalAlpha = 0.9;
  ctx.lineWidth = 1.6;
  starPath(ctx, cx, y, radius, 8, Math.PI / 8);
  ctx.stroke();
  ctx.lineWidth = 1.1;
  starPath(ctx, cx, y, radius * 0.44, 8, 0);
  ctx.stroke();

  // The pendant proper: a diamond hung directly below the rosette on the same
  // axis, tapering to a final point. Stacked on one axis it reads as an ending;
  // dots set side by side just read as punctuation.
  ctx.globalAlpha = 0.85;
  ctx.lineWidth = 1.3;
  diamondPath(ctx, cx, y + radius + height * 0.34, radius * 0.42);
  ctx.stroke();
  ctx.fillStyle = colors.accent;
  ctx.beginPath();
  ctx.arc(cx, y + radius + height * 0.72, 2.3, 0, Math.PI * 2);
  ctx.fill();

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
