"use client";

import { motion, useReducedMotion, type Variants } from "motion/react";
import type { ReactNode } from "react";

type Direction = "up" | "down" | "left" | "right" | "none";

const OFFSET = 26;

/**
 * Scroll-into-view reveal with a soft blur + spring settle. The workhorse
 * entrance used across the marketing surfaces. Honours reduced-motion by
 * rendering the final state immediately.
 */
export function FadeIn({
  children,
  delay = 0,
  direction = "up",
  className,
  once = true,
  amount = 0.3,
}: {
  children: ReactNode;
  delay?: number;
  direction?: Direction;
  className?: string;
  once?: boolean;
  amount?: number;
}) {
  const reduce = useReducedMotion();

  const dx = direction === "left" ? OFFSET : direction === "right" ? -OFFSET : 0;
  const dy = direction === "up" ? OFFSET : direction === "down" ? -OFFSET : 0;

  const variants: Variants = {
    hidden: reduce ? { opacity: 0 } : { opacity: 0, x: dx, y: dy, filter: "blur(8px)" },
    show: {
      opacity: 1,
      x: 0,
      y: 0,
      filter: "blur(0px)",
      transition: { duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] },
    },
  };

  return (
    <motion.div
      className={className}
      variants={variants}
      initial="hidden"
      whileInView="show"
      viewport={{ once, amount }}
    >
      {children}
    </motion.div>
  );
}
