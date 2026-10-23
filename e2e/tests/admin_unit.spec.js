const path = require("path");
const { test, expect } = require("../fixtures");
const { screenshot, shouldContain } = require("../fixtures/helpers");
const { createAdminUnit, createAdminUnitOrganizationInvitation } = require("../fixtures/flask");

test.describe("Admin Unit", () => {
  test("creates", async ({ page, login }) => {
    await login();
    await page.goto("/manage/organization/create");
    await page.locator("#name").fill("Second Crew");
    await page.locator("#location-postalCode").fill("38640");
    await page.locator("#location-city").fill("Goslar");
    await screenshot(page, "create");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(/\/manage\/admin_unit\//);
  });

  test("creates from invitation", async ({ page, login }) => {
    await login();

    const adminUnitId = createAdminUnit();
    const invitationId = createAdminUnitOrganizationInvitation(adminUnitId, "test@test.de");
    await page.goto(`/manage/organization/create?invitation_id=${invitationId}`);

    await expect(page.locator("#name")).toHaveValue("Invited Organization");
    await expect(page.locator("#short_name")).toHaveValue("invitedorganization");
    await expect(page.locator("#short_name")).toHaveClass(/is-valid/);

    await page.locator("#location-postalCode").fill("38640");
    await page.locator("#location-city").fill("Goslar");
    await screenshot(page, "create");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(/\/manage\/admin_unit\//);
  });

  test("updates", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(`/manage/admin_unit/${adminUnitId}/update`);
    await expect(page.locator("#name")).not.toHaveValue("");
    await screenshot(page, "update");

    await page.locator("#name").fill("Renamed Crew");
    await page.locator("#location-postalCode").fill("38640");
    await page.locator("#location-city").fill("Goslar");

    // Logo: choose a file, crop it, give the copyright.
    await page.locator("input[type=file]").setInputFiles(
      path.join(__dirname, "..", "..", "project", "presentation", "web", "static", "android-chrome-512x512.png")
    );
    await page.locator(".cropper-container").waitFor();
    await page.locator(".modal-footer .btn-primary").click();
    await expect(page.locator("[data-test=preview]")).toBeVisible();
    await page.locator("#logo-copyright_text").fill("Logo by Crew");

    await page.locator("#submit").click();
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/update`));
    await shouldContain(page.locator(".toast"), "Organisation erfolgreich aktualisiert");
    await expect(page.locator("#name")).toHaveValue("Renamed Crew");
    await expect(page.locator("[data-test=preview]")).toBeVisible();
  });

  test("update shows a taken name", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createAdminUnit("test@test.de", "Other Crew");
    await page.goto(`/manage/admin_unit/${adminUnitId}/update`);
    await expect(page.locator("#name")).not.toHaveValue("");

    await page.locator("#name").fill("Other Crew");
    await expect(page.locator("#name")).toHaveClass(/is-invalid/);
    await page.locator("#submit").click();
    await expect(page.locator("#name")).toHaveClass(/is-invalid/);
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/update`));
  });

  test("widgets", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(`/manage/admin_unit/${adminUnitId}/widgets`);
    await screenshot(page, "widgets");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/widgets`));
    await shouldContain(page.locator("div.alert"), "Einstellungen erfolgreich aktualisiert");
  });
});
