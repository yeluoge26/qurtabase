// @ts-check
import { test, expect } from "@playwright/test";

/**
 * TEST SUITE 6: Admin Panel — Tab navigation, form submission, match management UI
 */

test.describe("Admin Panel Page Load", () => {
  test("admin page loads with correct title and health dashboard", async ({ page }) => {
    await page.goto("/admin/");
    await page.waitForLoadState("networkidle");

    const title = await page.title();
    expect(title).toContain("Admin");

    // Wait for health data to load
    await page.waitForTimeout(2000);

    // Health dashboard should show STATUS text in the DOM
    const healthEl = page.locator("#health");
    const healthText = await healthEl.textContent();
    expect(healthText.toUpperCase()).toContain("STATUS");
  });

  test("health dashboard shows live metrics from API", async ({ page }) => {
    await page.goto("/admin/");
    await page.waitForTimeout(3000);

    const healthEl = page.locator("#health");
    const healthText = await healthEl.textContent();
    // Should show OK status and LIVE/DEMO mode
    expect(healthText).toMatch(/OK/i);
    expect(healthText).toMatch(/LIVE|DEMO/i);
  });
});

test.describe("Admin Tab Navigation", () => {
  test("clicking MATCHES tab shows matches panel", async ({ page }) => {
    await page.goto("/admin/");
    await page.waitForLoadState("networkidle");

    const matchesTab = page.locator(".tab").filter({ hasText: "MATCHES" });
    await matchesTab.click();
    await page.waitForTimeout(500);

    await expect(matchesTab).toHaveClass(/active/);
    const matchesPanel = page.locator("#panel-matches");
    await expect(matchesPanel).toHaveClass(/active/);
  });

  test("clicking ADD MATCH tab shows form", async ({ page }) => {
    await page.goto("/admin/");
    await page.waitForLoadState("networkidle");

    const addTab = page.locator(".tab").filter({ hasText: "ADD MATCH" });
    await addTab.click();
    await page.waitForTimeout(500);

    await expect(addTab).toHaveClass(/active/);
    await expect(page.locator("#f_match_id")).toBeVisible();
    await expect(page.locator("#f_league")).toBeVisible();
    await expect(page.locator("#f_home_name")).toBeVisible();
    await expect(page.locator("#f_away_name")).toBeVisible();
  });

  test("clicking FIXTURES tab shows fixtures panel", async ({ page }) => {
    await page.goto("/admin/");
    await page.waitForLoadState("networkidle");

    const fixturesTab = page.locator(".tab").filter({ hasText: "FIXTURES" });
    await fixturesTab.click();
    await page.waitForTimeout(500);

    await expect(fixturesTab).toHaveClass(/active/);
    await expect(page.locator("#fix_from")).toBeVisible();
    await expect(page.locator("#fix_to")).toBeVisible();
  });

  test("tabs are mutually exclusive (only one panel visible)", async ({ page }) => {
    await page.goto("/admin/");
    await page.waitForLoadState("networkidle");

    await page.locator(".tab").filter({ hasText: "ADD MATCH" }).click();
    await page.waitForTimeout(300);

    const addPanel = page.locator("#panel-add");
    const matchesPanel = page.locator("#panel-matches");
    const fixturesPanel = page.locator("#panel-fixtures");

    await expect(addPanel).toHaveClass(/active/);
    await expect(matchesPanel).not.toHaveClass(/active/);
    await expect(fixturesPanel).not.toHaveClass(/active/);
  });
});

test.describe("Admin Add Match Form", () => {
  const FORM_MATCH_ID = "playwright_form_test";

  test.afterEach(async ({ request }) => {
    await request.delete(`/api/admin/matches/${FORM_MATCH_ID}`);
  });

  test("filling form and clicking ADD creates a match", async ({ page, request }) => {
    await page.goto("/admin/");
    await page.waitForLoadState("networkidle");

    await page.locator(".tab").filter({ hasText: "ADD MATCH" }).click();
    await page.waitForTimeout(300);

    await page.locator("#f_match_id").fill(FORM_MATCH_ID);
    await page.locator("#f_league").fill("Playwright League");
    await page.locator("#f_round").fill("R99");
    await page.locator("#f_home_name").fill("PW Home");
    await page.locator("#f_home_short").fill("PWH");
    await page.locator("#f_away_name").fill("PW Away");
    await page.locator("#f_away_short").fill("PWA");
    await page.locator("#f_home_name_cn").fill("测试主");
    await page.locator("#f_away_name_cn").fill("测试客");

    const addBtn = page.locator("button.primary").filter({ hasText: /ADD|UPDATE/i });
    await addBtn.click();

    await page.waitForTimeout(1500);

    // Verify via API
    const resp = await request.get("/api/admin/matches");
    const list = await resp.json();
    const found = list.find((m) => m.match_id === FORM_MATCH_ID);
    expect(found).toBeTruthy();
    expect(found.league).toBe("Playwright League");
    expect(found.home_name).toBe("PW Home");
    expect(found.away_name).toBe("PW Away");
  });
});

test.describe("Admin Match Actions", () => {
  const ACTION_MATCH_ID = "playwright_action_test";

  test.beforeEach(async ({ request }) => {
    await request.delete(`/api/admin/matches/${ACTION_MATCH_ID}`);
    await request.post("/api/admin/matches", {
      data: {
        match_id: ACTION_MATCH_ID,
        league: "Action Test",
        home_name: "Action Home",
        away_name: "Action Away",
        home_short: "ACH",
        away_short: "ACA",
        active: true,
      },
    });
  });

  test.afterEach(async ({ request }) => {
    await request.delete(`/api/admin/matches/${ACTION_MATCH_ID}`);
  });

  test("toggle active via API changes match state", async ({ request }) => {
    const r1 = await request.put(`/api/admin/matches/${ACTION_MATCH_ID}/toggle`);
    const d1 = await r1.json();
    expect(d1.active).toBe(false);

    const r2 = await request.put(`/api/admin/matches/${ACTION_MATCH_ID}/toggle`);
    const d2 = await r2.json();
    expect(d2.active).toBe(true);
  });

  test("toggle live streaming via API changes state", async ({ request }) => {
    const r1 = await request.put(`/api/admin/matches/${ACTION_MATCH_ID}/live`);
    const d1 = await r1.json();
    expect(d1.live_enabled).toBe(true);

    const r2 = await request.put(`/api/admin/matches/${ACTION_MATCH_ID}/live`);
    const d2 = await r2.json();
    expect(d2.live_enabled).toBe(false);
  });

  test("delete match removes it from admin list", async ({ request }) => {
    const resp = await request.delete(`/api/admin/matches/${ACTION_MATCH_ID}`);
    expect(resp.status()).toBe(200);

    const listResp = await request.get("/api/admin/matches");
    const list = await listResp.json();
    const found = list.find((m) => m.match_id === ACTION_MATCH_ID);
    expect(found).toBeFalsy();
  });
});
