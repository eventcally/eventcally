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

import { setFlash } from "@/shared/flash";
import { mountPage } from "../testing";
import ApiKeysPage from "./ApiKeysPage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign, success].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

const page = (items: object[], over = {}) => ({
  data: {
    items,
    page: 1,
    per_page: 20,
    total: items.length,
    pages: 1,
    ...over,
  },
});

describe("ApiKeysPage", () => {
  it("lists the keys sorted by name and links to them", async () => {
    GET.mockResolvedValue(
      page([{ id: 4, name: "Mein Schluessel", created_at: "2026-11-03T14:41:00Z" }]),
    );
    const { wrapper } = await mountPage(ApiKeysPage, {}, "/user/api_keys");

    expect(GET).toHaveBeenCalledWith("/bff/user/api-keys", {
      params: { query: { page: 1, sort: "name" } },
    });
    expect(wrapper.find('a[href="/user/api_key/4"]').text()).toBe("Mein Schluessel");
    expect(wrapper.text()).toContain("Created at");
    expect(wrapper.find('a[href="/user/api_key/create"]').text()).toContain("Create API key");
    expect(wrapper.find(".breadcrumb").text()).toContain("API keys");
  });

  it("reloads with the other sort", async () => {
    GET.mockResolvedValue(page([]));
    const { wrapper } = await mountPage(ApiKeysPage, {}, "/user/api_keys");

    await wrapper.find("#sort").setValue("-created_at");
    await flushPromises();

    expect(GET).toHaveBeenLastCalledWith("/bff/user/api-keys", {
      params: { query: { page: 1, sort: "-created_at" } },
    });
  });

  it("shows the message a previous page left", async () => {
    GET.mockResolvedValue(page([]));
    setFlash("API key successfully deleted");
    await mountPage(ApiKeysPage, {}, "/user/api_keys");

    expect(success).toHaveBeenCalledWith("API key successfully deleted");
  });

  it("shows the error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const { wrapper } = await mountPage(ApiKeysPage, {}, "/user/api_keys");

    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });

  it("pages through the list", async () => {
    GET.mockResolvedValue(page([{ id: 1, name: "a" }], { total: 40, pages: 2 }));
    const { wrapper, router } = await mountPage(ApiKeysPage, {}, "/user/api_keys");

    await wrapper.find('button[aria-label="Next page"]').trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.query.page).toBe("2");
    expect(GET).toHaveBeenLastCalledWith("/bff/user/api-keys", {
      params: { query: { page: 2, sort: "name" } },
    });
  });
});
