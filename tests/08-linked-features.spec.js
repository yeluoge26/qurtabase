// @ts-check
import { test, expect } from "@playwright/test";

/**
 * TEST SUITE 8: Linked Features & Data Integrity
 */

// Helper: get WS payload from already-navigated page
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
            reject(new Error("WS error"));
          };
        });
    });
  });
}

test.describe("Match Discovery Pipeline", () => {
  const LINK_MATCH_ID = "pw_linked_001";

  test.afterEach(async ({ request }) => {
    await request.delete(`/api/admin/matches/${LINK_MATCH_ID}`);
  });

  test("admin-created active match appears in /api/matches/live", async ({ request }) => {
    await request.post("/api/admin/matches", {
      data: {
        match_id: LINK_MATCH_ID,
        league: "Linked League",
        home_name: "Linked Home",
        away_name: "Linked Away",
        home_short: "LNH",
        away_short: "LNA",
        active: true,
      },
    });

    const liveResp = await request.get("/api/matches/live");
    const liveMatches = await liveResp.json();
    const found = liveMatches.find((m) => m.match_id === LINK_MATCH_ID);
    expect(found).toBeTruthy();
    expect(found.league).toBe("Linked League");
    expect(found.active).toBe(true);
  });

  test("deactivated match does NOT appear in /api/matches/live", async ({ request }) => {
    await request.post("/api/admin/matches", {
      data: {
        match_id: LINK_MATCH_ID,
        league: "Inactive League",
        home_name: "Ghost Home",
        away_name: "Ghost Away",
        home_short: "GHO",
        away_short: "GHA",
        active: true,
      },
    });
    await request.put(`/api/admin/matches/${LINK_MATCH_ID}/toggle`);

    const liveResp = await request.get("/api/matches/live");
    const liveMatches = await liveResp.json();
    const found = liveMatches.find((m) => m.match_id === LINK_MATCH_ID);
    expect(found).toBeFalsy();
  });
});

test.describe("WebSocket ↔ Frontend Data Consistency", () => {
  test("page renders team codes from demo WebSocket data", async ({ page }) => {
    await page.goto("/");
    // Wait for the page to render WS data
    await page.waitForFunction(
      () => document.body.innerText.includes("%"),
      { timeout: 15000 }
    );

    // The frontend defaults to matchId="demo", get demo WS payload
    const wsPayload = await page.evaluate(() => {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error("WS timeout")), 25000);
        const proto = location.protocol === "https:" ? "wss:" : "ws:";
        const ws = new WebSocket(`${proto}//${location.host}/ws/demo`);
        ws.onmessage = (ev) => {
          try {
            const data = JSON.parse(ev.data);
            if (data.match) {
              clearTimeout(timeout);
              ws.close();
              resolve(data);
            }
          } catch {}
        };
        ws.onerror = () => {
          clearTimeout(timeout);
          reject(new Error("WS error"));
        };
      });
    });

    const homeCode = wsPayload.match?.home?.code;
    const awayCode = wsPayload.match?.away?.code;
    const body = await page.textContent("body");

    // Demo match team codes should appear in the rendered page
    if (homeCode) {
      expect(body.toUpperCase()).toContain(homeCode.toUpperCase());
    }
    if (awayCode) {
      expect(body.toUpperCase()).toContain(awayCode.toUpperCase());
    }
  });
});

test.describe("Total Goals Engine Consistency", () => {
  test("lambda values and O/U probabilities are consistent", async ({ page }) => {
    test.setTimeout(60000);
    await page.goto("/");
    const wsPayload = await getWsPayload(page);

    const tg = wsPayload.total_goals;
    const goals = (wsPayload.match.score || "0-0")
      .split("-")
      .reduce((a, b) => a + parseInt(b.trim() || "0"), 0);

    expect(tg.lambda_live).toBeGreaterThanOrEqual(goals - 0.01);

    if (tg.final_prob_over != null && tg.final_prob_under != null) {
      const sum = tg.final_prob_over + tg.final_prob_under;
      expect(sum).toBeGreaterThan(95);
      expect(sum).toBeLessThan(105);
    }

    if (tg.scanner) {
      expect(tg.scanner.length).toBeGreaterThanOrEqual(3);
      for (const line of tg.scanner) {
        const lineSum = line.over_prob + line.under_prob;
        expect(lineSum).toBeGreaterThan(95);
        expect(lineSum).toBeLessThan(105);
      }
    }
  });
});

test.describe("Quant & Risk Engine Consistency", () => {
  test("quant values are within expected ranges", async ({ page }) => {
    await page.goto("/");
    const wsPayload = await getWsPayload(page);

    const q = wsPayload.quant;
    expect(q.pressure_index).toBeGreaterThanOrEqual(5);
    expect(q.pressure_index).toBeLessThanOrEqual(98);
    expect(q.momentum).toBeGreaterThanOrEqual(-50);
    expect(q.momentum).toBeLessThanOrEqual(50);
    expect(q.volatility).toBeGreaterThanOrEqual(0.1);
    expect(q.volatility).toBeLessThanOrEqual(1.5);
    expect(q.confidence).toBeGreaterThanOrEqual(55);
    expect(q.confidence).toBeLessThanOrEqual(98);
  });

  test("risk engine values are within expected ranges", async ({ page }) => {
    await page.goto("/");
    const wsPayload = await getWsPayload(page);

    const risk = wsPayload.risk;
    expect(risk).toHaveProperty("model_variance");
    expect(risk).toHaveProperty("signal_stability");
    expect(risk).toHaveProperty("market_volatility");
    expect(risk.signal_stability).toBeGreaterThanOrEqual(0);
    expect(risk.signal_stability).toBeLessThanOrEqual(100);
    expect(["Low", "Medium", "High"]).toContain(risk.market_volatility);
  });
});

test.describe("Post-Match & Prediction History", () => {
  test("post-match summary has correct structure", async ({ page }) => {
    await page.goto("/");
    const wsPayload = await getWsPayload(page);

    const pm = wsPayload.post_match;
    expect(pm).toBeDefined();
    expect(pm).toHaveProperty("active");
    if (pm.active) {
      expect(pm).toHaveProperty("pre_lambda");
      expect(pm).toHaveProperty("final_goals");
      expect(pm).toHaveProperty("final_score");
      expect(typeof pm.final_goals).toBe("number");
    }
  });

  test("prediction history has correct structure", async ({ page }) => {
    await page.goto("/");
    const wsPayload = await getWsPayload(page);

    const ph = wsPayload.prediction_history;
    expect(ph).toBeDefined();
    expect(ph).toHaveProperty("total_matches");
    expect(ph).toHaveProperty("accuracy_1x2_pct");
    expect(ph).toHaveProperty("accuracy_ou_pct");
    expect(typeof ph.total_matches).toBe("number");
  });

  test("model_stats backtest data has correct structure", async ({ page }) => {
    await page.goto("/");
    const wsPayload = await getWsPayload(page);

    const ms = wsPayload.model_stats;
    if (ms) {
      expect(ms).toHaveProperty("total");
      expect(ms).toHaveProperty("accuracy_1x2");
      expect(ms).toHaveProperty("accuracy_ou");
      expect(typeof ms.total).toBe("number");
    }
  });
});

test.describe("Broadcast System", () => {
  test("broadcast field has valid structure", async ({ page }) => {
    await page.goto("/");
    const wsPayload = await getWsPayload(page);

    const bc = wsPayload.broadcast;
    expect(bc).toBeDefined();
    expect(bc).toHaveProperty("text");
    expect(bc).toHaveProperty("stage");
    expect(bc).toHaveProperty("priority");
    expect(bc).toHaveProperty("speaking");
    expect(typeof bc.speaking).toBe("boolean");
    expect(["normal", "high", "critical"]).toContain(bc.priority);
  });
});
