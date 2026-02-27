/**
 * RiskPanel -- v1.0
 * Compact risk metrics panel -- Bloomberg terminal style
 * Displays model variance, signal stability, market volatility, drawdown guard
 * Elite tier feature
 */

const C = {
  bg: "#0E1117", bgCard: "#131720",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  up: "#00C853", down: "#FF3D00",
  accent: "#F4C430", accentBlue: "#00C8FF",
};

const VOLATILITY_COLOR = {
  Low: C.up,
  Medium: C.accent,
  High: C.down,
};

function StabilityBar({ value, max = 100 }) {
  const blocks = 10;
  const filled = Math.round((value / max) * blocks);
  return (
    <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, letterSpacing: 0.5 }}>
      {Array.from({ length: blocks }, (_, i) => (
        <span key={i} style={{ color: i < filled ? C.accentBlue : C.textMuted }}>
          {i < filled ? "\u2588" : "\u2591"}
        </span>
      ))}
    </span>
  );
}

export default function RiskPanel({ data, label = "RISK PANEL" }) {
  if (!data) return null;

  const {
    model_variance = 0,
    signal_stability = 100,
    market_volatility = "Medium",
    drawdown_guard = "Active",
  } = data;

  const volColor = VOLATILITY_COLOR[market_volatility] || C.textDim;

  return (
    <div style={{
      padding: "8px 14px",
      background: C.bgCard,
      border: `1px solid ${C.border}`,
      borderBottom: `1px solid ${C.border}`,
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

      {/* Model Variance */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "3px 0" }}>
        <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1.2, fontWeight: 600 }}>Model Variance</span>
        <span style={{ fontWeight: 700, color: C.text }}>
          {typeof model_variance === "number" ? model_variance.toFixed(2) : model_variance}
        </span>
      </div>

      {/* Signal Stability */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "3px 0" }}>
        <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1.2, fontWeight: 600 }}>Signal Stability</span>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontWeight: 700, color: C.text }}>
            {signal_stability}<span style={{ fontSize: 9, color: C.textDim }}>%</span>
          </span>
          <StabilityBar value={signal_stability} />
        </div>
      </div>

      {/* Market Volatility */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "3px 0" }}>
        <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1.2, fontWeight: 600 }}>Market Volatility</span>
        <span style={{ fontWeight: 700, color: volColor }}>{market_volatility}</span>
      </div>

      {/* Drawdown Guard */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "3px 0" }}>
        <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1.2, fontWeight: 600 }}>Drawdown Guard</span>
        <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <span style={{ fontWeight: 700, color: drawdown_guard === "Active" ? C.up : C.textDim }}>
            {drawdown_guard}
          </span>
          <span style={{
            display: "inline-block", width: 6, height: 6, borderRadius: "50%",
            background: drawdown_guard === "Active" ? C.up : C.textMuted,
            boxShadow: drawdown_guard === "Active" ? `0 0 4px ${C.up}` : "none",
          }} />
        </div>
      </div>
    </div>
  );
}
