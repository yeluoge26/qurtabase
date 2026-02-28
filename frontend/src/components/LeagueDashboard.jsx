/**
 * LeagueDashboard — v1.0
 * Bloomberg-terminal-style league prediction dashboard.
 * Displays one card per league with AI prediction when no live match is active.
 * Used for livestream display.
 */

import { useState } from "react";

const C = {
  bg: "#0a0e17", bgCard: "#131720", bgRow: "#161B25",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  accent: "#F4C430", accentBright: "#FFD700",
  accentBlue: "#00C8FF",
  up: "#00C853", down: "#FF3D00",
};

const FONT = "'IBM Plex Mono', 'JetBrains Mono', 'Noto Sans SC', monospace";

const L = {
  en: {
    title: "LEAGUE PREDICTION DASHBOARD",
    subtitle: "AI MODEL PREDICTIONS",
    model: "XGBoost v3.2",
    accuracy: "1X2 ACC",
    roi: "BACKTEST ROI",
    sample: "SAMPLE",
    nextMatch: "NEXT",
    recentMatch: "RECENT",
    home: "HOME", draw: "DRAW", away: "AWAY",
    over: "OVER", under: "UNDER", line: "LINE",
    confidence: "CONFIDENCE",
    source: "SOURCE",
    backtestAcc: "BACKTEST",
    matches: "MATCHES",
    refresh: "AUTO-REFRESH 30m",
    scanning: "Scanning for live matches every 30s...",
    noData: "Loading league predictions...",
    switchLang: "中",
    disclaimer: "For reference only. Not financial advice.",
    upcoming: "UPCOMING",
    finished: "FINISHED",
    recommendation: "REC",
    ouRec: "O/U",
    lambda: "\u03BB",
    factors: "KEY FACTORS",
    eloAdvantage: "ELO ADVANTAGE",
    eloBalanced: "ELO BALANCED",
    expectedGoals: "EXPECTED GOALS",
    marketAligned: "MARKET ALIGNED",
    noMarketData: "NO MARKET DATA",
  },
  zh: {
    title: "\u8054\u8d5b\u9884\u6d4b\u9762\u677f",
    subtitle: "AI \u6a21\u578b\u9884\u6d4b",
    model: "XGBoost v3.2",
    accuracy: "1X2\u51c6\u786e\u7387",
    roi: "\u56de\u6d4bROI",
    sample: "\u6837\u672c",
    nextMatch: "\u4e0b\u4e00\u573a",
    recentMatch: "\u6700\u8fd1",
    home: "\u4e3b", draw: "\u5e73", away: "\u5ba2",
    over: "\u5927", under: "\u5c0f", line: "\u76d8\u53e3",
    confidence: "\u7f6e\u4fe1\u5ea6",
    source: "\u6570\u636e\u6e90",
    backtestAcc: "\u56de\u6d4b",
    matches: "\u573a",
    refresh: "\u81ea\u52a8\u5237\u65b0 30\u5206\u949f",
    scanning: "\u6bcf30\u79d2\u626b\u63cf\u76f4\u64ad\u8d5b\u4e8b...",
    noData: "\u6b63\u5728\u52a0\u8f7d\u8054\u8d5b\u9884\u6d4b...",
    switchLang: "EN",
    disclaimer: "\u4ec5\u4f9b\u53c2\u8003\uff0c\u4e0d\u6784\u6210\u6295\u8d44\u5efa\u8bae\u3002",
    upcoming: "\u672a\u5f00\u8d5b",
    finished: "\u5df2\u7ed3\u675f",
    recommendation: "\u63a8\u8350",
    ouRec: "\u5927\u5c0f",
    lambda: "\u03BB",
    factors: "\u5173\u952e\u56e0\u7d20",
    eloAdvantage: "ELO\u4f18\u52bf",
    eloBalanced: "ELO\u5747\u8861",
    expectedGoals: "\u9884\u671f\u8fdb\u7403",
    marketAligned: "\u5e02\u573a\u4e00\u81f4",
    noMarketData: "\u65e0\u5e02\u573a\u6570\u636e",
  },
};

const FACTOR_MAP = {
  elo_advantage: "eloAdvantage",
  elo_balanced: "eloBalanced",
  expected_goals: "expectedGoals",
  market_aligned: "marketAligned",
  no_market_data: "noMarketData",
};

function ProbBar({ label, value, isRec }) {
  const barColor = isRec ? C.accent : C.textMuted;
  return (
    <div style={{ flex: 1, textAlign: "center" }}>
      <div style={{
        fontSize: 8, letterSpacing: 1.5, marginBottom: 3,
        color: isRec ? C.accentBright : C.textMuted,
        fontWeight: isRec ? 700 : 400,
      }}>{label}</div>
      <div style={{
        height: 3, background: C.border, borderRadius: 2,
        margin: "0 2px", overflow: "hidden",
      }}>
        <div style={{
          width: `${Math.min(100, value)}%`, height: "100%",
          background: barColor, borderRadius: 2,
        }} />
      </div>
      <div style={{
        fontSize: isRec ? 18 : 12,
        fontWeight: isRec ? 800 : 600,
        fontFamily: "mono",
        color: isRec ? C.accentBright : C.textDim,
        marginTop: 3,
        textShadow: isRec ? `0 0 6px ${C.accent}40` : "none",
      }}>
        {value}<span style={{ fontSize: 9, color: C.textDim }}>%</span>
      </div>
    </div>
  );
}

function LeagueCard({ prediction, t }) {
  const p = prediction;
  const probs = p.probabilities || {};
  const rec = p.recommendation_1x2;
  const isUpcoming = p.match_status === "upcoming";

  const dirIcon = (d) => d === "positive" ? "\u25B2" : d === "negative" ? "\u25BC" : "\u25C6";
  const dirColor = (d) => d === "positive" ? C.up : d === "negative" ? C.down : C.textDim;

  return (
    <div style={{
      background: C.bgCard,
      border: `1px solid ${C.border}`,
      borderTop: `2px solid ${C.accent}`,
      fontFamily: FONT,
      overflow: "hidden",
    }}>
      {/* Header: League + Backtest badge */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "8px 12px", borderBottom: `1px solid ${C.borderLight}`,
        background: C.bgRow,
      }}>
        <span style={{
          fontSize: 11, fontWeight: 700, letterSpacing: 2, color: C.accentBright,
        }}>{p.league}</span>
        {p.backtest_accuracy > 0 && (
          <span style={{
            fontSize: 8, fontWeight: 700, letterSpacing: 1,
            padding: "2px 6px", borderRadius: 2,
            background: C.accent + "20", color: C.accent,
          }}>
            {t.backtestAcc} {p.backtest_accuracy}% ({p.backtest_total}{t.matches})
          </span>
        )}
      </div>

      {/* Match info */}
      <div style={{ padding: "8px 12px 4px", borderBottom: `1px solid ${C.borderLight}` }}>
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <div>
            <span style={{ fontSize: 12, fontWeight: 700, color: C.text }}>
              {p.home}
            </span>
            <span style={{ fontSize: 10, color: C.textMuted, margin: "0 6px" }}>vs</span>
            <span style={{ fontSize: 12, fontWeight: 700, color: C.text }}>
              {p.away}
            </span>
          </div>
          <span style={{
            fontSize: 7, letterSpacing: 1, fontWeight: 600,
            padding: "2px 5px", borderRadius: 2,
            background: isUpcoming ? C.up + "20" : C.accentBlue + "20",
            color: isUpcoming ? C.up : C.accentBlue,
          }}>
            {isUpcoming ? t.upcoming : t.finished}
          </span>
        </div>
        <div style={{ fontSize: 9, color: C.textDim, marginTop: 2 }}>
          {p.date} {p.time}{p.round ? ` | R${p.round}` : ""}
          {!isUpcoming && p.score ? ` | ${p.score}` : ""}
        </div>
      </div>

      {/* 1X2 Probabilities */}
      <div style={{ padding: "8px 12px", borderBottom: `1px solid ${C.borderLight}` }}>
        <div style={{ display: "flex", gap: 6 }}>
          <ProbBar label={t.home} value={probs.home || 0} isRec={rec === "HOME"} />
          <ProbBar label={t.draw} value={probs.draw || 0} isRec={rec === "DRAW"} />
          <ProbBar label={t.away} value={probs.away || 0} isRec={rec === "AWAY"} />
        </div>
      </div>

      {/* O/U + Confidence row */}
      <div style={{
        display: "grid", gridTemplateColumns: "1fr 1fr",
        borderBottom: `1px solid ${C.borderLight}`,
      }}>
        {/* O/U */}
        <div style={{ padding: "6px 12px", borderRight: `1px solid ${C.borderLight}` }}>
          <div style={{ fontSize: 7, letterSpacing: 1.5, color: C.textMuted, marginBottom: 3, fontWeight: 600 }}>
            {t.ouRec} {t.line} {p.ou_line}
          </div>
          <div style={{
            fontSize: 16, fontWeight: 800, fontFamily: "mono", letterSpacing: 1,
            color: p.ou_recommendation === "OVER" ? C.up : C.accentBlue,
          }}>
            {p.ou_recommendation === "OVER" ? t.over : t.under}
          </div>
          <div style={{ fontSize: 8, color: C.textDim, marginTop: 2 }}>
            {t.lambda} = {p.lambda_total}
          </div>
        </div>

        {/* Confidence */}
        <div style={{ padding: "6px 12px" }}>
          <div style={{ fontSize: 7, letterSpacing: 1.5, color: C.textMuted, marginBottom: 3, fontWeight: 600 }}>
            {t.confidence}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{
              flex: 1, height: 4, background: C.border, borderRadius: 2, overflow: "hidden",
            }}>
              <div style={{
                width: `${p.confidence}%`, height: "100%", borderRadius: 2,
                background: p.confidence >= 75 ? C.up : p.confidence >= 55 ? C.accent : C.down,
              }} />
            </div>
            <span style={{
              fontSize: 14, fontWeight: 800, fontFamily: "mono",
              color: p.confidence >= 75 ? C.up : p.confidence >= 55 ? C.accent : C.text,
            }}>{p.confidence}%</span>
          </div>
          <div style={{ fontSize: 8, color: C.textDim, marginTop: 3 }}>
            {t.source}: <span style={{ color: C.accent, fontWeight: 600 }}>{p.source}</span>
          </div>
        </div>
      </div>

      {/* Key Factors */}
      {(p.key_factors || []).length > 0 && (
        <div style={{ padding: "5px 12px 8px" }}>
          {(p.key_factors || []).map((f, i) => (
            <div key={i} style={{
              display: "flex", alignItems: "center", gap: 5,
              padding: "2px 0", fontSize: 8,
            }}>
              <span style={{ color: dirColor(f.direction), fontSize: 7 }}>
                {dirIcon(f.direction)}
              </span>
              <span style={{ color: C.textDim, flex: 1 }}>
                {t[FACTOR_MAP[f.factor]] || f.factor.replace(/_/g, " ").toUpperCase()}
              </span>
              <span style={{ fontFamily: "mono", color: C.text, fontWeight: 600 }}>
                {f.value}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function LeagueDashboard({ data, lang: initLang = "zh" }) {
  const [lang, setLang] = useState(initLang);
  const t = L[lang] || L.en;

  if (!data || !data.leagues || data.leagues.length === 0) {
    return (
      <div style={{
        background: C.bg, color: C.textDim, minHeight: "100vh",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: FONT, fontSize: 13,
      }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 28, color: C.textMuted, marginBottom: 16, letterSpacing: 4 }}>QURTABASE</div>
          <div style={{ color: C.textDim, marginBottom: 8 }}>{t.noData}</div>
          <div style={{ width: 120, height: 2, background: C.border, borderRadius: 1, overflow: "hidden", margin: "0 auto" }}>
            <div style={{ width: "40%", height: "100%", background: C.accent, animation: "pulse 2s ease-in-out infinite" }} />
          </div>
        </div>
      </div>
    );
  }

  const ms = data.model_stats || {};
  const refreshTime = data.last_refresh
    ? new Date(data.last_refresh * 1000).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })
    : "--:--";

  return (
    <div style={{ background: C.bg, minHeight: "100vh", fontFamily: FONT }}>
      <style>{dashCSS}</style>

      {/* ═══ TOP BAR ═══ */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "10px 20px",
        borderBottom: `1px solid ${C.border}`,
        background: C.bgCard,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{
            fontSize: 14, fontWeight: 800, letterSpacing: 3,
            color: C.accentBright,
            textShadow: `0 0 12px ${C.accent}30`,
          }}>QURTABASE</span>
          <span style={{ fontSize: 9, color: C.textMuted, letterSpacing: 2 }}>
            {t.title}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 8, color: C.textMuted }}>
            {refreshTime}
          </span>
          <div style={{ width: 5, height: 5, borderRadius: "50%", background: C.up, animation: "blink 2s infinite" }} />
          <span style={{ fontSize: 8, color: C.up, letterSpacing: 1 }}>LIVE</span>
          <button
            onClick={() => setLang(l => l === "en" ? "zh" : "en")}
            style={{
              background: "none", border: `1px solid ${C.border}`, color: C.textDim,
              fontSize: 9, padding: "2px 8px", cursor: "pointer", borderRadius: 2,
              fontFamily: FONT,
            }}
          >{t.switchLang}</button>
        </div>
      </div>

      {/* ═══ MODEL STATS BAR ═══ */}
      <div style={{
        display: "flex", justifyContent: "center", gap: 32,
        padding: "8px 20px",
        borderBottom: `2px solid ${C.accent}`,
        background: C.accent + "08",
      }}>
        <StatItem label={t.model} value="" color={C.textDim} />
        <StatItem label={t.accuracy} value={`${ms.accuracy_1x2 || 0}%`} color={C.accentBright} />
        <StatItem label={t.roi} value={`+${ms.roi?.roi_pct || 0}%`} color={C.up} />
        <StatItem label={t.sample} value={`${ms.total || 0}`} color={C.text} />
        <StatItem label="O/U ACC" value={`${ms.accuracy_ou || 0}%`} color={C.accentBlue} />
        <StatItem label="BRIER" value={`${ms.mean_brier || 0}`} color={C.textDim} />
      </div>

      {/* ═══ DISCLAIMER ═══ */}
      <div style={{
        textAlign: "center", padding: "3px 0", fontSize: 7,
        letterSpacing: 2, color: C.textMuted,
        background: C.down + "08", borderBottom: `1px solid ${C.border}`,
      }}>
        {t.disclaimer}
      </div>

      {/* ═══ LEAGUE CARDS GRID ═══ */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
        gap: 12, padding: "16px 20px",
      }}>
        {data.leagues.map((pred, i) => (
          <LeagueCard key={pred.league || i} prediction={pred} t={t} />
        ))}
      </div>

      {/* ═══ FOOTER ═══ */}
      <div style={{
        display: "flex", justifyContent: "center", alignItems: "center", gap: 16,
        padding: "12px 20px",
        borderTop: `1px solid ${C.border}`,
        fontSize: 9, color: C.textMuted,
      }}>
        <span>{t.refresh}</span>
        <span style={{ color: C.borderLight }}>|</span>
        <span>{t.scanning}</span>
        <span style={{ color: C.borderLight }}>|</span>
        <span>{data.league_count || 0} {lang === "zh" ? "\u4e2a\u8054\u8d5b" : "leagues"}</span>
      </div>
    </div>
  );
}

function StatItem({ label, value, color }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ fontSize: 7, letterSpacing: 1.5, color: C.textMuted, marginBottom: 2 }}>{label}</div>
      {value && <div style={{ fontSize: 12, fontWeight: 800, fontFamily: "mono", color, letterSpacing: 1 }}>{value}</div>}
    </div>
  );
}

const dashCSS = `
  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }
  @keyframes pulse {
    0%, 100% { transform: translateX(0); }
    50% { transform: translateX(100%); }
  }
`;
