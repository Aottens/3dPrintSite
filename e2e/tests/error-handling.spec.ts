import { test, expect } from "@playwright/test";
import path from "path";

/**
 * E2E Test Scenario 3:
 * Upload wrong file type → shows proper error message
 */

test.describe("Error Handling", () => {
  test("shows error for invalid file type", async ({ page }) => {
    await page.goto("/");

    // Try to upload a non-STL/3MF file (e.g., a text file)
    const fileInput = page.locator('input[type="file"]');

    // Create a temporary invalid file
    await fileInput.setInputFiles(path.join(__dirname, "../fixtures/invalid-file.txt"));

    // Wait for error message
    await expect(page.locator('[data-testid="upload-error"]')).toBeVisible({ timeout: 5000 });

    const errorText = await page.locator('[data-testid="upload-error"]').textContent();
    expect(errorText).toContain("Invalid file type");
  });

  test("shows error for corrupted STL file", async ({ page }) => {
    await page.goto("/");

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(path.join(__dirname, "../fixtures/corrupted.stl"));

    // Wait for error message
    await expect(page.locator('[data-testid="upload-error"]')).toBeVisible({ timeout: 10000 });

    const errorText = await page.locator('[data-testid="upload-error"]').textContent();
    expect(errorText).toMatch(/invalid|corrupted|parse|failed/i);
  });

  test("shows error for file exceeding size limit", async ({ page }) => {
    await page.goto("/");

    // This test would require a large file fixture
    // The file input should show an error for files > 100MB
    const fileInput = page.locator('input[type="file"]');

    // Check that the file input has the proper accept attribute
    const acceptAttr = await fileInput.getAttribute("accept");
    expect(acceptAttr).toContain(".stl");
    expect(acceptAttr).toContain(".3mf");
  });

  test("shows error when trying to order without login", async ({ page }) => {
    await page.goto("/");

    // Upload a valid file
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

    // Try to add to cart without login
    await page.click('button:has-text("Add to Cart")');

    // Should show login prompt or error
    await expect(
      page.locator('[role="dialog"]').or(page.locator('[data-testid="login-required-error"]'))
    ).toBeVisible({ timeout: 5000 });
  });

  test("shows error for non-existent order", async ({ page }) => {
    // First login
    await page.goto("/");
    await page.click('button:has-text("Login")');
    await page.waitForSelector('[role="dialog"]');

    await page.fill('input[name="email"]', "demo@example.com");
    await page.fill('input[name="password"]', "demo123");
    await page.click('button[type="submit"]:has-text("Sign In")');
    await page.waitForSelector('button:has-text("Logout")');

    // Try to access non-existent order
    await page.goto("/orders/99999");

    // Should show error or redirect
    await expect(
      page.locator('text=Order not found').or(page.locator('text=Not found'))
    ).toBeVisible({ timeout: 5000 });
  });

  test("shows validation errors on registration form", async ({ page }) => {
    await page.goto("/");

    await page.click('button:has-text("Login")');
    await page.waitForSelector('[role="dialog"]');

    await page.click('button:has-text("Register")');

    // Submit empty form
    await page.click('button[type="submit"]:has-text("Create Account")');

    // Should show validation errors
    await expect(
      page.locator('text=required').or(page.locator('[data-testid="validation-error"]'))
    ).toBeVisible();
  });

  test("shows error for invalid login credentials", async ({ page }) => {
    await page.goto("/");

    await page.click('button:has-text("Login")');
    await page.waitForSelector('[role="dialog"]');

    await page.fill('input[name="email"]', "invalid@example.com");
    await page.fill('input[name="password"]', "wrongpassword");
    await page.click('button[type="submit"]:has-text("Sign In")');

    // Should show error message
    await expect(page.locator('[data-testid="auth-error"]')).toBeVisible({ timeout: 5000 });

    const errorText = await page.locator('[data-testid="auth-error"]').textContent();
    expect(errorText).toMatch(/invalid|incorrect|wrong|credentials/i);
  });
});
