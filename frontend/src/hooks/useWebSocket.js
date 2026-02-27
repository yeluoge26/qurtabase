import { useState, useEffect, useRef, useCallback } from "react";

/**
 * v1.1 WebSocket hook
 * - Fibonacci backoff reconnect: 3s → 5s → 8s → 13s
 * - Single instance (close old before creating new)
 * - Health tracking from meta.health
 * - Works for both demo and live match IDs
 */

const BACKOFF = [3000, 5000, 8000, 13000];
const HEARTBEAT_INTERVAL = 15000; // 15s ping
const PONG_TIMEOUT = 5000;        // 5s pong deadline

export function useMatchData(matchId) {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);
  const [health, setHealth] = useState("OK");
  const wsRef = useRef(null);
  const timerRef = useRef(null);
  const attemptRef = useRef(0);
  const aliveRef = useRef(true);
  const heartbeatRef = useRef(null);
  const pongTimerRef = useRef(null);
  const awaitingPongRef = useRef(false);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatRef.current) { clearInterval(heartbeatRef.current); heartbeatRef.current = null; }
    if (pongTimerRef.current) { clearTimeout(pongTimerRef.current); pongTimerRef.current = null; }
    awaitingPongRef.current = false;
  }, []);

  const startHeartbeat = useCallback((ws) => {
    stopHeartbeat();
    heartbeatRef.current = setInterval(() => {
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      awaitingPongRef.current = true;
      try { ws.send(JSON.stringify({ type: "ping", ts: Date.now() })); } catch {}
      pongTimerRef.current = setTimeout(() => {
        if (awaitingPongRef.current) {
          setHealth("DEGRADED");
        }
      }, PONG_TIMEOUT);
    }, HEARTBEAT_INTERVAL);
  }, [stopHeartbeat]);

  const connect = useCallback(() => {
    if (!matchId || !aliveRef.current) return;

    // Kill previous
    stopHeartbeat();
    if (wsRef.current) {
      try { wsRef.current.close(); } catch {}
      wsRef.current = null;
    }

    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${proto}//${window.location.host}/ws/${matchId}`;

    const ws = new WebSocket(url);

    ws.onopen = () => {
      if (!aliveRef.current) { ws.close(); return; }
      setConnected(true);
      setHealth("OK");
      attemptRef.current = 0;
      startHeartbeat(ws);
    };

    ws.onclose = () => {
      if (!aliveRef.current) return;
      stopHeartbeat();
      setConnected(false);
      const delay = BACKOFF[Math.min(attemptRef.current, BACKOFF.length - 1)];
      attemptRef.current += 1;
      timerRef.current = setTimeout(() => {
        if (aliveRef.current) connect();
      }, delay);
    };

    ws.onerror = () => setHealth("DEGRADED");

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (!aliveRef.current) return;

        // Handle pong reply — clear degraded timer
        if (payload.type === "pong") {
          awaitingPongRef.current = false;
          if (pongTimerRef.current) { clearTimeout(pongTimerRef.current); pongTimerRef.current = null; }
          return;
        }

        if (payload.meta?.health) setHealth(payload.meta.health);
        setData(payload);
      } catch {}
    };

    wsRef.current = ws;
  }, [matchId, startHeartbeat, stopHeartbeat]);

  useEffect(() => {
    aliveRef.current = true;
    connect();
    return () => {
      aliveRef.current = false;
      stopHeartbeat();
      if (timerRef.current) clearTimeout(timerRef.current);
      if (wsRef.current) try { wsRef.current.close(); } catch {}
    };
  }, [connect]);

  return { data, connected, health };
}
