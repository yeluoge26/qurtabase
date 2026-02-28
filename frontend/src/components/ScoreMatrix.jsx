/**
 * ScoreMatrix -- v1.0
 * Poisson correct score probability matrix with heat map visualization
 * 6x6 grid (0-5 goals per team), color-coded by probability
 * Bloomberg terminal style
 */

const C = {
  bg: "#0E1117", bgCard: "#131720",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  accent: "#F4C430", accentBright: "#FFD700",
};
const FONT = "'IBM Plex Mono', monospace";

function cellColor(prob, maxProb) {
  if (prob <= 0) return "transparent";
  const intensity = Math.min(prob / Math.max(maxProb, 0.01), 1);
  const alpha = Math.round((0.08 + intensity * 0.77) * 255).toString(16).padStart(2, "0");
  return `#F4C430${alpha}`;
}

export default function ScoreMatrix({ data, homeName, awayName, lang, L }) {
  if (!data || !data.matrix || !Array.isArray(data.matrix) || data.matrix.length === 0) return null;

  const { matrix, top3, homeLambda, awayLambda } = data;

  // Find max probability for color scaling
  let maxProb = 0;
  let maxH = 0, maxA = 0;
  for (let h = 0; h < matrix.length; h++) {
    for (let a = 0; a < (matrix[h]?.length || 0); a++) {
      if (matrix[h][a] > maxProb) {
        maxProb = matrix[h][a];
        maxH = h;
        maxA = a;
      }
    }
  }

  const hName = homeName || "HOME";
  const aName = awayName || "AWAY";
  const cols = matrix[0]?.length || 0;

  return (
    <div style={{
      padding: "12px 14px",
      borderBottom: `1px solid ${C.border}`,
      fontFamily: FONT,
    }}>
      {/* Header */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: 8, paddingBottom: 6, borderBottom: `1px solid ${C.borderLight}`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{
            fontSize: 9, fontWeight: 700, letterSpacing: 3,
            color: C.accent,
          }}>
            {L?.scoreMatrix || "SCORE MATRIX"}
          </span>
          <span style={{
            fontSize: 7, padding: "1px 5px", borderRadius: 2,
            background: C.accent + "18", color: C.accent,
            letterSpacing: 1, fontWeight: 700,
          }}>{L?.poissonModel || "POISSON MODEL"}</span>
        </div>
        <span style={{ fontSize: 8, color: C.textMuted, fontFamily: FONT }}>
          {"\u03BB"} H:{homeLambda?.toFixed(2) || "0.00"} A:{awayLambda?.toFixed(2) || "0.00"}
        </span>
      </div>

      {/* Axis labels */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: 4,
      }}>
        <span style={{ fontSize: 7, color: C.accent, letterSpacing: 1.5, fontWeight: 700 }}>
          {hName} {"\u2192"}
        </span>
        <span style={{ fontSize: 7, color: C.textMuted, letterSpacing: 1 }}>
          {"\u2193"} {aName}
        </span>
      </div>

      {/* Grid */}
      <div style={{ overflowX: "auto" }}>
        <table style={{
          width: "100%",
          borderCollapse: "collapse",
          tableLayout: "fixed",
          fontSize: 8,
        }}>
          <thead>
            <tr>
              <th style={{
                width: 24, padding: "3px 2px",
                fontSize: 7, fontWeight: 700, color: C.textMuted,
                letterSpacing: 0.5, textAlign: "center",
                borderBottom: `1px solid ${C.borderLight}`,
                borderRight: `1px solid ${C.borderLight}`,
              }}>H\A</th>
              {Array.from({ length: cols }, (_, i) => (
                <th key={i} style={{
                  padding: "3px 1px",
                  fontSize: 8, fontWeight: 700, color: C.textDim,
                  textAlign: "center", letterSpacing: 0.5,
                  borderBottom: `1px solid ${C.borderLight}`,
                }}>{i}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, h) => (
              <tr key={h}>
                <td style={{
                  padding: "3px 2px",
                  fontSize: 8, fontWeight: 700, color: C.textDim,
                  textAlign: "center",
                  borderRight: `1px solid ${C.borderLight}`,
                  borderBottom: `1px solid ${C.border}`,
                }}>{h}</td>
                {(row || []).map((prob, a) => {
                  const isMax = h === maxH && a === maxA;
                  const pct = typeof prob === "number" ? prob : 0;
                  return (
                    <td key={a} style={{
                      padding: "2px 1px",
                      textAlign: "center",
                      background: cellColor(pct, maxProb),
                      border: isMax
                        ? `1px solid ${C.accent}`
                        : `1px solid ${C.border}`,
                      boxShadow: isMax ? `0 0 6px ${C.accent}40` : "none",
                      transition: "background 300ms",
                    }}>
                      <span style={{
                        fontSize: 8,
                        fontWeight: pct >= 2 ? 700 : 400,
                        color: pct >= 2 ? C.text : C.textMuted,
                        fontFamily: FONT,
                      }}>
                        {pct.toFixed(1)}%
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* TOP 3 MOST LIKELY */}
      {top3 && top3.length > 0 && (
        <div style={{
          marginTop: 8, paddingTop: 6,
          borderTop: `1px solid ${C.borderLight}`,
        }}>
          <div style={{
            fontSize: 8, fontWeight: 700, letterSpacing: 2,
            color: C.accent, marginBottom: 6,
          }}>
            {L?.topScores || "TOP 3 MOST LIKELY"}
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            {top3.map((s, i) => (
              <div key={i} style={{
                flex: 1,
                padding: "5px 4px",
                background: i === 0 ? C.accent + "14" : C.bgCard,
                border: `1px solid ${i === 0 ? C.accent + "40" : C.border}`,
                borderRadius: 2,
                textAlign: "center",
              }}>
                <div style={{
                  fontSize: 13, fontWeight: 800, color: i === 0 ? C.accentBright : C.text,
                  fontFamily: FONT, letterSpacing: 1,
                }}>
                  {s.score}
                </div>
                <div style={{
                  fontSize: 9, color: C.textDim, fontWeight: 600, marginTop: 2,
                }}>
                  {s.prob}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
