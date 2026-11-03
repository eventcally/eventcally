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
import OAuth2ClientPage from "./OAuth2ClientPage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign, success].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

const client = {
  data: {
    id: 3,
    client_id: "cid",
    client_secret: "csecret",
    client_name: "Mein Client",
    client_uri: null,
    scope: "openid",
    scopes: ["openid"],
    redirect_uris: ["/a"],
    grant_types: ["authorization_code"],
    response_types: ["code"],
    token_endpoint_auth_method: ["none"],
    audit: { created_at: "2026-11-03T14:41:00Z" },
  },
};

describe("OAuth2ClientPage", () => {
  it("shows the client with the actions", async () => {
    GET.mockResolvedValue(client);
    const { wrapper } = await mountPage(OAuth2ClientPage, { id: 3 }, "/user/oauth2_client/3");

    expect(wrapper.find(".breadcrumb").text()).toContain("Mein Client");
    expect(wrapper.text()).toContain("csecret");
    expect(wrapper.find('a[href="/user/oauth2_client/3/update"]').exists()).toBe(true);
    expect(wrapper.find('a[href="/user/oauth2_client/3/delete"]').exists()).toBe(true);
    expect(wrapper.find("[data-test=audit]").exists()).toBe(true);
  });

  it("shows the message of a save and the error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    setFlash("OAuth2 client successfully created");
    const { wrapper } = await mountPage(OAuth2ClientPage, { id: 3 }, "/user/oauth2_client/3");

    expect(success).toHaveBeenCalledWith("OAuth2 client successfully created");
    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
    expect(wrapper.find(".breadcrumb").text()).toContain("OAuth2 client 3");
  });
});
