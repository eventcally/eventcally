const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createUser } = require("../fixtures/flask");

test.describe("Organization", () => {
  test("lists and searches", async ({ page }) => {
    const adminUnitId = createAdminUnit();
    createUser("other@test.de", "password");
    createAdminUnit("other@test.de", "Andere Gruppe");
    await page.goto("/organizations");
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.getByRole("link", { name: /Meine Crew/ })).toBeVisible();
    await screenshot(page, "list");

    await page.locator("input[type=search]").fill("Andere");
    await expect(page.getByRole("link", { name: /Meine Crew/ })).toHaveCount(0);
    await expect(page.getByRole("link", { name: /Andere Gruppe/ })).toBeVisible();
    await screenshot(page, "list-search");

    await page.locator("input[type=search]").fill("Meine");
    await page.getByRole("link", { name: /Meine Crew/ }).click();
    await expect(page).toHaveURL(new RegExp(`/organizations/${adminUnitId}$`));
  });

  test("reads", async ({ page }) => {
    const adminUnitId = createAdminUnit();
    await page.goto(`/organizations/${adminUnitId}`);
    await expect(page.locator("h1")).toContainText("Meine Crew");
    await screenshot(page, "read");

    await page.getByRole("button", { name: /iCal/ }).click();
    await expect(page.locator("input[name=icalUrl]")).toHaveValue(
      new RegExp(`/organizations/${adminUnitId}/ical$`)
    );
    await screenshot(page, "ical");
  });
});
