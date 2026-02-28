/**
 * OUScanner -- v1.0
 * Multi-line O/U scanner table -- Bloomberg terminal style
 * Displays Poisson-derived over probabilities and edges across key lines
 * Pro/Elite tier feature
 */

import { LANG } from "../utils/i18n";

const C = {
  bg: "#0E1117", bgCard: "#131720",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  up: "#00C853", down: "#FF3D00",
  accent: "#F4C430", accentBlue: "#00C8FF",
};

function EdgeBar({ value, maxEdge = 12 }) {
  if (value == null) return <div style={{ width: 40, height: 6 }} />;
  const abs = Math.min(Math.abs(value), maxEdge);
  const pct = (abs / maxEdge) * 100;
  const color = value > 0 ? C.up : value < 0 ? C.down : C.textMuted;
  return (
    <div style={{ width: 40, height: 6, background: C.border, borderRadius: 1, overflow: "hidden" }}>
      <div style={{
        width: `${pct}%`,
        height: "100%",
        background: color,
        borderRadius: 1,
        transition: "width 300ms",
      }} />
    </div>
  );
}

export default function OUScanner({ data, label, lang = "en" }) {
  const L = LANG[lang];
  const displayLabel = label || L?.ouScanner || "O/U SCANNER";
  if (!data || !Array.isArray(data) || data.length === 0) return null;

  // Find the row with the best absolute edge (for highlight)
  let bestEdgeIdx = -1;
  let bestEdgeAbs = 0;
  data.forEach((row, i) => {
    if (row.edge != null && Math.abs(row.edge) > bestEdgeAbs) {
      bestEdgeAbs = Math.abs(row.edge);
      bestEdgeIdx = i;
    }
  });

  return (
    <div style={{ padding: "12px 14px", borderBottom: `1px solid ${C.border}` }}>
      {/* Header */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: 8, paddingBottom: 6, borderBottom: `1px solid ${C.borderLight}`,
      }}>
        <span style={{
          fontSize: 9, fontWeight: 700, letterSpacing: 3,
          color: C.accent, fontFamily: "'IBM Plex Mono', monospace",
        }}>{displayLabel}</span>
        <span style={{
          fontSize: 9, color: C.textMuted, fontFamily: "'IBM Plex Mono', monospace",
        }}>{L?.multiLine || "MULTI-LINE"}</span>
      </div>

      {/* Column headers */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "50px 1fr 60px 44px",
        alignItems: "center",
        padding: "4px 0",
        borderBottom: `1px solid ${C.borderLight}`,
        marginBottom: 2,
      }}>
        <span style={colHead}>{L?.lineLabel || "LINE"}</span>
        <span style={{ ...colHead, textAlign: "center" }}>{L?.overPct || "OVER%"}</span>
        <span style={{ ...colHead, textAlign: "right" }}>{L?.edgeLabel || "EDGE"}</span>
        <span style={{ ...colHead, textAlign: "right" }}></span>
      </div>

      {/* Rows */}
      {data.map((row, i) => {
        const isActive = row.is_active;
        const isBestEdge = i === bestEdgeIdx && bestEdgeAbs > 0;
        const edgeColor = row.edge != null
          ? (row.edge > 0 ? C.up : row.edge < 0 ? C.down : C.textDim)
          : C.textMuted;

        return (
          <div
            key={row.line}
            style={{
              display: "grid",
              gridTemplateColumns: "50px 1fr 60px 44px",
              alignItems: "center",
              padding: "4px 0",
              borderBottom: `1px solid ${C.border}`,
              borderLeft: isActive ? `3px solid ${C.accent}` : "3px solid transparent",
              paddingLeft: isActive ? 8 : 8,
              background: isBestEdge ? (row.edge > 0 ? C.up + "08" : C.down + "08") : "transparent",
              transition: "background 300ms",
            }}
          >
            {/* LINE */}
            <span style={{
              fontFamily: "'IBM Plex Mono', monospace",
              fontSize: 12,
              fontWeight: isActive ? 800 : 600,
              color: isActive ? C.accent : C.text,
              letterSpacing: -0.3,
            }}>
              {row.line.toFixed(row.line % 1 === 0 ? 1 : 2)}
            </span>

            {/* OVER% */}
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "center", gap: 6 }}>
              <span style={{
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: 11,
                fontWeight: 700,
                color: C.text,
              }}>
                {row.over_prob.toFixed(1)}
              </span>
              <span style={{
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: 9,
                color: C.textDim,
              }}>%</span>
            </div>

            {/* EDGE */}
            <span style={{
              fontFamily: "'IBM Plex Mono', monospace",
              fontSize: 11,
              fontWeight: 700,
              color: edgeColor,
              textAlign: "right",
            }}>
              {row.edge != null
                ? `${row.edge > 0 ? "+" : ""}${row.edge.toFixed(1)}`
                : "\u2014"
              }
            </span>

            {/* Mini bar */}
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <EdgeBar value={row.edge} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

const colHead = {
  fontSize: 8,
  fontWeight: 600,
  letterSpacing: 2,
  color: C.textMuted,
  fontFamily: "'IBM Plex Mono', monospace",
  textTransform: "uppercase",
};
