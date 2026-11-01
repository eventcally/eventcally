const fs = require("fs");
const path = require("path");
const { test, expect } = require("../fixtures");
const { screenshot } = require("../fixtures/helpers");
const { createAdminUnit, createEvent } = require("../fixtures/flask");

// The iframe page customers embed with `widget-loader.js` or a raw <iframe>. Its URL, query
// string and analytics messages are a contract; see frontend/src/apps/widget/legacyQuery.ts.
test.describe("Widget", () => {
  test("event dates", async ({ page }) => {
    const adminUnitId = createAdminUnit();
    createEvent(adminUnitId);
    createEvent(adminUnitId);
    const url = `/organizations/${adminUnitId}/widget/eventdates`;

    await page.goto(url);
    await expect(page.locator("[data-test=event-card]")).toHaveCount(2);
    await screenshot(page, "eventdates");

    // A search keeps the shape the server-rendered page produced.
    await page.getByLabel("Suche").fill("Name");
    await page.getByRole("button", { name: "Finden" }).click();
    await expect(page).toHaveURL(
      new RegExp(
        `${url}\\?s_ft=&s_bg=&s_pr=&s_li=&date_from=\\d{4}-\\d{2}-\\d{2}&date_to=&category_id=0&keyword=Name$`,
      ),
    );
    await expect(page.locator("[data-test=event-card]")).toHaveCount(2);

    // Page change, with a page size of one.
    await page.goto(`${url}?per_page=1`);
    await expect(page.locator("[data-test=event-card]")).toHaveCount(1);
    await page.getByRole("button", { name: "Next page" }).click();
    await expect(page).toHaveURL(new RegExp(`${url}\\?per_page=1&page=2$`));
    await expect(page.getByRole("navigation", { name: /Seite 2 von 2/ })).toBeVisible();

    // The card is a real link to the event date, opened in a new tab.
    const link = page.locator("a.stretched-link").first();
    await expect(link).toHaveAttribute("href", /\/eventdate\/\d+$/);
    await expect(link).toHaveAttribute("target", "_blank");

    // Unknown organizations and pages stay a 404.
    expect((await page.request.get("/organizations/4711/widget/eventdates")).status()).toBe(404);
    expect((await page.request.get(`${url}?page=9`)).status()).toBe(404);
    expect((await page.request.get(url)).headers()["x-frame-options"]).toBeUndefined();
  });

  test("embedded through widget-loader.js", async ({ page }) => {
    const adminUnitId = createAdminUnit();
    createEvent(adminUnitId);
    const origin = new URL(test.info().project.use.baseURL || "http://127.0.0.1:5000").origin;

    // The loader fetches iframeResizer from a CDN; serve the copy we ship.
    await page.route("**/iframe-resizer/4.3.2/iframeResizer.min.js", (route) =>
      route.fulfill({
        contentType: "text/javascript",
        body: fs.readFileSync(
          path.join(
            "project",
            "presentation",
            "web",
            "static",
            "ext",
            "iframeResizer.4.3.2.min.js",
          ),
        ),
      }),
    );
    await page.route(`${origin}/customer-page`, (route) =>
      route.fulfill({
        contentType: "text/html",
        body: `<!doctype html><html><body>
          <script>window.dataLayer = [];</script>
          <div class="eventcally-widget" data-widget-organization-id="${adminUnitId}"
               data-widget-resize="true" data-widget-height="400px"
               data-widget-google-tag-manager="true"></div>
          <script src="${origin}/static/widget-loader.js"></script>
        </body></html>`,
      }),
    );

    await page.goto(`${origin}/customer-page`);
    const frame = page.frameLocator("iframe");
    await expect(frame.locator("[data-test=event-card]")).toHaveCount(1);
    await screenshot(page, "embedded");

    const events = () => page.evaluate(() => window.dataLayer.map((e) => [e.event, e.url]));
    await expect
      .poll(events)
      .toEqual([["eventcallyWidget.pageView", expect.stringMatching(/\/widget\/eventdates\?$/)]]);

    // A search is a page view with the new URL.
    await frame.getByLabel("Suche").fill("Name");
    await frame.getByRole("button", { name: "Finden" }).click();
    await expect.poll(async () => (await events()).length).toBe(2);
    expect((await events())[1][1]).toContain("keyword=Name");

    // A click on the card is reported with the absolute event date URL.
    // The empty stretched link has no box to click; its handler reports the click.
    await frame.locator("a.stretched-link").first().dispatchEvent("click");
    await expect
      .poll(async () => (await events()).at(-1))
      .toEqual(["eventcallyWidget.linkClick", expect.stringMatching(/\/eventdate\/\d+$/)]);
  });
});
