// @ts-check
import { test, expect } from "@playwright/test";

/**
 * TEST SUITE 3: WebSocket data flow & payload structure
 */

// Helper: connect to WS from an already-navigated page and get the first data payload
async function getWsPayload(page) {
  return page.evaluate(() => {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error("WS timeout")), 25000);
      fetch("/api/matches/live")
        .then((r) => r.json())
        .then((matches) => {
          const matchId = matches[0]?.match_id || "demo";
          const proto = location.protocol === "https:" ? "wss:" : "ws:";
          const ws = new WebSocket(`${proto}//${location.host}/ws/${matchId}`);
          ws.onmessage = (ev) => {
            try {
              const data = JSON.parse(ev.data);
              if (data.type === "pong") return;
              clearTimeout(timeout);
              ws.close();
              resolve(data);
            } catch {}
          };
          ws.onerror = () => {
            clearTimeout(timeout);
            reject(new Error("WS connection error"));
          };
        });
    });
  });
}

test.describe("WebSocket Data Flow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("WebSocket delivers complete payload", async ({ page }) => {
    const wsPayload = await getWsPayload(page);
    const requiredKeys = [
      "meta", "match", "probability", "market", "stats",
      "events", "quant", "uncertainty", "explain", "report",
      "total_goals", "goal_window", "line_movement", "risk",
      "signal_control", "performance", "post_match",
      "prediction_history", "pre_match_rec", "model_stats",
      "broadcast",
    ];
    for (const key of requiredKeys) {
      expect(wsPayload, `Missing key: ${key}`).toHaveProperty(key);
    }
  });

  test("WebSocket meta section has correct structure", async ({ page }) => {
    const wsPayload = await getWsPayload(page);
    const meta = wsPayload.meta;
    expect(meta).toHaveProperty("match_id");
    expect(meta).toHaveProperty("source");
    expect(meta).toHaveProperty("last_update_ts");
    expect(meta).toHaveProperty("health");
    expect(meta).toHaveProperty("seq");
    expect(typeof meta.seq).toBe("number");
    expect(meta.seq).toBeGreaterThan(0);
  });

  test("WebSocket probability values are valid percentages", async ({ page }) => {
    const wsPayload = await getWsPayload(page);
    const prob = wsPayload.probability;
    expect(prob.home).toBeGreaterThanOrEqual(0);
    expect(prob.home).toBeLessThanOrEqual(100);
    expect(prob.draw).toBeGreaterThanOrEqual(0);
    expect(prob.draw).toBeLessThanOrEqual(100);
    expect(prob.away).toBeGreaterThanOrEqual(0);
    expect(prob.away).toBeLessThanOrEqual(100);
    const sum = prob.home + prob.draw + prob.away;
    expect(sum).toBeGreaterThan(95);
    expect(sum).toBeLessThan(105);
  });

  test("WebSocket stats arrays have correct shape [home, away]", async ({ page }) => {
    const wsPayload = await getWsPayload(page);
    const stats = wsPayload.stats;
    for (const key of ["shots", "shots_on_target", "possession", "corners", "fouls", "yellow_cards", "red_cards"]) {
      expect(stats[key], `stats.${key}`).toBeDefined();
      expect(Array.isArray(stats[key]), `stats.${key} not array`).toBe(true);
      expect(stats[key].length, `stats.${key} length`).toBe(2);
    }
  });

  test("WebSocket total_goals has lambda and signal data", async ({ page }) => {
    const wsPayload = await getWsPayload(page);
    const tg = wsPayload.total_goals;
    expect(tg).toHaveProperty("lambda_pre");
    expect(tg).toHaveProperty("lambda_live");
    expect(tg).toHaveProperty("lambda_remaining");
    expect(tg).toHaveProperty("line");
    expect(tg).toHaveProperty("model_prob_over");
    expect(tg).toHaveProperty("final_prob_over");
    expect(tg).toHaveProperty("edge");
    expect(tg).toHaveProperty("signal");
    expect(tg).toHaveProperty("tempo_index");
    expect(tg).toHaveProperty("scanner");
    expect(typeof tg.lambda_live).toBe("number");
    expect(tg.lambda_live).toBeGreaterThan(0);
  });

  test("WebSocket connection opens and stays alive", async ({ page }) => {
    const result = await page.evaluate(() => {
      return new Promise((resolve) => {
        const timeout = setTimeout(() => resolve({ opened: false }), 25000);
        fetch("/api/matches/live")
          .then((r) => r.json())
          .then((matches) => {
            const matchId = matches[0]?.match_id || "demo";
            const proto = location.protocol === "https:" ? "wss:" : "ws:";
            const ws = new WebSocket(`${proto}//${location.host}/ws/${matchId}`);
            ws.onopen = () => {
              // Connection opened — wait 3s to verify it stays open
              setTimeout(() => {
                const alive = ws.readyState === WebSocket.OPEN;
                clearTimeout(timeout);
                ws.close();
                resolve({ opened: true, stayedAlive: alive });
              }, 3000);
            };
            ws.onerror = () => {
              clearTimeout(timeout);
              resolve({ opened: false, error: true });
            };
          });
      });
    });
    expect(result.opened).toBe(true);
    expect(result.stayedAlive).toBe(true);
  });
});
