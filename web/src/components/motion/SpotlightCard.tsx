"use client";

import { motion, useMotionValue, useMotionTemplate, useReducedMotion } from "motion/react";
import { useRef, type ReactNode } from "react";

/**
 * Card wrapper with a cursor-following radial spotlight and a gentle 3D tilt.
 * Pure presentation — pass any content as children. The spotlight uses a
 * masked radial gradient tied to live pointer motion values.
 */
export function SpotlightCard({
  children,
  className = "",
  tilt = 6,
}: {
  children: ReactNode;
  className?: string;
  tilt?: number;
}) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const mx = useMotionValue(-200);
  const my = useMotionValue(-200);
  const rx = useMotionValue(0);
  const ry = useMotionValue(0);

  const spotlight = useMotionTemplate`radial-gradient(220px circle at ${mx}px ${my}px, color-mix(in srgb, var(--accent) 22%, transparent), transparent 65%)`;

  function handleMove(e: React.MouseEvent<HTMLDivElement>) {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    mx.set(px);
    my.set(py);
    if (!reduce) {
      ry.set(((px / rect.width) - 0.5) * tilt * 2);
      rx.set(-((py / rect.height) - 0.5) * tilt * 2);
    }
  }

  function reset() {
    mx.set(-200);
    my.set(-200);
    rx.set(0);
    ry.set(0);
  }

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMove}
      onMouseLeave={reset}
      style={{ rotateX: rx, rotateY: ry, transformPerspective: 1000 }}
      whileHover={reduce ? undefined : { y: -4 }}
      transition={{ type: "spring", stiffness: 250, damping: 20 }}
      className={`group/spot relative ${className}`}
    >
      <motion.span
        aria-hidden
        className="pointer-events-none absolute inset-0 rounded-[inherit] opacity-0 transition-opacity duration-300 group-hover/spot:opacity-100"
        style={{ background: spotlight }}
      />
      {children}
    </motion.div>
  );
}
