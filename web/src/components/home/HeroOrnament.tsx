/** Slow-rotating geometric rosette behind the hero — pure SVG, no assets.
 * Two layers spin in opposite directions at glacial speed so the page feels
 * alive without drawing attention to itself. Hidden from screen readers. */
export function HeroOrnament() {
  const spokes = Array.from({ length: 16 }, (_, i) => i * 22.5);

  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* soft color washes */}
      <div className="animate-drift absolute -top-32 left-1/2 h-[28rem] w-[28rem] -translate-x-[80%] rounded-full bg-accent/[0.07] blur-3xl" />
      <div
        className="animate-drift absolute -bottom-40 left-1/2 h-[26rem] w-[26rem] translate-x-[15%] rounded-full bg-gold/[0.09] blur-3xl"
        style={{ animationDelay: "-7s" }}
      />

      {/* rosette */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
        <svg
          viewBox="0 0 400 400"
          className="animate-spin-slower h-[42rem] w-[42rem] text-accent opacity-[0.08]"
          fill="none"
          stroke="currentColor"
          strokeWidth="1"
        >
          <circle cx="200" cy="200" r="196" />
          <circle cx="200" cy="200" r="150" />
          <circle cx="200" cy="200" r="100" />
          <rect x="60" y="60" width="280" height="280" />
          <rect x="60" y="60" width="280" height="280" transform="rotate(45 200 200)" />
          {spokes.map((angle) => (
            <line key={angle} x1="200" y1="4" x2="200" y2="50" transform={`rotate(${angle} 200 200)`} />
          ))}
        </svg>
        <svg
          viewBox="0 0 400 400"
          className="animate-spin-slower-reverse absolute inset-0 m-auto h-[30rem] w-[30rem] text-gold opacity-[0.1]"
          fill="none"
          stroke="currentColor"
          strokeWidth="1"
        >
          <circle cx="200" cy="200" r="180" strokeDasharray="2 10" />
          <rect x="88" y="88" width="224" height="224" transform="rotate(22.5 200 200)" />
          <rect x="88" y="88" width="224" height="224" transform="rotate(67.5 200 200)" />
        </svg>
      </div>
    </div>
  );
}
