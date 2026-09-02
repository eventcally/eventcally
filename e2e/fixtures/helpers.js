// DOM helpers for the e2e suite.
//
// Ported from cypress/support/commands.js:185-395. Each helper takes `page` as
// its first argument instead of being a chained Cypress command.
const path = require("path");
const { test, expect } = require("@playwright/test");
const { createUser, createOauth2Client } = require("./flask");

/**
 * Build the artifact path `e2e/screenshots/<spec>/<name>-<viewportWidth>.png`.
 *
 * The viewport suffix reproduces cypress/plugins/index.js:19-25 and is what
 * keeps the desktop and mobile runs from overwriting each other's artifacts.
 */
function screenshotPath(page, name) {
  const spec = path.basename(test.info().file);
  const width = page.viewportSize().width;

  return path.join("e2e", "screenshots", spec, `${name}-${width}.png`);
}

/**
 * Full-page screenshot, matching Cypress' `cy.screenshot()` default of
 * `capture: "fullPage"`.
 *
 * @param {import("@playwright/test").Page} page
 * @param {string} name
 */
async function screenshot(page, name) {
  await page.screenshot({ path: screenshotPath(page, name), fullPage: true });
}

/**
 * Element screenshot, matching Cypress' `cy.get(sel).screenshot()`.
 *
 * @param {import("@playwright/test").Locator} locator
 * @param {string} name
 */
async function screenshotElement(locator, name) {
  await locator.screenshot({ path: screenshotPath(locator.page(), name) });
}

/**
 * SOURCE: cypress/support/commands.js:185-188
 */
async function assertValid(page, fieldId) {
  await expect(page.locator(`#${fieldId}`)).toHaveClass(/is-valid/);
  await expect(page.locator(`#${fieldId}-error`)).toBeEmpty();
}

/**
 * SOURCE: cypress/support/commands.js:190-193
 */
async function assertInvalid(page, fieldId, msg) {
  await expect(page.locator(`#${fieldId}`)).toHaveClass(/is-invalid/);
  await expect(page.locator(`#${fieldId}-error`)).toContainText(msg);
}

/**
 * SOURCE: cypress/support/commands.js:195-197
 */
async function assertRequired(page, fieldId) {
  await assertInvalid(page, fieldId, "Pflichtfeld");
}

/**
 * SOURCE: cypress/support/commands.js:211-232
 */
async function select2(page, selectId, textToEnter, expectedText = null, expectedValue = null) {
  const container = page.locator(`#select2-${selectId}-container`);
  await container.click();

  const input = page.locator(`input[aria-controls="select2-${selectId}-results"]`);
  await input.pressSequentially(textToEnter, { delay: 500 });
  await input.press("Enter");

  if (expectedText) {
    // Cypress asserted `be.oneOf`: select2 renders a "×" clear affordance in
    // front of the label for some widget variants.
    await expect(async () => {
      const text = await container.textContent();
      expect([expectedText, `×${expectedText}`]).toContain(text);
    }).toPass();
  }

  if (expectedValue) {
    await expect(page.locator(`#${selectId}`)).toHaveValue(expectedValue);
  }
}

/**
 * Cypress' `.should("contain", text)` passes when ANY element in the matched set
 * contains the text (chai-jquery delegates to `.is(":contains(...)")`). Playwright's
 * `toContainText` on a locator that resolves to several elements is a strict-mode
 * violation instead, so selectors like `div.alert` break as soon as a second alert
 * is on the page. This restores the original semantics.
 */
async function shouldContain(locator, text) {
  await expect(locator.filter({ hasText: text }).first()).toBeAttached();
}

/**
 * SOURCE: cypress/support/commands.js:234-240
 */
async function inputsShouldHaveSameValue(page, input1, input2) {
  const value = await page.locator(input1).inputValue();
  await expect(page.locator(input2)).toHaveValue(value);
}

/**
 * SOURCE: cypress/support/commands.js:346-354
 */
async function screenshotDatepicker(page, elementId, screenshotName = "datepicker") {
  await page.locator(elementId).click();
  await expect(page.locator("#ui-datepicker-div")).toBeVisible();
  await page.locator(".ui-datepicker-next > .ui-icon").click();
  await screenshot(page, screenshotName);
}

/**
 * SOURCE: cypress/support/commands.js:242-310
 *
 * The heaviest port in the suite: jQuery UI datepicker + timepicker + the
 * recurrence modal, driven almost entirely through visibility toggling.
 */
async function checkEventStartEnd(page, update = false, recurrence = false, prefix = "") {
  const id = (suffix) => page.locator(`#${prefix}${suffix}`);
  // A second date definition adds a second `.modal-recurrence`, so every
  // `:visible` selector in the original has to stay scoped to the open one.
  const openModal = page.locator(".modal-recurrence").filter({ visible: true }).first();

  if (update && recurrence) {
    await expect(id("single-event-container")).toBeHidden();
    await expect(id("recc-event-container")).toBeVisible();
    await page.locator(`div[data-prefix="${prefix}"] [name="riedit"]`).click();
  } else {
    await checkEventAllday(page, prefix);

    await id("start-user").click();
    await expect(page.locator("#ui-datepicker-div")).toBeVisible();
    await page.locator("#ui-datepicker-div a.ui-state-default").first().click(); // select first date
    await expect(page.locator("#ui-datepicker-div")).toBeHidden();

    await id("start-time").click();
    const timepicker = page.locator(".ui-timepicker-wrapper").filter({ visible: true }).first();
    await expect(timepicker).toBeVisible();
    await timepicker.locator('.ui-timepicker-am[data-time="0"]').click(); // select 00:00
    await expect(page.locator("#ui-datepicker-div")).toBeHidden();

    await expect(id("end-container")).toBeHidden();
    await id("end-show-container").locator(".show-link").click();
    await expect(id("end-show-container")).toBeHidden();
    await expect(id("end-container")).toBeVisible();
    await inputsShouldHaveSameValue(page, `#${prefix}start-user`, `#${prefix}end-user`);
    await expect(id("end-time")).toHaveValue("03:00");
    await id("end-hide-container").locator(".hide-link").click();
    await expect(id("end-show-container")).toBeVisible();
    await expect(id("end-container")).toBeHidden();
    await expect(id("end-user")).toHaveValue("");
    await expect(id("end-time")).toHaveValue("");

    await expect(id("recc-event-container")).toBeHidden();
    await id("recc-button").click();
  }

  await expect(openModal).toBeVisible();
  // Cypress needed `cy.wait(1000)` here for the modal to copy the start values
  // across; the retrying value assertions below wait for the real thing.
  await inputsShouldHaveSameValue(page, `#${prefix}start-user`, `#${prefix}recc-start-user`);
  await inputsShouldHaveSameValue(page, `#${prefix}start-time`, `#${prefix}recc-start-time`);
  await expect(id("rirtemplate").locator("option")).toHaveCount(4);
  await expect(openModal.locator('input[value="BYENDDATE"]')).toBeChecked();
  await openModal.locator(".modal-footer .btn-primary").click();

  await expect(id("single-event-container")).toBeHidden();
  await expect(id("recc-event-container")).toBeVisible();

  if (recurrence === false) {
    await page.locator('[name="ridelete"]').filter({ visible: true }).first().click();
    await expect(id("single-event-container")).toBeVisible();
    await expect(id("recc-event-container")).toBeHidden();
    await expect(id("end-container")).toBeHidden();
  }
}

/**
 * SOURCE: cypress/support/commands.js:312-344
 */
async function checkEventAllday(page, prefix = "") {
  const id = (suffix) => page.locator(`#${prefix}${suffix}`);
  const openModal = page.locator(".modal-recurrence").filter({ visible: true }).first();

  // Turn on
  await id("allday").click();
  await expect(id("end-container")).toBeVisible();
  await expect(id("start-time")).toBeHidden();
  await expect(id("end-time")).toBeHidden();

  // Recurrence
  await id("recc-button").click();
  await expect(openModal).toBeVisible();
  await expect(id("recc-allday")).toBeChecked();
  await expect(id("recc-start-time")).toBeHidden();
  await expect(id("recc-fo-end-time")).toBeHidden();

  await id("recc-allday").click();
  await expect(id("recc-start-time")).toBeVisible();
  await expect(id("recc-fo-end-time")).toBeVisible();
  await openModal.locator(".modal-footer .btn-secondary").click();

  // Turn off
  await id("allday").click();
  await expect(id("start-time")).toBeVisible();
  await expect(id("end-time")).toBeVisible();

  // Turn again
  await id("allday").click();
  await expect(id("end-container")).toBeVisible();

  // Removing end turns off allday
  await id("end-hide-container").locator(".hide-link").click();
  await expect(id("allday")).not.toBeChecked();
  await expect(id("start-time")).toBeVisible();
}

/**
 * SOURCE: cypress/support/commands.js:356-395
 *
 * Uses `page.request` rather than the standalone `request` fixture so the token
 * POST shares the browser's session, the way `cy.request` did.
 */
async function authorize(page, login, takeScreenshot = false) {
  const userId = createUser("new@test.de", "password", true);
  const result = createOauth2Client(userId);

  await login("new@test.de");
  await page.goto(
    `/oauth/authorize?nonce=4711&response_type=code&client_id=${result.oauth2_client_client_id}` +
      `&scope=${result.oauth2_client_scope}&redirect_uri=/`
  );

  if (takeScreenshot) {
    await screenshot(page, "authorize");
  }

  await page.locator("#allow").click();

  await expect(page).not.toHaveURL(/authorize/);
  const code = new URL(page.url()).searchParams.get("code");

  const response = await page.request.post("/oauth/token", {
    form: {
      client_id: result.oauth2_client_client_id,
      client_secret: result.oauth2_client_secret,
      grant_type: "authorization_code",
      scope: result.oauth2_client_scope,
      code: code,
      redirect_uri: "/",
    },
  });
  // cy.request fails the test on a non-2xx response; keep that implicit assertion.
  expect(response.ok(), `token request failed: ${response.status()}`).toBeTruthy();

  return result;
}

module.exports = {
  screenshot,
  shouldContain,
  screenshotElement,
  assertValid,
  assertInvalid,
  assertRequired,
  select2,
  inputsShouldHaveSameValue,
  screenshotDatepicker,
  checkEventStartEnd,
  checkEventAllday,
  authorize,
};
