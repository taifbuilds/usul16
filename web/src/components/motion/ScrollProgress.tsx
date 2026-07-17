"use client";

import { motion, useScroll, useSpring } from "motion/react";

/**
 * Thin accent→gold progress bar pinned to the very top of the viewport,
 * tracking overall page scroll. Rendered once in the root layout.
 */
export function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 120, damping: 24, mass: 0.3 });

  return (
    <motion.div
      aria-hidden
      style={{ scaleX }}
      className="fixed inset-x-0 top-0 z-[60] h-[2px] origin-left bg-gradient-to-r from-accent via-accent to-gold"
    />
  );
}
