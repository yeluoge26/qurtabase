/**
 * LineMovement -- v1.0
 * Odds flow and market pressure indicator -- Bloomberg terminal style
 * Shows line changes, over/under odds movement, and market pressure direction
 * Pro tier feature
 */

const C = {
  bg: "#0E1117", bgCard: "#131720",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  up: "#00C853", down: "#FF3D00",
  accent: "#F4C430", accentBlue: "#00C8FF",
};

export default function LineMovement({ data, label = "LINE MOVEMENT" }) {
  if (!data) return null;

  const {
    current_line = 2.5,
    previous_line = 2.5,
    over_odds = 1.90,
    over_odds_prev = 1.90,
    under_odds = 1.90,
    direction = "NEUTRAL",
    pressure = "NEUTRAL",
  } = data;

  const lineChanged = Math.abs(current_line - previous_line) > 0.001;
  const lineColor = lineChanged ? C.accent : C.text;

  // Odds movement
  const oddsDelta = over_odds - over_odds_prev;
  const oddsMovedDown = oddsDelta < -0.005;
  const oddsMovedUp = oddsDelta > 0.005;
  // Lower over odds = more money on over = over pressure
  const oddsArrow = oddsMovedDown ? "\u25BC" : oddsMovedUp ? "\u25B2" : "";
  const oddsColor = oddsMovedDown ? C.up : oddsMovedUp ? C.down : C.textDim;

  // Pressure arrows
  const pressureColor = pressure === "OVER" ? C.up : pressure === "UNDER" ? C.down : C.textDim;
  const pressureArrows = pressure === "OVER" ? "\u25B2\u25B2" : pressure === "UNDER" ? "\u25BC\u25BC" : "\u2014";

  return (
    <div style={{
      padding: "6px 14px",
      background: C.bgCard,
      border: `1px solid ${C.border}`,
      borderBottom: `1px solid ${C.border}`,
      fontFamily: "'IBM Plex Mono', monospace",
      fontSize: 11,
      minHeight: 50,
    }}>
      {/* Header */}
      <div style={{
        fontSize: 9, fontWeight: 700, letterSpacing: 3, color: C.accent,
        marginBottom: 5, paddingBottom: 3, borderBottom: `1px solid ${C.borderLight}`,
      }}>
        {label}
      </div>

      {/* Line + Odds row */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "2px 0" }}>
        {/* Line movement */}
        <span style={{ color: lineChanged ? C.textDim : C.text, fontWeight: 600 }}>
          {previous_line.toFixed(1)}
        </span>
        <span style={{ color: C.textMuted, fontSize: 10 }}>{"\u2192"}</span>
        <span style={{ color: lineColor, fontWeight: 700 }}>
          {current_line.toFixed(1)}
        </span>

        <span style={{ color: C.textMuted, fontSize: 10, margin: "0 4px" }}>|</span>

        {/* Over odds movement */}
        <span style={{ color: C.textDim, fontSize: 10, fontWeight: 600 }}>Over:</span>
        <span style={{ color: C.textDim }}>
          {over_odds_prev.toFixed(2)}
        </span>
        <span style={{ color: C.textMuted, fontSize: 10 }}>{"\u2192"}</span>
        <span style={{ color: oddsColor, fontWeight: 700 }}>
          {over_odds.toFixed(2)}
        </span>
        {oddsArrow && (
          <span style={{ color: oddsColor, fontSize: 10, fontWeight: 700 }}>{oddsArrow}</span>
        )}
      </div>

      {/* Pressure row */}
      <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "2px 0" }}>
        <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1.2, fontWeight: 600 }}>Pressure:</span>
        <span style={{ fontWeight: 800, color: pressureColor, letterSpacing: 1 }}>
          {pressure}
        </span>
        <span style={{ color: pressureColor, fontWeight: 700 }}>
          {pressureArrows}
        </span>
      </div>
    </div>
  );
}
