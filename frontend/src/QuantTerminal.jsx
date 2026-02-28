import { useState, useEffect, useRef } from "react";
import { useMatchData } from "./hooks/useWebSocket";
import { LANG } from "./utils/i18n";
import { mapPayload } from "./utils/mapPayload";
import EventTape from "./components/EventTape";
import MarketEdge from "./components/MarketEdge";
import ExplainPanel from "./components/ExplainPanel";
import TotalGoalsPanel from "./components/TotalGoalsPanel";
import OUScanner from "./components/OUScanner";
import ReportBanner from "./components/ReportBanner";
import GoalWindow from "./components/GoalWindow";
import RiskPanel from "./components/RiskPanel";
import LineMovement from "./components/LineMovement";
import SignalCooldownBar from "./components/SignalCooldownBar";
import EdgeHeatBar from "./components/EdgeHeatBar";
import ModelCycleTimer from "./components/ModelCycleTimer";
import EventAlert from "./components/EventAlert";
import TrackRecord from "./components/TrackRecord";
import SignalControlPanel from "./components/SignalControlPanel";
import PostMatchSummary from "./components/PostMatchSummary";

/*
 * ═══════════════════════════════════════════════════════════════════
 *  AI FOOTBALL QUANT TERMINAL v2.0
 *  Bloomberg-style probability analytics terminal
 *
 *  v1.1: meta bar, market/edge, event tape, explain, uncertainty, report
 * ═══════════════════════════════════════════════════════════════════
 */

const C = {
  bg: "#0E1117", bgCard: "#131720", bgRow: "#161B25",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  up: "#00C853", down: "#FF3D00",
  accent: "#F4C430", accentBlue: "#00C8FF",
};

// ── Sparkline ────────────────────────────────────────────────
function MiniSpark({ data, color, h = 32, w = "100%" }) {
  if (!data || data.length < 2) return <div style={{ height: h }} />;
  const W = 300;
  const mn = Math.min(...data), mx = Math.max(...data), rng = mx - mn || 1;
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * W},${h - 2 - ((v - mn) / rng) * (h - 4)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${W} ${h}`} style={{ width: w, height: h, display: "block" }} preserveAspectRatio="none">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.2" strokeLinejoin="round" opacity="0.85" />
    </svg>
  );
}

function Delta({ value, suffix = "%" }) {
  if (value === 0 || value === undefined) return <span style={{ color: C.textMuted, fontFamily: "mono", fontSize: 11 }}>— 0.00{suffix}</span>;
  const up = value > 0;
  return (
    <span style={{ color: up ? C.up : C.down, fontFamily: "mono", fontSize: 11, fontWeight: 600 }}>
      {up ? "▲" : "▼"} {up ? "+" : ""}{typeof value === "number" ? value.toFixed(2) : value}{suffix}
    </span>
  );
}

function ProbRow({ label, value, delta, tag }) {
  return (
    <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", padding: "6px 0", borderBottom: `1px solid ${C.border}` }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 2, fontWeight: 600, minWidth: 80 }}>{label}</span>
        {tag && <span style={{ fontSize: 8, padding: "1px 5px", borderRadius: 2, background: C.accent + "18", color: C.accent, letterSpacing: 1, fontWeight: 700 }}>{tag}</span>}
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 16 }}>
        <span style={{ fontSize: 22, fontWeight: 800, color: C.text, fontFamily: "mono", letterSpacing: -0.5 }}>
          {value.toFixed(2)}<span style={{ fontSize: 13, color: C.textDim }}>%</span>
        </span>
        <span style={{ minWidth: 90, textAlign: "right" }}><Delta value={delta} /></span>
      </div>
    </div>
  );
}

function StatRow({ label, hv, av, suffix = "", highlight }) {
  return (
    <div style={{ display: "flex", alignItems: "center", padding: "4px 0", borderBottom: `1px solid ${C.border}` }}>
      <span style={{ flex: 1, textAlign: "right", fontFamily: "mono", fontSize: 12, fontWeight: 600, color: highlight === "home" ? C.up : C.text }}>{hv}{suffix}</span>
      <span style={{ width: 130, textAlign: "center", fontSize: 10, color: C.textDim, letterSpacing: 1.5, padding: "0 8px" }}>{label}</span>
      <span style={{ flex: 1, textAlign: "left", fontFamily: "mono", fontSize: 12, fontWeight: 600, color: highlight === "away" ? C.up : C.text }}>{av}{suffix}</span>
    </div>
  );
}

function QuantRow({ label, value, unit = "", tier = "free" }) {
  const tc = tier === "pro" ? C.accentBlue : tier === "elite" ? C.accent : C.text;
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "5px 0", borderBottom: `1px solid ${C.border}` }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1.5, fontWeight: 600 }}>{label}</span>
        {tier !== "free" && <span style={{ fontSize: 7, padding: "1px 4px", borderRadius: 2, border: `1px solid ${tc}30`, color: tc, letterSpacing: 1, fontWeight: 700 }}>{tier.toUpperCase()}</span>}
      </div>
      <span style={{ fontFamily: "mono", fontSize: 13, fontWeight: 700, color: tc, letterSpacing: -0.3 }}>
        {value}<span style={{ fontSize: 10, color: C.textDim, marginLeft: 2 }}>{unit}</span>
      </span>
    </div>
  );
}

// ── Alert Badges ─────────────────────────────────────────────
function AlertBadge({ label, bg, color }) {
  return (
    <span style={{
      display: "inline-block", fontSize: 7, fontWeight: 700, letterSpacing: 1.5,
      padding: "2px 6px", borderRadius: 9, lineHeight: 1.2,
      background: bg, color, fontFamily: "mono", whiteSpace: "nowrap",
    }}>{label}</span>
  );
}

function SectionHead({ label, right }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8, paddingBottom: 6, borderBottom: `1px solid ${C.borderLight}` }}>
      <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: 3, color: C.accent, fontFamily: "mono" }}>{label}</span>
      {right && <span style={{ fontSize: 9, color: C.textMuted, fontFamily: "mono" }}>{right}</span>}
    </div>
  );
}

function TrendTab({ tabs, active, onChange }) {
  return (
    <div style={{ display: "flex", gap: 0, marginBottom: 8 }}>
      {tabs.map(tb => (
        <button key={tb.k} onClick={() => onChange(tb.k)} style={{
          padding: "4px 10px", fontSize: 9, fontWeight: 600, letterSpacing: 1.5,
          border: "none", borderBottom: active === tb.k ? `2px solid ${C.accent}` : `2px solid transparent`,
          background: "transparent", color: active === tb.k ? C.accent : C.textMuted,
          cursor: "pointer", fontFamily: "mono",
        }}>{tb.l}</button>
      ))}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// MAIN TERMINAL v1.1
// ════════════════════════════════════════════════════════════════
export default function QuantTerminal({ matchId = "demo" }) {
  const [lang, setLang] = useState("en");
  const t = LANG[lang];
  const [trendTab, setTrendTab] = useState("prob");
  const [history, setHistory] = useState({ h: [], d: [], a: [], pressure: [], hxg: [], axg: [], lambda: [] });

  const { data: rawData, connected, health } = useMatchData(matchId);
  const d = rawData ? mapPayload(rawData) : null;

  // Accumulate history
  useEffect(() => {
    if (!d) return;
    setHistory(h => ({
      h: [...h.h.slice(-89), d.probability.home],
      d: [...h.d.slice(-89), d.probability.draw],
      a: [...h.a.slice(-89), d.probability.away],
      pressure: [...h.pressure.slice(-89), d.quant.pressure],
      hxg: [...h.hxg.slice(-89), d.stats.xg[0]],
      axg: [...h.axg.slice(-89), d.stats.xg[1]],
      lambda: [...h.lambda.slice(-89), d.totalGoals?.lambda_live || 0],
    }));
  }, [d?.meta?.seq]);

  // Loading
  if (!d) return (
    <div style={{ ...sty.root, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <style>{globalCSS}</style>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontFamily: "mono", fontSize: 14, color: C.accent, letterSpacing: 4, marginBottom: 8 }}>AI FOOTBALL QUANT TERMINAL</div>
        <div style={{ fontFamily: "mono", fontSize: 10, color: C.textMuted }}>{connected ? "Waiting for data..." : "Connecting..."}</div>
      </div>
    </div>
  );

  const hn = lang === "zh" && d.home.nameCn ? d.home.nameCn : d.home.name;
  const an = lang === "zh" && d.away.nameCn ? d.away.nameCn : d.away.name;
  const healthColor = health === "OK" ? C.up : health === "DEGRADED" ? C.accent : C.down;

  // Signal Control callbacks
  const handleSignalConfirm = () => {
    fetch("/api/signal/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ match_id: matchId, action: "confirm" }),
    }).catch(() => {});
  };
  const handleSignalReject = () => {
    fetch("/api/signal/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ match_id: matchId, action: "reject" }),
    }).catch(() => {});
  };

  return (
    <div style={sty.root}>
      <style>{globalCSS}</style>

      {/* ═══ LAYER 1: STATE BAR + META ═══ */}
      <div style={sty.stateBar}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontSize: 9, color: C.accent, letterSpacing: 3, fontWeight: 700 }}>QUANT TERMINAL</span>
          <span style={sty.divider}>|</span>
          <span style={{ color: C.textDim, fontSize: 10 }}>{d.league}</span>
          <span style={sty.divider}>|</span>
          <span style={{ color: C.textDim, fontSize: 10 }}>{d.round}</span>
          <span style={sty.divider}>|</span>
          <span style={{ color: C.text, fontSize: 10, fontWeight: 600 }}>{d.home.code}</span>
          <span style={{ color: C.accent, fontSize: 14, fontWeight: 800, fontFamily: "mono", letterSpacing: 1 }}>
            {d.score[0]} — {d.score[1]}
          </span>
          <span style={{ color: C.text, fontSize: 10, fontWeight: 600 }}>{d.away.code}</span>
          <span style={sty.divider}>|</span>
          <span style={{ fontFamily: "mono", fontSize: 12, fontWeight: 700, color: C.up }}>{d.minute}'</span>
          <span style={{ color: C.textMuted, fontSize: 9 }}>{d.half}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {/* v1.1 Meta info — flash red if delay < 30s (compliance minimum) */}
          <span style={{
            fontSize: 8, fontFamily: "mono", fontWeight: d.meta.dataDelaySec < 30 ? 700 : 400,
            color: d.meta.dataDelaySec < 30 ? C.down : C.textMuted,
            animation: d.meta.dataDelaySec < 30 ? "delayFlash 1s infinite" : "none",
          }}>
            DELAY {d.meta.dataDelaySec}s{d.meta.dataDelaySec < 30 ? " !" : ""}
          </span>
          <span style={sty.divider}>|</span>
          <span style={{ fontSize: 8, color: C.textMuted, fontFamily: "mono" }}>
            SRC {d.meta.source.live || "?"}
          </span>
          <span style={sty.divider}>|</span>
          {/* Alert badges */}
          {d.quant.volatility > 1.0 && <AlertBadge label="VOL SPIKE" bg="#F4C43030" color="#F4C430" />}
          {d.quant.goalWindow && /^\d+-\d+$/.test(d.quant.goalWindow) && <AlertBadge label="GOAL WINDOW" bg="#00C85325" color="#00C853" />}
          {health === "STALE" && <AlertBadge label="DATA STALE" bg="#FF3D0025" color="#FF3D00" />}
          <div style={{ width: 6, height: 6, borderRadius: "50%", background: healthColor, animation: connected ? "blink 2s infinite" : "none" }} />
          <span style={{ fontSize: 8, color: healthColor, letterSpacing: 2, fontWeight: 700 }}>{health}</span>
          <button onClick={() => setLang(l => l === "en" ? "zh" : "en")} style={sty.langBtn}>{t.switchLang}</button>
        </div>
      </div>

      {/* ═══ DISCLAIMER ═══ */}
      <div style={{ textAlign: "center", padding: "3px 0", fontSize: 8, letterSpacing: 2, color: C.textMuted, background: C.down + "08", borderBottom: `1px solid ${C.border}` }}>
        {t.disclaimer} &mdash; DATA VISUALIZATION ONLY &mdash; NOT FINANCIAL ADVICE
      </div>

      {/* ═══ REPORT BANNER ═══ */}
      <ReportBanner report={d.report} />

      {/* ═══ GOAL WINDOW BANNER ═══ */}
      <GoalWindow data={d.goalWindow} />

      {/* ═══ POST-MATCH SUMMARY ═══ */}
      <PostMatchSummary data={d.postMatch} t={t} />

      {/* ═══ MAIN GRID ═══ */}
      <div style={sty.mainGrid}>

        {/* ▌ LEFT — Probability + Market + Explain + Quant */}
        <div style={sty.panel}>
          <div style={sty.section}>
            <SectionHead label={t.probLabel} right={`MODEL v3.2 | CONF ${d.confidence}%`} />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1, marginBottom: 12 }}>
              <div style={sty.probPanel}>
                <div style={{ fontSize: 8, color: C.textMuted, letterSpacing: 2, marginBottom: 4 }}>{t.home} — {d.home.code}</div>
                <div style={{ fontSize: 32, fontWeight: 800, fontFamily: "mono", color: C.text, lineHeight: 1, letterSpacing: -1 }}>
                  {d.probability.home.toFixed(2)}<span style={{ fontSize: 14, color: C.textDim }}>%</span>
                </div>
                <div style={{ marginTop: 4 }}><Delta value={d.delta.home} /></div>
              </div>
              <div style={sty.probPanel}>
                <div style={{ fontSize: 8, color: C.textMuted, letterSpacing: 2, marginBottom: 4 }}>{t.away} — {d.away.code}</div>
                <div style={{ fontSize: 32, fontWeight: 800, fontFamily: "mono", color: C.text, lineHeight: 1, letterSpacing: -1 }}>
                  {d.probability.away.toFixed(2)}<span style={{ fontSize: 14, color: C.textDim }}>%</span>
                </div>
                <div style={{ marginTop: 4 }}><Delta value={d.delta.away} /></div>
              </div>
            </div>
            <ProbRow label={t.draw} value={d.probability.draw} delta={d.delta.draw} />

            {/* v1.1 Market + Edge (Pro) */}
            {d.market && (
              <div style={{ marginTop: 8, paddingTop: 6, borderTop: `1px solid ${C.border}` }}>
                <MarketEdge market={d.market} />
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, padding: "6px 0", borderTop: `1px solid ${C.border}` }}>
              <span style={{ fontSize: 9, color: C.textMuted }}>{t.modelConf}: <span style={{ color: C.accent, fontWeight: 700, fontFamily: "mono" }}>{d.confidence}%</span></span>
              <span style={{ fontSize: 9, color: C.textMuted }}>{t.modelVar}: <span style={{ color: C.text, fontFamily: "mono" }}>{d.quant.modelVariance}</span></span>
            </div>
          </div>

          {/* v1.2 Total Goals O/U Engine */}
          {d.totalGoals && (
            <TotalGoalsPanel totalGoals={d.totalGoals} quant={d.quant} />
          )}

          {/* v2.0 Edge Heat Bar */}
          {d.totalGoals && (
            <div style={{ padding: "4px 14px" }}>
              <EdgeHeatBar edge={d.totalGoals.edge || 0} />
            </div>
          )}

          {/* v2.0 Signal Cooldown Bar */}
          {d.totalGoals && (
            <div style={{ padding: "0 14px 4px" }}>
              <SignalCooldownBar
                signalState={
                  d.totalGoals.in_cooldown ? "cooldown"
                  : d.totalGoals.signal !== "NO SIGNAL" ? "ready"
                  : (d.totalGoals.edge || 0) > 2 ? "building"
                  : "monitoring"
                }
                cooldownSec={d.totalGoals.cooldown_remaining_sec || 0}
                cooldownTotal={180}
              />
            </div>
          )}

          {/* v2.1 Signal Control Panel (semi-automatic confirmation) */}
          {d.signalControl && (
            <div style={{ padding: "4px 14px" }}>
              <SignalControlPanel
                data={d.signalControl}
                onConfirm={handleSignalConfirm}
                onReject={handleSignalReject}
              />
            </div>
          )}

          {/* v2.0 O/U Scanner (multi-line) */}
          {d.totalGoals?.scanner && (
            <OUScanner data={d.totalGoals.scanner} label={t.ouScanner} />
          )}

          {/* Line Movement */}
          {d.lineMovement && (
            <LineMovement data={d.lineMovement} label={t.lineMovement} />
          )}

          {/* Risk Panel */}
          {d.risk && (
            <RiskPanel data={d.risk} label={t.riskPanel} />
          )}

          {/* v1.1 Explain (Pro) */}
          {d.explain && d.explain.topFactors?.length > 0 && (
            <div style={sty.section}>
              <ExplainPanel explain={d.explain} />
            </div>
          )}

          {/* Quant */}
          <div style={sty.section}>
            <SectionHead label={t.quantLabel} right="REFRESH 2s" />
            <QuantRow label={t.pressure} value={d.quant.pressure} tier="pro" />
            <QuantRow label={t.momentum} value={d.quant.momentum > 0 ? `+${d.quant.momentum}` : d.quant.momentum} tier="pro" />
            <QuantRow label={t.volatility} value={d.quant.volatility} tier="pro" />
            <QuantRow label={t.riskConcede} value={d.quant.riskConcede} unit="%" tier="pro" />
            <QuantRow label={t.xgDelta} value={d.quant.xgDelta > 0 ? `+${d.quant.xgDelta}` : d.quant.xgDelta} tier="pro" />
            <QuantRow label={t.goalWindow} value={d.quant.goalWindow} unit={t.min} tier="elite" />
            <QuantRow label={t.modelVar} value={d.quant.modelVariance} tier="elite" />

            {/* v1.1 Uncertainty (Elite) */}
            {d.uncertainty && (
              <>
                <div style={{ marginTop: 6, paddingTop: 4, borderTop: `1px solid ${C.borderLight}` }}>
                  <QuantRow label="CI95 HOME" value={`${d.uncertainty.ci95Home[0]}–${d.uncertainty.ci95Home[1]}`} unit="%" tier="elite" />
                  <QuantRow label="SHARPNESS" value={d.uncertainty.sharpness} tier="elite" />
                  {d.uncertainty.brierRolling != null && (
                    <QuantRow label="BRIER 20m" value={d.uncertainty.brierRolling} tier="elite" />
                  )}
                  <QuantRow label="MC RUNS" value={d.uncertainty.mcRuns?.toLocaleString()} tier="elite" />
                </div>
              </>
            )}
          </div>
        </div>

        {/* ▌ CENTER — Trend */}
        <div style={sty.panel}>
          <div style={sty.section}>
            <SectionHead label={t.trendLabel} right={`0' → ${d.minute}'`} />
            <TrendTab tabs={[
              { k: "prob", l: t.probTrend },
              { k: "pressure", l: t.pressureTrend },
              { k: "xg", l: t.xgTrend },
              { k: "lambda", l: t.lambdaTrend || "\u03BB TOTAL" },
            ]} active={trendTab} onChange={setTrendTab} />

            {trendTab === "prob" && (
              <div>
                <div style={{ marginBottom: 2 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                    <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1 }}>{t.homeWin}</span>
                    <span style={{ fontSize: 10, fontFamily: "mono", color: C.text, fontWeight: 600 }}>{d.probability.home.toFixed(2)}%</span>
                  </div>
                  <MiniSpark data={history.h} color={C.text} h={48} />
                </div>
                <div style={{ marginBottom: 2, marginTop: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                    <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1 }}>{t.draw}</span>
                    <span style={{ fontSize: 10, fontFamily: "mono", color: C.textDim, fontWeight: 600 }}>{d.probability.draw.toFixed(2)}%</span>
                  </div>
                  <MiniSpark data={history.d} color={C.textDim} h={32} />
                </div>
                <div style={{ marginTop: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                    <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1 }}>{t.awayWin}</span>
                    <span style={{ fontSize: 10, fontFamily: "mono", color: C.accentBlue, fontWeight: 600 }}>{d.probability.away.toFixed(2)}%</span>
                  </div>
                  <MiniSpark data={history.a} color={C.accentBlue} h={32} />
                </div>
              </div>
            )}

            {trendTab === "pressure" && (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1 }}>{t.pressure}</span>
                  <span style={{ fontSize: 12, fontFamily: "mono", color: d.quant.pressure > 60 ? C.up : C.text, fontWeight: 700 }}>{d.quant.pressure}</span>
                </div>
                <MiniSpark data={history.pressure} color={C.accent} h={100} />
              </div>
            )}

            {trendTab === "xg" && (
              <div>
                <div style={{ marginBottom: 2 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                    <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1 }}>{d.home.code} {t.xg}</span>
                    <span style={{ fontSize: 11, fontFamily: "mono", color: C.text, fontWeight: 700 }}>{d.stats.xg[0]}</span>
                  </div>
                  <MiniSpark data={history.hxg} color={C.text} h={50} />
                </div>
                <div style={{ marginTop: 10 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                    <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1 }}>{d.away.code} {t.xg}</span>
                    <span style={{ fontSize: 11, fontFamily: "mono", color: C.accentBlue, fontWeight: 700 }}>{d.stats.xg[1]}</span>
                  </div>
                  <MiniSpark data={history.axg} color={C.accentBlue} h={50} />
                </div>
                <div style={{ marginTop: 8, padding: "6px 0", borderTop: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 9, color: C.textMuted }}>{t.xgDelta}</span>
                  <span style={{ fontFamily: "mono", fontSize: 12, fontWeight: 700, color: d.quant.xgDelta > 0 ? C.up : d.quant.xgDelta < 0 ? C.down : C.text }}>
                    {d.quant.xgDelta > 0 ? "+" : ""}{d.quant.xgDelta}
                  </span>
                </div>
              </div>
            )}

            {trendTab === "lambda" && (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1 }}>{"\u03BB"}_TOTAL (LIVE)</span>
                  <span style={{ fontSize: 12, fontFamily: "mono", color: C.accent, fontWeight: 700 }}>
                    {d.totalGoals?.lambda_live?.toFixed(2) || "0.00"}
                  </span>
                </div>
                <MiniSpark data={history.lambda} color={C.accent} h={100} />
                {d.totalGoals && (
                  <div style={{ marginTop: 8, padding: "6px 0", borderTop: `1px solid ${C.border}` }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ fontSize: 9, color: C.textMuted }}>PRE {"\u03BB"}</span>
                      <span style={{ fontFamily: "mono", fontSize: 11, color: C.textDim }}>{d.totalGoals.lambda_pre?.toFixed(2)}</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ fontSize: 9, color: C.textMuted }}>MARKET {"\u03BB"}</span>
                      <span style={{ fontFamily: "mono", fontSize: 11, color: C.textDim }}>{d.totalGoals.lambda_market?.toFixed(2)}</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ fontSize: 9, color: C.textMuted }}>LINE</span>
                      <span style={{ fontFamily: "mono", fontSize: 11, fontWeight: 700, color: C.text }}>{d.totalGoals.line?.toFixed(1)}</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* ▌ RIGHT — Stats + Events */}
        <div style={sty.panel}>
          <div style={sty.section}>
            <SectionHead label={t.statsLabel} right="REFRESH 2s" />
            <div style={{ display: "flex", alignItems: "center", padding: "4px 0", borderBottom: `2px solid ${C.borderLight}` }}>
              <span style={{ flex: 1, textAlign: "right", fontSize: 9, color: C.accent, fontWeight: 700, letterSpacing: 1 }}>{d.home.code}</span>
              <span style={{ width: 130, textAlign: "center", fontSize: 9, color: C.textMuted, letterSpacing: 1 }}>STAT</span>
              <span style={{ flex: 1, textAlign: "left", fontSize: 9, color: C.accentBlue, fontWeight: 700, letterSpacing: 1 }}>{d.away.code}</span>
            </div>
            <div style={{ marginTop: 4 }}>
              <StatRow label={t.shots} hv={d.stats.shots[0]} av={d.stats.shots[1]} highlight={d.stats.shots[0] > d.stats.shots[1] ? "home" : d.stats.shots[1] > d.stats.shots[0] ? "away" : undefined} />
              <StatRow label={t.shotsOn} hv={d.stats.shotsOn[0]} av={d.stats.shotsOn[1]} />
              <StatRow label={t.shotsOff} hv={d.stats.shotsOff[0]} av={d.stats.shotsOff[1]} />
              <StatRow label={t.xg} hv={d.stats.xg[0]} av={d.stats.xg[1]} highlight={d.stats.xg[0] > d.stats.xg[1] ? "home" : "away"} />
              <StatRow label={t.dangerAtk} hv={d.stats.dangerAtk[0]} av={d.stats.dangerAtk[1]} />
              <StatRow label={t.corners} hv={d.stats.corners[0]} av={d.stats.corners[1]} />
            </div>
            <div style={{ marginTop: 8, paddingTop: 4, borderTop: `1px solid ${C.borderLight}` }}>
              <StatRow label={t.possession} hv={d.stats.possession[0]} av={d.stats.possession[1]} suffix="%" />
              <StatRow label={t.passAcc} hv={d.stats.passAcc[0]} av={d.stats.passAcc[1]} suffix="%" />
            </div>
            <div style={{ marginTop: 8, paddingTop: 4, borderTop: `1px solid ${C.borderLight}` }}>
              <StatRow label={t.fouls} hv={d.stats.fouls[0]} av={d.stats.fouls[1]} />
              <StatRow label={t.yellows} hv={d.stats.yellows[0]} av={d.stats.yellows[1]} />
              <StatRow label={t.reds} hv={d.stats.reds[0]} av={d.stats.reds[1]} />
              <StatRow label={t.offsides} hv={d.stats.offsides[0]} av={d.stats.offsides[1]} />
              <StatRow label={t.saves} hv={d.stats.saves[0]} av={d.stats.saves[1]} />
            </div>
          </div>

          {/* v1.1 Event Tape */}
          <div style={sty.section}>
            <SectionHead label="EVENT TAPE" right={`LAST ${Math.min(5, d.events.length)}`} />
            <EventTape events={d.events} maxShow={5} />
          </div>

          {/* v2.0 Model Cycle Timer */}
          <div style={sty.section}>
            <ModelCycleTimer
              state={d.totalGoals?.in_cooldown ? "recalculating" : "monitoring"}
              nextEvalSec={d.totalGoals?.cooldown_remaining_sec || 30}
              volatility={d.risk?.market_volatility || "Medium"}
            />
          </div>

          {/* Track Record / Performance */}
          {d.performance && (
            <TrackRecord data={d.performance} label={t.todayPerformance} />
          )}
        </div>
      </div>

      {/* ═══ FOOTER ═══ */}
      <div style={sty.footer}>
        <span style={{ color: C.textMuted }}>AI FOOTBALL QUANT TERMINAL v2.0 &copy; 2026</span>
        <span style={{ color: C.textMuted }}>
          SEQ {d.meta.seq} | REFRESH 2s | MODEL XGB+POISSON | {d.minute}'/90'
        </span>
      </div>

      {/* ═══ EVENT ALERT OVERLAY ═══ */}
      <EventAlert events={d.events} score={d.score} delta={d.delta} minute={d.minute} t={t} />

      {/* ═══ WATERMARK OVERLAY ═══ */}
      <div style={{
        position: "fixed", bottom: 28, right: 18, pointerEvents: "none", userSelect: "none",
        fontSize: 9, fontFamily: "mono", letterSpacing: 2, fontWeight: 600,
        color: C.textMuted, opacity: 0.35, lineHeight: 1,
      }}>
        DATA VISUALIZATION ONLY — NOT FINANCIAL ADVICE
      </div>
    </div>
  );
}

const globalCSS = `
  @keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}
  @keyframes delayFlash{0%,100%{opacity:1}50%{opacity:0.3}}
  *{box-sizing:border-box}
  ::-webkit-scrollbar{width:3px}
  ::-webkit-scrollbar-track{background:transparent}
  ::-webkit-scrollbar-thumb{background:${C.border};border-radius:1px}
`;

const sty = {
  root: { minHeight: "100vh", background: C.bg, fontFamily: "'IBM Plex Mono', 'Noto Sans SC', monospace", color: C.text, position: "relative" },
  stateBar: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 16px", background: C.bgCard, borderBottom: `1px solid ${C.border}`, fontFamily: "mono", fontSize: 10 },
  divider: { color: C.textMuted, margin: "0 2px", fontSize: 10 },
  langBtn: { padding: "3px 8px", fontSize: 8, fontWeight: 600, letterSpacing: 1, border: `1px solid ${C.border}`, borderRadius: 2, background: "transparent", color: C.textDim, cursor: "pointer", fontFamily: "mono" },
  mainGrid: { display: "grid", gridTemplateColumns: "1fr 1.1fr 0.9fr", gap: 1, background: C.border, height: "calc(100vh - 72px)", overflow: "hidden" },
  panel: { background: C.bg, overflow: "auto", padding: 0 },
  section: { padding: "12px 14px", borderBottom: `1px solid ${C.border}` },
  probPanel: { padding: "12px 14px", background: C.bgCard, border: `1px solid ${C.border}` },
  footer: { display: "flex", justifyContent: "space-between", padding: "4px 16px", fontSize: 8, letterSpacing: 1, fontFamily: "mono", borderTop: `1px solid ${C.border}`, background: C.bgCard },
};
