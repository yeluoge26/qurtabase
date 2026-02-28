/**
 * EdgeHeatBar -- v1.0
 * Visual horizontal bar representing Edge value
 * Color-coded by magnitude with threshold markers
 * Bloomberg terminal style
 */

const C = {
  bg: "#0E1117", bgCard: "#131720",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  up: "#00C853", down: "#FF3D00",
  accent: "#F4C430", accentBright: "#FFD700",
};

const FONT = "'IBM Plex Mono', monospace";

// ── Edge color by magnitude ─────────────────────────────────
function getEdgeColor(edge) {
  const abs = Math.abs(edge);
  if (edge < 0) return C.down;       // Negative: red
  if (abs < 2) return C.textMuted;   // No edge: gray
  if (abs < 4) return C.accent;      // Building: gold
  if (abs < 6) return "#F5CC3A";     // Brighter gold
  return C.accentBright;             // Strong: bright gold
}

function getEdgeGlow(edge) {
  const abs = Math.abs(edge);
  if (abs >= 6) return `0 0 6px ${C.accentBright}50`;
  return "none";
}

// ════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════
export default function EdgeHeatBar({ edge = 0, maxEdge = 15, L }) {
  const absEdge = Math.abs(edge);
  const pct = Math.min(100, (absEdge / maxEdge) * 100);
  const isNeg = edge < 0;
  const barColor = getEdgeColor(edge);
  const glow = getEdgeGlow(edge);

  // Threshold marker positions (percentage of half-bar width)
  const thresh4Pct = (4 / maxEdge) * 100;
  const thresh6Pct = (6 / maxEdge) * 100;

  return (
    <div style={{
      width: "100%",
      height: 22,
      display: "flex",
      alignItems: "center",
      gap: 8,
      fontFamily: FONT,
    }}>
      {/* Label */}
      <span style={{
        fontSize: 9,
        fontWeight: 700,
        letterSpacing: 2,
        color: C.textDim,
        minWidth: 38,
        flexShrink: 0,
      }}>
        {L?.edgeLabel || "EDGE"}
      </span>

      {/* Bar container */}
      <div style={{
        flex: 1,
        height: 10,
        background: C.border,
        borderRadius: 1,
        position: "relative",
        overflow: "hidden",
      }}>
        {/* Center line for negative/positive reference */}
        {isNeg ? (
          /* Negative edge: bar grows from right (center) to left */
          <div style={{
            position: "absolute",
            top: 0,
            right: 0,
            width: `${pct}%`,
            height: "100%",
            background: barColor,
            borderRadius: 1,
            transition: "width 400ms ease, background 300ms",
            boxShadow: glow,
          }} />
        ) : (
          /* Positive edge: bar grows from left to right */
          <div style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: `${pct}%`,
            height: "100%",
            background: barColor,
            borderRadius: 1,
            transition: "width 400ms ease, background 300ms",
            boxShadow: glow,
          }} />
        )}

        {/* Threshold marker at 4% */}
        <div style={{
          position: "absolute",
          top: 0,
          left: `${thresh4Pct}%`,
          width: 1,
          height: "100%",
          background: C.borderLight,
          opacity: 0.7,
          pointerEvents: "none",
        }} />

        {/* Threshold marker at 6% */}
        <div style={{
          position: "absolute",
          top: 0,
          left: `${thresh6Pct}%`,
          width: 1,
          height: "100%",
          background: C.borderLight,
          opacity: 0.7,
          pointerEvents: "none",
        }} />
      </div>

      {/* Value label */}
      <span style={{
        fontSize: 11,
        fontWeight: 700,
        fontFamily: FONT,
        color: barColor,
        minWidth: 52,
        textAlign: "right",
        flexShrink: 0,
        textShadow: absEdge >= 6 && !isNeg ? `0 0 6px ${C.accentBright}40` : "none",
      }}>
        {edge > 0 ? "+" : ""}{edge.toFixed(1)}%
      </span>
    </div>
  );
}
