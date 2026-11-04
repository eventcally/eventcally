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

import { mountPage } from "../testing";
import GeneralSettingsPage from "./GeneralSettingsPage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

describe("GeneralSettingsPage", () => {
  it("preselects the language and saves with a full page load", async () => {
    GET.mockResolvedValue({ data: { locale: "de" } });
    PUT.mockResolvedValue({ data: { redirect_url: "/profile" } });
    const { wrapper } = await mountPage(GeneralSettingsPage);

    expect(wrapper.find<HTMLSelectElement>("#locale").element.value).toBe("de");
    await wrapper.find("#locale").setValue("en");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith("/bff/user/settings/general", {
      body: { locale: "en" },
    });
    expect(assign).toHaveBeenCalledWith("/profile");
  });

  it("sends null for the default language", async () => {
    GET.mockResolvedValue({ data: { locale: null } });
    PUT.mockResolvedValue({ data: { redirect_url: "/profile" } });
    const { wrapper } = await mountPage(GeneralSettingsPage);

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith("/bff/user/settings/general", {
      body: { locale: null },
    });
  });

  it("shows a failed save and stays", async () => {
    GET.mockResolvedValue({ data: { locale: null } });
    PUT.mockResolvedValue({ error: { message: "Nope" } });
    const { wrapper } = await mountPage(GeneralSettingsPage);

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Nope");
    expect(assign).not.toHaveBeenCalled();
  });

  it("shows a failed load", async () => {
    GET.mockResolvedValue({ error: {} });
    const { wrapper } = await mountPage(GeneralSettingsPage);

    expect(wrapper.find(".alert-danger").text()).toBe("Error");
    expect(wrapper.find("form").exists()).toBe(false);
  });
});
