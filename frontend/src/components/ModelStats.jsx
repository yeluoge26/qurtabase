import { LANG } from "../utils/i18n";

const C = {
  bg: "#0E1117", bgCard: "#131720",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  up: "#00C853", down: "#FF3D00",
  accent: "#F4C430", accentBlue: "#00C8FF",
};

/**
 * ModelStats — Backtest results display (Bloomberg terminal style)
 * Shows: overall accuracy, by-league breakdown, by-confidence, ROI, streaks
 */
export default function ModelStats({ data, lang = "en" }) {
  const L = LANG[lang] || LANG.en;
  if (!data) return null;

  const {
    total = 0, testPeriod = "", accuracy1x2 = 0, accuracyOu = 0,
    meanBrier = 0, avgConfidence = 0,
    byLeague = {}, byConfidence = {}, roi = null, streak = null,
  } = data;

  const leagueEntries = Object.entries(byLeague).sort((a, b) => b[1].accuracy - a[1].accuracy);
  const confBands = [
    { key: "high", label: L.highConfPredictions || "HIGH", color: C.up },
    { key: "medium", label: L.medConfPredictions || "MED", color: C.accent },
    { key: "low", label: L.lowConfPredictions || "LOW", color: C.down },
  ];

  return (
    <div style={{ padding: "12px 14px", borderBottom: `1px solid ${C.border}` }}>
      {/* Header */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: 8, paddingBottom: 6, borderBottom: `1px solid ${C.borderLight}`,
      }}>
        <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: 3, color: C.accent, fontFamily: "mono" }}>
          {L.modelPerformance || "MODEL PERFORMANCE"}
        </span>
        <span style={{ fontSize: 8, color: C.textMuted, fontFamily: "mono" }}>
          {L.backtestResults || "BACKTEST"} | {total.toLocaleString()}
        </span>
      </div>

      {/* Overall Accuracy — 1X2 and O/U side by side */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 10 }}>
        <div style={{ background: C.bgCard, border: `1px solid ${C.border}`, padding: "8px 10px", textAlign: "center" }}>
          <div style={{ fontSize: 8, color: C.textMuted, letterSpacing: 2, marginBottom: 4 }}>
            {L.accuracy1x2 || "1X2 ACCURACY"}
          </div>
          <div style={{ fontSize: 24, fontWeight: 800, fontFamily: "mono", color: accuracy1x2 >= 60 ? C.up : C.text }}>
            {accuracy1x2.toFixed(1)}<span style={{ fontSize: 12, color: C.textDim }}>%</span>
          </div>
        </div>
        <div style={{ background: C.bgCard, border: `1px solid ${C.border}`, padding: "8px 10px", textAlign: "center" }}>
          <div style={{ fontSize: 8, color: C.textMuted, letterSpacing: 2, marginBottom: 4 }}>
            {L.accuracyOu || "O/U ACCURACY"}
          </div>
          <div style={{ fontSize: 24, fontWeight: 800, fontFamily: "mono", color: accuracyOu >= 55 ? C.up : C.text }}>
            {accuracyOu.toFixed(1)}<span style={{ fontSize: 12, color: C.textDim }}>%</span>
          </div>
        </div>
      </div>

      {/* ROI Section */}
      {roi && (
        <div style={{
          background: C.bgCard, border: `1px solid ${C.border}`, padding: "8px 10px",
          marginBottom: 10,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
            <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 2, fontWeight: 600 }}>
              {L.simulatedRoi || "SIMULATED ROI"}
            </span>
            <span style={{
              fontSize: 18, fontWeight: 800, fontFamily: "mono",
              color: roi.roiPct >= 0 ? C.up : C.down,
            }}>
              {roi.roiPct >= 0 ? "+" : ""}{roi.roiPct.toFixed(1)}%
            </span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 4 }}>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 7, color: C.textMuted, letterSpacing: 1 }}>{L.betsPlaced || "BETS"}</div>
              <div style={{ fontSize: 11, fontFamily: "mono", color: C.text, fontWeight: 600 }}>{roi.bets.toLocaleString()}</div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 7, color: C.textMuted, letterSpacing: 1 }}>{L.totalStaked || "STAKED"}</div>
              <div style={{ fontSize: 11, fontFamily: "mono", color: C.text, fontWeight: 600 }}>{roi.staked.toLocaleString()}</div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 7, color: C.textMuted, letterSpacing: 1 }}>{L.profit || "PROFIT"}</div>
              <div style={{
                fontSize: 11, fontFamily: "mono", fontWeight: 700,
                color: (roi.returned - roi.staked) >= 0 ? C.up : C.down,
              }}>
                {(roi.returned - roi.staked) >= 0 ? "+" : ""}{(roi.returned - roi.staked).toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* By Confidence */}
      {Object.keys(byConfidence).length > 0 && (
        <div style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 8, color: C.textMuted, letterSpacing: 2, marginBottom: 6, fontWeight: 600 }}>
            {L.byConfidence || "BY CONFIDENCE"}
          </div>
          {confBands.map(({ key, label, color }) => {
            const band = byConfidence[key];
            if (!band) return null;
            const pct = band.accuracy || 0;
            return (
              <div key={key} style={{
                display: "flex", alignItems: "center", gap: 8, padding: "3px 0",
                borderBottom: `1px solid ${C.border}`,
              }}>
                <span style={{ fontSize: 8, color, fontWeight: 700, letterSpacing: 1, minWidth: 40, fontFamily: "mono" }}>
                  {label}
                </span>
                <div style={{ flex: 1, height: 6, background: C.bgCard, borderRadius: 2, overflow: "hidden" }}>
                  <div style={{
                    width: `${Math.min(pct, 100)}%`, height: "100%",
                    background: color, borderRadius: 2, transition: "width 0.5s ease",
                  }} />
                </div>
                <span style={{ fontSize: 10, fontFamily: "mono", fontWeight: 700, color, minWidth: 42, textAlign: "right" }}>
                  {pct.toFixed(1)}%
                </span>
                <span style={{ fontSize: 8, color: C.textMuted, fontFamily: "mono", minWidth: 30, textAlign: "right" }}>
                  {band.total || 0}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* By League */}
      {leagueEntries.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 8, color: C.textMuted, letterSpacing: 2, marginBottom: 6, fontWeight: 600 }}>
            {L.byLeague || "BY LEAGUE"}
          </div>
          {leagueEntries.map(([league, info]) => (
            <div key={league} style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              padding: "3px 0", borderBottom: `1px solid ${C.border}`,
            }}>
              <span style={{ fontSize: 9, color: C.textDim, fontFamily: "mono", flex: 1 }}>{league}</span>
              <span style={{
                fontSize: 10, fontFamily: "mono", fontWeight: 700, minWidth: 46, textAlign: "right",
                color: info.accuracy >= 65 ? C.up : info.accuracy >= 55 ? C.accent : C.text,
              }}>
                {info.accuracy.toFixed(1)}%
              </span>
              <span style={{ fontSize: 8, color: C.textMuted, fontFamily: "mono", minWidth: 36, textAlign: "right" }}>
                {info.total}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Footer: streaks + meta */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        paddingTop: 6, borderTop: `1px solid ${C.borderLight}`,
      }}>
        <div style={{ display: "flex", gap: 12 }}>
          {streak && (
            <>
              <span style={{ fontSize: 8, color: C.textMuted, fontFamily: "mono" }}>
                {L.maxWinStreak || "WIN"} <span style={{ color: C.up, fontWeight: 700 }}>{streak.maxWin}</span>
              </span>
              <span style={{ fontSize: 8, color: C.textMuted, fontFamily: "mono" }}>
                {L.maxLossStreak || "LOSS"} <span style={{ color: C.down, fontWeight: 700 }}>{streak.maxLoss}</span>
              </span>
            </>
          )}
        </div>
        <span style={{ fontSize: 7, color: C.textMuted, fontFamily: "mono", letterSpacing: 1 }}>
          {testPeriod}
        </span>
      </div>
    </div>
  );
}
