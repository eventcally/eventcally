import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login", docsUrl: null } }));
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success: vi.fn(), error: vi.fn() }) }));
const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import { makeEvent } from "../components/eventFixture";
import EventPage from "./EventPage.vue";

async function mountPage() {
  const wrapper = mount(EventPage, {
    props: { id: 4 },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  await flushPromises();
  return wrapper;
}

describe("EventPage", () => {
  beforeEach(() => {
    GET.mockReset();
    document.body.innerHTML = "";
  });

  it("loads and renders the event", async () => {
    GET.mockResolvedValue({ data: makeEvent() });
    const wrapper = await mountPage();

    expect(GET).toHaveBeenCalledWith("/bff/public/events/{id}", { params: { path: { id: 4 } } });
    expect(wrapper.find("h1").text()).toContain("Stadtfest");
  });

  it("shows the load error", async () => {
    GET.mockResolvedValue({ error: { message: "Not found" } });
    const wrapper = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Not found");
    expect(wrapper.find("h1").exists()).toBe(false);
  });

  it("falls back to a generic error", async () => {
    GET.mockResolvedValue({ error: undefined });
    const wrapper = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Error");
  });
});
