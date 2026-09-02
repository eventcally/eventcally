const { test, expect } = require("../fixtures");
const { screenshot, assertValid, assertInvalid, assertRequired, shouldContain } = require("../fixtures/helpers");

// These forms are validated by jQuery Validate (see project/templates/_macros.html
// and security/register_user.html), which binds to `keyup` — not `input`. `fill()`
// would set the value without ever triggering validation, so every field that is
// asserted on immediately after typing must use `pressSequentially`.
async function retype(locator, value) {
  await locator.clear();
  await locator.pressSequentially(value);
}

test.describe("User", () => {
  test("registers user", async ({ page, baseURL }) => {
    await page.goto("/register");
    await screenshot(page, "register");

    // Blank
    await page.locator("#submit").click();
    await assertRequired(page, "email");
    await assertRequired(page, "password");
    await assertRequired(page, "password_confirm");
    await assertRequired(page, "accept_tos");

    // Email
    await page.locator("#email").pressSequentially("invalidmail");
    await assertInvalid(page, "email", "Geben Sie bitte eine gültige E-Mail-Adresse ein.");

    await retype(page.locator("#email"), "test@test.de");
    await assertInvalid(page, "email", "Mit dieser E-Mail existiert bereits ein Account.");

    await retype(page.locator("#email"), "firstname.lastname@gmail.com");
    await assertValid(page, "email");

    // Password
    await page.locator("#password").pressSequentially("short");
    await assertInvalid(page, "password", "Geben Sie bitte mindestens 8 Zeichen ein.");

    await retype(page.locator("#password"), "iloveeventcally");
    await assertValid(page, "password");

    // Confirm password
    await page.locator("#password_confirm").pressSequentially("different");
    await assertInvalid(page, "password_confirm", "Wiederholen Sie bitte denselben Wert.");

    await retype(page.locator("#password_confirm"), "iloveeventcally");
    await assertValid(page, "password_confirm");

    // Submit
    await page.locator("#accept_tos").check();
    await page.locator("#submit").click();

    await expect(page).toHaveURL(`${baseURL}/`);
    await shouldContain(page.locator("div.alert"), "bestätigen");
  });

  test("login", async ({ page, context }) => {
    await page.goto("/login");
    await screenshot(page, "login");

    // Blank
    await page.locator("#submit").click();
    await assertRequired(page, "email");
    await assertRequired(page, "password");

    // Email
    await page.locator("#email").pressSequentially("invalidmail");
    await assertInvalid(page, "email", "Geben Sie bitte eine gültige E-Mail-Adresse ein.");

    await retype(page.locator("#email"), "test@test.de");
    await assertValid(page, "email");

    // Password
    await page.locator("#password").pressSequentially("password");
    await assertValid(page, "password");

    // Submit
    await page.locator("#submit").click();

    await expect(page).toHaveURL(/\/manage/);
    await expect(page.locator("h1")).toContainText("Organisationen");
    expect((await context.cookies()).find((cookie) => cookie.name === "session")).toBeTruthy();

    // Profile
    await page.goto("/profile");
    await screenshot(page, "profile");
  });
});
