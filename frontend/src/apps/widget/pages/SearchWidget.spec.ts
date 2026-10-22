import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { defaultSettings, type SearchSettings } from "@/shared/customWidget";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import SearchWidget from "./SearchWidget.vue";

const photo = {
  url_200: "/image/1?s=200",
  url_500: "/image/1?s=500",
  copyright_text: "Fotograf",
  license_code: "CC0",
  license_url: "http://license",
};

function date(id: number, over: Record<string, unknown> = {}) {
  return {
    id,
    start: "2026-10-03T10:00:00",
    end: null,
    allday: false,
    event: {
      id,
      name: `Event ${id}`,
      description_preview: "Eine Beschreibung ".repeat(10).trim(),
      status: "cancelled",
      public_status: "published",
      booked_up: true,
      attendance_mode: "online",
      organization_name: "Crew",
      organizer_name: "Veranstalter",
      place_name: "Halle",
      photo,
      ...over,
    },
  };
}

function respond(items = [date(1), date(2)], total = items.length) {
  GET.mockImplementation(async (path: string) => {
    if (path === "/bff/public/widget/categories") {
      return { data: { items: [{ id: 4, name: "Musik" }] } };
    }
    return { data: { items, page: 1, per_page: 10, total, pages: 1 } };
  });
}

const search = () =>
  GET.mock.calls
    .filter((c) => c[0] === "/bff/public/widget/event-dates")
    .map((c) => c[1].params.query)
    .at(-1);

function send(settings: Partial<SearchSettings> = {}) {
  window.dispatchEvent(
    new CustomEvent("eventcally:settings", {
      detail: { ...defaultSettings("search", null), ...settings },
    }),
  );
}

function mountWidget() {
  return mount(SearchWidget, {
    attachTo: document.body,
    global: {
      plugins: [
        createBootstrap(),
        createI18n({
          legacy: false,
          locale: "en",
          messages: {
            en: { "EventStatus.cancelled": "Cancelled", "EventAttendanceMode.online": "Online" },
          },
        }),
      ],
    },
  });
}

describe("SearchWidget", () => {
  beforeEach(() => {
    GET.mockReset();
    window.__eventcallyWidget = { settings: null, ready: false };
    window.parentIFrame = { sendMessage: vi.fn(), scrollToOffset: vi.fn() };
    window.scrollTo = vi.fn() as unknown as typeof window.scrollTo;
    document.body.innerHTML = "";
  });

  it("renders nothing and does not load before the settings arrive", async () => {
    respond();
    const wrapper = mountWidget();
    await flushPromises();

    expect(wrapper.html()).toBe("<!--v-if-->");
    expect(GET).not.toHaveBeenCalled();
  });

  it("loads the event dates once the settings arrive", async () => {
    respond();
    const wrapper = mountWidget();
    send({ organizationId: 7, eventsPerPage: 80 });
    await flushPromises();

    expect(search()).toMatchObject({ page: 1, per_page: 50, organization_id: 7 });
    expect(search().date_from).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(wrapper.findAll('[data-test="event-card"]')).toHaveLength(2);
  });

  it("renders the card with pills, preview, organization, organizer and place", async () => {
    respond();
    const wrapper = mountWidget();
    send();
    await flushPromises();

    const card = wrapper.find('[data-test="event-card"]');
    expect(card.text()).toContain("Event 1");
    expect(card.text()).toContain("Cancelled");
    expect(card.text()).toContain("Online");
    expect(card.text()).toContain("Booked up");
    expect(card.text()).toContain("Eine Beschreibung");
    expect(card.text()).toContain("Crew");
    expect(card.text()).toContain("Veranstalter");
    expect(card.text()).toContain("Halle");
    expect(card.text()).toContain("© Fotograf");
    expect(card.find("a[href='http://license']").text()).toBe("CC0");
    expect(card.findAll("img").map((i) => i.attributes("src"))).toEqual([
      "/image/1?s=200",
      "/image/1?s=500",
    ]);
  });

  it("hides the organizer when it is the organization", async () => {
    respond([date(1, { organizer_name: "Crew" })]);
    const wrapper = mountWidget();
    send();
    await flushPromises();

    expect(wrapper.find(".fa-server").exists()).toBe(false);
  });

  it("renders one line per date in the text layout", async () => {
    respond();
    const wrapper = mountWidget();
    send({ layout: "text" });
    await flushPromises();

    expect(wrapper.findAll('[data-test="event-line"]')).toHaveLength(2);
    expect(wrapper.find('[data-test="event-card"]').exists()).toBe(false);
  });

  it("injects the stylesheet of the settings", async () => {
    respond();
    const wrapper = mountWidget();
    send({ linkColor: "#123456" });
    await flushPromises();

    expect(wrapper.find("style").text()).toContain("color: #123456;");
  });

  it("filters and loads the categories only with the filter", async () => {
    respond();
    const wrapper = mountWidget();
    send();
    await flushPromises();

    expect(GET).toHaveBeenCalledWith("/bff/public/widget/categories");
    expect(wrapper.find("select").text()).toContain("Musik");

    await wrapper.find("input[type=text], input:not([type])").setValue("jazz");
    await wrapper.find("select").setValue(4);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(search()).toMatchObject({ keyword: "jazz", category_id: 4, page: 1 });
  });

  it("has no filter and no category request when switched off", async () => {
    respond();
    const wrapper = mountWidget();
    send({ showFilter: false });
    await flushPromises();

    expect(wrapper.find("form").exists()).toBe(false);
    expect(GET).not.toHaveBeenCalledWith("/bff/public/widget/categories");
  });

  it("shows the pager only when there is more than one page and pages on click", async () => {
    respond([date(1)], 25);
    const wrapper = mountWidget();
    send({ eventsPerPage: 10 });
    await flushPromises();

    const next = wrapper.find(
      'button[aria-label="Go to next page"], button[aria-label="Next page"]',
    );
    expect(wrapper.find(".pagination").exists()).toBe(true);
    await next.trigger("click");
    await flushPromises();

    expect(search()).toMatchObject({ page: 2 });
    expect(window.parentIFrame!.scrollToOffset).toHaveBeenCalledWith(0, 0);
  });

  it("hides the pager for a single page and when switched off", async () => {
    respond([date(1)], 5);
    const wrapper = mountWidget();
    send();
    await flushPromises();
    expect(wrapper.find(".pagination").exists()).toBe(false);
  });

  it("reloads from page 1 when the settings change", async () => {
    respond();
    const wrapper = mountWidget();
    send({ organizationId: 1 });
    await flushPromises();

    send({ organizationId: 2 });
    await flushPromises();

    expect(search()).toMatchObject({ organization_id: 2 });
    expect(wrapper.findAll('[data-test="event-card"]')).toHaveLength(2);
  });

  it("opens the event date and reports the click", async () => {
    respond();
    const open = vi.spyOn(window, "open").mockImplementation(() => null);
    const wrapper = mountWidget();
    send();
    await flushPromises();

    await wrapper.find("a.stretched-link").trigger("click");

    expect(open).toHaveBeenCalledWith(`${location.origin}/eventdate/1`);
    expect(window.parentIFrame!.sendMessage).toHaveBeenCalledWith({
      type: "EVENTCALLY_ANALYTICS_EVENT",
      data: { event: "linkClick", url: `${location.origin}/eventdate/1` },
    });
  });

  it("opens the search with the current parameters", async () => {
    respond();
    const open = vi.spyOn(window, "open").mockImplementation(() => null);
    const wrapper = mountWidget();
    send({ organizationId: 7 });
    await flushPromises();

    await wrapper.find("a.underlined").trigger("click");

    const url = new URL(open.mock.calls.at(-1)![0] as string);
    expect(url.pathname).toBe("/eventdates");
    expect(url.searchParams.get("organization_id")).toBe("7");
    expect(url.searchParams.get("per_page")).toBe("10");
  });

  it("prints only when enabled and there are dates", async () => {
    respond();
    const print = vi.spyOn(window, "print").mockImplementation(() => {});
    const wrapper = mountWidget();
    send({ showPrintButton: true });
    await flushPromises();

    await wrapper.find(".btn-print").trigger("click");
    expect(print).toHaveBeenCalled();

    send({ showPrintButton: false });
    await flushPromises();
    expect(wrapper.find(".btn-print").exists()).toBe(false);
  });

  it("shows the error and retries", async () => {
    GET.mockResolvedValue({ error: { message: "Boom" } });
    const wrapper = mountWidget();
    send({ showFilter: false });
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Boom");

    respond();
    await wrapper.find("button[aria-label='Retry']").trigger("click");
    await flushPromises();

    expect(wrapper.find(".alert-danger").exists()).toBe(false);
    expect(wrapper.findAll('[data-test="event-card"]')).toHaveLength(2);
  });
});
