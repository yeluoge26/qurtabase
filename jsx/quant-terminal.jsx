import { useState, useEffect, useRef, useMemo } from "react";

/*
 * ═══════════════════════════════════════════════════════════════════
 *  AI FOOTBALL QUANT TERMINAL
 *  Bloomberg-style probability analytics terminal
 *  
 *  Design: Financial terminal — NOT sports broadcast
 *  No gauges, no glow, no rings, no sport aesthetics
 *  Pure monospace, delta arrows, thin lines, dense data
 *  
 *  5-Layer Architecture:
 *    1. State Layer      — match status bar
 *    2. Probability Layer — core 1X2 with delta
 *    3. Trend Layer       — probability sparklines
 *    4. Stat Layer        — technical stats table
 *    5. Quant Layer       — model-derived indicators
 * ═══════════════════════════════════════════════════════════════════
 */

// ── Color system (per PRD §5.1) ─────────────────────────────────
const C = {
  bg: "#0E1117",
  bgCard: "#131720",
  bgRow: "#161B25",
  border: "#1E2530",
  borderLight: "#252D3A",
  text: "#E5E5E5",
  textDim: "#6B7280",
  textMuted: "#3D4654",
  up: "#00C853",
  down: "#FF3D00",
  accent: "#F4C430",
  accentBlue: "#00C8FF",
  home: "#E5E5E5",
  away: "#E5E5E5",
};

// ── Match config ────────────────────────────────────────────────
const MATCH = {
  league: "EPL",
  home: { name: "ARS", full: "Arsenal", fullCN: "阿森纳" },
  away: { name: "CHE", full: "Chelsea", fullCN: "切尔西" },
  venue: "Emirates Stadium",
  round: "R28",
};

// ── i18n ────────────────────────────────────────────────────────
const LANG = {
  en: {
    stateLabel: "STATE", probLabel: "PROBABILITY", trendLabel: "TREND",
    statsLabel: "TECHNICAL STATISTICS", quantLabel: "QUANT INDICATORS",
    homeWin: "HOME WIN", draw: "DRAW", awayWin: "AWAY WIN",
    modelConf: "MODEL CONFIDENCE", modelVar: "MODEL VARIANCE",
    shots: "SHOTS", shotsOn: "ON TARGET", shotsOff: "OFF TARGET",
    xg: "xG", dangerAtk: "DANGEROUS ATK", corners: "CORNERS",
    possession: "POSSESSION", passAcc: "PASS ACCURACY",
    fouls: "FOULS", yellows: "YELLOW CARDS", reds: "RED CARDS",
    pressure: "PRESSURE INDEX", momentum: "MOMENTUM SHIFT",
    volatility: "VOLATILITY", riskConcede: "RISK OF CONCEDE",
    goalWindow: "EXPECTED GOAL WINDOW", confInterval: "CONF. INTERVAL",
    switchLang: "中文", live: "LIVE", half: "HALF",
    home: "HOME", away: "AWAY", delta: "Δ",
    free: "FREE", pro: "PRO", elite: "ELITE",
    disclaimer: "DATA VISUALIZATION ONLY — NO MATCH FOOTAGE — QUANT MODEL OUTPUT",
    xgDelta: "xG DELTA", riskIndex: "RISK INDEX",
    halfTimeSummary: "HT SUMMARY",
    attacks: "ATTACKS", saves: "SAVES", offsides: "OFFSIDES",
    probTrend: "1X2 PROBABILITY", pressureTrend: "PRESSURE", xgTrend: "xG CUMULATIVE",
    min: "MIN",
  },
  zh: {
    stateLabel: "比赛状态", probLabel: "概率面板", trendLabel: "走势图",
    statsLabel: "技术统计", quantLabel: "量化指标",
    homeWin: "主胜", draw: "平局", awayWin: "客胜",
    modelConf: "模型置信度", modelVar: "模型方差",
    shots: "射门", shotsOn: "射正", shotsOff: "射偏",
    xg: "期望进球", dangerAtk: "危险进攻", corners: "角球",
    possession: "控球率", passAcc: "传球成功率",
    fouls: "犯规", yellows: "黄牌", reds: "红牌",
    pressure: "压力指数", momentum: "攻防势头",
    volatility: "波动率", riskConcede: "失球风险",
    goalWindow: "预期进球窗口", confInterval: "置信区间",
    switchLang: "EN", live: "直播", half: "半场",
    home: "主队", away: "客队", delta: "Δ",
    free: "免费", pro: "专业", elite: "精英",
    disclaimer: "仅为数据可视化 — 不含比赛画面 — 量化模型输出",
    xgDelta: "xG差值", riskIndex: "风险指数",
    halfTimeSummary: "半场汇总",
    attacks: "进攻次数", saves: "扑救", offsides: "越位",
    probTrend: "胜平负概率", pressureTrend: "压力指数", xgTrend: "累计xG",
    min: "分钟",
  },
};

// ── Data simulation engine ──────────────────────────────────────
function simData(minute, prev) {
  const m = Math.max(1, minute);
  const cl = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const diff = prev.score[0] - prev.score[1];
  const tf = m / 90;

  // Goals
  let s = [...prev.score];
  if (minute > prev.minute) {
    if (Math.random() < 0.014) s[0]++;
    if (Math.random() < 0.011) s[1]++;
  }

  // Probability
  const pH = cl(50 + diff * 13 + diff * tf * 14 + (Math.random() - 0.5) * 2.5, 4, 94);
  const pA = cl(24 - diff * 11 + (Math.random() - 0.5) * 2, 3, 65);
  const pD = cl(100 - pH - pA, 3, 55);
  const total = pH + pD + pA;

  // xG
  const hxg = cl(prev.hxg + Math.random() * 0.065, 0, 5);
  const axg = cl(prev.axg + Math.random() * 0.050, 0, 5);

  // Stats
  const stats = {
    shots: [Math.floor(m / 7) + 2 + Math.floor(Math.random() * 2), Math.floor(m / 9) + 1 + Math.floor(Math.random() * 2)],
    shotsOn: [Math.floor(m / 14) + 1, Math.floor(m / 18) + 1],
    shotsOff: [0, 0],
    xg: [Math.round(hxg * 100) / 100, Math.round(axg * 100) / 100],
    dangerAtk: [Math.floor(m * 0.55) + Math.floor(Math.random() * 3), Math.floor(m * 0.40) + Math.floor(Math.random() * 3)],
    corners: [Math.floor(m / 14) + Math.floor(Math.random() * 2), Math.floor(m / 18) + Math.floor(Math.random() * 2)],
    possession: [cl(Math.round(53 + diff * 3 + (Math.random() - 0.5) * 6), 35, 70), 0],
    passAcc: [cl(Math.round(85 + (Math.random() - 0.5) * 8), 72, 95), cl(Math.round(81 + (Math.random() - 0.5) * 8), 70, 93)],
    fouls: [Math.floor(m / 10) + 1, Math.floor(m / 9) + 1],
    yellows: [Math.floor(m / 35), Math.floor(m / 30)],
    reds: [0, 0],
    attacks: [Math.floor(m * 1.1), Math.floor(m * 0.85)],
    saves: [Math.floor(m / 20), Math.floor(m / 15) + 1],
    offsides: [Math.floor(m / 25), Math.floor(m / 22)],
  };
  stats.shotsOff = [stats.shots[0] - stats.shotsOn[0], stats.shots[1] - stats.shotsOn[1]];
  stats.possession[1] = 100 - stats.possession[0];

  // Quant indicators
  const quant = {
    pressure: cl(Math.round(50 + diff * 12 + (Math.random() - 0.5) * 10), 10, 98),
    momentum: cl(Math.round(diff * 14 + (Math.random() - 0.5) * 8), -50, 50),
    volatility: cl(Math.round((0.5 + tf * 0.4 + Math.random() * 0.3) * 100) / 100, 0.1, 1.5),
    riskConcede: cl(Math.round(25 + (1 - tf) * 15 + Math.random() * 15), 5, 85),
    goalWindow: m < 80 ? `${Math.floor(Math.random() * 8 + 3)}-${Math.floor(Math.random() * 5 + 10)}` : "LOW",
    confInterval: cl(Math.round(88 + Math.random() * 10), 80, 99),
    modelVariance: cl(Math.round((0.08 + Math.random() * 0.12) * 1000) / 1000, 0.01, 0.3),
    xgDelta: Math.round((hxg - axg) * 100) / 100,
  };

  return {
    minute: m,
    score: s,
    half: m <= 45 ? "H1" : "H2",
    probability: { home: Math.round(pH / total * 10000) / 100, draw: Math.round(pD / total * 10000) / 100, away: Math.round(pA / total * 10000) / 100 },
    confidence: cl(Math.round(75 + Math.random() * 18), 60, 98),
    stats, quant, hxg, axg,
  };
}

// ── Micro sparkline (no glow, thin, minimal) ────────────────────
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

// ── Delta arrow display ─────────────────────────────────────────
function Delta({ value, suffix = "%" }) {
  if (value === 0 || value === undefined) return <span style={{ color: C.textMuted, fontFamily: "mono", fontSize: 11 }}>— 0.00{suffix}</span>;
  const up = value > 0;
  return (
    <span style={{ color: up ? C.up : C.down, fontFamily: "mono", fontSize: 11, fontWeight: 600 }}>
      {up ? "▲" : "▼"} {up ? "+" : ""}{typeof value === "number" ? value.toFixed(2) : value}{suffix}
    </span>
  );
}

// ── Probability row (stock-ticker style) ────────────────────────
function ProbRow({ label, value, delta, tag }) {
  return (
    <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", padding: "6px 0", borderBottom: `1px solid ${C.border}` }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 2, fontWeight: 600, minWidth: 80 }}>{label}</span>
        {tag && <span style={{ fontSize: 8, padding: "1px 5px", borderRadius: 2, background: C.accent + "18", color: C.accent, letterSpacing: 1, fontWeight: 700 }}>{tag}</span>}
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 16 }}>
        <span style={{ fontSize: 22, fontWeight: 800, color: C.text, fontFamily: "mono", letterSpacing: -0.5 }}>{value.toFixed(2)}<span style={{ fontSize: 13, color: C.textDim }}>%</span></span>
        <span style={{ minWidth: 90, textAlign: "right" }}><Delta value={delta} /></span>
      </div>
    </div>
  );
}

// ── Stat table row ──────────────────────────────────────────────
function StatRow({ label, hv, av, suffix = "", highlight }) {
  return (
    <div style={{ display: "flex", alignItems: "center", padding: "4px 0", borderBottom: `1px solid ${C.border}` }}>
      <span style={{ flex: 1, textAlign: "right", fontFamily: "mono", fontSize: 12, fontWeight: 600, color: highlight === "home" ? C.up : C.text }}>{hv}{suffix}</span>
      <span style={{ width: 130, textAlign: "center", fontSize: 10, color: C.textDim, letterSpacing: 1.5, padding: "0 8px" }}>{label}</span>
      <span style={{ flex: 1, textAlign: "left", fontFamily: "mono", fontSize: 12, fontWeight: 600, color: highlight === "away" ? C.up : C.text }}>{av}{suffix}</span>
    </div>
  );
}

// ── Quant indicator row ─────────────────────────────────────────
function QuantRow({ label, value, unit = "", tier = "free" }) {
  const tierColor = tier === "pro" ? C.accentBlue : tier === "elite" ? C.accent : C.text;
  const locked = false; // for demo all unlocked
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "5px 0", borderBottom: `1px solid ${C.border}` }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1.5, fontWeight: 600 }}>{label}</span>
        {tier !== "free" && <span style={{ fontSize: 7, padding: "1px 4px", borderRadius: 2, border: `1px solid ${tierColor}30`, color: tierColor, letterSpacing: 1, fontWeight: 700 }}>{tier.toUpperCase()}</span>}
      </div>
      <span style={{ fontFamily: "mono", fontSize: 13, fontWeight: 700, color: tierColor, letterSpacing: -0.3 }}>
        {locked ? "—" : <>{value}<span style={{ fontSize: 10, color: C.textDim, marginLeft: 2 }}>{unit}</span></>}
      </span>
    </div>
  );
}

// ── Section header ──────────────────────────────────────────────
function SectionHead({ label, right }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8, paddingBottom: 6, borderBottom: `1px solid ${C.borderLight}` }}>
      <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: 3, color: C.accent, fontFamily: "mono" }}>{label}</span>
      {right && <span style={{ fontSize: 9, color: C.textMuted, fontFamily: "mono" }}>{right}</span>}
    </div>
  );
}

// ── Trend tab ───────────────────────────────────────────────────
function TrendTab({ tabs, active, onChange }) {
  return (
    <div style={{ display: "flex", gap: 0, marginBottom: 8 }}>
      {tabs.map(tb => (
        <button key={tb.k} onClick={() => onChange(tb.k)} style={{
          padding: "4px 10px", fontSize: 9, fontWeight: 600, letterSpacing: 1.5,
          border: "none", borderBottom: active === tb.k ? `2px solid ${C.accent}` : `2px solid transparent`,
          background: "transparent", color: active === tb.k ? C.accent : C.textMuted,
          cursor: "pointer", fontFamily: "mono", transition: "all 0.2s",
        }}>{tb.l}</button>
      ))}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════
// MAIN TERMINAL
// ════════════════════════════════════════════════════════════════
export default function QuantTerminal() {
  const [lang, setLang] = useState("en");
  const t = LANG[lang];
  const [minute, setMinute] = useState(0);
  const [isLive, setIsLive] = useState(true);
  const [data, setData] = useState(null);
  const prevRef = useRef({ minute: 0, score: [0, 0], hxg: 0, axg: 0 });
  const [history, setHistory] = useState({ h: [], d: [], a: [], pressure: [], hxg: [], axg: [] });
  const [prevProb, setPrevProb] = useState({ home: 50, draw: 25, away: 25 });
  const [trendTab, setTrendTab] = useState("prob");

  useEffect(() => {
    const iv = setInterval(() => {
      if (!isLive) return;
      setMinute(prev => {
        const next = Math.min(prev + 1, 90);
        const d = simData(next, prevRef.current);
        prevRef.current = { minute: next, score: d.score, hxg: d.hxg, axg: d.axg };

        setPrevProb(p => data ? { home: data.probability.home, draw: data.probability.draw, away: data.probability.away } : p);
        setData(d);
        setHistory(h => ({
          h: [...h.h.slice(-89), d.probability.home],
          d: [...h.d.slice(-89), d.probability.draw],
          a: [...h.a.slice(-89), d.probability.away],
          pressure: [...h.pressure.slice(-89), d.quant.pressure],
          hxg: [...h.hxg.slice(-89), d.stats.xg[0]],
          axg: [...h.axg.slice(-89), d.stats.xg[1]],
        }));
        return next;
      });
    }, 2000);
    return () => clearInterval(iv);
  }, [isLive, data]);

  if (!data) return (
    <div style={{ ...sty.root, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <style>{globalCSS}</style>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontFamily: "mono", fontSize: 14, color: C.accent, letterSpacing: 4, marginBottom: 8 }}>AI FOOTBALL QUANT TERMINAL</div>
        <div style={{ fontFamily: "mono", fontSize: 10, color: C.textMuted }}>Initializing model...</div>
      </div>
    </div>
  );

  const hn = lang === "zh" ? MATCH.home.fullCN : MATCH.home.full;
  const an = lang === "zh" ? MATCH.away.fullCN : MATCH.away.full;
  const dH = data.probability.home - prevProb.home;
  const dD = data.probability.draw - prevProb.draw;
  const dA = data.probability.away - prevProb.away;

  return (
    <div style={sty.root}>
      <style>{globalCSS}</style>

      {/* ═══ LAYER 1: STATE BAR ═══ */}
      <div style={sty.stateBar}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontSize: 9, color: C.accent, letterSpacing: 3, fontWeight: 700 }}>QUANT TERMINAL</span>
          <span style={sty.divider}>|</span>
          <span style={{ color: C.textDim, fontSize: 10 }}>{MATCH.league}</span>
          <span style={sty.divider}>|</span>
          <span style={{ color: C.textDim, fontSize: 10 }}>{MATCH.round}</span>
          <span style={sty.divider}>|</span>
          <span style={{ color: C.text, fontSize: 10, fontWeight: 600 }}>{MATCH.home.name}</span>
          <span style={{ color: C.accent, fontSize: 14, fontWeight: 800, fontFamily: "mono", letterSpacing: 1 }}>{data.score[0]} — {data.score[1]}</span>
          <span style={{ color: C.text, fontSize: 10, fontWeight: 600 }}>{MATCH.away.name}</span>
          <span style={sty.divider}>|</span>
          <span style={{ fontFamily: "mono", fontSize: 12, fontWeight: 700, color: C.up }}>{data.minute}'</span>
          <span style={{ color: C.textMuted, fontSize: 9 }}>{data.half}</span>
          <span style={sty.divider}>|</span>
          <span style={{ fontSize: 9, color: C.textMuted }}>RC: {data.stats.reds[0]}-{data.stats.reds[1]}</span>
          <span style={{ fontSize: 9, color: C.textMuted }}>YC: {data.stats.yellows[0]}-{data.stats.yellows[1]}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 6, height: 6, borderRadius: "50%", background: isLive ? C.up : C.down, animation: isLive ? "blink 2s infinite" : "none" }} />
          <span style={{ fontSize: 8, color: isLive ? C.up : C.down, letterSpacing: 2, fontWeight: 700 }}>{t.live}</span>
          <button onClick={() => setLang(l => l === "en" ? "zh" : "en")} style={sty.langBtn}>{t.switchLang}</button>
          <button onClick={() => setIsLive(l => !l)} style={{ ...sty.langBtn, color: isLive ? C.down : C.up, borderColor: isLive ? C.down + "40" : C.up + "40" }}>
            {isLive ? "PAUSE" : "RESUME"}
          </button>
        </div>
      </div>

      {/* ═══ DISCLAIMER ═══ */}
      <div style={{ textAlign: "center", padding: "3px 0", fontSize: 8, letterSpacing: 2, color: C.textMuted, background: C.down + "08", borderBottom: `1px solid ${C.border}` }}>
        {t.disclaimer}
      </div>

      {/* ═══ MAIN CONTENT GRID ═══ */}
      <div style={sty.mainGrid}>

        {/* ▌ LEFT PANEL — Probability + Quant */}
        <div style={sty.panel}>

          {/* LAYER 2: CORE PROBABILITY */}
          <div style={sty.section}>
            <SectionHead label={t.probLabel} right={`MODEL v3.2 | CONF ${data.confidence}%`} />

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1, marginBottom: 12 }}>
              {/* Home panel */}
              <div style={sty.probPanel}>
                <div style={{ fontSize: 8, color: C.textMuted, letterSpacing: 2, marginBottom: 4 }}>{t.home} — {MATCH.home.name}</div>
                <div style={{ fontSize: 32, fontWeight: 800, fontFamily: "mono", color: C.text, lineHeight: 1, letterSpacing: -1 }}>
                  {data.probability.home.toFixed(2)}<span style={{ fontSize: 14, color: C.textDim }}>%</span>
                </div>
                <div style={{ marginTop: 4 }}><Delta value={dH} /></div>
              </div>
              {/* Away panel */}
              <div style={sty.probPanel}>
                <div style={{ fontSize: 8, color: C.textMuted, letterSpacing: 2, marginBottom: 4 }}>{t.away} — {MATCH.away.name}</div>
                <div style={{ fontSize: 32, fontWeight: 800, fontFamily: "mono", color: C.text, lineHeight: 1, letterSpacing: -1 }}>
                  {data.probability.away.toFixed(2)}<span style={{ fontSize: 14, color: C.textDim }}>%</span>
                </div>
                <div style={{ marginTop: 4 }}><Delta value={dA} /></div>
              </div>
            </div>

            {/* Draw row */}
            <ProbRow label={t.draw} value={data.probability.draw} delta={dD} />

            {/* Model meta */}
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, padding: "6px 0", borderTop: `1px solid ${C.border}` }}>
              <span style={{ fontSize: 9, color: C.textMuted }}>{t.modelConf}: <span style={{ color: C.accent, fontWeight: 700, fontFamily: "mono" }}>{data.confidence}%</span></span>
              <span style={{ fontSize: 9, color: C.textMuted }}>{t.modelVar}: <span style={{ color: C.text, fontFamily: "mono" }}>{data.quant.modelVariance}</span></span>
            </div>
          </div>

          {/* LAYER 5: QUANT INDICATORS */}
          <div style={sty.section}>
            <SectionHead label={t.quantLabel} right="REFRESH 10s" />
            <QuantRow label={t.pressure} value={data.quant.pressure} tier="pro" />
            <QuantRow label={t.momentum} value={data.quant.momentum > 0 ? `+${data.quant.momentum}` : data.quant.momentum} tier="pro" />
            <QuantRow label={t.volatility} value={data.quant.volatility} tier="pro" />
            <QuantRow label={t.riskConcede} value={data.quant.riskConcede} unit="%" tier="pro" />
            <QuantRow label={t.xgDelta} value={data.quant.xgDelta > 0 ? `+${data.quant.xgDelta}` : data.quant.xgDelta} tier="pro" />
            <QuantRow label={t.goalWindow} value={data.quant.goalWindow} unit={t.min} tier="elite" />
            <QuantRow label={t.confInterval} value={data.quant.confInterval} unit="%" tier="elite" />
            <QuantRow label={t.modelVar} value={data.quant.modelVariance} tier="elite" />
          </div>
        </div>

        {/* ▌ CENTER PANEL — Trend */}
        <div style={sty.panel}>
          <div style={sty.section}>
            <SectionHead label={t.trendLabel} right={`0' → ${data.minute}'`} />

            <TrendTab tabs={[
              { k: "prob", l: t.probTrend },
              { k: "pressure", l: t.pressureTrend },
              { k: "xg", l: t.xgTrend },
            ]} active={trendTab} onChange={setTrendTab} />

            {trendTab === "prob" && (
              <div>
                <div style={{ marginBottom: 2 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                    <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1 }}>{t.homeWin}</span>
                    <span style={{ fontSize: 10, fontFamily: "mono", color: C.text, fontWeight: 600 }}>{data.probability.home.toFixed(2)}%</span>
                  </div>
                  <MiniSpark data={history.h} color={C.text} h={48} />
                </div>
                <div style={{ marginBottom: 2, marginTop: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                    <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1 }}>{t.draw}</span>
                    <span style={{ fontSize: 10, fontFamily: "mono", color: C.textDim, fontWeight: 600 }}>{data.probability.draw.toFixed(2)}%</span>
                  </div>
                  <MiniSpark data={history.d} color={C.textDim} h={32} />
                </div>
                <div style={{ marginTop: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                    <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1 }}>{t.awayWin}</span>
                    <span style={{ fontSize: 10, fontFamily: "mono", color: C.accentBlue, fontWeight: 600 }}>{data.probability.away.toFixed(2)}%</span>
                  </div>
                  <MiniSpark data={history.a} color={C.accentBlue} h={32} />
                </div>
              </div>
            )}

            {trendTab === "pressure" && (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1 }}>{t.pressure}</span>
                  <span style={{ fontSize: 12, fontFamily: "mono", color: data.quant.pressure > 60 ? C.up : C.text, fontWeight: 700 }}>{data.quant.pressure}</span>
                </div>
                <MiniSpark data={history.pressure} color={C.accent} h={100} />
                <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
                  <span style={{ fontSize: 8, color: C.textMuted }}>← {t.away} {t.pressure.toLowerCase()}</span>
                  <span style={{ fontSize: 8, color: C.textMuted }}>{t.home} {t.pressure.toLowerCase()} →</span>
                </div>
              </div>
            )}

            {trendTab === "xg" && (
              <div>
                <div style={{ marginBottom: 2 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                    <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1 }}>{MATCH.home.name} {t.xg}</span>
                    <span style={{ fontSize: 11, fontFamily: "mono", color: C.text, fontWeight: 700 }}>{data.stats.xg[0]}</span>
                  </div>
                  <MiniSpark data={history.hxg} color={C.text} h={50} />
                </div>
                <div style={{ marginTop: 10 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                    <span style={{ fontSize: 8, color: C.textMuted, letterSpacing: 1 }}>{MATCH.away.name} {t.xg}</span>
                    <span style={{ fontSize: 11, fontFamily: "mono", color: C.accentBlue, fontWeight: 700 }}>{data.stats.xg[1]}</span>
                  </div>
                  <MiniSpark data={history.axg} color={C.accentBlue} h={50} />
                </div>
                <div style={{ marginTop: 8, padding: "6px 0", borderTop: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 9, color: C.textMuted }}>{t.xgDelta}</span>
                  <span style={{ fontFamily: "mono", fontSize: 12, fontWeight: 700, color: data.quant.xgDelta > 0 ? C.up : data.quant.xgDelta < 0 ? C.down : C.text }}>
                    {data.quant.xgDelta > 0 ? "+" : ""}{data.quant.xgDelta}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ▌ RIGHT PANEL — Stats */}
        <div style={sty.panel}>
          <div style={sty.section}>
            <SectionHead label={t.statsLabel} right="REFRESH 5s" />

            {/* Header row */}
            <div style={{ display: "flex", alignItems: "center", padding: "4px 0", borderBottom: `2px solid ${C.borderLight}` }}>
              <span style={{ flex: 1, textAlign: "right", fontSize: 9, color: C.accent, fontWeight: 700, letterSpacing: 1 }}>{MATCH.home.name}</span>
              <span style={{ width: 130, textAlign: "center", fontSize: 9, color: C.textMuted, letterSpacing: 1 }}>STAT</span>
              <span style={{ flex: 1, textAlign: "left", fontSize: 9, color: C.accentBlue, fontWeight: 700, letterSpacing: 1 }}>{MATCH.away.name}</span>
            </div>

            {/* Attack stats */}
            <div style={{ marginTop: 4 }}>
              <StatRow label={t.shots} hv={data.stats.shots[0]} av={data.stats.shots[1]} highlight={data.stats.shots[0] > data.stats.shots[1] ? "home" : data.stats.shots[1] > data.stats.shots[0] ? "away" : undefined} />
              <StatRow label={t.shotsOn} hv={data.stats.shotsOn[0]} av={data.stats.shotsOn[1]} />
              <StatRow label={t.shotsOff} hv={data.stats.shotsOff[0]} av={data.stats.shotsOff[1]} />
              <StatRow label={t.xg} hv={data.stats.xg[0]} av={data.stats.xg[1]} highlight={data.stats.xg[0] > data.stats.xg[1] ? "home" : "away"} />
              <StatRow label={t.dangerAtk} hv={data.stats.dangerAtk[0]} av={data.stats.dangerAtk[1]} />
              <StatRow label={t.corners} hv={data.stats.corners[0]} av={data.stats.corners[1]} />
              <StatRow label={t.attacks} hv={data.stats.attacks[0]} av={data.stats.attacks[1]} />
            </div>

            {/* Control stats */}
            <div style={{ marginTop: 8, paddingTop: 4, borderTop: `1px solid ${C.borderLight}` }}>
              <StatRow label={t.possession} hv={data.stats.possession[0]} av={data.stats.possession[1]} suffix="%" />
              <StatRow label={t.passAcc} hv={data.stats.passAcc[0]} av={data.stats.passAcc[1]} suffix="%" />
            </div>

            {/* Discipline */}
            <div style={{ marginTop: 8, paddingTop: 4, borderTop: `1px solid ${C.borderLight}` }}>
              <StatRow label={t.fouls} hv={data.stats.fouls[0]} av={data.stats.fouls[1]} />
              <StatRow label={t.yellows} hv={data.stats.yellows[0]} av={data.stats.yellows[1]} />
              <StatRow label={t.reds} hv={data.stats.reds[0]} av={data.stats.reds[1]} />
              <StatRow label={t.offsides} hv={data.stats.offsides[0]} av={data.stats.offsides[1]} />
              <StatRow label={t.saves} hv={data.stats.saves[0]} av={data.stats.saves[1]} />
            </div>
          </div>
        </div>
      </div>

      {/* ═══ FOOTER ═══ */}
      <div style={sty.footer}>
        <span style={{ color: C.textMuted }}>AI FOOTBALL QUANT TERMINAL © 2026</span>
        <span style={{ color: C.textMuted }}>REFRESH 2s | MODEL XGB+POISSON | {data.minute}'/90'</span>
      </div>
    </div>
  );
}

// ── Global CSS ──────────────────────────────────────────────────
const globalCSS = `
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap');
  @keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}
  *{box-sizing:border-box}
  ::-webkit-scrollbar{width:3px}
  ::-webkit-scrollbar-track{background:transparent}
  ::-webkit-scrollbar-thumb{background:${C.border};border-radius:1px}
`;

// ── Styles ──────────────────────────────────────────────────────
const sty = {
  root: {
    minHeight: "100vh",
    background: C.bg,
    fontFamily: "'IBM Plex Mono', 'Noto Sans SC', monospace",
    color: C.text,
    position: "relative",
  },
  stateBar: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "6px 16px",
    background: C.bgCard,
    borderBottom: `1px solid ${C.border}`,
    fontFamily: "mono", fontSize: 10,
  },
  divider: { color: C.textMuted, margin: "0 2px", fontSize: 10 },
  langBtn: {
    padding: "3px 8px", fontSize: 8, fontWeight: 600, letterSpacing: 1,
    border: `1px solid ${C.border}`, borderRadius: 2,
    background: "transparent", color: C.textDim,
    cursor: "pointer", fontFamily: "mono",
  },
  mainGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1.1fr 0.9fr",
    gap: 1,
    background: C.border,
    height: "calc(100vh - 72px)",
    overflow: "hidden",
  },
  panel: {
    background: C.bg,
    overflow: "auto",
    padding: 0,
  },
  section: {
    padding: "12px 14px",
    borderBottom: `1px solid ${C.border}`,
  },
  probPanel: {
    padding: "12px 14px",
    background: C.bgCard,
    border: `1px solid ${C.border}`,
  },
  footer: {
    display: "flex", justifyContent: "space-between",
    padding: "4px 16px", fontSize: 8, letterSpacing: 1,
    fontFamily: "mono",
    borderTop: `1px solid ${C.border}`,
    background: C.bgCard,
  },
};
