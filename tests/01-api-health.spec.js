// @ts-check
import { test, expect } from "@playwright/test";

/**
 * TEST SUITE 1: Backend API Health & Endpoints
 * Validates all REST API endpoints respond correctly
 */

test.describe("Backend API Endpoints", () => {
  test("GET /api/health returns valid status", async ({ request }) => {
    const resp = await request.get("/api/health");
    expect(resp.status()).toBe(200);
    const data = await resp.json();

    expect(data).toHaveProperty("status", "ok");
    expect(data).toHaveProperty("version");
    expect(data).toHaveProperty("demo_mode");
    expect(data).toHaveProperty("model_loaded");
    expect(data).toHaveProperty("active_matches");
    expect(data).toHaveProperty("live_matches");
    expect(data).toHaveProperty("ws_connections");
    expect(data).toHaveProperty("live_source");
    expect(data).toHaveProperty("has_odds");
    expect(data).toHaveProperty("timestamp");
    expect(typeof data.timestamp).toBe("number");
    expect(data.timestamp).toBeGreaterThan(0);
  });

  test("GET /api/matches/live returns match list", async ({ request }) => {
    const resp = await request.get("/api/matches/live");
    expect(resp.status()).toBe(200);
    const data = await resp.json();

    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBeGreaterThan(0);

    const match = data[0];
    expect(match).toHaveProperty("match_id");
    expect(match).toHaveProperty("active", true);
    // mode should be one of: live, finished, demo
    expect(["live", "finished", "demo"]).toContain(match.mode);
  });

  test("GET /api/admin/matches returns managed list", async ({ request }) => {
    const resp = await request.get("/api/admin/matches");
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(Array.isArray(data)).toBe(true);
  });

  test("GET /api/performance returns track record", async ({ request }) => {
    const resp = await request.get("/api/performance");
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data).toHaveProperty("total_signals");
    expect(data).toHaveProperty("wins");
    expect(data).toHaveProperty("losses");
    expect(data).toHaveProperty("roi_pct");
  });

  test("GET /api/signal/state returns signal state", async ({ request }) => {
    const resp = await request.get("/api/signal/state?match_id=demo");
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data).toHaveProperty("status", "ok");
    expect(data).toHaveProperty("signal_state");
    expect(data.signal_state).toHaveProperty("state");
    expect(["idle", "ready", "confirmed", "cooldown"]).toContain(data.signal_state.state);
  });
});
