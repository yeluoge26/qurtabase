/**
 * MatchGrid -- v1.0
 * Multi-match compact grid terminal
 * Shows 3-4 matches in a responsive grid layout
 * Each match is a compact card with key metrics
 * Bloomberg terminal style
 *
 * Props:
 *   matches  — array of { matchId, home, away, score, minute, status, lambdaLive, edge, signal }
 *   lang     — "en" | "zh"
 *   L        — i18n dict (uses L.multiMatch, L.noActiveMatches)
 *   onClick  — callback(matchId) when a card is clicked
 */

const C = {
  bg: "#0E1117", bgCard: "#131720", bgRow: "#161B25",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  up: "#00C853", down: "#FF3D00",
  accent: "#F4C430", accentBlue: "#00C8FF",
};

function StatusDot({ status }) {
  const isLive = status === "live" || status === "LIVE";
  return (
    <div style={{
      width: 6, height: 6, borderRadius: "50%",
      background: isLive ? C.up : C.textMuted,
      boxShadow: isLive ? `0 0 4px ${C.up}` : "none",
      animation: isLive ? "sysPulse 2s ease-in-out infinite" : "none",
    }} />
  );
}

function SignalIndicator({ signal, signalLabel = "SIGNAL" }) {
  if (!signal || signal === "NO SIGNAL") {
    return <span style={{ fontSize: 8, color: C.textMuted, fontWeight: 600 }}>--</span>;
  }
  const color = signal === "CONFIRMED" ? C.up : signal === "READY" ? C.accent : C.accentBlue;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 3 }}>
      <span style={{ fontSize: 8, fontWeight: 700, letterSpacing: 1, color }}>{signalLabel}</span>
      <div style={{
        width: 5, height: 5, borderRadius: "50%", background: color,
        boxShadow: `0 0 4px ${color}`,
      }} />
    </div>
  );
}

function MatchCard({ match, onClick, L = {} }) {
  const isLive = match.status === "live" || match.status === "LIVE";
  const edgeVal = match.edge || 0;
  const edgeColor = edgeVal > 0 ? C.up : edgeVal < 0 ? C.down : C.textDim;
  const scoreParts = (match.score || "0-0").split("-");

  return (
    <div
      onClick={() => onClick && onClick(match.matchId)}
      style={{
        background: C.bgCard,
        border: `1px solid ${C.border}`,
        borderRadius: 2,
        padding: "10px 12px",
        fontFamily: "'IBM Plex Mono', monospace",
        cursor: onClick ? "pointer" : "default",
        minWidth: 240,
        maxWidth: 320,
        transition: "border-color 0.2s, box-shadow 0.2s",
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = C.accent;
        e.currentTarget.style.boxShadow = `0 0 8px ${C.accent}25`;
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = C.border;
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      {/* Top: status dot + minute */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: 8, paddingBottom: 4, borderBottom: `1px solid ${C.border}`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <StatusDot status={match.status} />
          <span style={{ fontSize: 8, color: isLive ? C.up : C.textMuted, fontWeight: 600, letterSpacing: 1 }}>
            {isLive ? (L.liveStatus || "LIVE") : (L.upcoming || "UPCOMING")}
          </span>
        </div>
        {isLive && (
          <span style={{
            fontSize: 9, fontWeight: 700, color: C.up, fontFamily: "'IBM Plex Mono', monospace",
            background: C.up + "15", padding: "1px 6px", borderRadius: 2,
          }}>
            {match.minute}'
          </span>
        )}
      </div>

      {/* Center: HOME 2 - 1 AWAY */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
        margin: "6px 0",
      }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: C.text, letterSpacing: 0.5 }}>
          {match.home}
        </span>
        <span style={{
          fontSize: 14, fontWeight: 800, color: C.text, fontFamily: "'IBM Plex Mono', monospace",
          letterSpacing: 1,
        }}>
          {scoreParts[0]} - {scoreParts[1]}
        </span>
        <span style={{ fontSize: 11, fontWeight: 600, color: C.text, letterSpacing: 0.5 }}>
          {match.away}
        </span>
      </div>

      {/* Bottom row: lambda | EDGE | SIGNAL */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginTop: 8, paddingTop: 6, borderTop: `1px solid ${C.border}`,
        fontSize: 9, color: C.textDim, letterSpacing: 0.5,
      }}>
        <span>
          {"\u03BB"} <span style={{ color: C.accent, fontWeight: 700 }}>
            {match.lambdaLive != null ? match.lambdaLive.toFixed(2) : "--"}
          </span>
        </span>
        <span style={{ color: C.textMuted }}>|</span>
        <span>
          {L.edgeLabel || "EDGE"} <span style={{ color: edgeColor, fontWeight: 700 }}>
            {edgeVal > 0 ? "+" : ""}{edgeVal.toFixed(1)}%
          </span>
        </span>
        <span style={{ color: C.textMuted }}>|</span>
        <SignalIndicator signal={match.signal} signalLabel={L.signalLabel || "SIGNAL"} />
      </div>
    </div>
  );
}

export default function MatchGrid({ matches = [], lang = "en", L = {}, onClick }) {
  const headerLabel = L.multiMatchTerminal || "MULTI-MATCH TERMINAL";
  const emptyLabel = L.noActiveMatches || "No active matches";

  return (
    <div style={{
      padding: "12px 14px",
      background: C.bg,
      fontFamily: "'IBM Plex Mono', monospace",
    }}>
      {/* Header */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        fontSize: 9, fontWeight: 700, letterSpacing: 3, color: C.accent,
        marginBottom: 10, paddingBottom: 6, borderBottom: `1px solid ${C.borderLight}`,
      }}>
        <span>{headerLabel}</span>
        <span style={{
          fontSize: 8, fontWeight: 600, letterSpacing: 1, color: C.textDim,
          background: C.border, padding: "2px 8px", borderRadius: 2,
        }}>
          {matches.length}
        </span>
      </div>

      {/* Empty state */}
      {matches.length === 0 && (
        <div style={{
          padding: "32px 0", textAlign: "center",
          fontSize: 10, color: C.textMuted, letterSpacing: 2, fontWeight: 600,
        }}>
          {emptyLabel}
        </div>
      )}

      {/* Grid */}
      {matches.length > 0 && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
          gap: 8,
        }}>
          {matches.map(m => (
            <MatchCard key={m.matchId} match={m} onClick={onClick} L={L} />
          ))}
        </div>
      )}
    </div>
  );
}
