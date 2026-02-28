// @ts-check
import { test, expect } from "@playwright/test";

/**
 * TEST SUITE 7: Signal Control & Performance Tracking
 */

test.describe("Signal Control API", () => {
  test("GET /api/signal/state returns valid structure", async ({ request }) => {
    const resp = await request.get("/api/signal/state?match_id=demo");
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data.status).toBe("ok");

    const ss = data.signal_state;
    expect(ss).toHaveProperty("state");
    expect(ss).toHaveProperty("line");
    expect(ss).toHaveProperty("model_prob");
    expect(ss).toHaveProperty("market_prob");
    expect(ss).toHaveProperty("edge");
    expect(ss).toHaveProperty("cooldown_remaining");
    expect(typeof ss.line).toBe("number");
    expect(typeof ss.edge).toBe("number");
  });

  test("POST /api/signal/confirm with confirm action responds correctly", async ({ request }) => {
    const resp = await request.post("/api/signal/confirm", {
      headers: { "Content-Type": "application/json" },
      data: JSON.stringify({ match_id: "demo", action: "confirm" }),
    });
    // 200 if in ready state, 400 if not in ready state
    expect([200, 400]).toContain(resp.status());
    const data = await resp.json();
    // Either {status: "ok", signal_state: ...} or {detail: "..."}
    expect(data).toBeDefined();
  });

  test("POST /api/signal/confirm with reject action responds correctly", async ({ request }) => {
    const resp = await request.post("/api/signal/confirm", {
      headers: { "Content-Type": "application/json" },
      data: JSON.stringify({ match_id: "demo", action: "reject" }),
    });
    expect([200, 400]).toContain(resp.status());
  });

  test("POST /api/signal/confirm with invalid action returns 400", async ({ request }) => {
    const resp = await request.post("/api/signal/confirm", {
      headers: { "Content-Type": "application/json" },
      data: JSON.stringify({ match_id: "demo", action: "invalid_action" }),
    });
    expect(resp.status()).toBe(400);
  });
});

test.describe("Performance Tracker", () => {
  test("GET /api/performance returns valid summary", async ({ request }) => {
    const resp = await request.get("/api/performance");
    expect(resp.status()).toBe(200);
    const data = await resp.json();

    expect(data).toHaveProperty("total_signals");
    expect(data).toHaveProperty("wins");
    expect(data).toHaveProperty("losses");
    expect(data).toHaveProperty("pending");
    expect(data).toHaveProperty("roi_pct");
    expect(data).toHaveProperty("best_edge");
    expect(data).toHaveProperty("avg_edge");
    expect(data).toHaveProperty("signals");
    expect(Array.isArray(data.signals)).toBe(true);
    expect(typeof data.total_signals).toBe("number");
    expect(typeof data.roi_pct).toBe("number");
  });
});
