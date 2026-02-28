/**
 * InfoTicker — v1.0
 * Unified scrolling information bar combining:
 *  - AI broadcast messages (highest priority)
 *  - Report notifications (HT/FT ready)
 *  - Current time display
 *  - Disclaimer text (low priority loop)
 * Replaces: BroadcastBar + ReportBanner + Disclaimer line
 */
import { useState, useEffect, useRef } from "react";

const C = {
  bg: "#12151A",
  border: "#1E2530",
  text: "#E5E5E5",
  textDim: "#6B7280",
  textMuted: "#3D4654",
  accent: "#F4C430",
  accentBright: "#FFD700",
  up: "#00C853",
};

const FONT = "'IBM Plex Mono', 'Noto Sans SC', monospace";

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
  if (!stage) return null;
  return STAGE_COLORS[stage.toUpperCase()] || "#888";
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

export default function InfoTicker({
  broadcast = null,
  report = null,
  lang = "en",
  L = {},
}) {
  const [now, setNow] = useState(new Date());
  const [tickerOffset, setTickerOffset] = useState(0);
  const tickerRef = useRef(null);

  // Clock tick every second
  useEffect(() => {
    const iv = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(iv);
  }, []);

  // Determine display text and priority
  let displayText = "";
  let textColor = C.textMuted;
  let stageColor = null;
  let stageLabel = "";

  // Priority 1: AI broadcast
  if (broadcast?.text) {
    displayText = broadcast.text;
    stageColor = getStageColor(broadcast.stage);
    stageLabel = getStageLabel(broadcast.stage, L);
    textColor = stageColor || C.textDim;
  }
  // Priority 2: Report ready
  else if (report?.fullTimeReady) {
    displayText = `${L?.ftReportReady || "FT REPORT READY"} ${L?.pressToExport || "— PRESS [R] TO EXPORT"}`;
    textColor = C.accentBright;
    stageLabel = "REPORT";
    stageColor = C.accent;
  } else if (report?.halfTimeReady) {
    displayText = `${L?.htReportReady || "HT REPORT READY"} ${L?.pressToExport || "— PRESS [R] TO EXPORT"}`;
    textColor = C.accentBright;
    stageLabel = "REPORT";
    stageColor = C.accent;
  }
  // Priority 3: Disclaimer scroll
  else {
    displayText = L?.disclaimer
      ? `${L.disclaimer} — ${L.disclaimerShort}`
      : "DATA VISUALIZATION ONLY — NO MATCH FOOTAGE — QUANT MODEL OUTPUT — NOT FINANCIAL ADVICE";
    textColor = C.textMuted;
  }

  // Ticker animation for long text
  useEffect(() => {
    setTickerOffset(0);
    if (!displayText || displayText.length < 50) return;

    let offset = 0;
    tickerRef.current = setInterval(() => {
      offset += 1;
      if (offset > displayText.length * 5.5 + 300) offset = 0;
      setTickerOffset(offset);
    }, 50);

    return () => clearInterval(tickerRef.current);
  }, [displayText]);

  // Format time
  const timeStr = now.toLocaleTimeString("en-GB", { hour12: false });
  const dateStr = now.toLocaleDateString("en-GB", { day: "2-digit", month: "2-digit" });

  return (
    <div style={{
      width: "100%",
      height: 24,
      background: C.bg,
      borderBottom: `1px solid ${C.border}`,
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 12px",
      fontFamily: FONT,
      fontSize: 10,
      overflow: "hidden",
      flexShrink: 0,
    }}>

      {/* Left: stage badge */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        flexShrink: 0,
        minWidth: 70,
      }}>
        {stageColor && (
          <>
            <div style={{
              width: 5, height: 5, borderRadius: "50%",
              background: stageColor,
              boxShadow: `0 0 4px ${stageColor}60`,
            }} />
            <span style={{
              fontSize: 8, fontWeight: 700, letterSpacing: 1.5,
              color: stageColor, whiteSpace: "nowrap",
            }}>
              {stageLabel}
            </span>
            <span style={{ color: C.textMuted, fontSize: 10 }}>|</span>
          </>
        )}
      </div>

      {/* Center: scrolling text */}
      <div style={{
        flex: 1,
        overflow: "hidden",
        position: "relative",
        height: 14,
        margin: "0 8px",
      }}>
        <span style={{
          position: "absolute",
          top: 0, left: 0,
          whiteSpace: "nowrap",
          fontSize: 10,
          color: textColor,
          letterSpacing: 0.5,
          fontWeight: broadcast?.text ? 500 : 400,
          transform: displayText.length >= 50
            ? `translateX(-${tickerOffset}px)`
            : "none",
        }}>
          {displayText}
        </span>
      </div>

      {/* Right: clock */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        flexShrink: 0,
      }}>
        <span style={{
          fontSize: 9, color: C.textMuted, letterSpacing: 0.5,
        }}>
          {dateStr}
        </span>
        <span style={{
          fontSize: 10, fontWeight: 700, color: C.textDim,
          fontFamily: FONT, letterSpacing: 0.5,
        }}>
          {timeStr}
        </span>
      </div>
    </div>
  );
}
