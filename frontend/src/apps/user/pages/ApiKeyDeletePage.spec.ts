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
import ApiKeyDeletePage from "./ApiKeyDeletePage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign, success].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

const key = { data: { id: 5, name: "Mein Key", rate_limits: [] } };

describe("ApiKeyDeletePage", () => {
  it("asks for the name and deletes", async () => {
    GET.mockResolvedValue(key);
    POST.mockResolvedValue({ response: { ok: true } });
    const { wrapper, router } = await mountPage(
      ApiKeyDeletePage,
      { id: 5 },
      "/user/api_key/5/delete",
    );

    expect(wrapper.text()).toContain("Do you want to delete 'API key 5'?");
    await wrapper.find("#name").setValue("Mein Key");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/user/api-keys/{id}/delete", {
      params: { path: { id: 5 } },
      body: { name: "Mein Key" },
    });
    expect(router.currentRoute.value.fullPath).toBe("/user/api_keys");
    expect(takeFlash()).toBe("API key successfully deleted");
  });

  it("shows the mismatch at the field and stays", async () => {
    GET.mockResolvedValue(key);
    POST.mockResolvedValue({
      response: { ok: false },
      error: { errors: [{ loc: ["name"], msg: "Does not match" }] },
    });
    const { wrapper, router } = await mountPage(
      ApiKeyDeletePage,
      { id: 5 },
      "/user/api_key/5/delete",
    );

    await wrapper.find("#name").setValue("Falsch");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find("[data-test=field-error]").text()).toBe("Does not match");
    expect(router.currentRoute.value.name).toBe("api-key-delete");
  });

  it("shows other errors and a failed load", async () => {
    GET.mockResolvedValueOnce(key);
    POST.mockResolvedValue({
      response: { ok: false },
      error: { message: "Forbidden" },
    });
    const { wrapper } = await mountPage(ApiKeyDeletePage, { id: 5 }, "/user/api_key/5/delete");
    await wrapper.find("#name").setValue("Mein Key");
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");

    POST.mockResolvedValue({
      response: { ok: false },
      error: { errors: [{ loc: ["other"], msg: "Odd" }] },
    });
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Odd");

    GET.mockResolvedValue({ error: { message: "Gone" } });
    const failed = await mountPage(ApiKeyDeletePage, { id: 5 }, "/user/api_key/5/delete");
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Gone");
    expect(failed.wrapper.find("form").exists()).toBe(false);
  });
});
