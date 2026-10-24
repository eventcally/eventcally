import { describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({ boot: { base: "/" } }));
// FullCalendar does not render in jsdom; the router only needs the page component.
vi.mock("./pages/PlanningPage.vue", () => ({ default: { render: () => null } }));

import { routes } from "./router";

async function resolve(path: string) {
  const router = createRouter({ history: createMemoryHistory(), routes });
  await router.push(path);
  return router.currentRoute.value;
}

describe("manage router", () => {
  it("resolves the planning page", async () => {
    expect((await resolve("/planning")).name).toBe("planning");
  });

  it("resolves the custom widget list with a numeric organization", async () => {
    const route = await resolve("/manage/admin_unit/3/custom-widgets");
    expect(route.name).toBe("custom-widgets");
    expect(route.params.organizationId).toBe("3");
  });

  it("resolves the organization settings with a numeric organization", async () => {
    const route = await resolve("/manage/admin_unit/3/update");
    expect(route.name).toBe("organization-settings");
    expect(route.params.organizationId).toBe("3");
    expect((await resolve("/manage/admin_unit/x/update")).name).toBe("not-found");
  });

  it("resolves the organization create page and keeps the invitation", async () => {
    const route = await resolve("/manage/organization/create?invitation_id=4");
    expect(route.name).toBe("organization-create");
    expect(route.query.invitation_id).toBe("4");
  });

  it("resolves the event list with a numeric organization and keeps the query", async () => {
    const route = await resolve("/manage/admin_unit/3/events?event_place_id=5");
    expect(route.name).toBe("manage-events");
    expect(route.params.organizationId).toBe("3");
    expect(route.query.event_place_id).toBe("5");
    expect((await resolve("/manage/admin_unit/x/events")).name).toBe("not-found");
  });

  it("resolves the configurator for create and update", async () => {
    expect((await resolve("/manage/admin_unit/3/custom-widgets/create")).name).toBe(
      "custom-widget-create",
    );
    const update = await resolve("/manage/admin_unit/3/custom-widgets/8/update");
    expect(update.name).toBe("custom-widget-update");
    expect(update.params).toMatchObject({ organizationId: "3", id: "8" });
  });

  it("resolves the place form for create and update", async () => {
    const create = await resolve("/manage/admin_unit/3/event_place/create");
    expect(create.name).toBe("event-place-create");
    expect(create.params.organizationId).toBe("3");

    const update = await resolve("/manage/admin_unit/3/event_place/8/update");
    expect(update.name).toBe("event-place-update");
    expect(update.params).toMatchObject({ organizationId: "3", id: "8" });
    expect((await resolve("/manage/admin_unit/3/event_place/x/update")).name).toBe("not-found");
    expect((await resolve("/manage/admin_unit/x/event_place/create")).name).toBe("not-found");
  });

  it("does not take other organization paths", async () => {
    expect((await resolve("/manage/admin_unit/x/custom-widgets")).name).toBe("not-found");
    expect((await resolve("/manage/admin_unit/3/custom-widgets/x/update")).name).toBe("not-found");
  });

  it("renders unknown paths as not found", async () => {
    expect((await resolve("/x")).name).toBe("not-found");
  });
});
