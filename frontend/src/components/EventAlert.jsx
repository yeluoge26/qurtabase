/**
 * EventAlert — v1.0
 * Full-screen overlay for major match events:
 *   - Goal flash (gold, 2.5s)
 *   - Red card flash (red, 2s)
 *   - Probability swing (cyan, 3s)
 *
 * Also renders a thin top-border flash bar (3px) that pulses
 * on goals (gold, 3 pulses / 2s) and red cards (red, 2 pulses / 1.5s).
 *
 * pointer-events: none — never blocks user interaction.
 */

import { useMemo } from "react";
import { useEventAlert } from "../hooks/useEventAlert";

// ── Theme constants (Bloomberg-terminal palette) ─────────────
const THEME = {
  goal: {
    bg: "rgba(244, 196, 48, 0.06)",
    color: "#F4C430",
    glow: "0 0 60px rgba(244, 196, 48, 0.25), 0 0 120px rgba(244, 196, 48, 0.10)",
    border: "rgba(244, 196, 48, 0.35)",
    barColor: "#F4C430",
  },
  red_card: {
    bg: "rgba(255, 61, 0, 0.06)",
    color: "#FF3D00",
    glow: "0 0 60px rgba(255, 61, 0, 0.20), 0 0 120px rgba(255, 61, 0, 0.08)",
    border: "rgba(255, 61, 0, 0.35)",
    barColor: "#FF3D00",
  },
  prob_swing: {
    bg: "rgba(0, 200, 255, 0.06)",
    color: "#00C8FF",
    glow: "0 0 60px rgba(0, 200, 255, 0.20), 0 0 120px rgba(0, 200, 255, 0.08)",
    border: "rgba(0, 200, 255, 0.30)",
    barColor: "#00C8FF",
  },
};

// ── Keyframe CSS (injected once) ─────────────────────────────
const KEYFRAMES = `
@keyframes eventAlertFadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@keyframes eventAlertFadeOut {
  from { opacity: 1; }
  to   { opacity: 0; }
}
@keyframes goalBarPulse {
  0%, 100% { opacity: 0; }
  10%      { opacity: 1; }
  40%      { opacity: 0; }
  43%      { opacity: 1; }
  70%      { opacity: 0; }
  73%      { opacity: 1; }
  90%      { opacity: 0; }
}
@keyframes redBarPulse {
  0%, 100% { opacity: 0; }
  15%      { opacity: 1; }
  50%      { opacity: 0; }
  65%      { opacity: 1; }
  90%      { opacity: 0; }
}
`;

// ── Overlay content renderers ────────────────────────────────
function GoalContent({ data, t }) {
  const teamLabel = (data.team || "").toUpperCase() === "AWAY" ? (t.away || "AWAY") : (t.home || "HOME");
  const score = data.score || [0, 0];
  return (
    <div style={styles.contentWrap}>
      <div style={{ fontSize: 48, marginBottom: 8 }}>&#9917;</div>
      <div style={{ fontSize: 36, fontWeight: 800, letterSpacing: 6, marginBottom: 12, color: THEME.goal.color }}>
        {t.goalAlert || "GOAL"}
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: 2, marginBottom: 6, color: "#E5E5E5" }}>
        {teamLabel} {score[0]} &mdash; {score[1]}
      </div>
      <div style={{ fontSize: 16, fontWeight: 600, color: "#6B7280", letterSpacing: 3 }}>
        {data.minute}&apos;
      </div>
      <div style={styles.recalc}>
        {t.modelRecalc || "MODEL RECALCULATING..."}
      </div>
    </div>
  );
}

function RedCardContent({ data, t }) {
  const teamLabel = (data.team || "").toUpperCase() === "AWAY" ? (t.away || "AWAY") : (t.home || "HOME");
  return (
    <div style={styles.contentWrap}>
      <div style={{ fontSize: 48, marginBottom: 8 }}>&#x1F7E5;</div>
      <div style={{ fontSize: 32, fontWeight: 800, letterSpacing: 6, marginBottom: 12, color: THEME.red_card.color }}>
        {t.redCardAlert || "RED CARD"}
      </div>
      <div style={{ fontSize: 18, fontWeight: 600, color: "#E5E5E5", letterSpacing: 2 }}>
        {teamLabel} &mdash; {data.minute}&apos;
      </div>
    </div>
  );
}

function ProbSwingContent({ data, t }) {
  const delta = data.delta || {};
  const homeAbs = Math.abs(delta.home || 0);
  const awayAbs = Math.abs(delta.away || 0);

  // Show the larger swing (or both if both qualify)
  const lines = [];
  if (homeAbs > 15) {
    const sign = delta.home > 0 ? "+" : "";
    // We don't have previous values directly, so show the delta magnitude
    lines.push({ label: "HOME", delta: delta.home, sign, abs: homeAbs });
  }
  if (awayAbs > 15) {
    const sign = delta.away > 0 ? "+" : "";
    lines.push({ label: "AWAY", delta: delta.away, sign, abs: awayAbs });
  }

  return (
    <div style={styles.contentWrap}>
      <div style={{ fontSize: 40, marginBottom: 8 }}>&#9888;</div>
      <div style={{ fontSize: 28, fontWeight: 800, letterSpacing: 5, marginBottom: 16, color: THEME.prob_swing.color }}>
        {t.probSwing || "PROBABILITY SWING"}
      </div>
      {lines.map((l, i) => (
        <div key={i} style={{ fontSize: 20, fontWeight: 700, color: "#E5E5E5", letterSpacing: 2, marginBottom: 4 }}>
          {l.label}: {l.sign}{l.delta.toFixed(1)}%
        </div>
      ))}
    </div>
  );
}

// ── Main component ───────────────────────────────────────────
/**
 * @param {Object} props
 * @param {Array}  props.events  – mapped events array
 * @param {Array}  props.score   – [home, away] goals
 * @param {Object} props.delta   – { home, draw, away } probability deltas
 * @param {number} props.minute  – current match minute
 * @param {Object} props.t       – i18n translation object
 */
export default function EventAlert({ events, score, delta, minute, t = {} }) {
  const { alert } = useEventAlert(events, delta, score, minute);

  // Memoize keyframe style tag
  const styleTag = useMemo(() => <style>{KEYFRAMES}</style>, []);

  if (!alert || !alert.visible) {
    return styleTag; // keep keyframes mounted
  }

  const theme = THEME[alert.type] || THEME.goal;

  // ── Top flash bar (goal = 3 pulses / 2s, red = 2 pulses / 1.5s) ──
  const showBar = alert.type === "goal" || alert.type === "red_card";
  const barAnimation = alert.type === "goal"
    ? "goalBarPulse 2s ease-in-out forwards"
    : "redBarPulse 1.5s ease-in-out forwards";

  return (
    <>
      {styleTag}

      {/* ── Top flash bar ── */}
      {showBar && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          height: 3,
          background: theme.barColor,
          zIndex: 1001,
          pointerEvents: "none",
          animation: barAnimation,
        }} />
      )}

      {/* ── Full-screen overlay ── */}
      <div style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        pointerEvents: "none",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: theme.bg,
        boxShadow: theme.glow,
        border: `1px solid ${theme.border}`,
        fontFamily: "'IBM Plex Mono', 'Noto Sans SC', monospace",
        animation: `eventAlertFadeIn 200ms ease-out forwards`,
      }}>
        {/* Overlay content */}
        {alert.type === "goal" && <GoalContent data={alert.data} t={t} />}
        {alert.type === "red_card" && <RedCardContent data={alert.data} t={t} />}
        {alert.type === "prob_swing" && <ProbSwingContent data={alert.data} t={t} />}
      </div>
    </>
  );
}

// ── Inline styles ────────────────────────────────────────────
const styles = {
  contentWrap: {
    textAlign: "center",
    userSelect: "none",
  },
  recalc: {
    marginTop: 24,
    fontSize: 12,
    fontWeight: 600,
    letterSpacing: 4,
    color: "#6B7280",
    opacity: 0.8,
  },
};
