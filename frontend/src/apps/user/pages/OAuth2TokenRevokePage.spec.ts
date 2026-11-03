import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({
  boot: { base: "/", locale: "en", csrfToken: "x", loginUrl: "/login" },
}));

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
vi.mock("@/shared/api", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
  },
}));
const success = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({
  useNotify: () => ({ success, error: vi.fn() }),
}));

import { takeFlash } from "@/shared/flash";
import { mountPage } from "../testing";
import OAuth2TokenRevokePage from "./OAuth2TokenRevokePage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign, success].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

const token = { data: { id: 4, client_name: "Mein Client", status: null } };

describe("OAuth2TokenRevokePage", () => {
  it("asks and revokes", async () => {
    GET.mockResolvedValue(token);
    POST.mockResolvedValue({ response: { ok: true } });
    const { wrapper, router } = await mountPage(
      OAuth2TokenRevokePage,
      { id: 4 },
      "/user/oauth2_token/4/revoke",
    );

    expect(wrapper.text()).toContain("Do you want to revoke 'OAuth2 token 4 (Mein Client)'?");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/user/oauth2-tokens/{id}/revoke", {
      params: { path: { id: 4 } },
    });
    expect(router.currentRoute.value.fullPath).toBe("/user/oauth2_tokens");
    expect(takeFlash()).toBe("OAuth2 token successfully revoked");
  });

  it("shows a refused revoke and a failed load", async () => {
    GET.mockResolvedValueOnce(token);
    POST.mockResolvedValue({
      response: { ok: false },
      error: { message: "Already revoked" },
    });
    const { wrapper, router } = await mountPage(
      OAuth2TokenRevokePage,
      { id: 4 },
      "/user/oauth2_token/4/revoke",
    );
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Already revoked");
    expect(router.currentRoute.value.name).toBe("oauth2-token-revoke");

    GET.mockResolvedValue({ error: { message: "Gone" } });
    const failed = await mountPage(OAuth2TokenRevokePage, { id: 4 }, "/user/oauth2_token/4/revoke");
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Gone");
    expect(failed.wrapper.find("form").exists()).toBe(false);
  });
});
