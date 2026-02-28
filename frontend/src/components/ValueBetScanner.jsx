/**
 * ValueBetScanner -- v1.0
 * Expected Value scanner for O/U bets
 * Shows EV%, best side, confidence rating
 * Bloomberg terminal style
 */

const C = {
  bg: "#0E1117", bgCard: "#131720",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  up: "#00C853", down: "#FF3D00",
  accent: "#F4C430", accentBright: "#FFD700",
  cyan: "#00C8FF",
};
const FONT = "'IBM Plex Mono', monospace";

const CONF_COLORS = {
  LOW: { bg: C.textMuted + "20", color: C.textMuted },
  MED: { bg: "#00C8FF25", color: "#00C8FF" },
  HIGH: { bg: "#00C85320", color: "#00C853" },
  STRONG: { bg: "#FFD70025", color: "#FFD700" },
};

function ConfBadge({ level }) {
  const s = CONF_COLORS[level] || CONF_COLORS.LOW;
  return (
    <span style={{
      fontSize: 7, fontWeight: 700, letterSpacing: 1.5,
      padding: "2px 5px", borderRadius: 2,
      background: s.bg, color: s.color,
      fontFamily: FONT,
    }}>
      {level}
    </span>
  );
}

function EVBar({ value, maxRange = 20 }) {
  const pct = Math.min(Math.abs(value) / maxRange, 1) * 100;
  const color = value > 0 ? C.up : value < 0 ? C.down : C.textMuted;
  return (
    <div style={{
      width: "100%", height: 3, background: C.border,
      borderRadius: 2, overflow: "hidden", marginTop: 3,
    }}>
      <div style={{
        width: `${pct}%`, height: "100%",
        background: color, borderRadius: 2,
        transition: "width 400ms ease",
      }} />
    </div>
  );
}

export default function ValueBetScanner({ data, lang, L }) {
  if (!data) return null;

  const {
    evOver = 0,
    evUnder = 0,
    bestSide = "OVER",
    bestEv = 0,
    confidence = "LOW",
    isValue = false,
    line = 2.5,
  } = data;

  const fmtEv = (v) => `${v > 0 ? "+" : ""}${v.toFixed(2)}%`;

  return (
    <div style={{
      padding: "8px 14px",
      borderBottom: `1px solid ${C.border}`,
      fontFamily: FONT,
      fontSize: 11,
    }}>
      {/* Header */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: 6, paddingBottom: 4, borderBottom: `1px solid ${C.borderLight}`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{
            fontSize: 9, fontWeight: 700, letterSpacing: 3, color: C.accent,
          }}>
            {L?.valueBet || "VALUE BET"}
          </span>
          <span style={{
            fontSize: 7, padding: "1px 5px", borderRadius: 2,
            background: C.accent + "18", color: C.accent,
            letterSpacing: 1, fontWeight: 700,
          }}>{L?.expectedValue || "EV"}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <ConfBadge level={confidence} />
          {isValue && (
            <span style={{
              fontSize: 7, padding: "2px 6px", borderRadius: 9,
              background: C.accent + "20", color: C.accent,
              fontWeight: 700, letterSpacing: 1.5,
              animation: "valuePulse 2s ease-in-out infinite",
            }}>
              VALUE
            </span>
          )}
        </div>
      </div>

      {/* OVER row */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "4px 0",
        borderLeft: bestSide === "OVER" ? `3px solid ${C.accent}` : "3px solid transparent",
        paddingLeft: 8,
        background: bestSide === "OVER" ? C.accent + "08" : "transparent",
        transition: "background 300ms",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {bestSide === "OVER" && (
            <span style={{ fontSize: 9, color: C.accent, fontWeight: 700 }}>{"\u25B6"}</span>
          )}
          <span style={{
            fontSize: 10, fontWeight: 600, letterSpacing: 1.5,
            color: bestSide === "OVER" ? C.accent : C.textDim,
          }}>OVER {line}</span>
        </div>
        <span style={{
          fontFamily: FONT, fontSize: 13, fontWeight: 700,
          color: evOver > 0 ? C.up : evOver < 0 ? C.down : C.textDim,
          letterSpacing: -0.3,
        }}>
          {fmtEv(evOver)}
        </span>
      </div>
      <EVBar value={evOver} />

      {/* UNDER row */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "4px 0", marginTop: 4,
        borderLeft: bestSide === "UNDER" ? `3px solid ${C.accent}` : "3px solid transparent",
        paddingLeft: 8,
        background: bestSide === "UNDER" ? C.accent + "08" : "transparent",
        transition: "background 300ms",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {bestSide === "UNDER" && (
            <span style={{ fontSize: 9, color: C.accent, fontWeight: 700 }}>{"\u25B6"}</span>
          )}
          <span style={{
            fontSize: 10, fontWeight: 600, letterSpacing: 1.5,
            color: bestSide === "UNDER" ? C.accent : C.textDim,
          }}>UNDER {line}</span>
        </div>
        <span style={{
          fontFamily: FONT, fontSize: 13, fontWeight: 700,
          color: evUnder > 0 ? C.up : evUnder < 0 ? C.down : C.textDim,
          letterSpacing: -0.3,
        }}>
          {fmtEv(evUnder)}
        </span>
      </div>
      <EVBar value={evUnder} />

      {/* Best EV summary */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginTop: 6, paddingTop: 4,
        borderTop: `1px solid ${C.borderLight}`,
        fontSize: 9,
      }}>
        <span style={{ color: C.textMuted, letterSpacing: 1 }}>BEST {L?.expectedValue || "EV"}</span>
        <span style={{
          fontWeight: 700,
          color: bestEv > 0 ? C.up : C.textDim,
          fontFamily: FONT,
        }}>
          {bestSide} {fmtEv(bestEv)}
        </span>
      </div>

      {/* Inline CSS for pulse animation */}
      <style>{`@keyframes valuePulse{0%,100%{opacity:1}50%{opacity:0.5}}`}</style>
    </div>
  );
}
