const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createUser, createAdminUnit } = require("../fixtures/flask");

test.describe("Admin (Vue 3)", () => {
  test("users", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    await login("admin@test.de");

    await page.goto("/admin-next/users");
    await expect(page.locator("table tbody tr", { hasText: "admin@test.de" })).toBeVisible();
  });

  test("navigate from home to users without reload", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    await login("admin@test.de");

    await page.goto("/admin-next");
    await page.evaluate(() => {
      window.__noReload = true;
    });
    await page.locator("a.list-group-item", { hasText: /^\s*(Users|Nutzer)\s*$/ }).click();

    await expect(page).toHaveURL(/\/admin-next\/users/);
    await expect(page.locator("table tbody tr", { hasText: "admin@test.de" })).toBeVisible();
    expect(await page.evaluate(() => window.__noReload)).toBe(true);
  });

  test("update user roles", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    createUser("other@test.de", "password");
    await login("admin@test.de");

    await page.goto("/admin-next/users");
    const row = page.locator("table tbody tr", { hasText: "other@test.de" });
    await row.locator("a", { hasText: /^\s*(Edit|Bearbeiten)\s*$/ }).click();

    await expect(page).toHaveURL(/\/admin-next\/users\/\d+\/update/);
    const admin = page.getByLabel(/^Administrator/);
    await expect(admin).not.toBeChecked();
    await admin.check();
    await page.locator("button[type=submit]").click();

    await expect(page.locator(".toast")).toBeVisible();
    await expect(page).toHaveURL(/\/admin-next\/users$/);

    await row.locator("a", { hasText: /^\s*(Edit|Bearbeiten)\s*$/ }).click();
    await expect(page.getByLabel(/^Administrator/)).toBeChecked();
  });

  test("delete user", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    createUser("other@test.de", "password");
    await login("admin@test.de");

    await page.goto("/admin-next/users");
    const row = page.locator("table tbody tr", { hasText: "other@test.de" });
    await row.locator("button", { hasText: /^\s*(Delete|Löschen)\s*$/ }).click();

    const modal = page.locator(".modal.show");
    const ok = modal.locator(".btn-danger");
    await expect(ok).toBeDisabled();
    await modal.locator("input").fill("OTHER@test.de");
    await expect(ok).toBeEnabled();
    await ok.click();

    await expect(page.locator(".toast")).toBeVisible();
    await expect(row).toHaveCount(0);
  });

  test("organizations: search", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    createAdminUnit("admin@test.de", "Alpha Crew");
    createAdminUnit("admin@test.de", "Beta Crew");
    await login("admin@test.de");

    await page.goto("/admin-next/organizations");
    // The seed data brings one organization of its own.
    await expect(page.locator("table tbody tr")).toHaveCount(3);
    await page.locator("input[type=search]").fill("alp");

    await expect(page.locator("table tbody tr")).toHaveCount(1);
    await expect(page.locator("table tbody tr", { hasText: "Alpha Crew" })).toBeVisible();
    await expect(page).toHaveURL(/keyword=alp/);
    await screenshot(page, "organizations-list-search");
  });

  test("organizations: toggle capability", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    createAdminUnit("admin@test.de", "Alpha Crew");
    await login("admin@test.de");

    await page.goto("/admin-next/organizations");
    const row = page.locator("table tbody tr", { hasText: "Alpha Crew" });
    await row.locator("a", { hasText: /^\s*(Edit|Bearbeiten)\s*$/ }).click();

    await expect(page).toHaveURL(/\/admin-next\/organizations\/\d+\/update/);
    const verify = page.getByLabel(/^(Verify other organizations|Andere Organisationen verifizieren)/);
    await expect(verify).toBeChecked(); // the fixture organizations have all capabilities
    await screenshot(page, "organization-update");
    await verify.uncheck();

    await expect(page.locator(".toast")).toBeVisible();
    await screenshot(page, "organization-update-saved");
    await page.reload();
    await expect(
      page.getByLabel(/^(Verify other organizations|Andere Organisationen verifizieren)/),
    ).not.toBeChecked();
  });

  test("organizations: delete", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    createAdminUnit("admin@test.de", "Alpha Crew");
    await login("admin@test.de");

    await page.goto("/admin-next/organizations");
    const row = page.locator("table tbody tr", { hasText: "Alpha Crew" });
    await row.locator("button", { hasText: /^\s*(Delete|Löschen)\s*$/ }).click();

    const modal = page.locator(".modal.show");
    const ok = modal.locator(".btn-danger");
    await expect(ok).toBeDisabled();
    await modal.locator("input").fill("alpha crew");
    await expect(ok).toBeEnabled();
    await page.waitForTimeout(500); // let the modal fade in
    await screenshot(page, "organization-delete-modal");
    await ok.click();

    await expect(page.locator(".toast")).toBeVisible();
    await expect(row).toHaveCount(0);
  });

  const card = (page, label) =>
    page.locator(".card", { has: page.locator(".card-header", { hasText: label }) });
  const edit = (c) => c.locator("button", { hasText: /^\s*(Edit|Bearbeiten)\s*$/ }).click();
  const save = (c) => c.locator("button[type=submit]").click();

  test("settings: edit settings independently", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    await login("admin@test.de");

    await page.goto("/admin-next/settings");
    const legal = card(page, /Legal notice|Impressum/);
    await edit(legal);
    await legal.locator("textarea").fill("Impressum-Text");
    await save(legal);
    await expect(page.locator(".toast")).toBeVisible();
    await expect(legal).toContainText("Impressum-Text");

    const announcement = card(page, /Announcement|Ankündigung/);
    await edit(announcement);
    await announcement.locator("textarea").fill("Hallo-Welt");
    await save(announcement);
    await expect(announcement).toContainText("Hallo-Welt");

    await page.reload();
    await expect(card(page, /Legal notice|Impressum/)).toContainText("Impressum-Text");
    await expect(card(page, /Announcement|Ankündigung/)).toContainText("Hallo-Welt");
  });

  test("settings: reset terms of service acceptance", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    await login("admin@test.de");

    await page.goto("/admin-next/settings");
    await page.locator(".card.border-danger button").click();
    await page.locator(".modal.show .btn-danger").click();

    await expect(page.locator(".toast")).toBeVisible();
  });

  test("planning: invalid JSON shows an error, valid JSON is pretty-printed", async ({
    page,
    login,
  }) => {
    createUser("admin@test.de", "password", true);
    await login("admin@test.de");

    await page.goto("/admin-next/planning");
    const calendars = card(page, /External calendars|Externe Kalender/);
    await edit(calendars);
    await calendars.locator("textarea").fill("{");
    await save(calendars);
    await expect(calendars.locator(".alert-danger")).toBeVisible();

    await calendars.locator("textarea").fill('[{"title":"a","url":"https://x","active":true}]');
    await save(calendars);
    await expect(page.locator(".toast")).toBeVisible();
    await expect(calendars.locator("pre")).toContainText('"title": "a"');
  });

  test("email: config and sync test mail", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    await login("admin@test.de");

    await page.goto("/admin-next/email");
    await expect(page.locator("table")).toContainText("MAIL_PASSWORD");
    await expect(page.locator("table")).not.toContainText("password");

    await page.locator("input[type=email]").fill("to@test.de");
    await page.locator("button[type=submit]").click();
    await expect(page.locator(".toast")).toBeVisible();
  });

  test("email: async test mail", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    await login("admin@test.de");

    await page.goto("/admin-next/email");
    await page.locator("input[type=email]").fill("to@test.de");
    await page.locator("button[type=button]", { hasText: /asynchron/i }).click();

    await expect(page.locator(".alert-success")).toBeVisible();
  });

  test("newsletter: test recipient", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    await login("admin@test.de");

    await page.goto("/admin-next/newsletter");
    await page.locator("#newsletter-test-recipient").fill("to@test.de");
    await page.locator("#newsletter-message").fill("<p>Hello</p>");
    await page.locator("button[type=submit]").click();

    await expect(page.locator(".alert-success")).toBeVisible();
  });

  test("newsletter: all users need a confirmation with the count", async ({ page, login }) => {
    createUser("admin@test.de", "password", true);
    await login("admin@test.de");

    await page.goto("/admin-next/newsletter");
    await page.locator("input[type=radio][value=all]").check();
    await page.locator("#newsletter-message").fill("<p>Hello</p>");
    await page.locator("button[type=submit]").click();

    const modal = page.locator(".modal.show");
    await expect(modal).toContainText(/\d+ (Empf|recipients)/);
    await expect(page.locator(".alert-success")).toHaveCount(0);
    await modal.locator(".btn-primary").click();

    await expect(page.locator(".alert-success")).toBeVisible();
  });
});
