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

  it("renders unknown paths as not found", async () => {
    expect((await resolve("/x")).name).toBe("not-found");
  });
});
