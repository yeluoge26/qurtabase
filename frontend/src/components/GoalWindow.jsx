/**
 * GoalWindow -- v1.0
 * High Goal Window detection banner -- Bloomberg terminal style
 * Shows a compact gold-tinted banner when an elevated scoring window is active.
 * Automatically fades in/out with 300ms transition.
 */
import { useState, useEffect, useRef } from "react";
import { LANG } from "../utils/i18n";

const C = {
  bg: "#0E1117",
  bgCard: "#131720",
  border: "#1E2530",
  borderLight: "#252D3A",
  text: "#E5E5E5",
  textDim: "#6B7280",
  textMuted: "#3D4654",
  gold: "#F4C430",
  goldBg: "rgba(244, 196, 48, 0.08)",
};

// ── Elapsed timer hook ──────────────────────────────────────
function useElapsedTimer(active, initialSec) {
  const [sec, setSec] = useState(initialSec || 0);
  const ref = useRef(null);

  // Sync with incoming payload value
  useEffect(() => {
    setSec(initialSec || 0);
  }, [initialSec]);

  // Tick every second while active
  useEffect(() => {
    if (!active) {
      clearInterval(ref.current);
      return;
    }
    ref.current = setInterval(() => {
      setSec(s => s + 1);
    }, 1000);
    return () => clearInterval(ref.current);
  }, [active]);

  const mm = String(Math.floor(sec / 60)).padStart(2, "0");
  const ss = String(sec % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

// ════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════
export default function GoalWindow({ data, lang = "en" }) {
  const L = LANG[lang];
  const [visible, setVisible] = useState(false);
  const [render, setRender] = useState(false);

  const active = data?.active === true;
  const elapsed = useElapsedTimer(active, data?.elapsed_sec);

  // Manage fade-in / fade-out lifecycle
  useEffect(() => {
    if (active) {
      setRender(true);
      // Small delay to trigger CSS transition from opacity 0 -> 1
      const raf = requestAnimationFrame(() => setVisible(true));
      return () => cancelAnimationFrame(raf);
    } else {
      setVisible(false);
      // Keep in DOM for fade-out duration, then unmount
      const timeout = setTimeout(() => setRender(false), 320);
      return () => clearTimeout(timeout);
    }
  }, [active]);

  if (!render) return null;

  const confidence = data?.confidence ?? 0;
  const duration = data?.estimated_duration_min || "--";
  const tempoC = data?.tempo_c ?? 0;
  const lambdaRate = data?.lambda_rate ?? 0;

  return (
    <div style={{
      padding: "10px 14px",
      background: C.goldBg,
      borderLeft: `3px solid ${C.gold}`,
      borderBottom: `1px solid ${C.border}`,
      maxHeight: 60,
      overflow: "hidden",
      opacity: visible ? 1 : 0,
      transition: "opacity 300ms ease-in-out",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: 12,
    }}>
      {/* Left: Icon + Title */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
        <span style={{
          fontSize: 14,
          color: C.gold,
          lineHeight: 1,
          flexShrink: 0,
        }}>
          {"\u26A0"}
        </span>
        <span style={{
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: 2.5,
          color: C.gold,
          fontFamily: "'IBM Plex Mono', monospace",
          whiteSpace: "nowrap",
        }}>
          {L?.highGoalWindow}
        </span>
      </div>

      {/* Center: Duration + Confidence */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 16,
        fontFamily: "'IBM Plex Mono', monospace",
        fontSize: 10,
        color: C.text,
        whiteSpace: "nowrap",
      }}>
        <span>
          <span style={{ color: C.textDim, letterSpacing: 1, marginRight: 4 }}>{L?.estimated}</span>
          {duration}
          <span style={{ color: C.textDim, marginLeft: 2 }}>{L?.min}</span>
        </span>
        <span style={{ color: C.textMuted }}>|</span>
        <span>
          <span style={{ color: C.textDim, letterSpacing: 1, marginRight: 4 }}>{L?.confidence}</span>
          <span style={{ fontWeight: 700, color: confidence >= 60 ? C.gold : C.text }}>{confidence}</span>
          <span style={{ fontSize: 9, color: C.textDim }}>%</span>
        </span>
        <span style={{ color: C.textMuted }}>|</span>
        <span>
          <span style={{ color: C.textDim, letterSpacing: 1, marginRight: 4 }}>{L?.active}</span>
          <span style={{ fontWeight: 700, color: C.text }}>{elapsed}</span>
        </span>
      </div>

      {/* Right: Tempo + Lambda rate (compact diagnostics) */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        fontFamily: "'IBM Plex Mono', monospace",
        fontSize: 9,
        color: C.textDim,
        whiteSpace: "nowrap",
        flexShrink: 0,
      }}>
        <span>
          T<sub style={{ fontSize: 7 }}>c</sub> {tempoC.toFixed(2)}
        </span>
        <span>
          {"\u03BB"}/m {lambdaRate.toFixed(3)}
        </span>
      </div>
    </div>
  );
}
