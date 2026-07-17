"use client";

import { motion, useReducedMotion, type Variants } from "motion/react";
import type { ReactNode } from "react";

/**
 * Reveals a heading word-by-word with a rising blur. Pass the text as a
 * string; markup emphasis is handled by the caller via `highlight` (a set of
 * words rendered with solid scholarly emphasis).
 */
export function WordReveal({
  text,
  className,
  highlight,
  delay = 0,
  as: Tag = "h1",
}: {
  text: string;
  className?: string;
  highlight?: string[];
  delay?: number;
  as?: "h1" | "h2" | "h3" | "p";
}) {
  const reduce = useReducedMotion();
  const words = text.split(" ");
  const highlightSet = new Set((highlight ?? []).map((w) => w.toLowerCase()));

  const container: Variants = {
    hidden: {},
    show: { transition: { staggerChildren: 0.055, delayChildren: delay } },
  };
  const word: Variants = {
    hidden: reduce ? { opacity: 0 } : { opacity: 0, y: "0.5em", filter: "blur(10px)" },
    show: {
      opacity: 1,
      y: "0em",
      filter: "blur(0px)",
      transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
    },
  };

  const MotionTag = motion[Tag];

  return (
    <MotionTag
      className={className}
      variants={container}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.5 }}
    >
      {words.map((w, i) => {
        const clean = w.replace(/[.,;:]/g, "").toLowerCase();
        const isHi = highlightSet.has(clean);
        return (
          <span key={`${w}-${i}`} className="inline-block overflow-hidden align-bottom">
            <motion.span
              variants={word}
              className={`inline-block ${isHi ? "text-accent italic" : ""}`}
            >
              {w}
              {i < words.length - 1 ? " " : ""}
            </motion.span>
          </span>
        );
      })}
    </MotionTag>
  );
}

/** Small inline reveal for a block of arbitrary children (no word split). */
export function Rise({ children, className, delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduce ? { opacity: 0 } : { opacity: 0, y: 16, filter: "blur(6px)" }}
      whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
      viewport={{ once: true, amount: 0.4 }}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}
