/**
 * BroadcastBar -- v1.0
 * Thin bar at the bottom of the terminal showing broadcast status
 * Ticker-style last broadcast message with stage badge and cooldown timer
 * Bloomberg terminal style
 */
import { useState, useEffect, useRef } from "react";

const C = {
  bg: "#0E1117", bgCard: "#131720", bgBar: "#12151A",
  border: "#1E2530", borderLight: "#1E2330",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  accent: "#F4C430", accentBright: "#FFD700",
};

const FONT = "'IBM Plex Mono', monospace";

const STAGE_COLORS = {
  GOAL: "#FFD700",
  SIGNAL: "#00FF88",
  SIGNAL_CONFIRM: "#00FF88",
  SIGNAL_PENDING: "#00FF88",
  LATE_GAME: "#FF6B35",
  FINAL_WINDOW: "#FF6B35",
  TEMPO_BUILD: "#00C8FF",
  POST_MATCH: "#4A9EFF",
};

function getStageColor(stage) {
  if (!stage) return "#888";
  const upper = stage.toUpperCase();
  return STAGE_COLORS[upper] || "#888";
}

function getStageLabel(stage, L) {
  if (!stage) return "";
  const upper = stage.toUpperCase();
  if (upper === "GOAL") return L?.stageGoal || "GOAL";
  if (upper === "SIGNAL" || upper === "SIGNAL_CONFIRM" || upper === "SIGNAL_PENDING") return L?.stageSignal || "SIGNAL";
  if (upper === "LATE_GAME" || upper === "FINAL_WINDOW") return L?.stageLatGame || "LATE GAME";
  if (upper === "POST_MATCH") return L?.stagePostMatch || "POST-MATCH";
  if (upper === "TEMPO_BUILD") return L?.stageTempo || "TEMPO";
  return stage.replace(/_/g, " ");
}

// ── Cooldown countdown hook ─────────────────────────────────
function useCooldown(cooldownSec) {
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

  return sec;
}

// ════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════
export default function BroadcastBar({
  broadcast = null,
  cooldownSec = 0,
  lang = "en",
  L = {},
}) {
  const remaining = useCooldown(cooldownSec);
  const [tickerOffset, setTickerOffset] = useState(0);
  const tickerRef = useRef(null);
  const textRef = useRef(null);

  // Simple ticker scroll for long text
  useEffect(() => {
    setTickerOffset(0);
    if (!broadcast?.text) return;

    // Only animate if text is likely long
    const textLen = broadcast.text.length;
    if (textLen < 60) return;

    let offset = 0;
    tickerRef.current = setInterval(() => {
      offset += 1;
      if (offset > textLen * 5.5 + 200) offset = 0;
      setTickerOffset(offset);
    }, 50);

    return () => clearInterval(tickerRef.current);
  }, [broadcast?.text]);

  // Don't render if no broadcast data at all
  if (!broadcast && cooldownSec <= 0) return null;

  const stageColor = getStageColor(broadcast?.stage);
  const stageLabel = getStageLabel(broadcast?.stage, L);
  const broadcastText = broadcast?.text || "";
  const cooldownLabel = L?.broadcastCooldown || "NEXT";

  return (
    <div style={{
      width: "100%",
      height: 24,
      background: C.bgBar,
      borderTop: `1px solid ${C.borderLight}`,
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 12px",
      fontFamily: FONT,
      fontSize: 11,
      overflow: "hidden",
      flexShrink: 0,
    }}>
      <style>{broadcastCSS}</style>

      {/* Left side: stage badge + broadcast text */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        flex: 1,
        overflow: "hidden",
        minWidth: 0,
      }}>
        {/* Stage badge */}
        {stageLabel && (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: 4,
            flexShrink: 0,
          }}>
            <div style={{
              width: 5,
              height: 5,
              borderRadius: "50%",
              background: stageColor,
              boxShadow: `0 0 4px ${stageColor}60`,
              flexShrink: 0,
            }} />
            <span style={{
              fontSize: 9,
              fontWeight: 700,
              letterSpacing: 1.5,
              color: stageColor,
              whiteSpace: "nowrap",
            }}>
              {stageLabel}
            </span>
          </div>
        )}

        {/* Separator */}
        {stageLabel && broadcastText && (
          <span style={{ color: C.textMuted, fontSize: 10, flexShrink: 0 }}>|</span>
        )}

        {/* Broadcast text (ticker) */}
        {broadcastText && (
          <div style={{
            flex: 1,
            overflow: "hidden",
            position: "relative",
            height: 14,
          }}>
            <span
              ref={textRef}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                whiteSpace: "nowrap",
                fontSize: 10,
                color: C.textDim,
                letterSpacing: 0.3,
                transform: broadcastText.length >= 60
                  ? `translateX(-${tickerOffset}px)`
                  : "none",
                transition: "none",
              }}
            >
              {broadcastText}
            </span>
          </div>
        )}
      </div>

      {/* Right side: cooldown timer */}
      {remaining > 0 && (
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 4,
          flexShrink: 0,
          marginLeft: 8,
        }}>
          <span style={{
            fontSize: 9,
            color: C.textMuted,
            letterSpacing: 1,
            fontWeight: 600,
          }}>
            {cooldownLabel}:
          </span>
          <span style={{
            fontSize: 10,
            color: C.accent,
            fontWeight: 700,
            fontFamily: FONT,
            letterSpacing: 0.5,
          }}>
            {remaining}s
          </span>
        </div>
      )}
    </div>
  );
}

const broadcastCSS = `
  @keyframes broadcastFadeIn {
    0% { opacity: 0; }
    100% { opacity: 1; }
  }
`;
