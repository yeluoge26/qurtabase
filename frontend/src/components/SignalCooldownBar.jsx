/**
 * SignalCooldownBar -- v1.0
 * Displays signal cooldown state progression and countdown timer
 * States: MONITORING | EDGE BUILDING | SIGNAL READY | COOLDOWN
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

// ── Animated dots for EDGE BUILDING state ───────────────────
function useAnimatedDots() {
  const [dots, setDots] = useState("");
  const ref = useRef(null);

  useEffect(() => {
    ref.current = setInterval(() => {
      setDots(d => (d.length >= 3 ? "" : d + "."));
    }, 500);
    return () => clearInterval(ref.current);
  }, []);

  return dots;
}

// ── Cooldown countdown ──────────────────────────────────────
function useCooldownTimer(cooldownSec) {
  const [sec, setSec] = useState(cooldownSec || 0);
  const ref = useRef(null);

  useEffect(() => {
    setSec(cooldownSec || 0);
  }, [cooldownSec]);

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
  return { display: `${mm}:${ss}`, sec };
}

// ════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════
export default function SignalCooldownBar({
  signalState = "monitoring",
  cooldownSec = 0,
  cooldownTotal = 180,
  lang = "en",
}) {
  const L = LANG[lang];
  const dots = useAnimatedDots();
  const timer = useCooldownTimer(cooldownSec);
  const progressPct = cooldownTotal > 0
    ? Math.max(0, Math.min(100, (timer.sec / cooldownTotal) * 100))
    : 0;

  // Determine display content based on state
  let label = "";
  let labelColor = C.textMuted;
  let showPulse = false;
  let showGlow = false;
  let showProgress = false;

  switch (signalState) {
    case "monitoring":
      label = L?.monitoring;
      labelColor = C.textMuted;
      showPulse = true;
      break;
    case "building":
      label = `${L?.edgeBuilding}${dots}`;
      labelColor = C.accent;
      break;
    case "ready":
      label = L?.signalReady;
      labelColor = C.accentBright;
      showGlow = true;
      break;
    case "cooldown":
      label = `${L?.cooldownLabel} ${timer.display}`;
      labelColor = C.textDim;
      showProgress = true;
      break;
    default:
      label = L?.monitoring;
      labelColor = C.textMuted;
      showPulse = true;
  }

  return (
    <div style={{
      position: "relative",
      width: "100%",
      height: 30,
      background: C.bgCard,
      border: `1px solid ${C.border}`,
      display: "flex",
      alignItems: "center",
      overflow: "hidden",
      fontFamily: FONT,
    }}>
      <style>{cooldownCSS}</style>

      {/* Background progress bar for cooldown state */}
      {showProgress && (
        <div style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: `${progressPct}%`,
          height: "100%",
          background: "rgba(244, 196, 48, 0.15)",
          transition: "width 1s linear",
          pointerEvents: "none",
        }} />
      )}

      {/* Content */}
      <div style={{
        position: "relative",
        zIndex: 1,
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "0 12px",
        width: "100%",
      }}>
        {/* Status indicator dot */}
        {showPulse && (
          <div style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: C.textMuted,
            animation: "signalPulse 2.5s ease-in-out infinite",
            flexShrink: 0,
          }} />
        )}

        {signalState === "building" && (
          <div style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: C.accent,
            animation: "signalPulse 1.2s ease-in-out infinite",
            flexShrink: 0,
          }} />
        )}

        {showGlow && (
          <div style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: C.accentBright,
            boxShadow: `0 0 6px ${C.accentBright}, 0 0 12px ${C.accent}80`,
            animation: "signalGlow 1.5s ease-in-out infinite",
            flexShrink: 0,
          }} />
        )}

        {showProgress && (
          <div style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: C.textDim,
            flexShrink: 0,
          }} />
        )}

        {/* Label */}
        <span style={{
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: 2.5,
          color: labelColor,
          textTransform: "uppercase",
          textShadow: showGlow ? `0 0 8px ${C.accent}80` : "none",
          whiteSpace: "nowrap",
        }}>
          {label}
        </span>

        {/* Right side: state badge */}
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{
            fontSize: 8,
            fontWeight: 600,
            letterSpacing: 1.5,
            color: C.textMuted,
            textTransform: "uppercase",
          }}>
            {L?.signalCooldown}
          </span>
        </div>
      </div>
    </div>
  );
}

const cooldownCSS = `
  @keyframes signalPulse {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 1; }
  }
  @keyframes signalGlow {
    0%, 100% { box-shadow: 0 0 4px #FFD700, 0 0 8px #F4C43060; }
    50% { box-shadow: 0 0 8px #FFD700, 0 0 16px #F4C43090; }
  }
`;
