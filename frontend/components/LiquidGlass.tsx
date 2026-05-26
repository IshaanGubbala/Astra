"use client";

import { useCallback, useEffect, useId, useRef, useState, forwardRef } from "react";
import type { CSSProperties, ReactNode } from "react";

// ── Shader math (ported from liquid-glass-react) ──────────────────────────────

function smoothStep(a: number, b: number, t: number): number {
  t = Math.max(0, Math.min(1, (t - a) / (b - a)));
  return t * t * (3 - 2 * t);
}

function len(x: number, y: number): number {
  return Math.sqrt(x * x + y * y);
}

function roundedRectSDF(x: number, y: number, w: number, h: number, r: number): number {
  const qx = Math.abs(x) - w + r;
  const qy = Math.abs(y) - h + r;
  return Math.min(Math.max(qx, qy), 0) + len(Math.max(qx, 0), Math.max(qy, 0)) - r;
}

// Generates the displacement map at a capped resolution for performance
function generateDisplacementMap(elemW: number, elemH: number): string {
  const MAX = 256;
  const aspect = elemW / elemH;
  const w = Math.round(Math.min(MAX, elemW));
  const h = Math.round(Math.min(MAX, elemH));

  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d")!;

  const rawValues: number[] = [];
  let maxScale = 0;

  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const ix = x / w - 0.5;
      const iy = y / h - 0.5;

      // Rounded-rect SDF lens: radius 0.6 with half-extents (0.3, 0.2) = near-circle
      const dist = roundedRectSDF(ix, iy, 0.3, 0.2, 0.6);
      const disp = smoothStep(0.8, 0, dist - 0.15);
      const scaled = smoothStep(0, 1, disp);

      const dx = (ix * scaled + 0.5) * w - x;
      const dy = (iy * scaled + 0.5) * h - y;

      maxScale = Math.max(maxScale, Math.abs(dx), Math.abs(dy));
      rawValues.push(dx, dy);
    }
  }

  maxScale = Math.max(maxScale, 1);

  const imageData = ctx.createImageData(w, h);
  const data = imageData.data;
  let ri = 0;

  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const dx = rawValues[ri++];
      const dy = rawValues[ri++];
      const edge = Math.min(1, Math.min(x, y, w - x - 1, h - y - 1) / 2);
      const r = (dx * edge) / maxScale + 0.5;
      const g = (dy * edge) / maxScale + 0.5;
      const pi = (y * w + x) * 4;
      data[pi]     = Math.max(0, Math.min(255, r * 255));
      data[pi + 1] = Math.max(0, Math.min(255, g * 255));
      data[pi + 2] = Math.max(0, Math.min(255, g * 255));
      data[pi + 3] = 255;
    }
  }

  ctx.putImageData(imageData, 0, 0);
  void aspect; // keep for future anisotropic tuning
  return canvas.toDataURL("image/png");
}

// ── Component ─────────────────────────────────────────────────────────────────

export interface LiquidGlassProps {
  children?: ReactNode;
  className?: string;
  /** Styles for the outer container (position, width, height, etc.) */
  style?: CSSProperties;
  /** Styles for the content wrapper (display, flex, overflow, etc.) */
  contentStyle?: CSSProperties;
  borderRadius?: number;
  /** Displacement strength — default 28 */
  displacementScale?: number;
  /** Glass fill tint */
  tint?: string;
}

const LiquidGlass = forwardRef<HTMLDivElement, LiquidGlassProps>(
  (
    {
      children,
      className,
      style,
      contentStyle,
      borderRadius = 16,
      displacementScale = 28,
      tint = "rgba(215,228,242,0.20)",
    },
    ref,
  ) => {
    const rawId = useId();
    const uid = rawId.replace(/:/g, "");
    const containerRef = useRef<HTMLDivElement | null>(null);
    const [dispMap, setDispMap] = useState<string | null>(null);

    const generate = useCallback(() => {
      const el = containerRef.current;
      if (!el) return;
      const { offsetWidth: w, offsetHeight: h } = el;
      if (w > 0 && h > 0) setDispMap(generateDisplacementMap(w, h));
    }, []);

    useEffect(() => {
      generate();
      const ro = new ResizeObserver(generate);
      if (containerRef.current) ro.observe(containerRef.current);
      return () => ro.disconnect();
    }, [generate]);

    const filterId = `lgf-${uid}`;

    return (
      <div
        ref={(el) => {
          containerRef.current = el;
          if (typeof ref === "function") ref(el);
          else if (ref) (ref as React.MutableRefObject<HTMLDivElement | null>).current = el;
        }}
        className={className}
        style={{ position: "relative", borderRadius, overflow: "hidden", ...style }}
      >
        {/* Filter definition */}
        {dispMap && (
          <svg
            style={{ position: "absolute", width: 0, height: 0, overflow: "hidden" }}
            aria-hidden="true"
          >
            <defs>
              <filter
                id={filterId}
                x="0%"
                y="0%"
                width="100%"
                height="100%"
                colorInterpolationFilters="sRGB"
              >
                <feImage href={dispMap} result="dispMap" preserveAspectRatio="none" />
                <feDisplacementMap
                  in="SourceGraphic"
                  in2="dispMap"
                  scale={displacementScale}
                  xChannelSelector="R"
                  yChannelSelector="G"
                  result="displaced"
                />
              </filter>
            </defs>
          </svg>
        )}

        {/* Backdrop blur + distortion layer */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            backdropFilter: "blur(18px) saturate(180%)",
            WebkitBackdropFilter: "blur(18px) saturate(180%)",
            ...(dispMap ? { filter: `url(#${filterId})` } : {}),
            zIndex: 0,
          }}
        />

        {/* Glass tint + border */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: tint,
            border: "1px solid rgba(200,214,228,0.72)",
            boxShadow:
              "inset 0 1.5px 0 rgba(240,246,252,0.80), inset 0 -1px 0 rgba(180,200,220,0.22), 0 1px 3px rgba(0,0,10,0.07), 0 8px 28px rgba(0,0,10,0.10)",
            borderRadius,
            zIndex: 1,
            pointerEvents: "none",
          }}
        />

        {/* Top specular sheen */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: "46%",
            background:
              "linear-gradient(180deg, rgba(230,242,255,0.44) 0%, rgba(210,230,248,0.08) 60%, transparent 100%)",
            borderRadius: `${borderRadius}px ${borderRadius}px 0 0`,
            pointerEvents: "none",
            zIndex: 2,
          }}
        />

        {/* Content */}
        <div style={{ position: "relative", zIndex: 3, ...contentStyle }}>
          {children}
        </div>
      </div>
    );
  },
);

LiquidGlass.displayName = "LiquidGlass";
export default LiquidGlass;
