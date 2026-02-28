/**
 * TotalGoalsPanel -- v1.2
 * O/U Trading Panel -- Bloomberg terminal style
 * Displays lambda engine output, probability edge, signal, and micro bars
 * Pro/Elite tier feature
 */
import { useState, useEffect, useRef } from "react";

const C = {
  bg: "#0E1117", bgCard: "#131720",
  border: "#1E2530", borderLight: "#252D3A",
  text: "#E5E5E5", textDim: "#6B7280", textMuted: "#3D4654",
  up: "#00C853", down: "#FF3D00",
  accent: "#F4C430", accentBlue: "#00C8FF",
};

// ── MicroBar ────────────────────────────────────────────────
function MicroBar({ label, value, max = 100, color }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div style={{ display: "flex", alignItems: "center", padding: "3px 0" }}>
      <span style={{ fontSize: 9, color: C.textDim, letterSpacing: 1.5, minWidth: 120, fontWeight: 600 }}>{label}</span>
      <div style={{ flex: 1, height: 6, background: C.border, borderRadius: 1, marginRight: 8 }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 1, transition: "width 300ms" }} />
      </div>
      <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, fontWeight: 700, color: C.text, minWidth: 40, textAlign: "right" }}>
        {typeof value === "number" ? (value > 10 ? value : value.toFixed(2)) : value}
      </span>
    </div>
  );
}

// ── Divider ─────────────────────────────────────────────────
function Divider() {
  return (
    <div style={{ borderBottom: `1px solid ${C.borderLight}`, margin: "8px 0" }} />
  );
}

// ── Cooldown timer ──────────────────────────────────────────
function useCooldown(inCooldown, remainingSec) {
  const [sec, setSec] = useState(remainingSec || 0);
  const ref = useRef(null);

  useEffect(() => {
    setSec(remainingSec || 0);
  }, [remainingSec]);

  useEffect(() => {
    if (!inCooldown || sec <= 0) {
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
  }, [inCooldown, sec > 0]);

  const mm = String(Math.floor(sec / 60)).padStart(2, "0");
  const ss = String(sec % 60).padStart(2, "0");
  return { display: `${mm}:${ss}`, active: inCooldown && sec > 0 };
}

// ════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════════
export default function TotalGoalsPanel({ totalGoals, quant }) {
  if (!totalGoals) return null;

  const {
    lambda_pre = 0,
    lambda_live = 0,
    lambda_market = 0,
    line = 2.5,
    model_prob_over = 0,
    market_prob_over = 0,
    edge = 0,
    signal = "NO SIGNAL",
    signal_level = 0,
    tempo_index = 50,
    game_state_factor = 1.0,
    red_card_factor = 1.0,
    in_cooldown = false,
    cooldown_remaining_sec = 0,
  } = totalGoals;

  const pressure = quant?.pressure || 50;
  const volatility = quant?.volatility || 0.5;

  const lambdaDelta = lambda_live - lambda_pre;
  const hasSignal = signal && signal !== "NO SIGNAL";
  const cooldown = useCooldown(in_cooldown, cooldown_remaining_sec);

  // Edge color
  const edgeColor = edge > 3 ? C.up : edge < -3 ? C.down : C.textDim;
  // Signal color -- gold when active
  const signalBg = hasSignal ? C.accent + "18" : "transparent";
  const signalBorder = hasSignal ? C.accent + "40" : C.border;
  const signalText = hasSignal ? C.accent : C.textMuted;

  return (
    <div style={{ padding: "12px 14px", borderBottom: `1px solid ${C.border}` }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8, paddingBottom: 6, borderBottom: `1px solid ${C.borderLight}` }}>
        <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: 3, color: C.accent, fontFamily: "'IBM Plex Mono', monospace" }}>TOTAL GOALS ENGINE</span>
        <span style={{ fontSize: 9, color: C.textMuted, fontFamily: "'IBM Plex Mono', monospace" }}>O/U TRADING</span>
      </div>

      {/* PRE vs LIVE λ comparison strip */}
      {(() => {
        const lambdaPct = lambda_pre !== 0 ? ((lambda_live - lambda_pre) / lambda_pre) * 100 : 0;
        const tempoPct = ((tempo_index - 50) / 50) * 100;
        const lambdaColor = lambdaPct > 0 ? C.up : lambdaPct < 0 ? C.down : C.textMuted;
        const tempoColor = tempoPct > 0 ? C.up : tempoPct < 0 ? C.down : C.textMuted;
        const mono = "'IBM Plex Mono', monospace";
        const s = { fontSize: 8, fontFamily: mono, letterSpacing: 0.5 };
        return (
          <div style={{
            display: "flex", alignItems: "center", height: 16,
            padding: "0 4px", marginBottom: 6,
            background: C.bg, border: `1px solid ${C.borderLight}`, borderRadius: 2,
          }}>
            <span style={{ ...s, color: C.textDim }}>
              PRE {"\u03BB"} <span style={{ color: C.accent, fontWeight: 700 }}>{lambda_pre.toFixed(2)}</span>
              <span style={{ color: C.textMuted, margin: "0 2px" }}>{"\u2192"}</span>
              LIVE {"\u03BB"} <span style={{ color: C.accent, fontWeight: 700 }}>{lambda_live.toFixed(2)}</span>
              <span style={{ color: lambdaColor, fontWeight: 700, marginLeft: 3 }}>
                {"\u0394"}{lambdaPct > 0 ? "+" : ""}{lambdaPct.toFixed(1)}%
              </span>
            </span>
            <span style={{ ...s, color: C.textMuted, margin: "0 6px" }}>|</span>
            <span style={{ ...s, color: C.textDim }}>
              TEMPO <span style={{ color: C.accent, fontWeight: 700 }}>{tempo_index}</span>
              <span style={{ color: C.textMuted, margin: "0 2px" }}>(EXP 50)</span>
              <span style={{ color: tempoColor, fontWeight: 700, marginLeft: 3 }}>
                {"\u0394"}{tempoPct > 0 ? "+" : ""}{Math.round(tempoPct)}%
              </span>
            </span>
          </div>
        );
      })()}

      {/* Lambda values */}
      <div style={{ marginBottom: 4 }}>
        <LambdaRow label="Pre \u03BB_total" value={lambda_pre} />
        <LambdaRow label="Live \u03BB_total" value={lambda_live} delta={lambdaDelta} />
        <LambdaRow label="Market \u03BB" value={lambda_market} />
      </div>

      <Divider />

      {/* LINE display -- prominent */}
      <div style={{ textAlign: "center", padding: "6px 0" }}>
        <div style={{ fontSize: 9, color: C.textMuted, letterSpacing: 2, marginBottom: 4 }}>LINE</div>
        <div style={{ fontSize: 30, fontWeight: 800, fontFamily: "'IBM Plex Mono', monospace", color: C.text, letterSpacing: -1, lineHeight: 1 }}>
          {line.toFixed(1)}
        </div>
      </div>

      <Divider />

      {/* Probability comparison */}
      <div style={{ marginBottom: 4 }}>
        <ProbLine label="Model Prob" value={model_prob_over} />
        <ProbLine label="Market Prob" value={market_prob_over} />
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", padding: "4px 0" }}>
          <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1.5, fontWeight: 600 }}>Edge</span>
          <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 14, fontWeight: 800, color: edgeColor }}>
            {edge > 0 ? "+" : ""}{edge.toFixed(1)}
            <span style={{ fontSize: 10, color: C.textDim }}>%</span>
          </span>
        </div>
      </div>

      <Divider />

      {/* Confidence + CI */}
      {totalGoals.confidence != null && (
        <div style={{ marginBottom: 4 }}>
          <div style={{ display: "flex", justifyContent: "space-between", padding: "3px 0" }}>
            <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1.5, fontWeight: 600 }}>Confidence</span>
            <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 13, fontWeight: 700, color: C.text }}>
              {totalGoals.confidence}<span style={{ fontSize: 10, color: C.textDim }}>%</span>
            </span>
          </div>
          {totalGoals.ci95 && (
            <div style={{ display: "flex", justifyContent: "space-between", padding: "3px 0" }}>
              <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1.5, fontWeight: 600 }}>CI95</span>
              <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, color: C.textDim }}>
                {totalGoals.ci95[0].toFixed(1)}% &ndash; {totalGoals.ci95[1].toFixed(1)}%
              </span>
            </div>
          )}
          <Divider />
        </div>
      )}

      {/* Signal indicator */}
      <div style={{
        textAlign: "center",
        padding: "8px 10px",
        marginBottom: 6,
        background: signalBg,
        border: `1px solid ${signalBorder}`,
        borderRadius: 2,
      }}>
        <div style={{ fontSize: 9, color: C.textMuted, letterSpacing: 2, marginBottom: 4 }}>SIGNAL</div>
        <div style={{
          fontSize: 14, fontWeight: 800, fontFamily: "'IBM Plex Mono', monospace",
          color: signalText, letterSpacing: 2,
        }}>
          {signal}
        </div>
        {signal_level > 0 && (
          <div style={{ marginTop: 4 }}>
            {[1, 2, 3].map(i => (
              <span key={i} style={{
                display: "inline-block", width: 14, height: 4, marginRight: 2, borderRadius: 1,
                background: i <= signal_level ? C.accent : C.border,
              }} />
            ))}
          </div>
        )}
      </div>

      {/* Cooldown countdown */}
      {cooldown.active && (
        <div style={{
          textAlign: "center", padding: "4px 0", fontSize: 10, fontWeight: 600,
          fontFamily: "'IBM Plex Mono', monospace", color: C.textMuted, letterSpacing: 2,
        }}>
          NEXT EVAL IN {cooldown.display}
        </div>
      )}

      <Divider />

      {/* Micro bars: Tempo, Pressure, Volatility */}
      <MicroBar label="TEMPO INDEX" value={tempo_index} max={100} color={C.accentBlue} />
      <MicroBar label="PRESSURE INDEX" value={pressure} max={100} color={C.up} />
      <MicroBar label="VOLATILITY" value={volatility} max={2} color={C.accent} />

      {/* Game state factors */}
      {(game_state_factor !== 1.0 || red_card_factor !== 1.0) && (
        <div style={{ marginTop: 6, paddingTop: 4, borderTop: `1px solid ${C.borderLight}` }}>
          {game_state_factor !== 1.0 && (
            <div style={{ display: "flex", justifyContent: "space-between", padding: "2px 0" }}>
              <span style={{ fontSize: 9, color: C.textMuted, letterSpacing: 1 }}>GAME STATE FACTOR</span>
              <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 10, color: C.textDim }}>{game_state_factor.toFixed(2)}</span>
            </div>
          )}
          {red_card_factor !== 1.0 && (
            <div style={{ display: "flex", justifyContent: "space-between", padding: "2px 0" }}>
              <span style={{ fontSize: 9, color: C.down, letterSpacing: 1 }}>RED CARD FACTOR</span>
              <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 10, color: C.down }}>{red_card_factor.toFixed(2)}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Sub-components ──────────────────────────────────────────

function LambdaRow({ label, value, delta }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", padding: "3px 0" }}>
      <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1.5, fontWeight: 600 }}>{label}</span>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
        <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 15, fontWeight: 700, color: C.text }}>
          {value.toFixed(2)}
        </span>
        {delta !== undefined && (
          <span style={{
            fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, fontWeight: 600,
            color: delta > 0 ? C.up : delta < 0 ? C.down : C.textMuted,
          }}>
            {delta > 0 ? "\u25B2" : delta < 0 ? "\u25BC" : ""} {delta > 0 ? "+" : ""}{delta.toFixed(2)}
          </span>
        )}
      </div>
    </div>
  );
}

function ProbLine({ label, value }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", padding: "4px 0" }}>
      <span style={{ fontSize: 10, color: C.textDim, letterSpacing: 1.5, fontWeight: 600 }}>{label}</span>
      <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 13, fontWeight: 700, color: C.text }}>
        {value.toFixed(1)}<span style={{ fontSize: 10, color: C.textDim }}>%</span>
      </span>
    </div>
  );
}
