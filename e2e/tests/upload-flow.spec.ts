import { test, expect } from "@playwright/test";
import path from "path";

/**
 * E2E Test Scenario 1:
 * Upload STL → select FDM → select material → select profile → price appears → create order → order visible
 */

test.describe("Upload and Order Flow", () => {
  const testUser = {
    email: `test-${Date.now()}@example.com`,
    name: "Test User",
    password: "testpassword123",
  };

  test.beforeEach(async ({ page }) => {
    // Register a new user for testing
    await page.goto("/");

    // Open auth modal
    await page.click('button:has-text("Login")');
    await page.waitForSelector('[role="dialog"]');

    // Switch to register tab
    await page.click('button:has-text("Register")');

    // Fill registration form
    await page.fill('input[name="name"]', testUser.name);
    await page.fill('input[name="email"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);

    // Submit
    await page.click('button[type="submit"]:has-text("Create Account")');

    // Wait for auth to complete
    await page.waitForSelector('button:has-text("Logout")');
  });

  test("complete upload to order flow", async ({ page }) => {
    // Step 1: Upload an STL file
    await page.goto("/");

    // Find the file upload input
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(path.join(__dirname, "../fixtures/test-cube.stl"));

    // Wait for file to be processed
    await page.waitForSelector('[data-testid="model-metrics"]', { timeout: 30000 });

    // Verify metrics are displayed
    await expect(page.locator('[data-testid="volume-value"]')).toBeVisible();
    await expect(page.locator('[data-testid="surface-area-value"]')).toBeVisible();

    // Step 2: Select FDM technology
    await page.click('button:has-text("FDM")');

    // Step 3: Select a material
    const materialSelect = page.locator('[data-testid="material-select"]');
    await materialSelect.click();
    await page.click('text=PLA Standard');

    // Step 4: Select a color
    const colorSelect = page.locator('[data-testid="color-select"]');
    await colorSelect.click();
    await page.click('text=Black');

    // Step 5: Select a profile
    const profileSelect = page.locator('[data-testid="profile-select"]');
    await profileSelect.click();
    await page.click('text=Standard');

    // Step 6: Verify price appears
    await expect(page.locator('[data-testid="price-breakdown"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-price"]')).toBeVisible();

    const priceText = await page.locator('[data-testid="total-price"]').textContent();
    expect(priceText).toMatch(/€\s*\d+[.,]\d{2}/);

    // Step 7: Add to cart
    await page.click('button:has-text("Add to Cart")');

    // Step 8: Go to cart/checkout
    await page.click('button:has-text("Cart")');
    await expect(page.locator('[data-testid="cart-items"]')).toBeVisible();

    // Step 9: Create order
    await page.click('button:has-text("Place Order")');

    // Wait for order confirmation
    await page.waitForSelector('[data-testid="order-confirmation"]', { timeout: 10000 });

    // Step 10: Verify order is visible in account
    await page.goto("/account");
    await expect(page.locator('[data-testid="orders-list"]')).toBeVisible();

    // Verify order appears in the list
    const orderRow = page.locator('[data-testid="order-row"]').first();
    await expect(orderRow).toBeVisible();
    await expect(orderRow).toContainText("New");
  });

  test("model preview is displayed after upload", async ({ page }) => {
    await page.goto("/");

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(path.join(__dirname, "../fixtures/test-cube.stl"));

    // Wait for 3D preview to load
    await page.waitForSelector('[data-testid="model-viewer"]', { timeout: 30000 });

    // Verify the canvas is rendered
    await expect(page.locator("canvas")).toBeVisible();
  });
});
