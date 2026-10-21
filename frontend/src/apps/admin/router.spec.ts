import { afterEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({ boot: { base: "/admin/" } }));

import { routes } from "./router";

const assign = vi.fn();
vi.stubGlobal("location", { assign });

async function resolve(path: string) {
  const router = createRouter({ history: createMemoryHistory(), routes });
  await router.push(path);
  return router.currentRoute.value;
}

describe("admin router", () => {
  afterEach(() => assign.mockClear());

  it.each([
    ["/user/5/update", "user-update", { id: "5" }],
    ["/user/5/delete", "user-update", { id: "5" }],
    ["/organization/3/delete", "organization-update", { id: "3" }],
    ["/organization/3/update", "organization-update", { id: "3" }],
    ["/reset-tos-accepted", "settings", {}],
  ])("redirects the old URL %s", async (path, name, params) => {
    const route = await resolve(path);

    expect(route.name).toBe(name);
    expect(route.params).toMatchObject(params);
  });

  it("renders unknown paths as not found without leaving the SPA", async () => {
    const route = await resolve("/nope/deeper");

    expect(route.name).toBe("not-found");
    expect(assign).not.toHaveBeenCalled();
  });
});
