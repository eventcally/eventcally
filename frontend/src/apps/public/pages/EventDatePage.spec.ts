import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login", docsUrl: null } }));
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success: vi.fn(), error: vi.fn() }) }));
const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import { makeEvent } from "../components/eventFixture";
import EventDatePage from "./EventDatePage.vue";

async function mountPage() {
  const wrapper = mount(EventDatePage, {
    props: { id: 9 },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  await flushPromises();
  return wrapper;
}

describe("EventDatePage", () => {
  beforeEach(() => {
    GET.mockReset();
    document.body.innerHTML = "";
  });

  it("renders the event with the date of the page", async () => {
    GET.mockResolvedValue({
      data: {
        id: 9,
        start: "2026-12-05T17:00:00Z",
        end: null,
        allday: true,
        event: makeEvent({ calendar_links: { ics: "/eventdate/9/ical", google: "https://google.test" } }),
      },
    });
    const wrapper = await mountPage();

    expect(GET).toHaveBeenCalledWith("/bff/public/event-dates/{id}", { params: { path: { id: 9 } } });
    expect(wrapper.find("h1").text()).toContain("Stadtfest");
    expect(wrapper.text()).toContain("2026");
  });

  it("shows the load error", async () => {
    GET.mockResolvedValue({ error: { message: "Not found" } });
    const wrapper = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Not found");
  });

  it("falls back to a generic error", async () => {
    GET.mockResolvedValue({ error: undefined });
    const wrapper = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Error");
  });
});
