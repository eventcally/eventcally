import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({
  boot: { locale: "en", csrfToken: "x", loginUrl: "/login" },
}));

const GET = vi.fn();
const PUT = vi.fn();
vi.mock("@/shared/api", () => ({
  api: {
    GET: (...args: unknown[]) => GET(...args),
    PUT: (...args: unknown[]) => PUT(...args),
    POST: vi.fn(),
  },
}));

const success = vi.fn();
vi.mock("@/shared/notify", () => ({
  useNotify: () => ({ success, error: vi.fn() }),
}));

import SettingsPage from "./SettingsPage.vue";

const settings = {
  start_page: null,
  tos: "<p>Terms</p>",
  legal_notice: null,
  contact: null,
  privacy: null,
  announcement: null,
};

async function mountPage() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/", name: "home", component: { template: "<div/>" } }],
  });
  const wrapper = mount(SettingsPage, {
    global: {
      plugins: [
        router,
        createBootstrap(),
        createI18n({ legacy: false, locale: "en", messages: { en: {} } }),
      ],
    },
  });
  await flushPromises();
  return wrapper;
}

describe("SettingsPage", () => {
  beforeEach(() => {
    GET.mockReset();
    PUT.mockReset();
    success.mockReset();
  });

  it("renders one card per setting plus the reset card", async () => {
    GET.mockResolvedValue({ data: settings });
    const wrapper = await mountPage();

    expect(GET).toHaveBeenCalledWith("/bff/admin/settings");
    expect(wrapper.findAll(".card:not(.border-danger) .card-header")).toHaveLength(6);
    expect(wrapper.text()).toContain("Terms");
    expect(wrapper.find(".card.border-danger").exists()).toBe(true);
  });

  it("saves only the edited setting", async () => {
    GET.mockResolvedValue({ data: settings });
    PUT.mockResolvedValue({});
    const wrapper = await mountPage();

    const card = wrapper.findAll(".card:not(.border-danger)")[5];
    await card.find("button").trigger("click");
    await card.find("textarea").setValue("Hallo");
    await card.find("form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledTimes(1);
    expect(PUT).toHaveBeenCalledWith("/bff/admin/settings/{key}", {
      params: { path: { key: "announcement" } },
      body: { value: "Hallo" },
    });
    expect(card.text()).toContain("Hallo");
  });

  it("shows the server message inside the card when saving fails", async () => {
    GET.mockResolvedValue({ data: settings });
    PUT.mockResolvedValue({ error: { name: "Forbidden", message: "Nope" } });
    const wrapper = await mountPage();

    const card = wrapper.findAll(".card:not(.border-danger)")[0];
    await card.find("button").trigger("click");
    await card.find("textarea").setValue("x");
    await card.find("form").trigger("submit");
    await flushPromises();

    expect(card.find(".alert-danger").text()).toBe("Nope");
    expect(success).not.toHaveBeenCalled();
  });

  it("shows an alert when the settings cannot be loaded", async () => {
    GET.mockResolvedValue({ error: { name: "Forbidden", message: "Denied" } });
    const wrapper = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Denied");
    expect(wrapper.find(".card").exists()).toBe(false);
  });
});
