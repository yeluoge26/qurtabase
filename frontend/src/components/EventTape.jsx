/**
 * EventTape — v1.1
 * Shows last N match events (goals, cards, subs, VAR)
 * Bloomberg-style event log, newest first
 */

const C = {
  border: "#1E2530",
  textDim: "#6B7280",
  textMuted: "#3D4654",
  accent: "#F4C430",
  up: "#00C853",
  down: "#FF3D00",
  text: "#E5E5E5",
};

const TYPE_STYLE = {
  GOAL: { icon: "⚽", color: C.accent, bg: C.accent + "15" },
  YELLOW: { icon: "▪", color: "#FFD600", bg: "#FFD60010" },
  RED: { icon: "▪", color: C.down, bg: C.down + "10" },
  SUB: { icon: "↔", color: C.textDim, bg: "transparent" },
  VAR: { icon: "◉", color: "#9C27B0", bg: "#9C27B010" },
  PENALTY: { icon: "P", color: C.accent, bg: C.accent + "15" },
};

export default function EventTape({ events = [], maxShow = 5 }) {
  if (!events.length) {
    return (
      <div style={{ padding: "6px 0", fontSize: 9, color: C.textMuted, fontFamily: "mono", letterSpacing: 1 }}>
        NO EVENTS YET
      </div>
    );
  }

  return (
    <div>
      {events.slice(0, maxShow).map((ev, i) => {
        const s = TYPE_STYLE[ev.type] || TYPE_STYLE.SUB;
        return (
          <div
            key={ev.id || i}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "4px 6px",
              marginBottom: 1,
              background: s.bg,
              borderLeft: `2px solid ${s.color}`,
              fontFamily: "mono",
              fontSize: 10,
            }}
          >
            <span style={{ color: C.textMuted, minWidth: 24, textAlign: "right" }}>{ev.minute}'</span>
            <span style={{ color: s.color, fontWeight: 700, minWidth: 14 }}>{s.icon}</span>
            <span style={{ color: C.text, fontWeight: ev.type === "GOAL" ? 700 : 400 }}>{ev.text}</span>
          </div>
        );
      })}
    </div>
  );
}
