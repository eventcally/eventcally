const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createEvent } = require("../fixtures/flask");

test.describe("Planning", () => {
  test("search", async ({ page, login }) => {
    await login();
    const adminUnitId = createAdminUnit();
    createEvent(adminUnitId);

    await page.goto("/planning");
    // Replaces `cy.wait(2000) // Wait for Vue to load`: the calendar is rendered
    // by project/static/vue/planning/list.vue.js, and the spinner is bound to
    // `v-show="isLoading"`, so this waits for the real end of loading.
    await expect(page.locator("#vue-container .v-calendar")).toBeVisible();
    await expect(page.locator("#vue-container .v-progress-circular")).toBeHidden();
    await screenshot(page, "result");
  });
});
