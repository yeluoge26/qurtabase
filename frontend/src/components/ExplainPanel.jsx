/**
 * ExplainPanel — v1.1 (Why Delta)
 * Shows top factors driving probability changes
 * Builds trust — Pro tier
 */

const C = {
  border: "#1E2530",
  textDim: "#6B7280",
  textMuted: "#3D4654",
  accent: "#F4C430",
  up: "#00C853",
  down: "#FF3D00",
  text: "#E5E5E5",
};

const FACTOR_LABELS = {
  shots_on_target_delta: "SHOTS ON TARGET",
  pressure_index_delta: "PRESSURE INDEX",
  goal_scored: "GOAL SCORED",
  red_card_impact: "RED CARD",
  possession_swing: "POSSESSION",
  xg_delta_change: "xG DELTA",
  time_decay: "TIME DECAY",
};

export default function ExplainPanel({ explain }) {
  if (!explain || !explain.topFactors?.length) {
    return null;
  }

  return (
    <div style={{ padding: "8px 0" }}>
      <div style={{ fontSize: 9, color: C.accent, letterSpacing: 1.5, fontWeight: 600, marginBottom: 6 }}>
        WHY Δ
      </div>
      <div style={{ fontSize: 9, color: C.textDim, marginBottom: 6, fontFamily: "mono" }}>
        {explain.summary}
      </div>
      {explain.topFactors.map((f, i) => {
        const label = FACTOR_LABELS[f.name] || f.name.replace(/_/g, " ").toUpperCase();
        const isUp = f.direction === "up";
        const color = isUp ? C.up : f.direction === "down" ? C.down : C.textDim;
        const barWidth = Math.min(100, f.impact * 40);
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, padding: "3px 0" }}>
            <span style={{ color, fontSize: 10, fontWeight: 700, width: 12 }}>{isUp ? "▲" : "▼"}</span>
            <span style={{ fontSize: 9, color: C.textDim, minWidth: 100, letterSpacing: 0.5 }}>{label}</span>
            <div style={{ flex: 1, height: 4, background: C.border, borderRadius: 2, overflow: "hidden" }}>
              <div style={{ width: `${barWidth}%`, height: "100%", background: color, borderRadius: 2 }} />
            </div>
            <span style={{ fontSize: 9, color, fontFamily: "mono", minWidth: 30, textAlign: "right" }}>{f.impact.toFixed(1)}</span>
          </div>
        );
      })}
    </div>
  );
}
