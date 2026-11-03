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

import { setFlash } from "@/shared/flash";
import { mountPage } from "../testing";
import OAuth2TokensPage from "./OAuth2TokensPage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign, success].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

const items = [
  {
    id: 1,
    client_name: "Mein Client",
    scope: "openid",
    issued_at: "2026-11-03T14:38:45Z",
    expires_at: "2026-11-03T15:38:45Z",
    status: null,
  },
  {
    id: 2,
    client_name: "Mein Client",
    scope: "openid",
    issued_at: "2026-11-02T10:00:00Z",
    expires_at: "2026-11-02T11:00:00Z",
    status: "expired",
  },
  {
    id: 3,
    client_name: "Mein Client",
    scope: "openid",
    issued_at: "2026-11-03T14:38:45Z",
    expires_at: "2026-11-03T15:38:45Z",
    status: "revoked",
  },
];

describe("OAuth2TokensPage", () => {
  it("lists the tokens with their status and a revoke link for the unrevoked ones", async () => {
    GET.mockResolvedValue({
      data: { items, page: 1, per_page: 20, total: 3, pages: 1 },
    });
    const { wrapper } = await mountPage(OAuth2TokensPage, {}, "/user/oauth2_tokens");

    const rows = wrapper.findAll("tbody tr");
    expect(rows).toHaveLength(3);
    expect(rows[0].text()).not.toContain("Expired");
    expect(rows[0].find('a[href="/user/oauth2_token/1/revoke"]').exists()).toBe(true);
    expect(rows[1].text()).toContain("Expired");
    expect(rows[2].text()).toContain("Revoked");
    expect(rows[2].find("a").exists()).toBe(false);
    expect(wrapper.text()).toContain("Application");
  });

  it("shows the message of a revoke and the error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    setFlash("OAuth2 token successfully revoked");
    const { wrapper } = await mountPage(OAuth2TokensPage, {}, "/user/oauth2_tokens");

    expect(success).toHaveBeenCalledWith("OAuth2 token successfully revoked");
    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });
});
