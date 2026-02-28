/**
 * PostMatchSummary -- v1.0
 * Full-width post-match summary panel -- Bloomberg terminal style
 * Appears when match ends (active === true) with a 500ms fade-in.
 * Displays final score, lambda accuracy, peak metrics, and key analytics.
 */
import { useState, useEffect } from "react";

const C = {
  bg: "#0E1117",
  bgCard: "#131720",
  border: "#1E2530",
  borderLight: "#252D3A",
  text: "#E5E5E5",
  textDim: "#6B7280",
  textMuted: "#3D4654",
  gold: "#F4C430",
  goldBg: "rgba(244, 196, 48, 0.08)",
  green: "#00C853",
  red: "#FF3D00",
};

export default function PostMatchSummary({ data, t }) {
  const [visible, setVisible] = useState(false);
  const [render, setRender] = useState(false);

  const active = data?.active === true;

  // Manage fade-in / fade-out lifecycle
  useEffect(() => {
    if (active) {
      setRender(true);
      const raf = requestAnimationFrame(() => setVisible(true));
      return () => cancelAnimationFrame(raf);
    } else {
      setVisible(false);
      const timeout = setTimeout(() => setRender(false), 520);
      return () => clearTimeout(timeout);
    }
  }, [active]);

  if (!render) return null;

  const preLambda = data?.pre_lambda ?? 0;
  const finalGoals = data?.final_goals ?? 0;
  const finalScore = data?.final_score ?? "0-0";
  const peakLambda = data?.peak_lambda ?? 0;
  const bestEdge = data?.best_edge ?? 0;
  const avgLambda = data?.avg_lambda ?? 0;
  const accuracy = data?.lambda_accuracy ?? "MISS";
  const totalUpdates = data?.total_updates ?? 0;

  const scoreParts = finalScore.split("-");
  const isHit = accuracy === "HIT";

  return (
    <div style={{
      width: "100%",
      background: C.bgCard,
      borderTop: `3px solid ${C.gold}`,
      borderBottom: `1px solid ${C.border}`,
      opacity: visible ? 1 : 0,
      transition: "opacity 500ms ease-in-out",
      fontFamily: "'IBM Plex Mono', monospace",
      padding: "20px 24px",
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        marginBottom: 18,
        gap: 12,
        position: "relative",
      }}>
        <span style={{
          fontSize: 9,
          fontWeight: 700,
          letterSpacing: 4,
          color: C.gold,
        }}>
          {"═══"}
        </span>
        <span style={{
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: 4,
          color: C.gold,
        }}>
          {t?.matchSummary || "MATCH SUMMARY"}
        </span>
        <span style={{
          fontSize: 9,
          fontWeight: 700,
          letterSpacing: 4,
          color: C.gold,
        }}>
          {"═══════════════════════════════════"}
        </span>
        <button
          onClick={() => {
            const now = new Date();
            const pad = n => String(n).padStart(2, "0");
            const fname = `match_summary_${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}_${pad(now.getHours())}-${pad(now.getMinutes())}.json`;
            const exportData = {
              timestamp: now.toISOString(),
              home: data?.home ?? "",
              away: data?.away ?? "",
              score: finalScore,
              pre_lambda: preLambda,
              peak_lambda: peakLambda,
              avg_lambda: avgLambda,
              best_edge: bestEdge,
              lambda_accuracy: accuracy,
            };
            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = fname;
            a.click();
            URL.revokeObjectURL(url);
          }}
          style={{
            position: "absolute",
            right: 0,
            top: "50%",
            transform: "translateY(-50%)",
            fontSize: 8,
            fontWeight: 700,
            fontFamily: "'IBM Plex Mono', monospace",
            letterSpacing: 1,
            color: C.textDim,
            background: "transparent",
            border: `1px solid ${C.border}`,
            borderRadius: 2,
            padding: "3px 8px",
            cursor: "pointer",
            transition: "color 200ms, border-color 200ms",
          }}
          onMouseEnter={e => { e.currentTarget.style.color = C.gold; e.currentTarget.style.borderColor = C.gold; }}
          onMouseLeave={e => { e.currentTarget.style.color = C.textDim; e.currentTarget.style.borderColor = C.border; }}
        >
          EXPORT JSON
        </button>
      </div>

      {/* Top row: Final Score + Primary metrics */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr 1fr 1fr",
        gap: 24,
        marginBottom: 20,
        alignItems: "center",
      }}>
        {/* Final Score */}
        <div style={{ textAlign: "center" }}>
          <div style={{
            fontSize: 9,
            color: C.textDim,
            letterSpacing: 2,
            marginBottom: 6,
            fontWeight: 600,
          }}>
            {t?.finalScore || "FINAL SCORE"}
          </div>
          <div style={{
            fontSize: 28,
            fontWeight: 800,
            color: C.text,
            letterSpacing: 2,
            lineHeight: 1,
          }}>
            {scoreParts[0]} <span style={{ color: C.textMuted }}>{"\u2014"}</span> {scoreParts[1]}
          </div>
        </div>

        {/* Pre Lambda */}
        <div style={{ textAlign: "center" }}>
          <div style={{
            fontSize: 9,
            color: C.textDim,
            letterSpacing: 2,
            marginBottom: 6,
            fontWeight: 600,
          }}>
            Pre {"\u03BB"}
          </div>
          <div style={{
            fontSize: 22,
            fontWeight: 700,
            color: C.text,
            letterSpacing: -0.5,
          }}>
            {preLambda.toFixed(2)}
          </div>
        </div>

        {/* Peak Lambda */}
        <div style={{ textAlign: "center" }}>
          <div style={{
            fontSize: 9,
            color: C.textDim,
            letterSpacing: 2,
            marginBottom: 6,
            fontWeight: 600,
          }}>
            {t?.peakLambda || "Peak \u03BB"}
          </div>
          <div style={{
            fontSize: 22,
            fontWeight: 700,
            color: C.gold,
            letterSpacing: -0.5,
          }}>
            {peakLambda.toFixed(2)}
          </div>
        </div>

        {/* Avg Lambda */}
        <div style={{ textAlign: "center" }}>
          <div style={{
            fontSize: 9,
            color: C.textDim,
            letterSpacing: 2,
            marginBottom: 6,
            fontWeight: 600,
          }}>
            Avg {"\u03BB"}
          </div>
          <div style={{
            fontSize: 22,
            fontWeight: 700,
            color: C.text,
            letterSpacing: -0.5,
          }}>
            {avgLambda.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Bottom row: Edge + Accuracy + Updates */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr 1fr",
        gap: 24,
        marginBottom: 18,
        paddingTop: 14,
        borderTop: `1px solid ${C.border}`,
      }}>
        {/* Best Edge */}
        <div style={{ textAlign: "center" }}>
          <div style={{
            fontSize: 9,
            color: C.textDim,
            letterSpacing: 2,
            marginBottom: 6,
            fontWeight: 600,
          }}>
            BEST EDGE
          </div>
          <div style={{
            fontSize: 18,
            fontWeight: 700,
            color: bestEdge >= 5 ? C.green : C.text,
          }}>
            +{bestEdge.toFixed(1)}%
          </div>
        </div>

        {/* Lambda Accuracy */}
        <div style={{ textAlign: "center" }}>
          <div style={{
            fontSize: 9,
            color: C.textDim,
            letterSpacing: 2,
            marginBottom: 6,
            fontWeight: 600,
          }}>
            {"\u03BB"} ACCURACY
          </div>
          <div style={{
            fontSize: 18,
            fontWeight: 800,
            color: isHit ? C.green : C.red,
            letterSpacing: 2,
          }}>
            {accuracy}
          </div>
        </div>

        {/* Total Updates */}
        <div style={{ textAlign: "center" }}>
          <div style={{
            fontSize: 9,
            color: C.textDim,
            letterSpacing: 2,
            marginBottom: 6,
            fontWeight: 600,
          }}>
            UPDATES
          </div>
          <div style={{
            fontSize: 18,
            fontWeight: 700,
            color: C.text,
          }}>
            {totalUpdates}
          </div>
        </div>
      </div>

      {/* Accuracy summary line */}
      <div style={{
        textAlign: "center",
        padding: "10px 0 4px",
        borderTop: `1px solid ${C.border}`,
      }}>
        <span style={{
          fontSize: 10,
          color: C.textDim,
          letterSpacing: 1,
        }}>
          Pre {"\u03BB"}: <span style={{ color: C.text, fontWeight: 700 }}>{preLambda.toFixed(2)}</span>
          <span style={{ color: C.textMuted, margin: "0 8px" }}>{"\u2192"}</span>
          Final Goals: <span style={{ color: C.text, fontWeight: 700 }}>{finalGoals}</span>
          <span style={{ color: C.textMuted, margin: "0 8px" }}>{"\u2192"}</span>
          Accuracy: <span style={{
            color: isHit ? C.green : C.red,
            fontWeight: 800,
          }}>{accuracy} {isHit ? "\u2713" : "\u2717"}</span>
        </span>
      </div>
    </div>
  );
}
