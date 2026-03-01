/**
 * TrendPanel — Per-minute momentum chart from Nami trend data
 * Shows momentum timeline (positive=home, negative=away) + incident markers
 */

const C = {
  bg: "#0E1117", bgCard: "#131720",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  up: "#00C853", down: "#FF3D00",
  accent: "#F4C430", accentBlue: "#00C8FF",
};

const LANG = {
  en: {
    trendTitle: "MATCH MOMENTUM",
    home: "HOME",
    away: "AWAY",
    goal: "GOAL",
    corner: "COR",
    yellow: "YEL",
    red: "RED",
  },
  zh: {
    trendTitle: "比赛动量",
    home: "主队",
    away: "客队",
    goal: "进球",
    corner: "角球",
    yellow: "黄牌",
    red: "红牌",
  },
};

const INC_ICON = { 1: "⚽", 2: "📐", 3: "🟨", 4: "🟥", 5: "↔", 7: "⚽", 8: "⚽" };

function MomentumChart({ data, incidents, h = 60 }) {
  if (!data || data.length < 2) return null;
  const W = 300;
  const midY = h / 2;
  const maxMinute = Math.max(...data.map(d => d.minute), 1);
  const maxAbs = Math.max(...data.map(d => Math.abs(d.value)), 1);

  // Build bar chart (momentum per minute)
  const barW = W / Math.max(data.length, 1);

  return (
    <div style={{ position: "relative" }}>
      <svg viewBox={`0 0 ${W} ${h}`} style={{ width: "100%", height: h, display: "block" }} preserveAspectRatio="none">
        {/* Center line */}
        <line x1="0" y1={midY} x2={W} y2={midY} stroke={C.borderLight} strokeWidth="0.5" />

        {/* Momentum bars */}
        {data.map((d, i) => {
          const x = (d.minute / maxMinute) * W - barW / 2;
          const barH = Math.abs(d.value) / maxAbs * (midY - 2);
          const isHome = d.value >= 0;
          const y = isHome ? midY - barH : midY;
          return (
            <rect
              key={i}
              x={x}
              y={y}
              width={Math.max(barW - 0.5, 1)}
              height={barH || 0.5}
              fill={isHome ? C.accent : C.accentBlue}
              opacity={0.7}
            />
          );
        })}

        {/* Incident markers */}
        {incidents?.map((inc, i) => {
          const x = (inc.time / maxMinute) * W;
          const isGoal = [1, 7, 8].includes(inc.type);
          if (!isGoal) return null;
          return (
            <circle
              key={`inc${i}`}
              cx={x}
              cy={inc.position === 1 ? 4 : h - 4}
              r={3}
              fill={inc.position === 1 ? C.accent : C.accentBlue}
              stroke={C.bg}
              strokeWidth={0.5}
            />
          );
        })}
      </svg>

      {/* Incident timeline below chart */}
      {incidents?.length > 0 && (
        <div style={{
          display: "flex", gap: 6, flexWrap: "wrap", marginTop: 4,
          fontSize: 8, fontFamily: "mono", color: C.textDim,
        }}>
          {incidents.map((inc, i) => {
            const icon = INC_ICON[inc.type];
            if (!icon) return null;
            return (
              <span key={i} style={{
                color: inc.position === 1 ? C.accent : C.accentBlue,
              }}>
                {inc.time}' {icon}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function TrendPanel({ data, lang = "en" }) {
  const L = LANG[lang] || LANG.en;

  if (!data) return null;
  if (!data.momentum?.length) return null;

  return (
    <div style={{ padding: "12px 14px", borderBottom: `1px solid ${C.border}` }}>
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: 8, paddingBottom: 6, borderBottom: `1px solid ${C.borderLight}`,
      }}>
        <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: 3, color: C.accent, fontFamily: "mono" }}>
          {L.trendTitle}
        </span>
        <div style={{ display: "flex", gap: 12, fontSize: 8, fontFamily: "mono" }}>
          <span style={{ color: C.accent }}>▲ {L.home}</span>
          <span style={{ color: C.accentBlue }}>▼ {L.away}</span>
        </div>
      </div>

      <MomentumChart
        data={data.momentum}
        incidents={data.incidents}
        h={60}
      />
    </div>
  );
}
