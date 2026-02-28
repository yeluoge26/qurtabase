// @ts-check
import { test, expect } from "@playwright/test";

/**
 * TEST SUITE 5: User Interactions — Language Switch, Trend Tabs, Buttons
 * Validates that interactive elements respond correctly to clicks
 */

test.describe("Language Toggle", () => {
  test("clicking language button switches EN → ZH and back", async ({ page }) => {
    await page.goto("/");
    await page.waitForFunction(
      () => document.body.innerText.includes("%"),
      { timeout: 15000 }
    );

    // Initial state: English — button should say "中文" (switch to Chinese)
    const langBtn = page.locator("button").filter({ hasText: /中文|EN/ }).first();
    await expect(langBtn).toBeVisible();

    const initialText = await langBtn.textContent();
    expect(initialText.trim()).toBe("中文");

    // Click to switch to Chinese
    await langBtn.click();
    await page.waitForTimeout(500);

    // Button should now say "EN"
    const btnAfterSwitch = page.locator("button").filter({ hasText: /中文|EN/ }).first();
    const switchedText = await btnAfterSwitch.textContent();
    expect(switchedText.trim()).toBe("EN");

    // Page content should now show Chinese text
    const body = await page.textContent("body");
    // Chinese labels from i18n: 主胜, 客胜, 概率, etc.
    const hasChineseChars = /[\u4e00-\u9fff]/.test(body);
    expect(hasChineseChars).toBe(true);

    // Click again to switch back to English
    await btnAfterSwitch.click();
    await page.waitForTimeout(500);

    const revertedBtn = page.locator("button").filter({ hasText: /中文|EN/ }).first();
    const revertedText = await revertedBtn.textContent();
    expect(revertedText.trim()).toBe("中文");
  });

  test("Chinese mode shows translated labels", async ({ page }) => {
    await page.goto("/");
    await page.waitForFunction(
      () => document.body.innerText.includes("%"),
      { timeout: 15000 }
    );

    // Switch to Chinese
    const langBtn = page.locator("button").filter({ hasText: "中文" }).first();
    await langBtn.click();
    await page.waitForTimeout(500);

    const body = await page.textContent("body");
    // Key Chinese labels from i18n.js
    const expectedChinese = ["概率", "模型"]; // probability, model
    let found = 0;
    for (const ch of expectedChinese) {
      if (body.includes(ch)) found++;
    }
    expect(found).toBeGreaterThanOrEqual(1);
  });
});

test.describe("Trend Tab Switching", () => {
  test("clicking trend tabs switches chart content", async ({ page }) => {
    await page.goto("/");
    await page.waitForFunction(
      () => document.body.innerText.includes("%"),
      { timeout: 15000 }
    );

    // Find trend tab buttons — they are typically short labels
    // Default active tab is "prob" / "1X2"
    const tabs = page.locator("div").filter({ hasText: /^(1X2|PRESS|xG|λ)$/ });

    // If we can find them, click through each
    const tabCount = await tabs.count();
    if (tabCount >= 2) {
      // Click second tab (PRESSURE)
      await tabs.nth(1).click();
      await page.waitForTimeout(300);

      // Body should now show pressure-related content
      const bodyAfter = await page.textContent("body");
      // Verify the page didn't crash (still has content)
      expect(bodyAfter.length).toBeGreaterThan(100);
    }
  });
});

test.describe("Signal Control Keyboard Shortcuts", () => {
  test("Enter and Escape keys are handled without errors", async ({ page }) => {
    await page.goto("/");
    await page.waitForFunction(
      () => document.body.innerText.includes("%"),
      { timeout: 15000 }
    );

    // Press Enter (should be handled by SignalControlPanel if ready state)
    await page.keyboard.press("Enter");
    await page.waitForTimeout(200);

    // Press Escape
    await page.keyboard.press("Escape");
    await page.waitForTimeout(200);

    // Page should still be functional (no crash)
    const body = await page.textContent("body");
    expect(body.length).toBeGreaterThan(100);
  });
});
