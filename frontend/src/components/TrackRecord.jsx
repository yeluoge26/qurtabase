/**
 * TrackRecord -- v1.0
 * Compact performance / track record panel -- Bloomberg terminal style
 * Displays today's signal performance: wins, losses, ROI, edge, signal log
 */

const C = {
  bg: "#0E1117", bgCard: "#131720",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  up: "#00C853", down: "#FF3D00",
  accent: "#F4C430", accentBlue: "#00C8FF",
};

const RESULT_CFG = {
  win:     { marker: "\u2713", color: C.up,     label: "WIN"  },
  loss:    { marker: "\u2717", color: C.down,   label: "LOSS" },
  pending: { marker: "\u25CF", color: C.accent, label: "PEND" },
};

export default function TrackRecord({ data, label = "TODAY PERFORMANCE" }) {
  if (!data) return null;

  const {
    total_signals = 0,
    wins = 0,
    losses = 0,
    pending = 0,
    roi_pct = 0,
    best_edge = 0,
    avg_edge = 0,
    signals = [],
  } = data;

  const roiColor = roi_pct > 0 ? C.up : roi_pct < 0 ? C.down : C.textDim;

  return (
    <div style={{
      padding: "8px 14px",
      background: C.bgCard,
      border: `1px solid ${C.border}`,
      fontFamily: "'IBM Plex Mono', monospace",
      fontSize: 11,
      minHeight: 80,
    }}>
      {/* Header */}
      <div style={{
        fontSize: 9, fontWeight: 700, letterSpacing: 3, color: C.accent,
        marginBottom: 6, paddingBottom: 4, borderBottom: `1px solid ${C.borderLight}`,
      }}>
        {label}
      </div>

      {/* Summary Row 1: Signals + Wins */}
      <div style={{ display: "flex", justifyContent: "space-between", padding: "2px 0" }}>
        <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1, fontWeight: 600 }}>
          Signals: <span style={{ color: C.text, fontWeight: 700 }}>{total_signals}</span>
        </span>
        <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1, fontWeight: 600 }}>
          Wins: <span style={{ color: C.up, fontWeight: 700 }}>{wins}</span>
        </span>
      </div>

      {/* Summary Row 2: Loss + ROI */}
      <div style={{ display: "flex", justifyContent: "space-between", padding: "2px 0" }}>
        <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1, fontWeight: 600 }}>
          Loss: <span style={{ color: C.down, fontWeight: 700 }}>{losses}</span>
        </span>
        <span style={{ fontSize: 14, fontWeight: 800, fontFamily: "'IBM Plex Mono', monospace", color: roiColor }}>
          {roi_pct > 0 ? "+" : ""}{roi_pct.toFixed(1)}%
          <span style={{ fontSize: 9, color: C.textDim, fontWeight: 600, marginLeft: 4 }}>ROI</span>
        </span>
      </div>

      {/* Best Edge */}
      <div style={{ display: "flex", justifyContent: "space-between", padding: "3px 0 2px", marginTop: 2 }}>
        <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1, fontWeight: 600 }}>
          Best Edge
        </span>
        <span style={{ fontSize: 11, fontWeight: 700, color: C.up, fontFamily: "'IBM Plex Mono', monospace" }}>
          +{best_edge.toFixed(1)}%
        </span>
      </div>

      {/* Divider */}
      {signals.length > 0 && (
        <div style={{ borderTop: `1px solid ${C.borderLight}`, margin: "4px 0 3px" }} />
      )}

      {/* Signal Log */}
      {signals.map((sig) => {
        const rc = RESULT_CFG[sig.result] || RESULT_CFG.pending;
        return (
          <div key={sig.id} style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "1px 0", fontSize: 10, fontFamily: "'IBM Plex Mono', monospace",
          }}>
            <span style={{ color: C.textDim, minWidth: 28 }}>{sig.minute}'</span>
            <span style={{ color: C.text, minWidth: 38 }}>{sig.type}</span>
            <span style={{ color: C.textDim, minWidth: 32 }}>{sig.line}</span>
            <span style={{ color: C.up, minWidth: 34, textAlign: "right" }}>+{sig.edge}%</span>
            <span style={{ color: rc.color, minWidth: 12, textAlign: "center", fontWeight: 700, fontSize: 11 }}>
              {rc.marker}
            </span>
            <span style={{ color: rc.color, fontWeight: 700, fontSize: 9, letterSpacing: 1, minWidth: 32, textAlign: "right" }}>
              {rc.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
