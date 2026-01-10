import { test, expect } from "@playwright/test";
import path from "path";

/**
 * E2E Test Scenario 2:
 * Admin changes material price → new quote uses new rule set version → price changes
 */

test.describe("Admin Pricing Changes", () => {
  const adminCredentials = {
    email: "admin@novaprint.local",
    password: "admin123",
  };

  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto("/");

    await page.click('button:has-text("Login")');
    await page.waitForSelector('[role="dialog"]');

    await page.fill('input[name="email"]', adminCredentials.email);
    await page.fill('input[name="password"]', adminCredentials.password);
    await page.click('button[type="submit"]:has-text("Sign In")');

    await page.waitForSelector('button:has-text("Logout")');
  });

  test("price changes after updating pricing rule set", async ({ page }) => {
    // Step 1: Upload a file and get initial quote
    await page.goto("/");

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(path.join(__dirname, "../fixtures/test-cube.stl"));

    await page.waitForSelector('[data-testid="model-metrics"]', { timeout: 30000 });

    // Select options
    await page.click('button:has-text("FDM")');

    const materialSelect = page.locator('[data-testid="material-select"]');
    await materialSelect.click();
    await page.click('text=PLA Standard');

    const colorSelect = page.locator('[data-testid="color-select"]');
    await colorSelect.click();
    await page.click('text=Black');

    const profileSelect = page.locator('[data-testid="profile-select"]');
    await profileSelect.click();
    await page.click('text=Standard');

    // Get initial price
    await expect(page.locator('[data-testid="total-price"]')).toBeVisible();
    const initialPrice = await page.locator('[data-testid="total-price"]').textContent();

    // Step 2: Go to admin panel and update pricing
    await page.goto("/admin/pricing");

    // Wait for pricing configurations to load
    await expect(page.locator('[data-testid="pricing-rules-list"]')).toBeVisible();

    // Create a new pricing rule set with higher machine rate
    await page.click('button:has-text("New Rule Set")');
    await page.waitForSelector('[role="dialog"]');

    // Fill in new rule set details
    await page.fill('input[name="version"]', "2.0.0");
    await page.fill('input[name="name"]', "Updated Pricing");

    // Increase machine rate for FDM from 15 to 25 EUR/hour
    await page.fill('input[name="machine_rate_fdm"]', "25");

    await page.click('button:has-text("Save")');

    // Wait for confirmation
    await page.waitForSelector('text=Rule set created successfully');

    // Activate the new rule set
    await page.click('[data-testid="activate-ruleset-2.0.0"]');
    await page.waitForSelector('text=Rule set activated');

    // Step 3: Go back to quote and verify price increased
    await page.goto("/");

    // Re-upload and configure (or refresh existing quote)
    const fileInput2 = page.locator('input[type="file"]');
    await fileInput2.setInputFiles(path.join(__dirname, "../fixtures/test-cube.stl"));

    await page.waitForSelector('[data-testid="model-metrics"]', { timeout: 30000 });

    await page.click('button:has-text("FDM")');

    const materialSelect2 = page.locator('[data-testid="material-select"]');
    await materialSelect2.click();
    await page.click('text=PLA Standard');

    const colorSelect2 = page.locator('[data-testid="color-select"]');
    await colorSelect2.click();
    await page.click('text=Black');

    const profileSelect2 = page.locator('[data-testid="profile-select"]');
    await profileSelect2.click();
    await page.click('text=Standard');

    // Get new price
    await expect(page.locator('[data-testid="total-price"]')).toBeVisible();
    const newPrice = await page.locator('[data-testid="total-price"]').textContent();

    // Verify price has changed (increased)
    expect(newPrice).not.toBe(initialPrice);

    // Extract numeric values for comparison
    const extractPrice = (text: string | null): number => {
      if (!text) return 0;
      const match = text.match(/(\d+[.,]\d{2})/);
      return match ? parseFloat(match[1].replace(",", ".")) : 0;
    };

    const initialNumeric = extractPrice(initialPrice);
    const newNumeric = extractPrice(newPrice);

    expect(newNumeric).toBeGreaterThan(initialNumeric);
  });

  test("admin can view and manage materials", async ({ page }) => {
    await page.goto("/admin/materials");

    // Wait for materials list to load
    await expect(page.locator('[data-testid="materials-list"]')).toBeVisible();

    // Verify materials are displayed
    const materialRows = page.locator('[data-testid="material-row"]');
    await expect(materialRows.first()).toBeVisible();

    // Click on a material to edit
    await materialRows.first().click();
    await page.waitForSelector('[role="dialog"]');

    // Verify edit form is displayed
    await expect(page.locator('input[name="name"]')).toBeVisible();
    await expect(page.locator('input[name="cost_per_kg"]')).toBeVisible();
  });

  test("admin can view orders and update status", async ({ page }) => {
    await page.goto("/admin/orders");

    // Wait for orders list to load
    await expect(page.locator('[data-testid="orders-table"]')).toBeVisible();

    // If there are orders, test status update
    const orderRows = page.locator('[data-testid="order-row"]');
    const orderCount = await orderRows.count();

    if (orderCount > 0) {
      // Click status dropdown on first order
      const statusButton = orderRows.first().locator('[data-testid="status-dropdown"]');
      await statusButton.click();

      // Change status
      await page.click('text=In Planning');

      // Verify status was updated
      await expect(orderRows.first()).toContainText("In Planning");
    }
  });
});
