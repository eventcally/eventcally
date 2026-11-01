import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "de", csrfToken: "x", loginUrl: "/login" } }));
vi.mock("vue-router", () => ({ useRoute: () => ({ params: { id: "5" } }) }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import EventDatesWidget from "./EventDatesWidget.vue";

const EVENT_URL = "/bff/public/widget/organizations/{id}/event-dates";

const photo = {
  url_200: "/image/1?s=200",
  url_500: "/image/1?s=500",
  copyright_text: "Fotograf",
  license_code: "CC0",
  license_url: "http://license",
};

function date(id: number, over: Record<string, unknown> = {}, extra: Record<string, unknown> = {}) {
  return {
    id,
    start: "2040-04-02T17:00:00Z",
    end: null,
    allday: false,
    event: {
      id,
      name: `Event ${id}`,
      description_preview: "Eine Beschreibung ".repeat(10).trim(),
      status: "cancelled",
      public_status: "published",
      booked_up: false,
      attendance_mode: "offline",
      organization_id: 5,
      organization_name: "Crew",
      organizer_name: "Veranstalter",
      place_name: "Halle",
      photo,
      ...over,
    },
    ...extra,
  };
}

function respond(items = [date(1), date(2)], total = items.length) {
  GET.mockImplementation(async (path: string) => {
    if (path === "/bff/public/widget/categories") {
      return { data: { items: [{ id: 4, name: "Musik" }] } };
    }
    return { data: { items, page: 1, per_page: 20, total, pages: Math.ceil(total / 20) } };
  });
}

const eventQueries = () =>
  GET.mock.calls.filter((c) => c[0] === EVENT_URL).map((c) => c[1].params.query);

const mounted: { unmount: () => void }[] = [];

function mountWidget(settings: Record<string, unknown> | null = {}) {
  window.__eventcallyWidget = {
    settings: settings && { showPagination: true, eventsPerPage: 20, ...settings },
    ready: false,
    initialHref: "http://host/organizations/5/widget/eventdates?",
  };
  const wrapper = mount(EventDatesWidget, {
    attachTo: document.body,
    global: {
      plugins: [
        createBootstrap(),
        createI18n({
          legacy: false,
          locale: "en",
          messages: {
            en: {
              "EventStatus.cancelled": "Cancelled",
              "Page %(page)d of %(pages)d (%(total)d total)":
                "Page {page} of {pages} ({total} total)",
            },
          },
        }),
      ],
    },
  });
  mounted.push(wrapper);
  return wrapper;
}

describe("EventDatesWidget", () => {
  beforeEach(() => {
    GET.mockReset();
    window.parentIFrame = { sendMessage: vi.fn(), scrollToOffset: vi.fn() };
    window.scrollTo = vi.fn() as unknown as typeof window.scrollTo;
    window.history.replaceState(null, "", "/organizations/5/widget/eventdates");
    document.body.innerHTML = "";
  });

  afterEach(() => {
    mounted.splice(0).forEach((w) => w.unmount());
  });

  const sent = () =>
    (window.parentIFrame!.sendMessage as ReturnType<typeof vi.fn>).mock.calls.map((c) => c[0].data);

  it("sends what the legacy URL says to the BFF, without waiting for any message", async () => {
    window.history.replaceState(
      null,
      "",
      "/organizations/5/widget/eventdates?date_from=2040-04-01&keyword=Jam&category_id=3&tag=music&page=2&per_page=3&s_ft=Arial",
    );
    respond();
    const wrapper = mountWidget();
    await flushPromises();

    expect(eventQueries()).toEqual([
      {
        date_from: "2040-04-01",
        keyword: "Jam",
        category_id: "3",
        tag: "music",
        page: "2",
        per_page: "3",
      },
    ]);
    expect(GET.mock.calls[0][1].params.path).toEqual({ id: 5 });
    expect((wrapper.find("input[type=date]").element as HTMLInputElement).value).toBe("2040-04-01");
  });

  it("renders the start only in Berlin time, the organizer of an own event and a real link", async () => {
    respond();
    const wrapper = mountWidget();
    await flushPromises();

    const card = wrapper.find('[data-test="event-card"]');
    expect(card.text()).toContain("Event 1");
    expect(card.text()).toContain("Cancelled");
    expect(card.text()).toContain("02.04.2040 19:00");
    expect(card.text()).toContain("Veranstalter");
    expect(card.text()).not.toContain("Crew");
    expect(card.text()).toContain("© Fotograf");
    expect(card.findAll("a.stretched-link").map((a) => a.attributes("href"))).toEqual([
      `${location.origin}/eventdate/1`,
      `${location.origin}/eventdate/1`,
    ]);
    expect(card.find("a.stretched-link").attributes("target")).toBe("_blank");
    expect(card.find("a.stretched-link").attributes("rel")).toBe("noopener noreferrer");
  });

  it("shows the organization of an event of another organization and no time for all-day", async () => {
    respond([date(1, { organization_id: 9, organization_name: "Andere" }, { allday: true })]);
    const wrapper = mountWidget();
    await flushPromises();

    const card = wrapper.find('[data-test="event-card"]');
    expect(card.text()).toContain("Andere");
    expect(card.text()).not.toContain("Veranstalter");
    expect(card.text()).toContain("02.04.2040");
    expect(card.text()).not.toContain("19:00");
  });

  it("cuts the description on the mobile card", async () => {
    respond([date(1, { description_preview: "wort ".repeat(40).trim(), photo: null })]);
    const wrapper = mountWidget();
    await flushPromises();

    const texts = wrapper.findAll(".card-text").map((p) => p.text());
    expect(texts[0].length).toBeGreaterThan(150);
    expect(texts[1].length).toBeLessThan(101);
    expect(texts[1].endsWith("…")).toBe(true);
  });

  it("reports the page view of the loaded URL once the resizer is ready and link clicks", async () => {
    respond();
    window.__eventcallyWidget = undefined;
    const wrapper = mountWidget();
    await flushPromises();
    expect(sent()).toEqual([]);

    window.__eventcallyWidget!.ready = true;
    window.dispatchEvent(new CustomEvent("eventcally:ready"));
    expect(sent()).toEqual([
      { event: "pageView", url: "http://host/organizations/5/widget/eventdates?" },
    ]);

    const link = wrapper.find("a.stretched-link");
    link.element.addEventListener("click", (e) => e.preventDefault());
    await link.trigger("click");
    expect(sent().at(-1)).toEqual({ event: "linkClick", url: `${location.origin}/eventdate/1` });
  });

  it("searches with the legacy URL shape, loads, scrolls to the top and counts a page view", async () => {
    window.history.replaceState(null, "", "/organizations/5/widget/eventdates?s_ft=Verdana&page=2");
    respond();
    const wrapper = mountWidget();
    await flushPromises();

    const inputs = wrapper.findAll("input");
    await inputs[0].setValue("2040-01-01");
    await inputs[2].setValue("Jam");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(location.pathname + location.search).toBe(
      "/organizations/5/widget/eventdates?s_ft=Verdana&s_bg=&s_pr=&s_li=&date_from=2040-01-01&date_to=&category_id=0&keyword=Jam",
    );
    expect(eventQueries().at(-1)).toEqual({
      date_from: "2040-01-01",
      date_to: "",
      keyword: "Jam",
      category_id: "0",
    });
    expect(window.parentIFrame!.scrollToOffset).toHaveBeenCalledWith(0, 0);
    expect(sent().at(-1)).toEqual({ event: "pageView", url: location.href });
  });

  it("changes the page through the pager and keeps the other parameters", async () => {
    window.history.replaceState(null, "", "/organizations/5/widget/eventdates?keyword=Jam");
    respond(
      Array.from({ length: 3 }, (_, i) => date(i + 1)),
      45,
    );
    const wrapper = mountWidget();
    await flushPromises();
    expect(wrapper.text()).toContain("Page 1 of 3 (45 total)");

    await wrapper.find("button[aria-label='Next page']").trigger("click");
    await flushPromises();

    expect(location.search).toBe("?keyword=Jam&page=2");
    expect(eventQueries().at(-1)).toEqual({ keyword: "Jam", page: "2" });
    expect(sent().at(-1)).toEqual({ event: "pageView", url: location.href });
  });

  it("reloads on the back button", async () => {
    respond();
    const wrapper = mountWidget();
    await flushPromises();
    window.history.replaceState(null, "", "/organizations/5/widget/eventdates?keyword=Back");
    window.dispatchEvent(new PopStateEvent("popstate"));
    await flushPromises();

    expect(eventQueries().at(-1)).toEqual({ keyword: "Back" });
    expect((wrapper.findAll("input")[2].element as HTMLInputElement).value).toBe("Back");
  });

  it("shows an error and retries", async () => {
    GET.mockImplementation(async (path: string) =>
      path === "/bff/public/widget/categories"
        ? { data: { items: [] } }
        : { error: { message: "Boom" } },
    );
    const wrapper = mountWidget();
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Boom");

    respond();
    await wrapper.find("button[aria-label='Retry']").trigger("click");
    await flushPromises();
    expect(wrapper.find(".alert-danger").exists()).toBe(false);
    expect(wrapper.findAll('[data-test="event-card"]')).toHaveLength(2);
  });

  it("falls back to a generic error text", async () => {
    GET.mockImplementation(async (path: string) =>
      path === "/bff/public/widget/categories" ? { data: { items: [] } } : { error: {} },
    );
    const wrapper = mountWidget();
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Error");
  });

  it("drops an unsafe style and applies a safe one", async () => {
    respond();
    const wrapper = mountWidget({ fontFamily: "Verdana", background: "red;} body{x:y" });
    await flushPromises();

    const css = wrapper.find("style").text();
    expect(css).toContain("font-family: Verdana;");
    expect(css).not.toContain("x:y");
  });

  it("hides the pager when pagination is off, and works without parentIFrame or settings", async () => {
    respond();
    delete window.parentIFrame;
    const wrapper = mountWidget(null);
    await flushPromises();
    expect(wrapper.findAll('[data-test="event-card"]')).toHaveLength(2);
    expect(wrapper.find(".pagination").exists()).toBe(true);
    wrapper.unmount();

    const off = mountWidget({ showPagination: false });
    await flushPromises();
    expect(off.find(".pagination").exists()).toBe(false);
  });

  it("prints", async () => {
    respond();
    window.print = vi.fn();
    const wrapper = mountWidget();
    await flushPromises();
    await wrapper.find(".btn-print").trigger("click");
    expect(window.print).toHaveBeenCalled();
  });
});
