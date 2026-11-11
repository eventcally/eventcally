import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));

const success = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

const calendarCalls = vi.hoisted(() => ({ next: vi.fn(), changeView: vi.fn(), today: vi.fn() }));

// FullCalendar does not render reliably in jsdom; the stub only emits what the real one would.
vi.mock("../components/PlanningCalendar.vue", async () => {
  const { defineComponent, h } = await import("vue");
  return {
    default: defineComponent({
      props: {
        events: { type: Array, default: () => [] },
        initialView: { type: String, default: "dayGridMonth" },
        initialDate: { type: String, default: undefined },
      },
      emits: ["range", "select"],
      setup(_, { expose }) {
        expose({ prev: vi.fn(), scrollToHour: vi.fn(), ...calendarCalls });
        return () => h("div", { class: "calendar-stub" });
      },
    }),
  };
});

import { setFlash } from "@/shared/flash";
import CalendarStub from "../components/PlanningCalendar.vue";
import ManageEventsPage from "./ManageEventsPage.vue";

const options = {
  default_date_from: "2030-10-01",
  categories: [],
  statuses: [{ value: 1, name: "scheduled", label: "Scheduled" }],
  public_statuses: [
    { value: 1, name: "draft", label: "Draft" },
    { value: 2, name: "published", label: "Published" },
  ],
  distances: [],
  can_write: true,
  can_request_reference: true,
  can_read_references: true,
  can_write_references: true,
  calendars: [] as { id: number; name: string; private: boolean }[],
  can_write_calendars: false,
};

const item = (over = {}) => ({
  id: 11,
  name: "Jam Session",
  start: "2030-10-03T10:00:00+02:00",
  allday: false,
  is_recurring: false,
  number_of_dates: 1,
  organizer_name: "Jam Crew",
  place_label: "Rathaus 38640 Goslar",
  category_names: ["Music", "Party"],
  tags: "live",
  internal_tags: "secret",
  status: "scheduled",
  public_status: "draft",
  has_photo: false,
  number_of_references: 0,
  number_of_reference_requests: 0,
  last_modified_at: "2030-09-01T10:00:00+02:00",
  is_reference: false,
  reference_id: null,
  organization_name: null,
  ...over,
});

const listPage = (items = [item()], over = {}) => ({
  data: { items, page: 1, per_page: 50, total: items.length, pages: 1, ...over },
});

async function mountPage(url = "/manage/admin_unit/3/events") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: "/manage/admin_unit/:organizationId/events",
        name: "manage-events",
        component: ManageEventsPage,
      },
      {
        path: "/manage/admin_unit/:organizationId/incoming_event_reference/:id",
        name: "incoming-event-reference",
        component: { template: "<div />" },
      },
    ],
  });
  router.push(url);
  await router.isReady();
  const wrapper = mount(ManageEventsPage, {
    props: { organizationId: 3 },
    attachTo: document.body,
    global: {
      plugins: [
        router,
        createBootstrap(),
        createI18n({
          legacy: false,
          locale: "en",
          messages: {
            en: { "Do you want to delete '%(object_title)s'?": "Do you want to delete '{object_title}'?" },
          },
        }),
      ],
    },
  });
  await flushPromises();
  return { wrapper, router };
}

const listCalls = () =>
  GET.mock.calls.filter(([path]) => path === "/bff/manage/organizations/{id}/events");
const dateCalls = () =>
  GET.mock.calls.filter(([path]) => path === "/bff/manage/organizations/{id}/event-dates");

const dateRow = (over = {}) => ({
  id: 7,
  start: "2030-11-04T09:00:00Z",
  end: null,
  allday: false,
  event: {
    id: 11,
    name: "Jam Session",
    is_recurring: false,
    status: "scheduled",
    public_status: "published",
    organizer_name: null,
    place_label: null,
    is_reference: false,
    reference_id: null,
    organization_name: null,
  },
  ...over,
});

const month = {
  date_from: "2030-10-28",
  date_to: "2030-12-08",
  title: "November 2030",
  view: "dayGridMonth",
  current: "2030-11-01",
};

function respond(dates: unknown = { data: { items: [dateRow()], truncated: false } }) {
  GET.mockReset().mockImplementation((path: string) =>
    Promise.resolve(
      path.endsWith("/options")
        ? { data: options }
        : path.endsWith("/event-dates")
          ? dates
          : listPage(),
    ),
  );
}

async function emitRange(wrapper: ReturnType<typeof mount>, over = {}) {
  wrapper.findComponent(CalendarStub).vm.$emit("range", { ...month, ...over });
  await flushPromises();
}

describe("ManageEventsPage", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    success.mockReset();
    POST.mockReset();
    GET.mockReset().mockImplementation((path: string) =>
      Promise.resolve(path.endsWith("/options") ? { data: options } : listPage()),
    );
  });

  it("loads the options and the list of the organization", async () => {
    await mountPage();

    expect(GET).toHaveBeenCalledWith("/bff/manage/organizations/{id}/events/options", {
      params: { path: { id: 3 } },
    });
    expect(listCalls()[0][1]).toEqual({
      params: {
        path: { id: 3 },
        query: { page: 1, date_from: "2030-10-01", sort: "min_start" },
      },
    });
  });

  it("renders the columns of a row", async () => {
    const { wrapper } = await mountPage();
    const text = wrapper.text();

    expect(text).toContain("Jam Session");
    expect(text).toContain("Jam Crew");
    expect(text).toContain("Rathaus 38640 Goslar");
    expect(text).toContain("Music, Party");
    expect(text).toContain("secret");
    expect(text).toContain("Scheduled");
    expect(text).toContain("Draft");
  });

  it("offers creating events only with write access", async () => {
    const { wrapper } = await mountPage();
    expect(wrapper.find('a[href="/manage/admin_unit/3/event/create"]').exists()).toBe(true);

    GET.mockReset().mockImplementation((path: string) =>
      Promise.resolve(
        path.endsWith("/options") ? { data: { ...options, can_write: false } } : listPage(),
      ),
    );
    const readOnly = await mountPage();
    expect(readOnly.wrapper.find('a[href="/manage/admin_unit/3/event/create"]').exists()).toBe(
      false,
    );
  });

  it("passes the legacy query of a place link on and shows the place name", async () => {
    GET.mockReset().mockImplementation((path: string) =>
      Promise.resolve(
        path.endsWith("/options")
          ? { data: options }
          : listPage([item()], { event_place: { id: 5, name: "Rathaus" } }),
      ),
    );
    const { wrapper } = await mountPage("/manage/admin_unit/3/events?event_place_id=5");

    expect(listCalls()[0][1].params.query.event_place_id).toBe(5);
    expect((wrapper.find("#event_place_id").element as HTMLInputElement).value).toBe("Rathaus");
  });

  it("searches again when the filter changes the URL", async () => {
    const { wrapper, router } = await mountPage();
    await wrapper.find("#keyword").setValue("Jam");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(router.currentRoute.value.query).toEqual({ keyword: "Jam" });
    expect(listCalls()).toHaveLength(2);
    expect(listCalls()[1][1].params.query.keyword).toBe("Jam");
  });

  it("shows the pager with the total even for a single page", async () => {
    const { wrapper } = await mountPage();

    expect(wrapper.find("nav[aria-label*='total']").exists()).toBe(true);
  });

  it("shows the empty text", async () => {
    GET.mockReset().mockImplementation((path: string) =>
      Promise.resolve(path.endsWith("/options") ? { data: options } : listPage([])),
    );
    const { wrapper } = await mountPage();

    expect(wrapper.text()).toContain("No events found");
  });

  it("shows an error", async () => {
    GET.mockReset().mockImplementation((path: string) =>
      Promise.resolve(
        path.endsWith("/options") ? { data: options } : { error: { message: "Kaputt" } },
      ),
    );
    const { wrapper } = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Kaputt");
  });

  it("deletes an event from its row in a modal and searches again", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve(
        path.endsWith("/options")
          ? { data: options }
          : path.endsWith("/delete-form")
            ? { data: { id: 11, name: "Jam Session", has_multiple_dates: false } }
            : listPage(),
      ),
    );
    POST.mockResolvedValue({
      data: { message: "Event successfully deleted", redirect_url: "/manage/admin_unit/3/events" },
    });
    const { wrapper } = await mountPage();

    await wrapper.find(".event-actions button").trigger("click");
    const remove = [...document.querySelectorAll<HTMLElement>(".dropdown-item")].find(
      (i) => i.textContent?.trim() === "Delete",
    );
    remove?.click();
    await flushPromises();

    expect(document.body.textContent).toContain("Do you want to delete 'Jam Session'?");
    document.querySelector<HTMLButtonElement>("#submit")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/manage/organizations/{id}/events/{event_id}/delete", {
      params: { path: { id: 3, event_id: 11 } },
      body: { inline: true },
    });
    expect(success).toHaveBeenCalledWith("Event successfully deleted");
    expect(listCalls()).toHaveLength(2);
  });

  it("shows the flash message of a legacy action", async () => {
    setFlash("Event deleted");
    await mountPage();

    expect(success).toHaveBeenCalledWith("Event deleted");
  });

  describe("calendar", () => {
    const CALENDAR_URL = "/manage/admin_unit/3/events?view=calendar&calendar_date=2030-11-01";

    beforeEach(() => {
      respond();
      Object.values(calendarCalls).forEach((f) => f.mockReset());
    });

    it("switches from the list to the calendar at the list's start date", async () => {
      const { wrapper, router } = await mountPage("/manage/admin_unit/3/events?keyword=Jam&page=2");
      expect(wrapper.find('[data-test="view-list"]').classes()).toContain("active");

      await wrapper.find('[data-test="view-calendar"]').trigger("click");
      await flushPromises();

      expect(router.currentRoute.value.query).toEqual({
        keyword: "Jam",
        view: "calendar",
        calendar_date: "2030-10-01",
      });
      expect(wrapper.find("table").exists()).toBe(false);
      const stub = wrapper.findComponent(CalendarStub);
      expect(stub.props("initialDate")).toBe("2030-10-01");
      expect(stub.props("initialView")).toBe("dayGridMonth");
      expect(listCalls()).toHaveLength(1);
    });

    it("switches back to the list without the calendar keys", async () => {
      const { wrapper, router } = await mountPage(`${CALENDAR_URL}&keyword=Jam`);

      await wrapper.find('[data-test="view-list"]').trigger("click");
      await flushPromises();

      expect(router.currentRoute.value.query).toEqual({ keyword: "Jam" });
      expect(wrapper.find("table").exists()).toBe(true);
      expect(listCalls()).toHaveLength(1);
      expect(listCalls()[0][1].params.query.keyword).toBe("Jam");
    });

    it("ignores a click on the active view", async () => {
      const { wrapper, router } = await mountPage(CALENDAR_URL);
      const push = vi.spyOn(router, "push");

      await wrapper.find('[data-test="view-calendar"]').trigger("click");

      expect(push).not.toHaveBeenCalled();
    });

    it("opens at the position of the URL and queries the dates of the visible range", async () => {
      const { wrapper } = await mountPage(
        "/manage/admin_unit/3/events?view=calendar&calendar_view=timeGridWeek&calendar_date=2030-11-04&keyword=Jam&sort=-created_at&page=3",
      );
      const stub = wrapper.findComponent(CalendarStub);
      expect(stub.props("initialView")).toBe("timeGridWeek");
      expect(stub.props("initialDate")).toBe("2030-11-04");
      expect(listCalls()).toHaveLength(0);

      await emitRange(wrapper, {
        date_from: "2030-11-04",
        date_to: "2030-11-10",
        view: "timeGridWeek",
        current: "2030-11-04",
      });

      expect(dateCalls()).toHaveLength(1);
      expect(dateCalls()[0][1]).toEqual({
        params: {
          path: { id: 3 },
          query: { keyword: "Jam", date_from: "2030-11-04", date_to: "2030-11-10" },
        },
      });
      expect(stub.props("events")).toHaveLength(1);
      expect(wrapper.find('[data-test="count"]').exists()).toBe(true);
      expect(calendarCalls.today).not.toHaveBeenCalled();
    });

    it("keeps the calendar position in the URL without a history entry", async () => {
      const { wrapper, router } = await mountPage(CALENDAR_URL);
      const replace = vi.spyOn(router, "replace");

      await emitRange(wrapper);
      expect(replace).not.toHaveBeenCalled();

      await emitRange(wrapper, { current: "2030-12-01", view: "timeGridWeek" });
      await flushPromises();

      expect(replace).toHaveBeenCalledTimes(1);
      expect(router.currentRoute.value.query).toEqual({
        view: "calendar",
        calendar_view: "timeGridWeek",
        calendar_date: "2030-12-01",
      });
      // One load per range, none for the URL update.
      expect(dateCalls()).toHaveLength(2);
      expect(listCalls()).toHaveLength(0);
    });

    it("reloads the dates when the filter changes", async () => {
      const { wrapper, router } = await mountPage(CALENDAR_URL);
      await emitRange(wrapper);

      await router.push({ query: { ...router.currentRoute.value.query, keyword: "Jam" } });
      await flushPromises();

      expect(dateCalls()).toHaveLength(2);
      expect(dateCalls()[1][1].params.query.keyword).toBe("Jam");
      expect(listCalls()).toHaveLength(0);
    });

    it("reloads the dates when an unchanged filter is searched again", async () => {
      const { wrapper } = await mountPage(CALENDAR_URL);
      await emitRange(wrapper);

      await wrapper.find('[data-test="form"]').trigger("submit");
      await flushPromises();

      expect(dateCalls()).toHaveLength(2);
    });

    it("forwards navigation and view changes to the calendar", async () => {
      const { wrapper } = await mountPage(CALENDAR_URL);
      await emitRange(wrapper);

      await wrapper.find('[data-test="next"]').trigger("click");
      await wrapper.find('[data-test="today"]').trigger("click");
      await wrapper.find('[data-test="view-timeGridDay"]').trigger("click");

      expect(calendarCalls.next).toHaveBeenCalled();
      expect(calendarCalls.today).toHaveBeenCalled();
      expect(calendarCalls.changeView).toHaveBeenCalledWith("timeGridDay");
      expect(wrapper.find('[data-test="view-dayGridMonth"]').classes()).toContain("active");
      expect(wrapper.find('[data-test="title"]').text()).toBe("November 2030");
    });

    it("warns when the dates were truncated", async () => {
      respond({ data: { items: [dateRow()], truncated: true } });
      const { wrapper } = await mountPage(CALENDAR_URL);
      await emitRange(wrapper);

      expect(wrapper.find('[data-test="truncated"]').exists()).toBe(true);
    });

    it("shows the error when the dates cannot be loaded", async () => {
      respond({ error: { message: "Boom" } });
      const { wrapper } = await mountPage(CALENDAR_URL);
      await emitRange(wrapper);

      expect(wrapper.find('[data-test="calendar-error"]').text()).toBe("Boom");
      expect(wrapper.findComponent(CalendarStub).props("events")).toHaveLength(0);
    });

    it("ignores out-of-order responses", async () => {
      let resolveFirst: (value: unknown) => void = () => {};
      GET.mockReset().mockImplementation((path: string, init: { params: { query: { date_from: string } } }) => {
        if (path.endsWith("/options")) return Promise.resolve({ data: options });
        if (init.params.query.date_from === "2030-10-28") {
          return new Promise((resolve) => (resolveFirst = resolve));
        }
        return Promise.resolve({ data: { items: [dateRow({ id: 8 })], truncated: false } });
      });
      const { wrapper } = await mountPage(CALENDAR_URL);

      wrapper.findComponent(CalendarStub).vm.$emit("range", month);
      await emitRange(wrapper, { date_from: "2030-12-01", date_to: "2031-01-11", current: "2030-12-01" });
      resolveFirst({ data: { items: [dateRow({ id: 7 })], truncated: false } });
      await flushPromises();

      const events = wrapper.findComponent(CalendarStub).props("events") as { id: string }[];
      expect(events.map((e) => e.id)).toEqual(["d8"]);
    });

    it("scrolls to the earliest date outside the month view", async () => {
      const { wrapper } = await mountPage(CALENDAR_URL);
      await emitRange(wrapper, { view: "timeGridWeek" });

      const exposed = wrapper.findComponent(CalendarStub).vm as unknown as {
        scrollToHour: ReturnType<typeof vi.fn>;
      };
      expect(exposed.scrollToHour).toHaveBeenCalled();
    });

    it("opens a date and deletes its event, then reloads the dates", async () => {
      POST.mockResolvedValue({ data: { message: "Event successfully deleted", redirect_url: "/x" } });
      GET.mockImplementation((path: string) => {
        if (path.endsWith("/delete-form")) {
          return Promise.resolve({ data: { id: 11, name: "Jam Session", has_multiple_dates: false } });
        }
        return Promise.resolve(
          path.endsWith("/options")
            ? { data: options }
            : { data: { items: [dateRow()], truncated: false } },
        );
      });
      const { wrapper } = await mountPage(CALENDAR_URL);
      await emitRange(wrapper);

      wrapper.findComponent(CalendarStub).vm.$emit("select", { row: dateRow() });
      await flushPromises();
      document.body.querySelector<HTMLElement>('[data-test="delete"]')!.click();
      await flushPromises();

      expect(document.body.textContent).toContain("Do you want to delete 'Jam Session'?");
      document.querySelector<HTMLButtonElement>("#submit")!.click();
      await flushPromises();

      expect(POST).toHaveBeenCalledWith("/bff/manage/organizations/{id}/events/{event_id}/delete", {
        params: { path: { id: 3, event_id: 11 } },
        body: { inline: true },
      });
      expect(success).toHaveBeenCalledWith("Event successfully deleted");
      expect(dateCalls()).toHaveLength(2);
      expect(listCalls()).toHaveLength(0);
    });
  });
  describe("references", () => {
    const referenceItem = () =>
      item({
        id: 12,
        name: "Fremdes Fest",
        is_reference: true,
        reference_id: 9,
        organization_name: "Andere Crew",
        internal_tags: null,
        number_of_references: null,
        number_of_reference_requests: null,
      });

    // The menus are teleported to the body in row order.
    const menu = (index: number) => document.querySelectorAll<HTMLElement>("ul.dropdown-menu")[index];

    const openActions = async (wrapper: ReturnType<typeof mount>, index: number) => {
      await wrapper.findAll(".event-actions button")[index].trigger("click");
      await flushPromises();
      return [...menu(index).querySelectorAll<HTMLElement>(".dropdown-item")].map((i) =>
        i.textContent?.trim(),
      );
    };

    beforeEach(() => {
      GET.mockReset().mockImplementation((path: string) =>
        Promise.resolve(
          path.endsWith("/options")
            ? { data: options }
            : path.endsWith("/event-dates")
              ? {
                  data: {
                    items: [
                      dateRow({
                        event: {
                          ...dateRow().event,
                          is_reference: true,
                          reference_id: 9,
                          organization_name: "Andere Crew",
                        },
                      }),
                    ],
                    truncated: false,
                  },
                }
              : listPage([item(), referenceItem()]),
        ),
      );
      POST.mockResolvedValue({
        data: { message: "Incoming reference successfully deleted", redirect_url: "/x" },
        response: { ok: true },
      });
    });

    it("passes the filter and marks reference rows with their own actions", async () => {
      const { wrapper } = await mountPage("/manage/admin_unit/3/events?include_references=1");

      expect(listCalls()[0][1].params.query.include_references).toBe(true);
      const marker = wrapper.find('[data-test="reference"]');
      expect(marker.text()).toContain("Reference");
      expect(marker.text()).toContain("Andere Crew");

      expect(await openActions(wrapper, 1)).toEqual([
        "View",
        "View reference",
        "Delete reference",
        "More",
      ]);
      expect(
        menu(1).querySelector('[data-test="view-reference"]')?.getAttribute("href"),
      ).toBe("/manage/admin_unit/3/incoming_event_reference/9");
    });

    it("hides deleting a reference without the write permission", async () => {
      GET.mockImplementation((path: string) =>
        Promise.resolve(
          path.endsWith("/options")
            ? { data: { ...options, can_write_references: false } }
            : listPage([referenceItem()]),
        ),
      );
      const { wrapper } = await mountPage();

      expect(await openActions(wrapper, 0)).toEqual(["View", "View reference", "More"]);
    });

    it("deletes a reference from its row after a confirmation and searches again", async () => {
      const { wrapper } = await mountPage();
      await openActions(wrapper, 1);
      menu(1).querySelector<HTMLElement>('[data-test="delete-reference"]')!.click();
      await flushPromises();

      expect(document.body.textContent).toContain("Do you want to delete 'Fremdes Fest'?");
      [...document.querySelectorAll<HTMLButtonElement>(".modal-footer .btn-danger")]
        .find((b) => b.textContent?.trim() === "Delete reference")!
        .click();
      await flushPromises();

      expect(POST).toHaveBeenCalledWith(
        "/bff/manage/organizations/{id}/incoming-event-references/{reference_id}/delete",
        { params: { path: { id: 3, reference_id: 9 } }, body: { inline: true } },
      );
      expect(success).toHaveBeenCalledWith("Incoming reference successfully deleted");
      expect(listCalls()).toHaveLength(2);
    });

    it("deletes a reference from the calendar and reloads the dates", async () => {
      const { wrapper } = await mountPage(
        "/manage/admin_unit/3/events?view=calendar&calendar_date=2030-11-01&include_references=1",
      );
      await emitRange(wrapper);
      expect(dateCalls()[0][1].params.query.include_references).toBe(true);
      const events = wrapper.findComponent(CalendarStub).props("events") as { className: string }[];
      expect(events[0].className).toBe("ec-reference");

      wrapper.findComponent(CalendarStub).vm.$emit("select", {
        row: (await GET("/x/event-dates")).data.items[0],
      });
      await flushPromises();
      document.body.querySelector<HTMLElement>('[data-test="details"] [data-test="delete-reference"]')!.click();
      await flushPromises();
      [...document.querySelectorAll<HTMLButtonElement>(".modal-footer .btn-danger")]
        .find((b) => b.textContent?.trim() === "Delete reference")!
        .click();
      await flushPromises();

      expect(POST).toHaveBeenCalledWith(
        "/bff/manage/organizations/{id}/incoming-event-references/{reference_id}/delete",
        { params: { path: { id: 3, reference_id: 9 } }, body: { inline: true } },
      );
      expect(dateCalls()).toHaveLength(2);
      expect(listCalls()).toHaveLength(0);
    });
  });

  describe("calendars", () => {
    const withCalendars = { ...options, calendars: [{ id: 5, name: "Sport", private: false }], can_write_calendars: true };
    const foreign = () =>
      item({ id: 13, name: "Fremdes Konzert", is_own: false, organization_name: "Andere Crew", internal_tags: null });

    const menu = (index: number) => document.querySelectorAll<HTMLElement>("ul.dropdown-menu")[index];
    const openActions = async (wrapper: ReturnType<typeof mount>, index: number) => {
      await wrapper.findAll(".event-actions button")[index].trigger("click");
      await flushPromises();
      return [...menu(index).querySelectorAll<HTMLElement>(".dropdown-item")].map((i) =>
        i.textContent?.trim(),
      );
    };

    beforeEach(() => {
      GET.mockReset().mockImplementation((path: string) =>
        Promise.resolve(
          path.endsWith("/options")
            ? { data: withCalendars }
            : path.endsWith("/calendars")
              ? { data: { choices: withCalendars.calendars, selected_ids: [] } }
              : listPage([item(), foreign()]),
        ),
      );
    });

    it("filters by calendar from the URL and offers the filter", async () => {
      const { wrapper } = await mountPage("/manage/admin_unit/3/events?calendar_id=5");

      expect(listCalls()[0][1].params.query.calendar_id).toBe(5);
      expect((wrapper.find("#calendar_id").element as HTMLSelectElement).value).toBe("5");
    });

    it("offers the calendar action on own and foreign rows, but edit only on own rows", async () => {
      const { wrapper } = await mountPage();

      expect(await openActions(wrapper, 0)).toContain("Edit");
      expect(await openActions(wrapper, 0)).toContain("Calendars…");
      expect(await openActions(wrapper, 1)).toEqual(["View", "Calendars…", "More"]);
    });

    it("opens the assign modal for the row", async () => {
      const { wrapper } = await mountPage();
      await openActions(wrapper, 1);
      menu(1).querySelector<HTMLElement>('[data-test="assign-calendars"]')!.click();
      await flushPromises();

      expect(GET).toHaveBeenCalledWith(
        "/bff/manage/organizations/{id}/events/{event_id}/calendars",
        { params: { path: { id: 3, event_id: 13 } } },
      );
    });

    it("hides the filter and the action without calendars", async () => {
      GET.mockReset().mockImplementation((path: string) =>
        Promise.resolve(path.endsWith("/options") ? { data: options } : listPage([item()])),
      );
      const { wrapper } = await mountPage();

      expect(wrapper.find("#calendar_id").exists()).toBe(false);
      expect(await openActions(wrapper, 0)).not.toContain("Calendars…");
    });
  });
});
