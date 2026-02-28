/**
 * VotePanel -- v1.0
 * Live audience voting panel
 * Displays vote distribution for match outcome (1/X/2)
 * Model vs Audience comparison
 * Bloomberg terminal style
 *
 * Props:
 *   votes      — { home: 45, draw: 20, away: 35, total: 100 }
 *   modelProbs — { home: 0.42, draw: 0.28, away: 0.30 }
 *   lang       — "en" | "zh"
 *   L          — i18n dict
 */

const C = {
  bg: "#0E1117", bgCard: "#131720",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  up: "#00C853", down: "#FF3D00",
  accent: "#F4C430", accentBlue: "#00C8FF",
};

const BAR_COLORS = {
  home: "#4A9EFF",
  draw: "#888888",
  away: "#FF6B35",
};

function VoteBar({ label, pct, color }) {
  return (
    <div style={{ marginBottom: 6 }}>
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: 3,
      }}>
        <span style={{ fontSize: 9, fontWeight: 700, color, letterSpacing: 1.5 }}>
          {label}
        </span>
        <span style={{ fontSize: 10, fontWeight: 700, color: C.text, fontFamily: "'IBM Plex Mono', monospace" }}>
          {pct.toFixed(1)}%
        </span>
      </div>
      <div style={{
        width: "100%", height: 6, background: C.border, borderRadius: 2, overflow: "hidden",
      }}>
        <div style={{
          width: `${pct}%`, height: "100%", background: color,
          borderRadius: 2, transition: "width 0.5s ease",
        }} />
      </div>
    </div>
  );
}

function ComparisonRow({ label, modelVal, audienceVal, divergent, vsLabel = "vs", divergeLabel = "DIVERGE" }) {
  return (
    <div style={{
      display: "flex", justifyContent: "space-between", alignItems: "center",
      padding: "3px 0", borderBottom: `1px solid ${C.border}`,
    }}>
      <span style={{ fontSize: 9, color: C.textDim, fontWeight: 600, letterSpacing: 1, minWidth: 50 }}>
        {label}
      </span>
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <span style={{
          fontSize: 10, fontWeight: 700, color: C.accentBlue,
          fontFamily: "'IBM Plex Mono', monospace", minWidth: 48, textAlign: "right",
        }}>
          {(modelVal * 100).toFixed(1)}%
        </span>
        <span style={{ fontSize: 8, color: C.textMuted }}>{vsLabel}</span>
        <span style={{
          fontSize: 10, fontWeight: 700, color: C.text,
          fontFamily: "'IBM Plex Mono', monospace", minWidth: 48, textAlign: "right",
        }}>
          {audienceVal.toFixed(1)}%
        </span>
        {divergent && (
          <span style={{
            fontSize: 7, fontWeight: 700, letterSpacing: 1,
            padding: "1px 5px", borderRadius: 2,
            background: C.accent + "20", color: C.accent,
            border: `1px solid ${C.accent}30`,
          }}>
            {divergeLabel}
          </span>
        )}
      </div>
    </div>
  );
}

export default function VotePanel({ votes = {}, modelProbs = {}, lang = "en", L = {} }) {
  const headerLabel = L.audiencePoll || "AUDIENCE POLL";
  const compLabel = L.modelVsAudience || "MODEL vs AUDIENCE";
  const emptyLabel = L.votingOpens || "Voting opens at kickoff";

  const total = votes.total || (votes.home || 0) + (votes.draw || 0) + (votes.away || 0);
  const pctHome = total > 0 ? ((votes.home || 0) / total) * 100 : 0;
  const pctDraw = total > 0 ? ((votes.draw || 0) / total) * 100 : 0;
  const pctAway = total > 0 ? ((votes.away || 0) / total) * 100 : 0;

  const mp = {
    home: modelProbs.home || 0,
    draw: modelProbs.draw || 0,
    away: modelProbs.away || 0,
  };

  // Divergence check (>10%)
  const divHome = Math.abs(mp.home * 100 - pctHome) > 10;
  const divDraw = Math.abs(mp.draw * 100 - pctDraw) > 10;
  const divAway = Math.abs(mp.away * 100 - pctAway) > 10;

  return (
    <div style={{
      padding: "10px 14px",
      background: C.bgCard,
      border: `1px solid ${C.border}`,
      fontFamily: "'IBM Plex Mono', monospace",
    }}>
      {/* Header */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        fontSize: 9, fontWeight: 700, letterSpacing: 3, color: C.accent,
        marginBottom: 8, paddingBottom: 5, borderBottom: `1px solid ${C.borderLight}`,
      }}>
        <span>{headerLabel}</span>
        <span style={{
          fontSize: 8, fontWeight: 600, letterSpacing: 1, color: C.textDim,
          background: C.border, padding: "2px 8px", borderRadius: 2,
        }}>
          {total}
        </span>
      </div>

      {/* Empty state */}
      {total === 0 && (
        <div style={{
          padding: "20px 0", textAlign: "center",
          fontSize: 10, color: C.textMuted, letterSpacing: 2, fontWeight: 600,
        }}>
          {emptyLabel}
        </div>
      )}

      {/* Vote bars */}
      {total > 0 && (
        <>
          <VoteBar label={L.voteHome || "1  HOME"} pct={pctHome} color={BAR_COLORS.home} />
          <VoteBar label={L.voteDraw || "X  DRAW"} pct={pctDraw} color={BAR_COLORS.draw} />
          <VoteBar label={L.voteAway || "2  AWAY"} pct={pctAway} color={BAR_COLORS.away} />

          {/* Comparison section */}
          <div style={{
            marginTop: 10, paddingTop: 8, borderTop: `1px solid ${C.borderLight}`,
          }}>
            <div style={{
              fontSize: 8, fontWeight: 700, letterSpacing: 2, color: C.textDim, marginBottom: 6,
              display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <span>{compLabel}</span>
              <div style={{ display: "flex", gap: 12 }}>
                <span style={{ fontSize: 7, color: C.accentBlue, letterSpacing: 1 }}>{L.modelLabel || "MODEL"}</span>
                <span style={{ fontSize: 7, color: C.textMuted, letterSpacing: 1 }}>{L.audienceLabel || "AUDIENCE"}</span>
              </div>
            </div>
            <ComparisonRow label={L.home || "HOME"} modelVal={mp.home} audienceVal={pctHome} divergent={divHome} vsLabel={L.vs || "vs"} divergeLabel={L.diverged || "DIVERGE"} />
            <ComparisonRow label={L.draw || "DRAW"} modelVal={mp.draw} audienceVal={pctDraw} divergent={divDraw} vsLabel={L.vs || "vs"} divergeLabel={L.diverged || "DIVERGE"} />
            <ComparisonRow label={L.away || "AWAY"} modelVal={mp.away} audienceVal={pctAway} divergent={divAway} vsLabel={L.vs || "vs"} divergeLabel={L.diverged || "DIVERGE"} />
          </div>

          {/* Footer */}
          <div style={{
            marginTop: 8, paddingTop: 4, textAlign: "center",
            fontSize: 8, color: C.textMuted, letterSpacing: 1,
          }}>
            {(L.basedOnVotes || "Based on {n} votes").replace("{n}", total)}
          </div>
        </>
      )}
    </div>
  );
}
