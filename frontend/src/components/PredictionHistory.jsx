/**
 * PredictionHistory — v1.0
 * Shows historical prediction accuracy across matches.
 * Bloomberg terminal style panel:
 *  - 1X2 accuracy % and O/U accuracy % (large numbers)
 *  - Streak indicator (recent 5 with check/cross)
 *  - Confidence breakdown: HIGH/MED/LOW accuracy with mini bars
 *  - Avg Brier score + avg confidence footer
 */

import { LANG } from "../utils/i18n";

const C = {
  bg: "#0E1117", bgCard: "#131720",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  accent: "#F4C430", accentBlue: "#00C8FF",
  up: "#00C853", down: "#FF3D00",
};

const FONT = "'IBM Plex Mono', 'Noto Sans SC', monospace";

function ConfBar({ label, total, correct, pct, color }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
      <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1, minWidth: 28, fontWeight: 700 }}>{label}</span>
      <div style={{ flex: 1, height: 6, background: C.border, borderRadius: 3, overflow: "hidden" }}>
        <div style={{
          width: `${Math.min(100, pct)}%`,
          height: "100%",
          background: color,
          borderRadius: 3,
          transition: "width 0.3s ease",
        }} />
      </div>
      <span style={{ fontSize: 9, fontFamily: "mono", color: C.text, fontWeight: 700, minWidth: 40, textAlign: "right" }}>
        {pct}%
      </span>
      <span style={{ fontSize: 8, color: C.textMuted, minWidth: 30, textAlign: "right" }}>
        {correct}/{total}
      </span>
    </div>
  );
}

export default function PredictionHistory({ data, lang = "en" }) {
  const L = LANG[lang];
  if (!data || data.totalMatches === 0) return null;

  const bc = data.byConfidence || {};
  const streakColor = data.streak > 0 ? C.up : data.streak < 0 ? C.down : C.textDim;
  const streakText = data.streak > 0 ? `+${data.streak}` : `${data.streak}`;

  return (
    <div style={{
      padding: "12px 14px",
      borderBottom: `1px solid ${C.border}`,
      fontFamily: FONT,
    }}>
      {/* Header */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: 10, paddingBottom: 6, borderBottom: `1px solid ${C.borderLight}`,
      }}>
        <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: 2, color: C.accent }}>
          {L?.predictionHistory || "PREDICTION HISTORY"}
        </span>
        <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1 }}>
          {L?.totalMatches || "TOTAL"} {data.totalMatches}
        </span>
      </div>

      {/* Accuracy row: 1X2 + O/U side by side */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 10 }}>
        {/* 1X2 accuracy */}
        <div style={{
          background: C.bgCard, border: `1px solid ${C.border}`,
          padding: "8px 10px", textAlign: "center",
        }}>
          <div style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1.5, marginBottom: 4 }}>
            {L?.accuracy1x2 || "1X2 ACCURACY"}
          </div>
          <div style={{
            fontSize: 26, fontWeight: 800, fontFamily: "mono",
            color: data.accuracy1x2Pct >= 60 ? C.up : data.accuracy1x2Pct >= 45 ? C.accent : C.down,
            lineHeight: 1,
          }}>
            {data.accuracy1x2Pct}<span style={{ fontSize: 12, color: C.textDim }}>%</span>
          </div>
          <div style={{ fontSize: 8, color: C.textDim, marginTop: 2 }}>
            {data.correct1x2}/{data.totalMatches}
          </div>
        </div>

        {/* O/U accuracy */}
        <div style={{
          background: C.bgCard, border: `1px solid ${C.border}`,
          padding: "8px 10px", textAlign: "center",
        }}>
          <div style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1.5, marginBottom: 4 }}>
            {L?.accuracyOu || "O/U ACCURACY"}
          </div>
          <div style={{
            fontSize: 26, fontWeight: 800, fontFamily: "mono",
            color: data.accuracyOuPct >= 60 ? C.up : data.accuracyOuPct >= 45 ? C.accent : C.down,
            lineHeight: 1,
          }}>
            {data.accuracyOuPct}<span style={{ fontSize: 12, color: C.textDim }}>%</span>
          </div>
          <div style={{ fontSize: 8, color: C.textDim, marginTop: 2 }}>
            {data.correctOu}/{data.totalMatches}
          </div>
        </div>
      </div>

      {/* Streak + Recent 5 */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "6px 0", borderBottom: `1px solid ${C.borderLight}`, marginBottom: 8,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1.5 }}>
            {L?.streak || "STREAK"}
          </span>
          <span style={{
            fontSize: 14, fontWeight: 800, fontFamily: "mono", color: streakColor,
          }}>
            {streakText}
          </span>
        </div>
        <div style={{ display: "flex", gap: 3 }}>
          {(data.recent5 || []).map((r, i) => (
            <div key={i} style={{
              width: 16, height: 16,
              display: "flex", alignItems: "center", justifyContent: "center",
              background: r.correct ? C.up + "20" : C.down + "20",
              border: `1px solid ${r.correct ? C.up + "40" : C.down + "40"}`,
              borderRadius: 2, fontSize: 9, fontWeight: 700,
              color: r.correct ? C.up : C.down,
            }} title={r.match}>
              {r.correct ? "\u2713" : "\u2717"}
            </div>
          ))}
        </div>
      </div>

      {/* Confidence breakdown */}
      <div style={{ marginBottom: 8 }}>
        <div style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1.5, marginBottom: 6 }}>
          {L?.byConfidence || "BY CONFIDENCE"}
        </div>
        {bc.high && (
          <ConfBar
            label={L?.highConf || "HIGH"}
            total={bc.high.total}
            correct={bc.high.correct}
            pct={bc.high.pct}
            color={C.up}
          />
        )}
        {bc.medium && (
          <ConfBar
            label={L?.medConf || "MED"}
            total={bc.medium.total}
            correct={bc.medium.correct}
            pct={bc.medium.pct}
            color={C.accent}
          />
        )}
        {bc.low && (
          <ConfBar
            label={L?.lowConf || "LOW"}
            total={bc.low.total}
            correct={bc.low.correct}
            pct={bc.low.pct}
            color={C.down}
          />
        )}
      </div>

      {/* Footer: Avg Brier + Avg Confidence */}
      <div style={{
        display: "flex", justifyContent: "space-between",
        padding: "6px 0", borderTop: `1px solid ${C.borderLight}`,
        fontSize: 9, color: C.textDim,
      }}>
        <span>
          {L?.avgBrier || "AVG BRIER"}: <span style={{ color: C.text, fontFamily: "mono", fontWeight: 700 }}>{data.avgBrier}</span>
        </span>
        <span>
          {L?.avgConf || "AVG CONF"}: <span style={{ color: C.accent, fontFamily: "mono", fontWeight: 700 }}>{data.avgConfidence}%</span>
        </span>
      </div>
    </div>
  );
}
