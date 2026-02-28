// @ts-check
import { test, expect } from "@playwright/test";

/**
 * TEST SUITE 2: Admin CRUD — Add / Toggle / Delete matches via API
 * Tests the full lifecycle of match management and data persistence
 */

const TEST_MATCH = {
  match_id: "test_pw_001",
  league: "TEST_LEAGUE",
  round: "R1",
  home_name: "PW Home FC",
  away_name: "PW Away United",
  home_short: "PHF",
  away_short: "PAU",
  home_name_cn: "测试主队",
  away_name_cn: "测试客队",
  home_elo: 1600,
  away_elo: 1450,
  api_football_id: "",
  odds_sport: "soccer_epl",
  active: true,
  kickoff: "",
  status: "",
  live_enabled: false,
};

test.describe("Admin CRUD Operations", () => {
  // Clean up any leftover test match before starting
  test.beforeAll(async ({ request }) => {
    await request.delete(`/api/admin/matches/${TEST_MATCH.match_id}`);
  });

  test.afterAll(async ({ request }) => {
    await request.delete(`/api/admin/matches/${TEST_MATCH.match_id}`);
  });

  test("POST /api/admin/matches creates a new match", async ({ request }) => {
    const resp = await request.post("/api/admin/matches", { data: TEST_MATCH });
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data.status).toBe("ok");
    expect(data.match_id).toBe(TEST_MATCH.match_id);

    // Verify it's in the list
    const listResp = await request.get("/api/admin/matches");
    const list = await listResp.json();
    const found = list.find((m) => m.match_id === TEST_MATCH.match_id);
    expect(found).toBeTruthy();
    expect(found.league).toBe("TEST_LEAGUE");
    expect(found.home_name).toBe("PW Home FC");
    expect(found.away_name).toBe("PW Away United");
    expect(found.home_elo).toBe(1600);
    expect(found.away_elo).toBe(1450);
    expect(found.active).toBe(true);
  });

  test("PUT toggle active state flips correctly", async ({ request }) => {
    // Deactivate
    const resp1 = await request.put(`/api/admin/matches/${TEST_MATCH.match_id}/toggle`);
    expect(resp1.status()).toBe(200);
    const d1 = await resp1.json();
    expect(d1.active).toBe(false);

    // Activate again
    const resp2 = await request.put(`/api/admin/matches/${TEST_MATCH.match_id}/toggle`);
    expect(resp2.status()).toBe(200);
    const d2 = await resp2.json();
    expect(d2.active).toBe(true);
  });

  test("PUT toggle live streaming flips correctly", async ({ request }) => {
    // Enable streaming
    const resp1 = await request.put(`/api/admin/matches/${TEST_MATCH.match_id}/live`);
    expect(resp1.status()).toBe(200);
    const d1 = await resp1.json();
    expect(d1.live_enabled).toBe(true);

    // Disable streaming
    const resp2 = await request.put(`/api/admin/matches/${TEST_MATCH.match_id}/live`);
    expect(resp2.status()).toBe(200);
    const d2 = await resp2.json();
    expect(d2.live_enabled).toBe(false);
  });

  test("POST duplicate match_id updates existing entry", async ({ request }) => {
    const updated = { ...TEST_MATCH, league: "UPDATED_LEAGUE", home_elo: 1700 };
    const resp = await request.post("/api/admin/matches", { data: updated });
    expect(resp.status()).toBe(200);

    // Verify update
    const listResp = await request.get("/api/admin/matches");
    const list = await listResp.json();
    const found = list.find((m) => m.match_id === TEST_MATCH.match_id);
    expect(found.league).toBe("UPDATED_LEAGUE");
    expect(found.home_elo).toBe(1700);
  });

  test("DELETE /api/admin/matches/{id} removes match", async ({ request }) => {
    const resp = await request.delete(`/api/admin/matches/${TEST_MATCH.match_id}`);
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data.status).toBe("ok");

    // Verify removal
    const listResp = await request.get("/api/admin/matches");
    const list = await listResp.json();
    const found = list.find((m) => m.match_id === TEST_MATCH.match_id);
    expect(found).toBeFalsy();
  });

  test("DELETE non-existent match succeeds silently", async ({ request }) => {
    const resp = await request.delete("/api/admin/matches/nonexistent_999");
    // Backend returns 200 even for non-existent (idempotent delete)
    expect(resp.status()).toBe(200);
  });

  test("PUT toggle non-existent match returns 404", async ({ request }) => {
    const resp = await request.put("/api/admin/matches/nonexistent_999/toggle");
    expect(resp.status()).toBe(404);
  });
});
