/**
 * PreMatchPanel — v1.0
 * Full-width pre-match banner showing AI prediction recommendation.
 * Gold top border, centered header, 1X2 + O/U recommendations.
 * Fades out when match goes live (active → false).
 * Bloomberg terminal style.
 */

import { LANG } from "../utils/i18n";

const C = {
  bg: "#0E1117", bgCard: "#131720",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  accent: "#F4C430", accentBright: "#FFD700",
  accentBlue: "#00C8FF",
  up: "#00C853", down: "#FF3D00",
};

const FONT = "'IBM Plex Mono', 'Noto Sans SC', monospace";

const FACTOR_LABELS = {
  en: {
    elo_advantage: "ELO ADVANTAGE",
    elo_balanced: "ELO BALANCED",
    expected_goals: "EXPECTED GOALS",
    market_aligned: "MARKET ALIGNED",
    no_market_data: "NO MARKET DATA",
  },
  zh: {
    elo_advantage: "ELO优势",
    elo_balanced: "ELO均衡",
    expected_goals: "预期进球",
    market_aligned: "市场一致",
    no_market_data: "无市场数据",
  },
};

function ProbBar({ label, value, isRecommended }) {
  const barColor = isRecommended ? C.accent : C.textMuted;
  return (
    <div style={{ flex: 1, textAlign: "center" }}>
      <div style={{
        fontSize: 8, letterSpacing: 1.5, marginBottom: 4,
        color: isRecommended ? C.accentBright : C.textMuted,
        fontWeight: isRecommended ? 700 : 400,
      }}>
        {label}
      </div>
      <div style={{
        height: 4, background: C.border, borderRadius: 2,
        margin: "0 4px", overflow: "hidden",
      }}>
        <div style={{
          width: `${Math.min(100, value)}%`,
          height: "100%",
          background: barColor,
          borderRadius: 2,
        }} />
      </div>
      <div style={{
        fontSize: isRecommended ? 20 : 14,
        fontWeight: isRecommended ? 800 : 600,
        fontFamily: "mono",
        color: isRecommended ? C.accentBright : C.textDim,
        marginTop: 4,
        textShadow: isRecommended ? `0 0 8px ${C.accent}40` : "none",
      }}>
        {value}<span style={{ fontSize: 10, color: C.textDim }}>%</span>
      </div>
    </div>
  );
}

export default function PreMatchPanel({ data, homeName = "HOME", awayName = "AWAY", lang = "en" }) {
  const L = LANG[lang];
  if (!data || !data.active) return null;

  const factorLabels = FACTOR_LABELS[lang] || FACTOR_LABELS.en;
  const probs = data.probabilities || {};
  const rec = data.recommendation1x2;

  const directionIcon = (d) => {
    if (d === "positive") return "\u25B2";
    if (d === "negative") return "\u25BC";
    return "\u25C6";
  };
  const directionColor = (d) => {
    if (d === "positive") return C.up;
    if (d === "negative") return C.down;
    return C.textDim;
  };

  return (
    <div style={{
      borderBottom: `1px solid ${C.border}`,
      borderTop: `2px solid ${C.accent}`,
      background: C.bgCard,
      fontFamily: FONT,
      animation: "preMatchFadeIn 0.5s ease-out",
    }}>
      <style>{preMatchCSS}</style>

      {/* Header */}
      <div style={{
        textAlign: "center", padding: "10px 0 6px",
        borderBottom: `1px solid ${C.borderLight}`,
      }}>
        <span style={{
          fontSize: 10, fontWeight: 700, letterSpacing: 3,
          color: C.accentBright,
          textShadow: `0 0 10px ${C.accent}40`,
        }}>
          {L?.preMatchAnalysis || "PRE-MATCH ANALYSIS"}
        </span>
      </div>

      <div style={{
        display: "grid", gridTemplateColumns: "1fr 1fr 1fr",
        gap: 16, padding: "12px 20px",
      }}>

        {/* LEFT: 1X2 Recommendation */}
        <div>
          <div style={{
            fontSize: 8, letterSpacing: 1.5, color: C.textMuted,
            marginBottom: 8, fontWeight: 600,
          }}>
            {L?.recommendation1x2 || "1X2 RECOMMENDATION"}
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <ProbBar
              label={L?.home || "HOME"}
              value={probs.home || 0}
              isRecommended={rec === "HOME"}
            />
            <ProbBar
              label={L?.draw || "DRAW"}
              value={probs.draw || 0}
              isRecommended={rec === "DRAW"}
            />
            <ProbBar
              label={L?.away || "AWAY"}
              value={probs.away || 0}
              isRecommended={rec === "AWAY"}
            />
          </div>
        </div>

        {/* CENTER: O/U Recommendation */}
        <div style={{ borderLeft: `1px solid ${C.borderLight}`, paddingLeft: 16 }}>
          <div style={{
            fontSize: 8, letterSpacing: 1.5, color: C.textMuted,
            marginBottom: 8, fontWeight: 600,
          }}>
            {L?.recommendationOu || "O/U RECOMMENDATION"}
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{
              fontSize: 9, color: C.textDim, marginBottom: 4,
            }}>
              {L?.line || "LINE"} {data.ouLine}
            </div>
            <div style={{
              fontSize: 22, fontWeight: 800, fontFamily: "mono",
              color: data.ouRecommendation === "OVER" ? C.up : C.accentBlue,
              letterSpacing: 2,
            }}>
              {data.ouRecommendation === "OVER" ? (L?.over || "OVER") : (L?.under || "UNDER")}
            </div>
            <div style={{
              display: "flex", justifyContent: "center", gap: 16, marginTop: 6,
              fontSize: 9, fontFamily: "mono",
            }}>
              <span style={{ color: data.ouRecommendation === "OVER" ? C.up : C.textDim }}>
                {L?.over || "O"} {data.probOver}%
              </span>
              <span style={{ color: data.ouRecommendation === "UNDER" ? C.accentBlue : C.textDim }}>
                {L?.under || "U"} {data.probUnder}%
              </span>
            </div>
            <div style={{
              fontSize: 8, color: C.textMuted, marginTop: 4,
            }}>
              {"\u03BB"} = {data.lambdaTotal}
            </div>
          </div>
        </div>

        {/* RIGHT: Confidence + Key Factors */}
        <div style={{ borderLeft: `1px solid ${C.borderLight}`, paddingLeft: 16 }}>
          {/* Confidence bar */}
          <div style={{
            fontSize: 8, letterSpacing: 1.5, color: C.textMuted,
            marginBottom: 6, fontWeight: 600,
          }}>
            {L?.confidence || "CONFIDENCE"}
          </div>
          <div style={{
            display: "flex", alignItems: "center", gap: 8, marginBottom: 10,
          }}>
            <div style={{
              flex: 1, height: 6, background: C.border, borderRadius: 3, overflow: "hidden",
            }}>
              <div style={{
                width: `${data.confidence}%`,
                height: "100%",
                background: data.confidence >= 75 ? C.up : data.confidence >= 55 ? C.accent : C.down,
                borderRadius: 3,
              }} />
            </div>
            <span style={{
              fontSize: 12, fontWeight: 800, fontFamily: "mono",
              color: data.confidence >= 75 ? C.up : data.confidence >= 55 ? C.accent : C.text,
            }}>
              {data.confidence}%
            </span>
          </div>

          {/* Key Factors */}
          <div style={{
            fontSize: 8, letterSpacing: 1.5, color: C.textMuted,
            marginBottom: 6, fontWeight: 600,
          }}>
            {L?.keyFactors || "KEY FACTORS"}
          </div>
          {(data.keyFactors || []).map((f, i) => (
            <div key={i} style={{
              display: "flex", alignItems: "center", gap: 6,
              padding: "3px 0", fontSize: 9,
            }}>
              <span style={{ color: directionColor(f.direction), fontSize: 8 }}>
                {directionIcon(f.direction)}
              </span>
              <span style={{ color: C.textDim, flex: 1 }}>
                {factorLabels[f.factor] || f.factor.replace(/_/g, " ").toUpperCase()}
              </span>
              <span style={{ fontFamily: "mono", color: C.text, fontWeight: 600 }}>
                {f.value}
              </span>
            </div>
          ))}

          {/* Source */}
          <div style={{
            marginTop: 6, paddingTop: 4, borderTop: `1px solid ${C.borderLight}`,
            fontSize: 8, color: C.textMuted,
          }}>
            {L?.modelSource || "SOURCE"}: <span style={{ color: C.accent, fontWeight: 600 }}>{data.source}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

const preMatchCSS = `
  @keyframes preMatchFadeIn {
    0% { opacity: 0; transform: translateY(-4px); }
    100% { opacity: 1; transform: translateY(0); }
  }
`;
