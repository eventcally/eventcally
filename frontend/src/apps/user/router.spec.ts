import { describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({ boot: { base: "/" } }));

import { routes } from "./router";

async function resolve(path: string) {
  const router = createRouter({ history: createMemoryHistory(), routes });
  await router.push(path);
  return router.currentRoute.value;
}

type PropsFn = (route: unknown) => Record<string, unknown>;
const propsOf = (route: Awaited<ReturnType<typeof resolve>>) => {
  const props = route.matched[0].props.default as PropsFn | Record<string, unknown> | undefined;
  return typeof props === "function" ? props(route) : props;
};

describe("user router", () => {
  it.each([
    ["/profile", "profile"],
    ["/user/general", "general"],
    ["/user/notifications", "notifications"],
    ["/user/request-deletion", "request-deletion"],
    ["/user/cancel-deletion", "cancel-deletion"],
    ["/user/accept-tos", "accept-tos"],
    ["/user/api_keys", "api-keys"],
    ["/user/api_key/create", "api-key-create"],
    ["/user/api_key/4", "api-key"],
    ["/user/api_key/4/update", "api-key-update"],
    ["/user/api_key/4/delete", "api-key-delete"],
    ["/user/oauth2_clients", "oauth2-clients"],
    ["/user/oauth2_client/create", "oauth2-client-create"],
    ["/user/oauth2_client/4", "oauth2-client"],
    ["/user/oauth2_client/4/update", "oauth2-client-update"],
    ["/user/oauth2_client/4/delete", "oauth2-client-delete"],
    ["/user/oauth2_tokens", "oauth2-tokens"],
    ["/user/oauth2_token/4/revoke", "oauth2-token-revoke"],
    ["/user/organization_members", "memberships"],
    ["/user/organization_member/4/delete", "membership-leave"],
    ["/user/organization_member_invitations", "member-invitations"],
    ["/user/organization_member_invitation/4/negotiate", "member-invitation"],
    ["/user/organization_invitations", "organization-invitations"],
    ["/user/organization_invitation/4/negotiate", "organization-invitation"],
  ])("resolves %s", async (path, name) => {
    expect((await resolve(path)).name).toBe(name);
  });

  it("passes numeric ids to the pages", async () => {
    expect(propsOf(await resolve("/user/api_key/4/update"))).toEqual({ id: 4 });
    expect(propsOf(await resolve("/user/oauth2_token/7/revoke"))).toEqual({
      id: 7,
    });
    expect(propsOf(await resolve("/user/organization_member/9/delete"))).toEqual({ id: 9 });
  });

  it("tells the deletion pages their mode", async () => {
    expect(propsOf(await resolve("/user/request-deletion"))).toEqual({
      mode: "request",
    });
    expect(propsOf(await resolve("/user/cancel-deletion"))).toEqual({
      mode: "cancel",
    });
  });

  it("passes `next` to the accept-ToS page", async () => {
    expect(propsOf(await resolve("/user/accept-tos?next=/manage"))).toEqual({
      next: "/manage",
    });
    expect(propsOf(await resolve("/user/accept-tos"))).toEqual({
      next: undefined,
    });
  });

  it("does not take non-numeric ids and unknown paths", async () => {
    expect((await resolve("/user/api_key/x")).name).toBe("not-found");
    expect((await resolve("/user/unknown")).name).toBe("not-found");
  });
});
