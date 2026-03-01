/**
 * LineupPanel — Formation + player list from Nami lineup data
 * Shows starting XI with formation, shirt numbers, ratings
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
    lineupTitle: "LINEUP",
    formation: "FORMATION",
    home: "HOME",
    away: "AWAY",
    starting: "STARTING XI",
    bench: "BENCH",
    confirmed: "CONFIRMED",
    unconfirmed: "PREDICTED",
  },
  zh: {
    lineupTitle: "阵容",
    formation: "阵型",
    home: "主队",
    away: "客队",
    starting: "首发",
    bench: "替补",
    confirmed: "已确认",
    unconfirmed: "预测",
  },
};

const POS_COLOR = { GK: "#F4C430", DF: "#00C853", MF: "#00C8FF", FW: "#FF3D00" };

const INC_TYPE = {
  1: "⚽", 3: "🟨", 4: "🟥", 5: "↔", 7: "⚽", 8: "⚽", 11: "🟨🟨",
};

function PlayerRow({ player }) {
  const posColor = POS_COLOR[player.position] || C.textDim;
  const rating = parseFloat(player.rating);
  const ratingColor = rating >= 7.5 ? C.up : rating >= 6.5 ? C.accent : rating > 0 ? C.textDim : C.textMuted;
  const incIcons = player.incidents?.map(i => INC_TYPE[i.type]).filter(Boolean).join("") || "";

  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 4, padding: "2px 0",
      borderBottom: `1px solid ${C.border}`, fontSize: 10, fontFamily: "mono",
    }}>
      <span style={{
        width: 18, textAlign: "center", fontSize: 8, fontWeight: 700,
        color: "#0E1117", background: posColor, borderRadius: 2, padding: "0 2px",
        lineHeight: "14px",
      }}>{player.position || "?"}</span>
      <span style={{ width: 16, textAlign: "center", color: C.textDim, fontSize: 9 }}>
        {player.shirtNumber || ""}
      </span>
      <span style={{
        flex: 1, color: C.text, fontSize: 9, overflow: "hidden",
        textOverflow: "ellipsis", whiteSpace: "nowrap",
      }}>
        {player.name}
        {player.isCaptain && <span style={{ color: C.accent, fontSize: 7, marginLeft: 2 }}>©</span>}
      </span>
      {incIcons && <span style={{ fontSize: 8, marginRight: 2 }}>{incIcons}</span>}
      {rating > 0 && (
        <span style={{ fontWeight: 700, color: ratingColor, fontSize: 9, minWidth: 22, textAlign: "right" }}>
          {player.rating}
        </span>
      )}
    </div>
  );
}

function TeamLineup({ players, formation, teamLabel, teamColor }) {
  const starters = players.filter(p => p.first === 1);
  const bench = players.filter(p => p.first !== 1);

  // Sort starters by position order: GK → DF → MF → FW
  const posOrder = { GK: 0, DF: 1, MF: 2, FW: 3 };
  starters.sort((a, b) => (posOrder[a.position] ?? 9) - (posOrder[b.position] ?? 9));

  return (
    <div style={{ flex: 1, minWidth: 0 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontSize: 9, color: teamColor, fontWeight: 700, letterSpacing: 1 }}>{teamLabel}</span>
        {formation && <span style={{ fontSize: 9, color: C.textDim, fontFamily: "mono" }}>{formation}</span>}
      </div>
      {starters.map(p => (
        <PlayerRow key={p.id || p.shirtNumber} player={p} />
      ))}
      {bench.length > 0 && (
        <div style={{ marginTop: 4, paddingTop: 2, borderTop: `1px solid ${C.borderLight}` }}>
          <div style={{ fontSize: 7, color: C.textMuted, letterSpacing: 1.5, marginBottom: 2 }}>BENCH</div>
          {bench.slice(0, 7).map(p => (
            <PlayerRow key={p.id || p.shirtNumber} player={p} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function LineupPanel({ data, homeName, awayName, lang = "en" }) {
  const L = LANG[lang] || LANG.en;

  if (!data) return null;
  if (!data.home?.length && !data.away?.length) return null;

  return (
    <div style={{ padding: "12px 14px", borderBottom: `1px solid ${C.border}` }}>
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: 8, paddingBottom: 6, borderBottom: `1px solid ${C.borderLight}`,
      }}>
        <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: 3, color: C.accent, fontFamily: "mono" }}>
          {L.lineupTitle}
        </span>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {data.confirmed != null && (
            <span style={{
              fontSize: 7, padding: "1px 5px", borderRadius: 2,
              background: data.confirmed ? C.up + "20" : C.accent + "18",
              color: data.confirmed ? C.up : C.accent,
              letterSpacing: 1, fontWeight: 700,
            }}>
              {data.confirmed ? L.confirmed : L.unconfirmed}
            </span>
          )}
          <span style={{ fontSize: 8, color: C.textMuted, fontFamily: "mono" }}>
            {data.homeFormation && data.awayFormation
              ? `${data.homeFormation} vs ${data.awayFormation}`
              : L.formation}
          </span>
        </div>
      </div>

      <div className="qt-lineup-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        {data.home?.length > 0 && (
          <TeamLineup
            players={data.home}
            formation={data.homeFormation}
            teamLabel={homeName || L.home}
            teamColor={C.accent}
          />
        )}
        {data.away?.length > 0 && (
          <TeamLineup
            players={data.away}
            formation={data.awayFormation}
            teamLabel={awayName || L.away}
            teamColor={C.accentBlue}
          />
        )}
      </div>
    </div>
  );
}
