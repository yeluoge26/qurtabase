/**
 * useVoiceHighlight -- v1.0
 * Custom hook that provides panel highlighting when AI speaks about a section.
 * Maps broadcast stages to specific panel glow styles.
 *
 * Usage:
 *   const highlights = useVoiceHighlight(speaking, stage);
 *   <div style={{ ...panelStyle, ...getHighlightStyle(highlights, "signal") }}>
 */
import { useState, useEffect, useRef } from "react";

// ── Stage → Panel mapping ─────────────────────────────────────
const STAGE_PANEL_MAP = {
  SIGNAL_CONFIRM: "signal",
  SIGNAL_PENDING: "signal",
  SIGNAL: "signal",
  GOAL: "score",
  TEMPO_BUILD: "quant",
  LATE_GAME: "lambda",
  FINAL_WINDOW: "lambda",
  POST_MATCH: "postMatch",
};

// ── Panel → Glow color mapping ────────────────────────────────
const PANEL_GLOW = {
  signal: { color: "#FFD700", shadow: "0 0 8px #FFD70040, 0 0 16px #FFD70020, inset 0 0 4px #FFD70010" },
  score: { color: "#FFD700", shadow: "0 0 8px #FFD70040, 0 0 16px #FFD70020, inset 0 0 4px #FFD70010" },
  quant: { color: "#00FF88", shadow: "0 0 8px #00FF8840, 0 0 16px #00FF8820, inset 0 0 4px #00FF8810" },
  lambda: { color: "#FF9500", shadow: "0 0 8px #FF950040, 0 0 16px #FF950020, inset 0 0 4px #FF950010" },
  postMatch: { color: "#4A9EFF", shadow: "0 0 8px #4A9EFF40, 0 0 16px #4A9EFF20, inset 0 0 4px #4A9EFF10" },
};

// ── Fade duration ─────────────────────────────────────────────
const GLOW_FADE_MS = 800;

/**
 * useVoiceHighlight(speaking, stage)
 * Returns a map of { panelName: styleObject } for active highlight glows.
 */
export function useVoiceHighlight(speaking, stage) {
  const [highlights, setHighlights] = useState({});
  const fadeTimerRef = useRef(null);

  useEffect(() => {
    clearTimeout(fadeTimerRef.current);

    if (!speaking || !stage) {
      // Fade out: after short delay, clear highlights
      fadeTimerRef.current = setTimeout(() => {
        setHighlights({});
      }, GLOW_FADE_MS);
      return;
    }

    const upperStage = stage.toUpperCase();
    const panelName = STAGE_PANEL_MAP[upperStage];

    if (!panelName) {
      setHighlights({});
      return;
    }

    const glow = PANEL_GLOW[panelName];
    if (!glow) {
      setHighlights({});
      return;
    }

    setHighlights({
      [panelName]: {
        boxShadow: glow.shadow,
        borderColor: glow.color + "40",
        transition: `box-shadow ${GLOW_FADE_MS}ms ease-in-out, border-color ${GLOW_FADE_MS}ms ease-in-out`,
      },
    });

    return () => clearTimeout(fadeTimerRef.current);
  }, [speaking, stage]);

  return highlights;
}

/**
 * getHighlightStyle(highlights, panelName)
 * Returns the style object for a specific panel, or empty object if not highlighted.
 */
export function getHighlightStyle(highlights, panelName) {
  if (!highlights || !panelName) return {};
  return highlights[panelName] || {};
}

export default useVoiceHighlight;
