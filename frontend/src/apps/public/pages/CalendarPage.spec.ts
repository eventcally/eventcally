import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({
  boot: { locale: "en", csrfToken: "x", loginUrl: "/login", docsUrl: null },
}));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success: vi.fn(), error: vi.fn() }) }));

import CalendarPage from "./CalendarPage.vue";

const calendar = (over = {}) => ({
  id: 4,
  name: "Sport",
  description: "Alles rund um https://sport.test",
  private: false,
  organization: { id: 2, name: "Jam Org" },
  ical_url: "http://localhost/calendars/4/ical",
  manage_url: null,
  ...over,
});

const date = (id: number) => ({
  id,
  start: "2030-10-03T10:00:00+02:00",
  end: null,
  allday: false,
  event: {
    id: id + 100,
    name: `Event ${id}`,
    description_preview: null,
    status: null,
    public_status: "published",
    booked_up: false,
    attendance_mode: null,
    organization: { id: 2, name: "Jam Org" },
    organizer_name: "Crew",
    place: null,
    photo: null,
    reference: null,
  },
});

const dates = (items: unknown[], pages = 1) => ({
  data: { items, page: 1, per_page: 50, total: items.length, pages },
});

function answer(cal: object | null, list: object = dates([date(1), date(2)])) {
  GET.mockImplementation(async (path: string) =>
    path === "/bff/public/calendars/{id}"
      ? cal
        ? { data: cal }
        : { error: { message: "Not found" } }
      : list,
  );
}

async function mountPage() {
  const wrapper = mount(CalendarPage, {
    props: { id: 4 },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  await flushPromises();
  return wrapper;
}

describe("CalendarPage", () => {
  beforeEach(() => {
    GET.mockReset();
    document.body.innerHTML = "";
  });

  it("shows the header and the upcoming dates of the calendar", async () => {
    answer(calendar());
    const wrapper = await mountPage();

    expect(wrapper.find("h1").text()).toBe("Sport");
    expect(wrapper.find("[data-test=organization]").attributes("href")).toBe("/organizations/2");
    expect(wrapper.find("[data-test=description] a").attributes("href")).toBe("https://sport.test");
    expect(wrapper.find("[data-test=private]").exists()).toBe(false);
    expect(wrapper.find("[data-test=search]").attributes("href")).toBe("/eventdates?calendar_id=4");
    expect(wrapper.find("[data-test=manage]").exists()).toBe(false);
    expect(wrapper.findAll(".event-date-card")).toHaveLength(2);
    expect(GET).toHaveBeenCalledWith("/bff/public/event-dates", {
      params: { query: { calendar_id: [4], page: 1 } },
    });
  });

  it("offers the subscription through the iCal dialog", async () => {
    answer(calendar());
    const wrapper = await mountPage();

    await wrapper.find("[data-test=subscribe]").trigger("click");
    await flushPromises();

    expect(
      (document.querySelector("input[name=icalUrl]") as HTMLInputElement).value,
    ).toBe("http://localhost/calendars/4/ical");
  });

  it("shows the private notice to members and no subscription", async () => {
    answer(calendar({ private: true, manage_url: "/manage/admin_unit/2/calendar/4/update" }));
    const wrapper = await mountPage();

    expect(wrapper.find("[data-test=private]").exists()).toBe(true);
    expect(wrapper.find("[data-test=private-notice]").text()).toBe("This calendar is private.");
    expect(wrapper.find("[data-test=subscribe]").exists()).toBe(false);
    expect(wrapper.find("[data-test=manage]").attributes("href")).toBe(
      "/manage/admin_unit/2/calendar/4/update",
    );
  });

  it("shows the empty state", async () => {
    answer(calendar({ description: null }), dates([]));
    const wrapper = await mountPage();

    expect(wrapper.find("[data-test=description]").exists()).toBe(false);
    expect(wrapper.find("[data-test=empty]").text()).toBe("No upcoming events in this calendar");
  });

  it("pages through the dates", async () => {
    answer(calendar(), dates([date(1)], 3));
    const wrapper = await mountPage();

    await wrapper.find('button[aria-label="Next page"]').trigger("click");
    await flushPromises();

    expect(GET).toHaveBeenLastCalledWith("/bff/public/event-dates", {
      params: { query: { calendar_id: [4], page: 2 } },
    });
  });

  it("shows the error of a failed load and loads no dates", async () => {
    answer(null);
    const wrapper = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Not found");
    expect(GET).toHaveBeenCalledTimes(1);
  });

  it("shows the error of failed dates", async () => {
    answer(calendar(), { error: { message: "Boom" } });
    const wrapper = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Boom");
  });
});
