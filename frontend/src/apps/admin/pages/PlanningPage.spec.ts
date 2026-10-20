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
  },
}));

vi.mock("@/shared/notify", () => ({
  useNotify: () => ({ success: vi.fn(), error: vi.fn() }),
}));

import PlanningPage from "./PlanningPage.vue";

async function mountPage() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/", name: "home", component: { template: "<div/>" } }],
  });
  const wrapper = mount(PlanningPage, {
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

async function edit(wrapper: Awaited<ReturnType<typeof mountPage>>, text: string) {
  await wrapper.find("button").trigger("click");
  await wrapper.find("textarea").setValue(text);
  await wrapper.find("form").trigger("submit");
  await flushPromises();
}

describe("PlanningPage", () => {
  beforeEach(() => {
    GET.mockReset();
    PUT.mockReset();
  });

  it("shows the normalized value returned by the server after saving", async () => {
    GET.mockResolvedValue({ data: { planning_external_calendars: null } });
    PUT.mockResolvedValue({
      data: { planning_external_calendars: "[\n  1\n]" },
    });
    const wrapper = await mountPage();

    await edit(wrapper, "[1]");

    expect(PUT).toHaveBeenCalledWith("/bff/admin/planning", {
      body: { planning_external_calendars: "[1]" },
    });
    expect(wrapper.find("pre").text()).toBe("[\n  1\n]");
  });

  it("shows the JSON error inline and stays in the editor", async () => {
    GET.mockResolvedValue({ data: { planning_external_calendars: null } });
    PUT.mockResolvedValue({
      error: {
        name: "Unprocessable Entity",
        message: "m",
        errors: [{ loc: ["planning_external_calendars"], msg: "Expecting value" }],
      },
    });
    const wrapper = await mountPage();

    await edit(wrapper, "{");

    expect(wrapper.find(".alert-danger").text()).toBe("Expecting value");
    expect(wrapper.find("textarea").exists()).toBe(true);
  });
});
