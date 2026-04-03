import { test, expect } from "@playwright/test";

test.describe("Antibody Quality Registry", () => {
  test("page renders with tabs and form elements", async ({ page }) => {
    // Mock the GET issues endpoint to return empty list
    await page.route("**/quality-registry/issues**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
    });

    await page.goto("/quality-registry");

    // Verify page title
    await expect(page.locator("h1")).toContainText("Antibody Quality Registry");

    // Verify three tabs exist
    await expect(page.getByText("Register")).toBeVisible();
    await expect(page.getByText("Issue History")).toBeVisible();
    await expect(page.getByText("Review Queue")).toBeVisible();

    // Verify registration form fields are visible
    await expect(page.getByTestId("quality-issue-textarea")).toBeVisible();
    await expect(page.getByTestId("quality-reporter-input")).toBeVisible();
    await expect(page.getByTestId("quality-species-select")).toBeVisible();
    await expect(page.getByTestId("quality-marker-input")).toBeVisible();
    await expect(page.getByTestId("quality-fluorochrome-input")).toBeVisible();
    await expect(page.getByTestId("quality-brand-input")).toBeVisible();
  });

  test("form validation shows errors for required fields", async ({ page }) => {
    // Mock the GET issues endpoint to return empty list
    await page.route("**/quality-registry/issues**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
    });

    await page.goto("/quality-registry");

    // Click submit without filling any fields
    await page.getByTestId("quality-submit-btn").click();

    // Verify validation errors appear for issue_text and reported_by
    await expect(page.getByText("Please describe the observed quality issue.")).toBeVisible();
    await expect(page.getByText("Reporter name is required.")).toBeVisible();
  });

  test("successful submission switches to issue history tab", async ({ page }) => {
    const mockIssueResponse = {
      id: "issue-test-001",
      feedback_key: {
        species: "Human (人)",
        normalized_marker: "cd3",
        fluorochrome: "PE",
        brand: "BioLegend",
        clone: null,
      },
      entity_key: null,
      issue_text: "High background staining observed",
      reported_by: "Test User",
      status: "submitted",
      created_at: "2025-01-15T10:30:00Z",
      updated_at: "2025-01-15T10:30:00Z",
    };

    // Mock GET issues endpoint (initial load + post-submit refresh)
    await page.route("**/quality-registry/issues**", async (route) => {
      const url = route.request().url();
      // After submission, return the issue; before submission, return empty
      if (url.includes("status=")) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([]),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([mockIssueResponse]),
        });
      }
    });

    // Mock POST create issue endpoint
    await page.route("**/quality-registry/issues", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockIssueResponse),
        });
      } else {
        await route.continue();
      }
    });

    // Mock candidate lookup (return no candidates)
    await page.route("**/quality-registry/candidates/lookup**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ candidates: [] }),
      });
    });

    // Mock history endpoint
    await page.route("**/quality-registry/issues/*/history**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
    });

    await page.goto("/quality-registry");

    // Fill in form fields
    await page.getByTestId("quality-issue-textarea").fill("High background staining observed");
    await page.getByTestId("quality-reporter-input").fill("Test User");
    await page.getByTestId("quality-species-select").selectOption("Human (人)");
    await page.getByTestId("quality-marker-input").fill("CD3");
    await page.getByTestId("quality-fluorochrome-input").fill("PE");
    await page.getByTestId("quality-brand-input").fill("BioLegend");

    // Click submit
    await page.getByTestId("quality-submit-btn").click();

    // Verify tab switches to "Issue History"
    await expect(page.getByTestId("quality-history-tab")).toHaveAttribute("data-state", "active");

    // Verify the issue appears in the list
    await expect(page.getByTestId("quality-issues-list")).toBeVisible();
    await expect(page.locator("text=cd3")).toBeVisible();
    await expect(page.locator("text=PE")).toBeVisible();
    await expect(page.locator("text=BioLegend")).toBeVisible();
  });
});
