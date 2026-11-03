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
import OAuth2ClientsPage from "./OAuth2ClientsPage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign, success].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

describe("OAuth2ClientsPage", () => {
  it("lists the clients and links to them", async () => {
    GET.mockResolvedValue({
      data: {
        items: [{ id: 3, client_name: "Mein Client" }],
        page: 1,
        per_page: 20,
        total: 1,
        pages: 1,
      },
    });
    const { wrapper } = await mountPage(OAuth2ClientsPage, {}, "/user/oauth2_clients");

    expect(GET).toHaveBeenCalledWith("/bff/user/oauth2-clients", {
      params: { query: { page: 1 } },
    });
    expect(wrapper.find('a[href="/user/oauth2_client/3"]').text()).toBe("Mein Client");
    expect(wrapper.find('a[href="/user/oauth2_client/create"]').text()).toContain(
      "Create OAuth2 client",
    );
  });

  it("shows the message a previous page left and the error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    setFlash("OAuth2 client successfully deleted");
    const { wrapper } = await mountPage(OAuth2ClientsPage, {}, "/user/oauth2_clients");

    expect(success).toHaveBeenCalledWith("OAuth2 client successfully deleted");
    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });
});
