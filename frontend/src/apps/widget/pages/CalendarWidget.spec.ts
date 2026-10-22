import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { defaultSettings, type CalendarSettings } from "@/shared/customWidget";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

const fc = vi.hoisted(() => ({
  options: null as Record<string, any> | null,
  changeView: vi.fn(),
  prev: vi.fn(),
  next: vi.fn(),
  scrollToTime: vi.fn(),
}));

// FullCalendar does not render reliably in jsdom; the stub only exposes what the page uses.
vi.mock("@fullcalendar/vue3", async () => {
  const { defineComponent, h } = await import("vue");
  return {
    default: defineComponent({
      props: ["options"],
      setup(props, { expose }) {
        expose({ getApi: () => fc });
        return () => {
          fc.options = props.options;
          return h("div", { class: "fc-stub" });
        };
      },
    }),
  };
});

import CalendarWidget from "./CalendarWidget.vue";

const row = (id: number, start: string, over: Record<string, unknown> = {}) => ({
  id,
  start,
  end: null,
  allday: false,
  event: {
    id,
    name: `Event ${id}`,
    description_preview: null,
    status: null,
    public_status: "published",
    booked_up: null,
    attendance_mode: "offline",
    organization_name: "Crew",
    organizer_name: "Veranstalter",
    place_name: "Halle",
    photo: null,
    ...over,
  },
});

function respond(items = [row(1, "2026-10-03T10:00:00"), row(2, "2026-10-04T08:30:00")]) {
  GET.mockResolvedValue({ data: { items, page: 1, per_page: 50, total: items.length, pages: 1 } });
}

function send(settings: Partial<CalendarSettings> = {}) {
  window.dispatchEvent(
    new CustomEvent("eventcally:settings", {
      detail: { ...defaultSettings("calendar", null), ...settings },
    }),
  );
}

const datesSet = (start = "2026-09-28T00:00:00", end = "2026-11-02T00:00:00", title = "October") =>
  fc.options!.datesSet({ start: new Date(start), end: new Date(end), view: { title } });

function mountWidget() {
  return mount(CalendarWidget, {
    attachTo: document.body,
    global: {
      plugins: [
        createBootstrap(),
        createI18n({ legacy: false, locale: "en", messages: { en: {} } }),
      ],
    },
  });
}

describe("CalendarWidget", () => {
  beforeEach(() => {
    [GET, fc.changeView, fc.prev, fc.next, fc.scrollToTime].forEach((f) => f.mockReset());
    fc.options = null;
    window.__eventcallyWidget = { settings: null, ready: false };
    window.parentIFrame = { sendMessage: vi.fn(), scrollToOffset: vi.fn() };
    document.body.innerHTML = "";
  });

  it("renders nothing before the settings arrive", async () => {
    const wrapper = mountWidget();
    await flushPromises();

    expect(wrapper.find(".fc-stub").exists()).toBe(false);
    expect(GET).not.toHaveBeenCalled();
  });

  it.each([
    ["week", "timeGridWeek"],
    ["month", "dayGridMonth"],
  ] as const)("maps the %s calendar type to %s", async (calendarType, view) => {
    const wrapper = mountWidget();
    send({ calendarType });
    await flushPromises();

    expect(wrapper.find(".fc-stub").exists()).toBe(true);
    expect(fc.options!.initialView).toBe(view);
    expect(fc.options!.firstDay).toBe(1);
  });

  it("uses the event colour and the iframe height", async () => {
    mountWidget();
    send({ eventBackgroundColor: "#123456", iFrameHeight: "700" });
    await flushPromises();

    expect(fc.options!.eventColor).toBe("#123456");
    expect(fc.options!.height).toBe(700 - 88);
  });

  it("requests the visible range of the organization and passes the events on", async () => {
    respond();
    const wrapper = mountWidget();
    send({ organizationId: 7 });
    await flushPromises();
    datesSet();
    await flushPromises();

    expect(GET).toHaveBeenCalledWith("/bff/public/widget/event-dates", {
      params: {
        query: {
          date_from: "2026-09-28",
          date_to: "2026-11-01",
          per_page: 50,
          organization_id: 7,
        },
      },
    });
    expect(wrapper.find('[data-test="title"]').text()).toBe("October");
    await flushPromises();
    expect(fc.options!.events.map((e: { title: string }) => e.title)).toEqual([
      "Event 1",
      "Event 2",
    ]);
  });

  it("scrolls the week view to the earliest event hour", async () => {
    respond();
    mountWidget();
    send({ calendarType: "week" });
    await flushPromises();
    datesSet();
    await flushPromises();

    expect(fc.scrollToTime).toHaveBeenCalledWith({ hours: 8 });
  });

  it("does not scroll the month view", async () => {
    respond();
    mountWidget();
    send({ calendarType: "month" });
    await flushPromises();
    datesSet();
    await flushPromises();

    expect(fc.scrollToTime).not.toHaveBeenCalled();
  });

  it("changes the view when the type changes", async () => {
    mountWidget();
    send({ calendarType: "week" });
    await flushPromises();
    send({ calendarType: "month" });
    await flushPromises();

    expect(fc.changeView).toHaveBeenCalledWith("dayGridMonth");
  });

  it("navigates with the toolbar", async () => {
    const wrapper = mountWidget();
    send();
    await flushPromises();

    await wrapper.find('[data-test="prev"]').trigger("click");
    await wrapper.find('[data-test="next"]').trigger("click");

    expect(fc.prev).toHaveBeenCalled();
    expect(fc.next).toHaveBeenCalled();
  });

  it("shows the details of a clicked event and opens the event date", async () => {
    respond();
    const open = vi.spyOn(window, "open").mockImplementation(() => null);
    const wrapper = mountWidget();
    send();
    await flushPromises();
    datesSet();
    await flushPromises();

    fc.options!.eventClick({
      jsEvent: { preventDefault: vi.fn() },
      event: { extendedProps: { row: row(1, "2026-10-03T10:00:00") } },
    });
    await flushPromises();

    const details = document.querySelector('[data-test="details"]')!;
    expect(details.textContent).toContain("Crew");
    expect(details.textContent).toContain("Veranstalter");
    expect(details.textContent).toContain("Halle");

    (document.querySelector('[data-test="open"]') as HTMLButtonElement).click();

    expect(open).toHaveBeenCalledWith(`${location.origin}/eventdate/1`);
    expect(window.parentIFrame!.sendMessage).toHaveBeenCalledWith({
      type: "EVENTCALLY_ANALYTICS_EVENT",
      data: { event: "linkClick", url: `${location.origin}/eventdate/1` },
    });
    wrapper.unmount();
  });
});
