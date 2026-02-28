/**
 * AISpeakingIndicator -- v1.0
 * Compact indicator showing AI voice commentary status
 * Pulsing gold glow + audio wave bars when speaking
 * Bloomberg terminal style
 */
import { useState, useEffect, useRef } from "react";
import { LANG } from "../utils/i18n";

const C = {
  bg: "#0E1117", bgCard: "#131720",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  accent: "#F4C430", accentBright: "#FFD700",
  up: "#00C853",
};

const FONT = "'IBM Plex Mono', monospace";

export default function AISpeakingIndicator({ speaking = false, text = "", lang = "en" }) {
  const [visible, setVisible] = useState(false);
  const fadeRef = useRef(null);

  // Fade in/out with slight delay for smooth transition
  useEffect(() => {
    if (speaking) {
      setVisible(true);
    } else {
      fadeRef.current = setTimeout(() => setVisible(false), 400);
    }
    return () => clearTimeout(fadeRef.current);
  }, [speaking]);

  const L = LANG[lang];
  const labelSpeaking = L?.aiSpeaking || "AI SPEAKING...";
  const labelReady = L?.aiReady || "AI READY";

  return (
    <div style={{
      display: "inline-flex",
      flexDirection: "column",
      alignItems: "flex-end",
      minWidth: 120,
      maxWidth: 200,
      fontFamily: FONT,
      transition: "opacity 0.3s ease",
      opacity: speaking || visible ? 1 : 0.5,
    }}>
      <style>{indicatorCSS}</style>

      <div style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
      }}>
        {/* Audio wave bars (visible only when speaking) */}
        {speaking && (
          <div style={{
            display: "flex",
            alignItems: "flex-end",
            gap: 2,
            height: 14,
          }}>
            <div className="ai-wave-bar" style={{ ...waveBarBase, animationDelay: "0s" }} />
            <div className="ai-wave-bar" style={{ ...waveBarBase, animationDelay: "0.15s" }} />
            <div className="ai-wave-bar" style={{ ...waveBarBase, animationDelay: "0.3s" }} />
          </div>
        )}

        {/* Status dot */}
        <div style={{
          width: 5,
          height: 5,
          borderRadius: "50%",
          background: speaking ? C.accentBright : "#555",
          boxShadow: speaking ? `0 0 6px ${C.accentBright}, 0 0 10px ${C.accent}60` : "none",
          animation: speaking ? "aiDotPulse 1.5s ease-in-out infinite" : "none",
          flexShrink: 0,
        }} />

        {/* Label */}
        <span style={{
          fontSize: 9,
          fontWeight: 700,
          letterSpacing: 2,
          color: speaking ? C.accentBright : "#555",
          textShadow: speaking ? `0 0 8px ${C.accent}60` : "none",
          animation: speaking ? "aiTextGlow 2s ease-in-out infinite" : "none",
          whiteSpace: "nowrap",
        }}>
          {speaking ? labelSpeaking : labelReady}
        </span>
      </div>

      {/* Broadcast text preview (only when speaking and text available) */}
      {speaking && text && (
        <div style={{
          marginTop: 3,
          maxWidth: 200,
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          fontSize: 8,
          color: C.textDim,
          letterSpacing: 0.5,
          fontFamily: FONT,
          animation: "aiFadeIn 0.3s ease-in",
        }}>
          {text}
        </div>
      )}
    </div>
  );
}

const waveBarBase = {
  width: 2,
  minHeight: 3,
  background: "#FFD700",
  borderRadius: 1,
};

const indicatorCSS = `
  @keyframes aiWaveOscillate {
    0%, 100% { height: 3px; }
    50% { height: 12px; }
  }
  .ai-wave-bar {
    animation: aiWaveOscillate 0.6s ease-in-out infinite;
  }
  @keyframes aiDotPulse {
    0%, 100% { opacity: 0.6; box-shadow: 0 0 4px #FFD700, 0 0 8px #F4C43040; }
    50% { opacity: 1; box-shadow: 0 0 8px #FFD700, 0 0 14px #F4C43080; }
  }
  @keyframes aiTextGlow {
    0%, 100% { text-shadow: 0 0 4px #F4C43040; }
    50% { text-shadow: 0 0 10px #F4C43080; }
  }
  @keyframes aiFadeIn {
    0% { opacity: 0; transform: translateY(-2px); }
    100% { opacity: 1; transform: translateY(0); }
  }
`;
