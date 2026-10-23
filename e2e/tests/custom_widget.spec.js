const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createEvent } = require("../fixtures/flask");

test.describe("Custom widget", () => {
  test("configure, install, edit, embed and delete", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createEvent(adminUnitId);
    const listUrl = `/manage/admin_unit/${adminUnitId}/custom-widgets`;

    // The list starts empty.
    await page.goto(listUrl);
    await expect(page.getByText("Keine Widgets gefunden")).toBeVisible();
    await screenshot(page, "list-empty");

    // The configurator previews the search widget with the seeded event dates.
    await page.getByRole("link", { name: "Widget hinzufügen" }).click();
    await expect(page).toHaveURL(new RegExp(`${listUrl}/create$`));
    const preview = page.frameLocator("[data-test=widget-preview]");
    await expect(preview.locator(".card:visible").first()).toBeVisible();
    await screenshot(page, "configurator-search");

    // A style change reaches the iframe without a reload.
    await page.getByRole("tab", { name: "Styles" }).click();
    await page.locator("#field-linkColor").fill("#ff0000");
    await expect(preview.locator("a.underlined")).toHaveCSS("color", "rgb(255, 0, 0)");
    await screenshot(page, "configurator-styles");

    await page.locator("[data-test=widget-name]").fill("Mein Widget");
    await page.getByRole("button", { name: "Speichern" }).click();

    // Saved: back on the list, with the message of the editor.
    await expect(page).toHaveURL(new RegExp(`${listUrl}$`));
    await expect(page.getByText("Widget erfolgreich gespeichert")).toBeVisible();
    await expect(page.getByRole("cell", { name: "Mein Widget" })).toBeVisible();
    await screenshot(page, "list");

    // The installation snippet carries the widget id.
    await page.getByRole("button", { name: "Installation" }).click();
    await expect(page.locator("[data-test=install-body]")).toHaveValue(
      /class="eventcally-widget" data-widget-id="\d+"/
    );
    await expect(page.locator("[data-test=install-header]")).toHaveValue(
      /static\/widget-loader\.js/
    );
    await screenshot(page, "installation");
    await page.getByRole("button", { name: "Schließen" }).click();

    // Edit: the values were persisted; switch to the calendar and save.
    const editLink = page.getByRole("link", { name: "Bearbeiten" });
    const widgetId = (await editLink.getAttribute("href")).match(/custom-widgets\/(\d+)\/update/)[1];
    await editLink.click();
    await expect(page.locator("[data-test=widget-name]")).toHaveValue("Mein Widget");
    await page.getByRole("tab", { name: "Styles" }).click();
    await expect(page.locator("#field-linkColor")).toHaveValue("#ff0000");

    await page.locator("[data-test=widget-type]").selectOption("calendar");
    await expect(preview.locator("[data-test=title]")).toBeVisible();
    await screenshot(page, "configurator-calendar");
    await page.getByRole("button", { name: "Speichern" }).click();
    await expect(page).toHaveURL(new RegExp(`${listUrl}$`));

    // What widget-loader.js on a customer site reads.
    const loaded = await page.request.get(`/js/wlcw/${widgetId}`);
    expect(loaded.ok()).toBe(true);
    const body = await loaded.json();
    expect(body.widget_type).toBe("calendar");
    expect(body.settings.calendarType).toBe("week");
    expect(body.organization.id).toBe(adminUnitId);

    // The embedded page itself is public and may be framed.
    const embedded = await page.request.get("/custom_widget/calendar");
    expect(embedded.ok()).toBe(true);
    expect(embedded.headers()["x-frame-options"]).toBeUndefined();

    // Delete through the modal.
    await page.getByRole("button", { name: "Löschen" }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Löschen" }).click();
    await expect(page.getByText("Widget erfolgreich gelöscht")).toBeVisible();
    await expect(page.getByText("Keine Widgets gefunden")).toBeVisible();
  });

  test("embedded widgets", async ({ page }) => {
    const adminUnitId = createAdminUnit();
    createEvent(adminUnitId);

    // Outside an iframe no settings arrive: the page stays empty instead of failing.
    await page.goto("/custom_widget/search");
    await expect(page.locator("#app")).toBeEmpty();
  });
});
