import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({
  boot: { locale: "en", csrfToken: "x", loginUrl: "/login", docsUrl: "https://docs.test" },
}));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

const calls = vi.hoisted(() => ({ scrollToHour: vi.fn(), changeView: vi.fn(), next: vi.fn() }));

// FullCalendar does not render reliably in jsdom; the stub only emits what the real one would.
vi.mock("../components/PlanningCalendar.vue", async () => {
  const { defineComponent, h } = await import("vue");
  return {
    default: defineComponent({
      props: { events: { type: Array, default: () => [] } },
      emits: ["range", "select"],
      setup(_, { expose }) {
        expose({ prev: vi.fn(), today: vi.fn(), ...calls });
        return () => h("div", { class: "calendar-stub" });
      },
    }),
  };
});

import CalendarStub from "../components/PlanningCalendar.vue";
import PlanningPage from "./PlanningPage.vue";

const options = {
  categories: [
    { id: 1, name: "Music" },
    { id: 2, name: "Sport" },
  ],
  distances: [{ value: 500, label: "500 m" }],
  external_calendars: [{ title: "Holidays", url: "http://h", active: false }],
  max_dates: 200,
};

const range = {
  date_from: "2026-09-28",
  date_to: "2026-11-08",
  title: "October 2026",
  view: "dayGridMonth",
};

function row(id: number, start = "2026-10-03T08:00:00Z") {
  return {
    id,
    start,
    end: null,
    allday: false,
    event: {
      id,
      name: `E${id}`,
      status: "scheduled",
      public_status: "published",
      booked_up: null,
      attendance_mode: "offline",
      has_status_info: false,
      organization_name: "Org",
      organizer_name: null,
      place_name: null,
    },
  };
}

function respond(path: string) {
  if (path === "/bff/manage/planning") return Promise.resolve({ data: options });
  if (path === "/bff/manage/planning/event-dates") {
    return Promise.resolve({ data: { items: [row(1), row(2)], truncated: false } });
  }
  return Promise.resolve({
    data: {
      url: "http://h",
      items: [{ name: "Holiday", start: "2026-10-12", end: null, allday: true, location: null, description: null }],
    },
  });
}

async function mountPage() {
  const wrapper = mount(PlanningPage, {
    attachTo: document.body,
    global: {
      plugins: [
        createBootstrap(),
        createI18n({
          legacy: false,
          locale: "en",
          messages: { en: { "%(count)d event dates": "{count} event dates" } },
        }),
      ],
    },
  });
  await flushPromises();
  return wrapper;
}

async function emitRange(wrapper: ReturnType<typeof mount>, over = {}) {
  wrapper.findComponent(CalendarStub).vm.$emit("range", { ...range, ...over });
  await flushPromises();
}

const datesCalls = () => GET.mock.calls.filter((c) => c[0] === "/bff/manage/planning/event-dates");

describe("PlanningPage", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    GET.mockReset().mockImplementation(respond);
    Object.values(calls).forEach((fn) => fn.mockReset());
  });

  it("loads the options and links the docs", async () => {
    const wrapper = await mountPage();

    expect(GET).toHaveBeenCalledWith("/bff/manage/planning");
    expect(wrapper.find("h1").text()).toBe("Event Planning");
    expect(wrapper.find('a[href="https://docs.test/goto/event-planning"]').exists()).toBe(true);
  });

  it("shows the error when the options cannot be loaded", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const wrapper = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
    expect(wrapper.findComponent(CalendarStub).exists()).toBe(false);
  });

  it("queries the event dates of the visible range and shows the count", async () => {
    const wrapper = await mountPage();
    await emitRange(wrapper);

    expect(datesCalls()[0][1]).toEqual({
      params: {
        query: { date_from: "2026-09-28", date_to: "2026-11-08", exclude_recurring: true },
      },
    });
    expect(wrapper.find('[data-test="count"]').text()).toBe("2 event dates");
    expect(wrapper.find('[data-test="title"]').text()).toBe("October 2026");
    expect(wrapper.findComponent(CalendarStub).props("events")).toHaveLength(2);
    expect(calls.scrollToHour).not.toHaveBeenCalled();
  });

  it("scrolls to the earliest event outside the month view", async () => {
    const wrapper = await mountPage();
    await emitRange(wrapper, { view: "timeGridWeek" });

    expect(calls.scrollToHour).toHaveBeenCalledWith(new Date("2026-10-03T08:00:00Z").getHours());
  });

  it("re-queries with the category array when the filter is applied", async () => {
    const wrapper = await mountPage();
    await emitRange(wrapper);
    GET.mockClear();

    await wrapper.find('[data-test="filter"]').trigger("click");
    await flushPromises();
    document.body.querySelector<HTMLInputElement>("#planning-category-2")!.click();
    document.body.querySelector<HTMLButtonElement>('[data-test="refresh"]')!.click();
    await flushPromises();

    expect(datesCalls()).toHaveLength(1);
    expect(datesCalls()[0][1].params.query).toMatchObject({ category_id: [2] });
  });

  it("warns when the dates were truncated", async () => {
    GET.mockImplementation((path: string) =>
      path === "/bff/manage/planning/event-dates"
        ? Promise.resolve({ data: { items: [row(1)], truncated: true } })
        : respond(path),
    );
    const wrapper = await mountPage();
    await emitRange(wrapper);

    expect(wrapper.find('[data-test="truncated"]').text()).toContain("maximum number of dates");
  });

  it("ignores out-of-order responses", async () => {
    const pending: Array<(v: unknown) => void> = [];
    GET.mockImplementation((path: string) =>
      path === "/bff/manage/planning/event-dates"
        ? new Promise((resolve) => pending.push(resolve))
        : respond(path),
    );
    const wrapper = await mountPage();

    await emitRange(wrapper);
    await emitRange(wrapper, { date_from: "2026-11-01" });
    pending[1]({ data: { items: [row(2)], truncated: false } });
    await flushPromises();
    pending[0]({ data: { items: [row(1), row(3)], truncated: true } });
    await flushPromises();

    expect(wrapper.find('[data-test="count"]').text()).toBe("1 event dates");
    expect(wrapper.find('[data-test="truncated"]').exists()).toBe(false);
  });

  it("loads an external calendar when it is switched on", async () => {
    const wrapper = await mountPage();
    await emitRange(wrapper);
    expect(GET.mock.calls.some((c) => c[0] === "/bff/manage/planning/external-calendar-events")).toBe(false);

    await wrapper.find('[data-test="external"]').trigger("click");
    await flushPromises();
    document.body.querySelector<HTMLInputElement>('[id="external-calendar-http://h"]')!.click();
    document.body.querySelector<HTMLButtonElement>('[data-test="external-close"]')!.click();
    await flushPromises();

    expect(GET).toHaveBeenCalledWith("/bff/manage/planning/external-calendar-events", {
      params: { query: { url: "http://h", date_from: "2026-09-28", date_to: "2026-11-08" } },
    });
    expect(wrapper.findComponent(CalendarStub).props("events")).toHaveLength(3);
  });

  it("warns when an external calendar fails but keeps the dates", async () => {
    GET.mockImplementation((path: string) =>
      path === "/bff/manage/planning/external-calendar-events"
        ? Promise.resolve({ error: { message: "nope" } })
        : respond(path),
    );
    const wrapper = await mountPage();
    await emitRange(wrapper);
    await wrapper.find('[data-test="external"]').trigger("click");
    await flushPromises();
    document.body.querySelector<HTMLInputElement>('[id="external-calendar-http://h"]')!.click();
    document.body.querySelector<HTMLButtonElement>('[data-test="external-close"]')!.click();
    await flushPromises();

    expect(wrapper.find('[data-test="external-failed"]').exists()).toBe(true);
    expect(wrapper.findComponent(CalendarStub).props("events")).toHaveLength(2);
  });

  it("forwards view changes and navigation to the calendar", async () => {
    const wrapper = await mountPage();
    await emitRange(wrapper);

    await wrapper.find('[data-test="view-timeGridWeek"]').trigger("click");
    await wrapper.find('[data-test="next"]').trigger("click");

    expect(calls.changeView).toHaveBeenCalledWith("timeGridWeek");
    expect(calls.next).toHaveBeenCalled();
  });

  it("opens the details of a selected date", async () => {
    const wrapper = await mountPage();
    await emitRange(wrapper);

    wrapper.findComponent(CalendarStub).vm.$emit("select", { kind: "date", row: row(7) });
    await flushPromises();

    expect(document.body.querySelector('[data-test="view"]')!.getAttribute("href")).toBe("/eventdate/7");
  });
});
