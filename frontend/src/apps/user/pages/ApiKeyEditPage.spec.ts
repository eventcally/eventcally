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
import ApiKeyEditPage from "./ApiKeyEditPage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign, success].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

describe("ApiKeyEditPage", () => {
  it("creates a key and hands the key to the read page", async () => {
    POST.mockResolvedValue({ data: { id: 5, key: "SECRET" } });
    const { wrapper, router } = await mountPage(ApiKeyEditPage, {}, "/user/api_key/create");
    const push = vi.spyOn(router, "push");

    expect(wrapper.find(".breadcrumb").text()).toContain("Create API key");
    await wrapper.find("#name").setValue("Mein Key");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/user/api-keys", {
      body: { name: "Mein Key" },
    });
    expect(push).toHaveBeenCalledWith({
      name: "api-key",
      params: { apiKeyId: 5 },
      state: { key: "SECRET" },
    });
    expect(router.currentRoute.value.fullPath).toBe("/user/api_key/5");
    expect(router.currentRoute.value.fullPath).not.toContain("SECRET");
  });

  it("shows the refusal of a second key", async () => {
    POST.mockResolvedValue({
      error: { message: "The maximum number of API keys has been reached." },
    });
    const { wrapper, router } = await mountPage(ApiKeyEditPage, {}, "/user/api_key/create");

    await wrapper.find("#name").setValue("Zweiter");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toContain("maximum number");
    expect(router.currentRoute.value.name).toBe("api-key-create");
  });

  it("renames a key and leaves a message for the read page", async () => {
    GET.mockResolvedValue({ data: { id: 5, name: "Alt", rate_limits: [] } });
    PUT.mockResolvedValue({ response: { ok: true } });
    const { wrapper, router } = await mountPage(
      ApiKeyEditPage,
      { id: 5 },
      "/user/api_key/5/update",
    );

    expect(wrapper.find<HTMLInputElement>("#name").element.value).toBe("Alt");
    expect(wrapper.find(".breadcrumb").text()).toContain("Update API key");
    await wrapper.find("#name").setValue("Neu");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith("/bff/user/api-keys/{id}", {
      params: { path: { id: 5 } },
      body: { name: "Neu" },
    });
    expect(router.currentRoute.value.fullPath).toBe("/user/api_key/5");
    expect(takeFlash()).toBe("API key successfully updated");
  });

  it("shows the field error of a failed update", async () => {
    GET.mockResolvedValue({ data: { id: 5, name: "Alt", rate_limits: [] } });
    PUT.mockResolvedValue({
      response: { ok: false },
      error: { errors: [{ loc: ["name"], msg: "Required" }] },
    });
    const { wrapper } = await mountPage(ApiKeyEditPage, { id: 5 }, "/user/api_key/5/update");

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find("[data-test=field-error]").text()).toBe("Required");
  });

  it("shows unmapped errors and a failed load", async () => {
    GET.mockResolvedValueOnce({
      data: { id: 5, name: "Alt", rate_limits: [] },
    });
    PUT.mockResolvedValue({
      response: { ok: false },
      error: { errors: [{ loc: ["x"], msg: "Odd" }] },
    });
    const { wrapper } = await mountPage(ApiKeyEditPage, { id: 5 }, "/user/api_key/5/update");
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Odd");

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(ApiKeyEditPage, { id: 5 }, "/user/api_key/5/update");
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");
    expect(failed.wrapper.find("form").exists()).toBe(false);
  });
});
