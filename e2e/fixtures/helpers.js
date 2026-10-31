// DOM helpers for the e2e suite.
//
// Each helper takes `page` (or a locator) as its first argument.
const path = require("path");
const { test, expect } = require("@playwright/test");
const { createUser, createOauth2Client } = require("./flask");

/**
 * Build the artifact path `e2e/screenshots/<spec>/<name>-<viewportWidth>.png`.
 *
 * The viewport suffix is what keeps the desktop and mobile runs from
 * overwriting each other's artifacts.
 */
function screenshotPath(page, name) {
  const spec = path.basename(test.info().file);
  const width = page.viewportSize().width;

  return path.join("e2e", "screenshots", spec, `${name}-${width}.png`);
}

/**
 * Full-page screenshot.
 *
 * @param {import("@playwright/test").Page} page
 * @param {string} name
 */
async function screenshot(page, name) {
  await page.screenshot({ path: screenshotPath(page, name), fullPage: true });
}

/**
 * Element screenshot.
 *
 * @param {import("@playwright/test").Locator} locator
 * @param {string} name
 */
async function screenshotElement(locator, name) {
  await locator.screenshot({ path: screenshotPath(locator.page(), name) });
}

async function assertValid(page, fieldId) {
  await expect(page.locator(`#${fieldId}`)).toHaveClass(/is-valid/);
  await expect(page.locator(`#${fieldId}-error`)).toBeEmpty();
}

async function assertInvalid(page, fieldId, msg) {
  await expect(page.locator(`#${fieldId}`)).toHaveClass(/is-invalid/);
  await expect(page.locator(`#${fieldId}-error`)).toContainText(msg);
}

async function assertRequired(page, fieldId) {
  await assertInvalid(page, fieldId, "Pflichtfeld");
}

/**
 * Picks an option in an `AppTypeahead` (Vue 3 pages): types into `#<inputId>`, waits for the
 * lookup and clicks the option with `expectedText`.
 */
async function typeahead(page, inputId, textToEnter, expectedText) {
  const input = page.locator(`#${inputId}`);
  await input.pressSequentially(textToEnter);
  await page.locator("[data-test=option]", { hasText: expectedText }).click();
  await expect(input).toHaveValue(expectedText);
}

/**
 * Asserts that ANY element in the matched set contains the text. Playwright's
 * `toContainText` on a locator resolving to several elements is a strict-mode
 * violation instead, so selectors like `div.alert` would otherwise break as soon
 * as a second alert is on the page.
 */
async function shouldContain(locator, text) {
  await expect(locator.filter({ hasText: text }).first()).toBeAttached();
}

async function screenshotDatepicker(page, elementId, screenshotName = "datepicker") {
  await page.locator(elementId).click();
  await expect(page.locator("#ui-datepicker-div")).toBeVisible();
  await page.locator(".ui-datepicker-next > .ui-icon").click();
  await screenshot(page, screenshotName);
}

/**
 * One date card of the Vue event form (`EventDateDefinitionFields`): start, the end that
 * "+ End" opens three hours later, all-day and the recurrence editor. With `recurrence`
 * the date keeps a weekly rule.
 */
async function checkVueEventStartEnd(page, index, recurrence = false) {
  const prefix = `date_definitions-${index}-`;
  const id = (suffix) => page.locator(`#${prefix}${suffix}`);
  const testId = (suffix) => page.locator(`[data-test="${prefix}${suffix}"]`);

  await id("start").fill("2030-12-30");
  await id("start-time").fill("21:30");

  // The end opens three hours after the start and closes again.
  await testId("end-show").click();
  await expect(id("end")).toHaveValue("2030-12-31");
  await expect(id("end-time")).toHaveValue("00:30");
  await testId("end-hide").click();
  await expect(id("end")).toBeHidden();

  // All-day opens the end at the end of the day and hides the times.
  await id("allday").check();
  await expect(id("end")).toHaveValue("2030-12-30");
  await expect(id("start-time")).toBeHidden();
  await expect(id("end-time")).toBeHidden();
  // Hiding the end turns all-day off again.
  await testId("end-hide").click();
  await expect(id("allday")).not.toBeChecked();
  await expect(id("start-time")).toBeVisible();

  // The recurrence editor: a new rule is daily until the start, with a preview.
  await id("recc-button").click();
  const modal = page.locator(`[data-test="${prefix}recurrence-modal"]`);
  await expect(modal.locator(`#${prefix}recc-freq`)).toHaveValue("DAILY");
  await expect(modal.locator(`#${prefix}recc-end-until`)).toBeChecked();
  await expect(modal.locator("[data-test=occurrence]").first()).toBeVisible();
  await modal.locator(`#${prefix}recc-freq`).selectOption("WEEKLY");
  await modal.locator(`#${prefix}recc-end-count`).check();
  await modal.locator(`#${prefix}recc-count`).fill("3");
  await expect(modal.locator("[data-test=occurrence]")).toHaveCount(3);
  await modal.locator("[data-test=apply]").click();
  await expect(modal).toBeHidden();
  await expect(testId("recurrence-summary")).toContainText("Woche");

  if (!recurrence) {
    await testId("recc-remove").click();
    await expect(testId("recurrence-summary")).toBeHidden();
  }
}

/**
 * Uses `page.request` rather than the standalone `request` fixture so the token
 * POST shares the browser's session.
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
  typeahead,
  screenshotDatepicker,
  checkVueEventStartEnd,
  authorize,
};
