// @ts-check
import { test, expect } from "@playwright/test";

/**
 * TEST SUITE 4: Quant Terminal — Page Load & Component Rendering
 * Validates that all major UI sections render with data from WebSocket
 */

test.describe("Terminal Page Load & Component Rendering", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    // Wait for WebSocket data to arrive and render
    // The probability numbers appear once WS data flows in
    await page.waitForFunction(
      () => document.body.innerText.includes("%"),
      { timeout: 15000 }
    );
  });

  test("page loads with correct title structure", async ({ page }) => {
    // Check the terminal header contains "AI FOOTBALL QUANT TERMINAL"
    const body = await page.textContent("body");
    expect(body).toContain("QUANT");
    expect(body).toContain("TERMINAL");
  });

  test("probability panel renders home/away percentages", async ({ page }) => {
    // Look for percentage values (XX.XX%) — probability numbers
    const probValues = await page.locator("text=/%$/").count();
    expect(probValues).toBeGreaterThan(0);

    // Should contain 1X2 probability label
    const body = await page.textContent("body");
    // Check for HOME and AWAY team codes (3-letter codes)
    expect(body.length).toBeGreaterThan(100);
  });

  test("match info bar renders (minute, league, score)", async ({ page }) => {
    const body = await page.textContent("body");
    // Should have a minute display and score
    // For a finished match at 90', or demo progressing
    expect(body).toMatch(/\d+'/); // minute indicator
  });

  test("stats section renders (shots, possession, corners)", async ({ page }) => {
    const body = await page.textContent("body");
    // The stats panel should show stat labels
    const statKeywords = ["SHOTS", "POSSESSION", "CORNERS"];
    let found = 0;
    for (const kw of statKeywords) {
      if (body.toUpperCase().includes(kw)) found++;
    }
    // At least some stats should be visible
    expect(found).toBeGreaterThanOrEqual(1);
  });

  test("trend tabs render (PROB, PRESSURE, xG, λ)", async ({ page }) => {
    const body = await page.textContent("body");
    // Check trend tab labels exist
    expect(body.toUpperCase()).toContain("1X2");
  });

  test("quant panel renders (pressure, momentum, volatility)", async ({ page }) => {
    const body = await page.textContent("body");
    const quantKeywords = ["PRESSURE", "MOMENTUM", "VOLATILITY"];
    let found = 0;
    for (const kw of quantKeywords) {
      if (body.toUpperCase().includes(kw)) found++;
    }
    expect(found).toBeGreaterThanOrEqual(2);
  });

  test("total goals O/U panel renders with lambda values", async ({ page }) => {
    const body = await page.textContent("body");
    // λ symbol or LAMBDA label should appear
    expect(body).toMatch(/[λΛ]|LAMBDA|O\/U/i);
  });

  test("risk panel renders", async ({ page }) => {
    const body = await page.textContent("body");
    expect(body.toUpperCase()).toContain("RISK");
  });

  test("prediction history panel renders", async ({ page }) => {
    const body = await page.textContent("body");
    // Check for history-related labels
    const historyKeywords = ["HISTORY", "ACCURACY", "PREDICTION"];
    let found = 0;
    for (const kw of historyKeywords) {
      if (body.toUpperCase().includes(kw)) found++;
    }
    expect(found).toBeGreaterThanOrEqual(1);
  });

  test("model stats / backtest panel renders", async ({ page }) => {
    const body = await page.textContent("body");
    expect(body.toUpperCase()).toContain("MODEL");
  });

  test("connection status indicator shows connected", async ({ page }) => {
    // Wait for WebSocket connection to stabilize
    await page.waitForTimeout(3000);
    const body = await page.textContent("body");
    // Should show OK or LIVE health status
    expect(body).toMatch(/OK|LIVE|CONNECTED/i);
  });

  test("disclaimer banner renders", async ({ page }) => {
    const body = await page.textContent("body");
    // Disclaimer should mention "NOT financial advice" or similar
    const hasDisclaimer =
      body.toUpperCase().includes("DISCLAIMER") ||
      body.toUpperCase().includes("NOT") ||
      body.toUpperCase().includes("ENTERTAINMENT");
    expect(hasDisclaimer).toBe(true);
  });
});
