/**
 * useSoundEffects -- v1.0
 * Bloomberg terminal-style audio cues using Web Audio API.
 * Generates sounds programmatically — no external files required.
 *
 * Sounds:
 *   goal()       — Trade execution: ascending 3-note arpeggio (C5-E5-G5, 80ms each)
 *   redCard()    — Alarm: two short beeps (400Hz, 100ms on/100ms off)
 *   probSwing()  — Limit-up alert: quick ascending sweep (800→1600Hz, 200ms)
 *   halfTime()   — Closing bell: decaying sine 800Hz, 600ms
 *   modelDing()  — Clean ding: 1200Hz sine, 150ms with fast decay
 *   signal()     — Confirmation: two-tone (E5 60ms, G5 120ms)
 */
import { useRef, useCallback } from "react";

export default function useSoundEffects(enabled = true) {
  const ctxRef = useRef(null);

  const getCtx = useCallback(() => {
    if (!ctxRef.current) {
      try {
        ctxRef.current = new (window.AudioContext || window.webkitAudioContext)();
      } catch { return null; }
    }
    return ctxRef.current;
  }, []);

  const playTone = useCallback((freq, duration, type = "sine", volume = 0.15, delay = 0) => {
    if (!enabled) return;
    const ctx = getCtx();
    if (!ctx) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(volume, ctx.currentTime + delay);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + delay + duration);
    osc.connect(gain).connect(ctx.destination);
    osc.start(ctx.currentTime + delay);
    osc.stop(ctx.currentTime + delay + duration);
  }, [enabled, getCtx]);

  const goal = useCallback(() => {
    playTone(523, 0.08, "sine", 0.12, 0);     // C5
    playTone(659, 0.08, "sine", 0.12, 0.08);   // E5
    playTone(784, 0.15, "sine", 0.15, 0.16);   // G5 (longer)
  }, [playTone]);

  const redCard = useCallback(() => {
    playTone(400, 0.1, "square", 0.1, 0);
    playTone(400, 0.1, "square", 0.1, 0.2);
  }, [playTone]);

  const probSwing = useCallback(() => {
    if (!enabled) return;
    const ctx = getCtx();
    if (!ctx) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(800, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(1600, ctx.currentTime + 0.2);
    gain.gain.setValueAtTime(0.1, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
    osc.connect(gain).connect(ctx.destination);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.3);
  }, [enabled, getCtx]);

  const halfTime = useCallback(() => {
    playTone(800, 0.6, "sine", 0.12, 0);
  }, [playTone]);

  const modelDing = useCallback(() => {
    playTone(1200, 0.15, "sine", 0.1, 0);
  }, [playTone]);

  const signal = useCallback(() => {
    playTone(659, 0.06, "sine", 0.1, 0);    // E5
    playTone(784, 0.12, "sine", 0.12, 0.06); // G5
  }, [playTone]);

  return { goal, redCard, probSwing, halfTime, modelDing, signal };
}
