/**
 * MarketEdge — v1.1
 * Shows market implied probability + AI vs Market edge
 * Pro tier feature — core monetization
 */

import { LANG } from "../utils/i18n";

const C = {
  border: "#1E2530",
  textDim: "#6B7280",
  textMuted: "#3D4654",
  accent: "#F4C430",
  accentBlue: "#00C8FF",
  up: "#00C853",
  down: "#FF3D00",
  text: "#E5E5E5",
};

export default function MarketEdge({ market, tier = "pro", lang = "en" }) {
  const L = LANG[lang];
  if (!market) {
    return (
      <div style={{ padding: "6px 0", fontSize: 9, color: C.textMuted, fontFamily: "mono" }}>
        {L?.marketUnavailable}
      </div>
    );
  }

  const { implied, edge, odds } = market;

  return (
    <div>
      {/* Odds row */}
      <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: `1px solid ${C.border}` }}>
        <span style={{ fontSize: 9, color: C.textMuted, letterSpacing: 1.5 }}>{L?.odds}</span>
        <div style={{ display: "flex", gap: 16, fontFamily: "mono", fontSize: 11 }}>
          <span style={{ color: C.text }}>{odds.home}</span>
          <span style={{ color: C.textDim }}>{odds.draw}</span>
          <span style={{ color: C.text }}>{odds.away}</span>
        </div>
      </div>

      {/* Market implied */}
      <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: `1px solid ${C.border}` }}>
        <span style={{ fontSize: 9, color: C.textMuted, letterSpacing: 1.5 }}>{L?.mktImplied}</span>
        <div style={{ display: "flex", gap: 16, fontFamily: "mono", fontSize: 11 }}>
          <span style={{ color: C.textDim }}>{implied.home}%</span>
          <span style={{ color: C.textDim }}>{implied.draw}%</span>
          <span style={{ color: C.textDim }}>{implied.away}%</span>
        </div>
      </div>

      {/* Edge (AI - Market) */}
      <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: `1px solid ${C.border}` }}>
        <span style={{ fontSize: 9, color: C.accentBlue, letterSpacing: 1.5, fontWeight: 600 }}>{L?.edgeAiMkt}</span>
        <div style={{ display: "flex", gap: 16, fontFamily: "mono", fontSize: 11, fontWeight: 600 }}>
          {["home", "draw", "away"].map((k) => {
            const v = edge[k];
            const color = v > 1 ? C.up : v < -1 ? C.down : C.textDim;
            return (
              <span key={k} style={{ color }}>
                {v > 0 ? "+" : ""}{v}%
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}
