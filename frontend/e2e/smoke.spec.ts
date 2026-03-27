import { test, expect } from "@playwright/test";

test.describe("Application Smoke Tests", () => {
  test("home page loads and shows navigation", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("h1")).toContainText("FlowCyt");
    await expect(page.getByRole("link", { name: /Experimental Design/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /Panel Generation/i })).toBeVisible();
  });

  test("experimental design page loads with form elements", async ({ page }) => {
    await page.goto("/exp-design");
    await expect(page.locator("h1")).toContainText("Experimental Design");
    await expect(page.getByPlaceholder(/experimental goal/i)).toBeVisible();
  });

  test("panel design page loads with form elements", async ({ page }) => {
    await page.goto("/panel-design");
    await expect(page.locator("h1")).toContainText("Panel");
    await expect(page.getByPlaceholder(/marker/i)).toBeVisible();
  });

  test("navigation between pages works", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: /Panel Generation/i }).first().click();
    await expect(page).toHaveURL(/\/panel-design/);
    await page.getByRole("link", { name: /home/i }).first().click();
    await expect(page).toHaveURL(/\/$/);
  });
});
