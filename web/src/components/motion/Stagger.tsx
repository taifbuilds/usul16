"use client";

import { motion, useReducedMotion, type Variants } from "motion/react";
import type { ReactNode } from "react";

/**
 * Container that reveals its <StaggerItem> children one after another as it
 * scrolls into view. Compose the two: <Stagger><StaggerItem/>…</Stagger>.
 */
export function Stagger({
  children,
  className,
  delay = 0,
  gap = 0.09,
  amount = 0.2,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
  gap?: number;
  amount?: number;
}) {
  const variants: Variants = {
    hidden: {},
    show: { transition: { staggerChildren: gap, delayChildren: delay } },
  };
  return (
    <motion.div
      className={className}
      variants={variants}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount }}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({
  children,
  className,
  direction = "up",
}: {
  children: ReactNode;
  className?: string;
  direction?: "up" | "down" | "none";
}) {
  const reduce = useReducedMotion();
  const dy = direction === "up" ? 24 : direction === "down" ? -24 : 0;
  const variants: Variants = {
    hidden: reduce ? { opacity: 0 } : { opacity: 0, y: dy, filter: "blur(6px)" },
    show: {
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
    },
  };
  return (
    <motion.div className={className} variants={variants}>
      {children}
    </motion.div>
  );
}
