import { describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({ boot: { base: "/" } }));

import { routes } from "./router";

async function resolve(path: string) {
  const router = createRouter({ history: createMemoryHistory(), routes });
  await router.push(path);
  return router.currentRoute.value;
}

describe("public router", () => {
  it("resolves the event report page", async () => {
    const route = await resolve("/event/12/report");

    expect(route.name).toBe("event-report");
    expect(route.params).toMatchObject({ id: "12" });
  });

  it("resolves the event pages", async () => {
    const event = await resolve("/event/12");
    expect(event.name).toBe("event");
    expect(event.params).toMatchObject({ id: "12" });

    expect((await resolve("/event/12/actions")).name).toBe("event-actions");

    const date = await resolve("/eventdate/4");
    expect(date.name).toBe("event-date");
    expect(date.params).toMatchObject({ id: "4" });

    expect((await resolve("/eventdate/x")).name).toBe("not-found");
  });

  it("resolves the organizer page", async () => {
    const route = await resolve("/organizers/5");

    expect(route.name).toBe("organizer");
    expect(route.params).toMatchObject({ id: "5" });
  });

  it("resolves the event dates page with legacy query arguments", async () => {
    const route = await resolve("/eventdates?admin_unit_id=3&keyword=jam");

    expect(route.name).toBe("event-dates");
    expect(route.query).toMatchObject({ admin_unit_id: "3", keyword: "jam" });
  });

  it("resolves the organizations pages", async () => {
    expect((await resolve("/organizations")).name).toBe("organizations");

    const route = await resolve("/organizations/7");
    expect(route.name).toBe("organization");
    expect(route.params).toMatchObject({ id: "7" });

    expect((await resolve("/organizations/x")).name).toBe("not-found");
  });

  it("renders unknown paths as not found", async () => {
    expect((await resolve("/event/x/report")).name).toBe("not-found");
  });
});
