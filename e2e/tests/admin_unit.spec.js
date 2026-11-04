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
    await expect(page.getByText("Organisation erfolgreich erstellt")).toBeVisible();
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
    await expect(page.locator("#widget_primary_color")).toHaveValue("#007bff");
    await screenshot(page, "widgets");

    await page.locator("#widget_background_color").fill("#eceef0");
    await page.locator("#submit").click();
    await expect(page.locator(".toast")).toContainText("Einstellungen erfolgreich aktualisiert");
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/widgets`));

    await page.reload();
    await expect(page.locator("#widget_background_color")).toHaveValue("#eceef0");

    // The embed instructions are a modal with two tabs.
    await page.locator("[data-test=embed]").click();
    await expect(page.locator("[data-test=head-snippet]")).toBeVisible();
    await expect(page.locator("[data-test=body-snippet]")).toHaveValue(
      new RegExp(`data-widget-organization-id="${adminUnitId}"`)
    );
    await screenshot(page, "widgets-embed");
    await page.getByRole("tab", { name: "Alternative iFrame" }).click();
    await expect(page.locator("[data-test=iframe-snippet]")).toHaveValue(
      new RegExp(`/organizations/${adminUnitId}/widget/eventdates`)
    );
    await screenshot(page, "widgets-embed-iframe");
  });

  test("requests and cancels the deletion", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    await page.goto(`/manage/admin_unit/${adminUnitId}/request-deletion`);
    await expect(page.locator("[data-test=instruction]")).toBeVisible();
    await screenshot(page, "request-deletion");

    // A wrong name is shown at the field.
    await page.locator("#name").fill("Falsche Crew");
    await page.locator("#submit").click();
    await expect(page.locator("[data-test=field-error]")).toContainText(
      "Der eingegebene Name entspricht nicht dem Namen der Organisation"
    );
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/request-deletion`));
    await screenshot(page, "request-deletion-mismatch");

    await page.locator("#name").fill("Meine Crew");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/events`));

    // Once requested, the request page leads to the cancel page.
    await page.goto(`/manage/admin_unit/${adminUnitId}/request-deletion`);
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/cancel-deletion`));
    await expect(page.locator("#submit")).toHaveText("Löschen abbrechen");
    await screenshot(page, "cancel-deletion");

    await page.locator("#name").fill("Meine Crew");
    await page.locator("#submit").click();
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/events`));

    // And back: nothing to cancel any more.
    await page.goto(`/manage/admin_unit/${adminUnitId}/cancel-deletion`);
    await expect(page).toHaveURL(new RegExp(`/manage/admin_unit/${adminUnitId}/request-deletion`));
  });
});
