/**
 * SignalControlPanel -- v1.0
 * Semi-automatic signal confirmation panel
 * Bloomberg terminal style -- gold/green/dim states
 *
 * States:
 *   idle      - hidden (edge < threshold)
 *   ready     - gold border, CONFIRM/REJECT buttons
 *   confirmed - green border, locked message
 *   cooldown  - dim border, countdown timer
 */
import { useState, useEffect, useRef, useCallback } from "react";
import { LANG } from "../utils/i18n";

const C = {
  bg: "#131720",
  border: "#1E2530",
  borderLight: "#252D3A",
  text: "#E5E5E5",
  textDim: "#6B7280",
  textMuted: "#3D4654",
  up: "#00C853",
  down: "#FF3D00",
  accent: "#F4C430",
  gold: "#F4C430",
  green: "#00C853",
};

// ── Cooldown countdown hook ──────────────────────────────────
function useCooldown(remaining) {
  const [sec, setSec] = useState(remaining || 0);
  const ref = useRef(null);

  useEffect(() => {
    setSec(remaining || 0);
  }, [remaining]);

  useEffect(() => {
    if (sec <= 0) {
      clearInterval(ref.current);
      return;
    }
    ref.current = setInterval(() => {
      setSec((s) => {
        if (s <= 1) {
          clearInterval(ref.current);
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(ref.current);
  }, [sec > 0]);

  const mm = String(Math.floor(sec / 60)).padStart(2, "0");
  const ss = String(sec % 60).padStart(2, "0");
  return { display: `${mm}:${ss}`, seconds: sec };
}

// ════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════════
export default function SignalControlPanel({ data, onConfirm, onReject, lang = "en" }) {
  const L = LANG[lang];
  const [confirmHover, setConfirmHover] = useState(false);
  const [rejectHover, setRejectHover] = useState(false);

  if (!data) return null;

  const {
    state = "idle",
    line = 0,
    model_prob = 0,
    market_prob = 0,
    edge = 0,
    confirmed_at = null,
    cooldown_remaining = 0,
  } = data;

  // Hidden when idle
  if (state === "idle") return null;

  const cooldown = useCooldown(state === "cooldown" ? cooldown_remaining : 0);

  // ── Keyboard shortcuts ──
  useEffect(() => {
    function handleKey(e) {
      if (state !== "ready") return;
      if (e.key === "Enter") {
        e.preventDefault();
        onConfirm?.();
      } else if (e.key === "Escape") {
        e.preventDefault();
        onReject?.();
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [state, onConfirm, onReject]);

  // ── Border + background by state ──
  let borderColor = C.border;
  let bgTint = C.bg;
  let headerIcon = "";
  let headerText = "";
  let headerColor = C.textDim;

  if (state === "ready") {
    borderColor = C.gold;
    bgTint = C.gold + "08";
    headerIcon = "\u26A1";
    headerText = L?.signalReady || "SIGNAL READY";
    headerColor = C.gold;
  } else if (state === "confirmed") {
    borderColor = C.green;
    bgTint = C.green + "0C";
    headerIcon = "\u2713";
    headerText = L?.signalConfirmed || "SIGNAL CONFIRMED";
    headerColor = C.green;
  } else if (state === "cooldown") {
    borderColor = C.borderLight;
    bgTint = C.bg;
    headerIcon = "";
    headerText = `${L?.cooldownLabel || "COOLDOWN"} ${cooldown.display}`;
    headerColor = C.textMuted;
  }

  const edgeSign = edge > 0 ? "+" : "";

  return (
    <div
      style={{
        padding: "10px 14px",
        background: bgTint,
        border: `1px solid ${borderColor}`,
        borderRadius: 2,
        fontFamily: "'IBM Plex Mono', monospace",
        transition: "border-color 300ms, background 300ms",
      }}
    >
      {/* ── Header ── */}
      <div
        style={{
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: 2.5,
          color: headerColor,
          marginBottom: state === "cooldown" ? 4 : 8,
        }}
      >
        {headerIcon && (
          <span style={{ marginRight: 6, fontSize: 12 }}>{headerIcon}</span>
        )}
        {headerText}
      </div>

      {/* ── READY state body ── */}
      {state === "ready" && (
        <>
          {/* Data row */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginBottom: 6,
            }}
          >
            <div style={{ display: "flex", gap: 20 }}>
              <DataPair label={L?.line || "Line"} value={line.toFixed(2)} />
              <DataPair
                label={L?.edge || "Edge"}
                value={`${edgeSign}${edge.toFixed(1)}%`}
                color={edge > 0 ? C.up : edge < 0 ? C.down : C.textDim}
              />
            </div>
            <div style={{ display: "flex", gap: 20 }}>
              <DataPair
                label={L?.model || "Model"}
                value={`${model_prob.toFixed(1)}%`}
              />
              <DataPair
                label={L?.market || "Market"}
                value={`${market_prob.toFixed(1)}%`}
              />
            </div>
          </div>

          {/* Action buttons */}
          <div
            style={{
              display: "flex",
              gap: 10,
              marginTop: 10,
            }}
          >
            {/* CONFIRM */}
            <button
              onClick={onConfirm}
              onMouseEnter={() => setConfirmHover(true)}
              onMouseLeave={() => setConfirmHover(false)}
              style={{
                flex: 1,
                padding: "7px 0",
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 2,
                fontFamily: "'IBM Plex Mono', monospace",
                border: "none",
                borderRadius: 2,
                cursor: "pointer",
                background: confirmHover ? "#FFD54F" : C.gold,
                color: "#0E1117",
                transition: "background 150ms",
              }}
            >
              {"\u2713"} {L?.confirm || "CONFIRM"}
            </button>

            {/* REJECT */}
            <button
              onClick={onReject}
              onMouseEnter={() => setRejectHover(true)}
              onMouseLeave={() => setRejectHover(false)}
              style={{
                flex: 1,
                padding: "7px 0",
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 2,
                fontFamily: "'IBM Plex Mono', monospace",
                border: `1px solid ${rejectHover ? C.down : C.borderLight}`,
                borderRadius: 2,
                cursor: "pointer",
                background: "transparent",
                color: rejectHover ? C.down : C.textDim,
                transition: "border-color 150ms, color 150ms",
              }}
            >
              {"\u2717"} {L?.reject || "REJECT"}
            </button>
          </div>

          {/* Keyboard hint */}
          <div
            style={{
              textAlign: "center",
              marginTop: 6,
              fontSize: 8,
              color: C.textMuted,
              letterSpacing: 1.5,
            }}
          >
            {L?.enterConfirm || "ENTER = CONFIRM | ESC = REJECT"}
          </div>
        </>
      )}

      {/* ── CONFIRMED state body ── */}
      {state === "confirmed" && (
        <div>
          <div
            style={{
              fontSize: 12,
              fontWeight: 700,
              color: C.text,
              marginBottom: 4,
            }}
          >
            {L?.over || "OVER"} {line.toFixed(2)}{" "}
            <span style={{ color: C.green, marginLeft: 6 }}>
              | {L?.edge || "Edge"} {edgeSign}{edge.toFixed(1)}%
            </span>
          </div>
          <div
            style={{
              fontSize: 10,
              color: C.textDim,
              letterSpacing: 1,
            }}
          >
            {L?.locked || "Locked \u2014 entering cooldown..."}
          </div>
        </div>
      )}

      {/* ── COOLDOWN state body ── */}
      {state === "cooldown" && (
        <div
          style={{
            fontSize: 10,
            color: C.textMuted,
            letterSpacing: 1,
          }}
        >
          {L?.nextEvalAfterCooldown || "Next evaluation after cooldown"}
        </div>
      )}
    </div>
  );
}

// ── Sub-component ────────────────────────────────────────────
function DataPair({ label, value, color }) {
  return (
    <div>
      <div
        style={{
          fontSize: 9,
          color: C.textMuted,
          letterSpacing: 1.5,
          marginBottom: 2,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: 13,
          fontWeight: 700,
          color: color || C.text,
          fontFamily: "'IBM Plex Mono', monospace",
        }}
      >
        {value}
      </div>
    </div>
  );
}
