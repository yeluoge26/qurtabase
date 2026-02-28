/**
 * ModelCycleTimer -- v1.0
 * Shows model evaluation cycle countdown and current state
 * States: monitoring | evaluating | recalculating
 * Bloomberg terminal style
 */
import { useState, useEffect, useRef } from "react";
import { LANG } from "../utils/i18n";

const C = {
  bg: "#0E1117", bgCard: "#131720",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  up: "#00C853", down: "#FF3D00",
  accent: "#F4C430", accentBright: "#FFD700",
};

const FONT = "'IBM Plex Mono', monospace";

// ── Volatility color mapping ────────────────────────────────
function getVolColor(vol) {
  switch (vol) {
    case "Low": return C.up;
    case "Medium": return C.accent;
    case "High": return C.down;
    default: return C.textMuted;
  }
}

// ── State dot color ─────────────────────────────────────────
function getStateDotColor(state) {
  switch (state) {
    case "monitoring": return C.up;
    case "evaluating": return C.accent;
    case "recalculating": return C.down;
    default: return C.textMuted;
  }
}

// ── State label ─────────────────────────────────────────────
function getStateLabel(state, L) {
  switch (state) {
    case "monitoring": return L?.monitoringState;
    case "evaluating": return L?.evaluatingState;
    case "recalculating": return L?.recalcState;
    default: return L?.monitoringState;
  }
}

// ── Countdown hook ──────────────────────────────────────────
function useCountdown(nextEvalSec) {
  const [sec, setSec] = useState(nextEvalSec || 0);
  const ref = useRef(null);

  useEffect(() => {
    setSec(nextEvalSec || 0);
  }, [nextEvalSec]);

  useEffect(() => {
    if (sec <= 0) {
      clearInterval(ref.current);
      return;
    }
    ref.current = setInterval(() => {
      setSec(s => {
        if (s <= 1) { clearInterval(ref.current); return 0; }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(ref.current);
  }, [sec > 0]);

  const mm = String(Math.floor(sec / 60)).padStart(2, "0");
  const ss = String(sec % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

// ── Animated lambda for recalculating ───────────────────────
function useAnimatedLambda(L) {
  const [frame, setFrame] = useState(0);
  const ref = useRef(null);

  useEffect(() => {
    ref.current = setInterval(() => {
      setFrame(f => (f + 1) % 4);
    }, 400);
    return () => clearInterval(ref.current);
  }, []);

  const dots = ".".repeat(frame);
  return `${L?.recalcLambda}${dots}`;
}

// ════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════
export default function ModelCycleTimer({
  state = "monitoring",
  nextEvalSec = 0,
  volatility = "Low",
  lang = "en",
}) {
  const L = LANG[lang];
  const countdown = useCountdown(nextEvalSec);
  const recalcLabel = useAnimatedLambda(L);
  const dotColor = getStateDotColor(state);
  const volColor = getVolColor(volatility);
  const isRecalc = state === "recalculating";

  return (
    <div style={{
      width: "100%",
      height: 50,
      background: C.bgCard,
      border: `1px solid ${C.border}`,
      padding: "6px 12px",
      fontFamily: FONT,
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      gap: 4,
    }}>
      <style>{cycleCSS}</style>

      {/* Row 1: Header + Countdown */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}>
        <span style={{
          fontSize: 9,
          fontWeight: 700,
          letterSpacing: 2.5,
          color: C.accent,
          textTransform: "uppercase",
        }}>
          {L?.modelCycle}
        </span>
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
        }}>
          <span style={{
            fontSize: 9,
            color: C.textMuted,
            letterSpacing: 1,
          }}>
            {L?.nextEval + ":"}
          </span>
          <span style={{
            fontSize: 11,
            fontWeight: 700,
            color: C.text,
            letterSpacing: 0.5,
          }}>
            {countdown}
          </span>
        </div>
      </div>

      {/* Row 2: State + Volatility OR Recalculating animation */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}>
        {isRecalc ? (
          /* Recalculating state: animated label */
          <span style={{
            fontSize: 10,
            fontWeight: 600,
            color: C.down,
            letterSpacing: 1.5,
            animation: "cycleRecalcPulse 1s ease-in-out infinite",
          }}>
            {recalcLabel}
          </span>
        ) : (
          /* Normal states: State + Volatility */
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}>
            {/* State indicator */}
            <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{
                fontSize: 9,
                color: C.textMuted,
                letterSpacing: 1,
              }}>
                {L?.stateLabel2}
              </span>
              <div style={{
                width: 5,
                height: 5,
                borderRadius: "50%",
                background: dotColor,
                animation: "cycleDotPulse 2s ease-in-out infinite",
                flexShrink: 0,
              }} />
              <span style={{
                fontSize: 10,
                fontWeight: 600,
                color: C.text,
                letterSpacing: 0.5,
              }}>
                {getStateLabel(state, L)}
              </span>
            </div>

            {/* Divider */}
            <span style={{ color: C.textMuted, fontSize: 10 }}>|</span>

            {/* Volatility */}
            <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{
                fontSize: 9,
                color: C.textMuted,
                letterSpacing: 1,
              }}>
                {L?.volLabel}
              </span>
              <span style={{
                fontSize: 10,
                fontWeight: 700,
                color: volColor,
                letterSpacing: 0.5,
              }}>
                {volatility}
              </span>
            </div>
          </div>
        )}

        {/* Recalculating state also shows volatility on right side */}
        {isRecalc && (
          <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <span style={{ fontSize: 9, color: C.textMuted, letterSpacing: 1 }}>{L?.volLabel}</span>
            <span style={{ fontSize: 10, fontWeight: 700, color: volColor }}>{volatility}</span>
          </div>
        )}
      </div>
    </div>
  );
}

const cycleCSS = `
  @keyframes cycleDotPulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
  }
  @keyframes cycleRecalcPulse {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
  }
`;
