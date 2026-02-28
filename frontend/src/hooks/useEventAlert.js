/**
 * useEventAlert — v1.0
 * Detects new GOAL, RED_CARD, and probability swing events
 * and returns an alert object for the EventAlert overlay.
 *
 * Only fires once per event ID. Queues alerts sequentially.
 */

import { useState, useRef, useEffect, useCallback } from "react";

const DURATIONS = {
  goal: 2500,
  red_card: 2000,
  prob_swing: 3000,
};

/**
 * @param {Array}  events  – mapped event objects [{id, minute, type, team, text}, ...]
 * @param {Object} delta   – { home: number, draw: number, away: number }
 * @param {Array}  score   – [homeGoals, awayGoals]
 * @param {number} minute  – current match minute
 * @returns {{ alert: object|null, dismissAlert: function }}
 */
export function useEventAlert(events = [], delta = {}, score = [0, 0], minute = 0) {
  const processedEventIds = useRef(new Set());
  const lastProbSwingKey = useRef(null);      // prevents duplicate prob swing per cycle
  const [queue, setQueue] = useState([]);     // queued alerts
  const [active, setActive] = useState(null); // currently visible alert
  const timerRef = useRef(null);

  // ── Detect new alerts ──────────────────────────────────────
  useEffect(() => {
    const incoming = [];

    // Scan events for new GOALs and RED cards
    for (const ev of events) {
      if (!ev.id || processedEventIds.current.has(ev.id)) continue;
      processedEventIds.current.add(ev.id);

      const upperType = (ev.type || "").toUpperCase();

      if (upperType === "GOAL" || upperType === "PENALTY") {
        incoming.push({
          type: "goal",
          data: {
            team: ev.team,       // "home" | "away"
            minute: ev.minute,
            text: ev.text,
            score,               // snapshot at time of alert
          },
          duration: DURATIONS.goal,
        });
      } else if (upperType === "RED" || upperType === "RED_CARD") {
        incoming.push({
          type: "red_card",
          data: {
            team: ev.team,
            minute: ev.minute,
            text: ev.text,
          },
          duration: DURATIONS.red_card,
        });
      }
    }

    // Check probability swing (|delta| > 15 on home or away)
    const homeSwing = Math.abs(delta.home || 0) > 15;
    const awaySwing = Math.abs(delta.away || 0) > 15;
    if (homeSwing || awaySwing) {
      // Build a key so we don't fire the same swing repeatedly
      const swingKey = `${Math.round(delta.home || 0)}_${Math.round(delta.away || 0)}_${minute}`;
      if (swingKey !== lastProbSwingKey.current) {
        lastProbSwingKey.current = swingKey;
        incoming.push({
          type: "prob_swing",
          data: { delta, minute },
          duration: DURATIONS.prob_swing,
        });
      }
    }

    if (incoming.length > 0) {
      setQueue(q => [...q, ...incoming]);
    }
  }, [events, delta, score, minute]);

  // ── Process queue → show next alert ────────────────────────
  useEffect(() => {
    if (active || queue.length === 0) return;

    const next = queue[0];
    setActive({ ...next, visible: true });
    setQueue(q => q.slice(1));

    timerRef.current = setTimeout(() => {
      setActive(null);
      timerRef.current = null;
    }, next.duration);
  }, [active, queue]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const dismissAlert = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setActive(null);
  }, []);

  return { alert: active, dismissAlert };
}
