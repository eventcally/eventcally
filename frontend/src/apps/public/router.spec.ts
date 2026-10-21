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

  it("renders unknown paths as not found", async () => {
    expect((await resolve("/event/x/report")).name).toBe("not-found");
  });
});
