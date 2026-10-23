import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", base: "/", csrfToken: "t" } }));

const GET = vi.fn();
const POST = vi.fn();
const DELETE = vi.fn();
vi.mock("@/shared/api", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    DELETE: (...a: unknown[]) => DELETE(...a),
  },
}));

const notify = { success: vi.fn(), error: vi.fn() };
vi.mock("@/shared/notify", () => ({ useNotify: () => notify }));

const flyTo = vi.fn();
vi.mock("../components/EventDatesMap.vue", () => ({
  __esModule: true,
  default: {
    name: "EventDatesMapStub",
    props: ["eventDates", "locale"],
    setup(_: unknown, { expose }: { expose: (v: unknown) => void }) {
      expose({ flyTo });
      return () => null;
    },
  },
}));

import EventDatesPage from "./EventDatesPage.vue";

type Ref = { id: number; name: string } | null;
const options: {
  default_date_from: string;
  categories: unknown[];
  distances: unknown[];
  sorts: unknown[];
  organization: Ref;
  organizer: Ref;
  referencing_organization: Ref;
} = {
  default_date_from: "2030-10-01",
  categories: [{ id: 3, name: "Music" }],
  distances: [{ value: 500, label: "500 m" }],
  sorts: [
    { value: "start", label: "Earliest start first" },
    { value: "-created_at", label: "Newest first" },
  ],
  organization: null,
  organizer: null,
  referencing_organization: null,
};

function item(id: number, reference: unknown = null, place: unknown = null) {
  return {
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
      organization: { id: 1, name: "Org" },
      organizer_name: "Crew",
      place,
      photo: null,
      reference,
    },
  };
}

function searchResult(items: unknown[], pages = 1) {
  return { data: { items, page: 1, per_page: 50, total: items.length, pages } };
}

let current = { options, search: searchResult([item(1), item(2)]) };

async function mountPage(url = "/eventdates") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/eventdates", name: "event-dates", component: EventDatesPage }],
  });
  await router.push(url);
  await router.isReady();
  const wrapper = mount(EventDatesPage, {
    global: {
      plugins: [
        router,
        createBootstrap(),
        createI18n({ legacy: false, locale: "en", messages: { en: {} } }),
      ],
    },
  });
  await flushPromises();
  return { wrapper, router };
}

const searchCalls = () => GET.mock.calls.filter(([path]) => path === "/bff/public/event-dates");

describe("EventDatesPage", () => {
  beforeEach(() => {
    current = { options, search: searchResult([item(1), item(2)]) };
    notify.success.mockReset();
    notify.error.mockReset();
    flyTo.mockReset();
    POST.mockReset().mockResolvedValue({ data: { id: 1 } });
    DELETE.mockReset().mockResolvedValue({});
    GET.mockReset().mockImplementation((path: string) =>
      Promise.resolve(
        path === "/bff/public/event-dates/options"
          ? { data: current.options }
          : current.search,
      ),
    );
  });

  it("loads the options, then searches with the default date", async () => {
    const { wrapper } = await mountPage();

    expect(GET).toHaveBeenNthCalledWith(1, "/bff/public/event-dates/options", {
      params: { query: { admin_unit_id: undefined, organizer_id: undefined } },
    });
    expect(searchCalls()).toHaveLength(1);
    expect(searchCalls()[0][1].params.query).toMatchObject({
      page: 1,
      date_from: "2030-10-01",
      sort: "start",
    });
    expect(wrapper.findAll(".event-date-card")).toHaveLength(2);
  });

  it("applies legacy query arguments", async () => {
    current.options = {
      ...options,
      organization: { id: 4, name: "Jam Org" },
      organizer: { id: 8, name: "Jam Crew" },
    };
    await mountPage("/eventdates?admin_unit_id=4&organizer_id=8&keyword=jam&category_id=0");

    expect(GET).toHaveBeenNthCalledWith(1, "/bff/public/event-dates/options", {
      params: { query: { admin_unit_id: 4, organizer_id: 8 } },
    });
    expect(searchCalls()[0][1].params.query).toMatchObject({
      admin_unit_id: 4,
      organizer_id: 8,
      keyword: "jam",
      category_id: undefined,
    });
  });

  it("writes the filter to the URL on submit and searches again", async () => {
    const { wrapper, router } = await mountPage();

    await wrapper.find("#keyword").setValue("jam");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(router.currentRoute.value.query).toEqual({ keyword: "jam" });
    expect(searchCalls()).toHaveLength(2);
    expect(searchCalls()[1][1].params.query).toMatchObject({ keyword: "jam", page: 1 });
  });

  it("searches again when the same filter is submitted twice", async () => {
    const { wrapper } = await mountPage();

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(searchCalls()).toHaveLength(2);
  });

  it("follows back and forward navigation", async () => {
    const { router } = await mountPage();

    await router.push("/eventdates?keyword=other");
    await flushPromises();

    expect(searchCalls()).toHaveLength(2);
    expect(searchCalls()[1][1].params.query).toMatchObject({ keyword: "other" });
  });

  it("changes the page with the pager", async () => {
    current.search = searchResult([item(1)], 3);
    const { wrapper, router } = await mountPage();

    await wrapper.find('button[aria-label="Next page"]').trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.query).toEqual({ page: "2" });
    expect(searchCalls()[1][1].params.query).toMatchObject({ page: 2 });
  });

  it("shows the empty state", async () => {
    current.search = searchResult([]);
    const { wrapper } = await mountPage();

    expect(wrapper.find('[data-test="empty"]').exists()).toBe(true);
  });

  it("shows the error when the search fails", async () => {
    current.search = { error: { name: "Error", message: "Boom" } } as never;
    const { wrapper } = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Boom");
  });

  it("shows the error when the options fail", async () => {
    GET.mockResolvedValue({ error: { name: "Error", message: "No options" } });
    const { wrapper } = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("No options");
    expect(searchCalls()).toHaveLength(0);
  });

  describe("references", () => {
    beforeEach(() => {
      current.options = {
        ...options,
        referencing_organization: { id: 5, name: "Mine" },
      };
      current.search = searchResult([
        item(1, { state: "none", reference_id: null }),
        item(2, { state: "referenced", reference_id: 77 }),
        item(3, { state: "own", reference_id: null }),
      ]);
    });

    it("creates a reference and searches again", async () => {
      const { wrapper } = await mountPage();

      await wrapper.find('[data-test="reference-none"]').trigger("click");
      await flushPromises();

      expect(POST).toHaveBeenCalledWith("/bff/manage/organizations/{id}/event-references", {
        params: { path: { id: 5 } },
        body: { event_id: 101 },
      });
      expect(notify.success).toHaveBeenCalled();
      expect(searchCalls()).toHaveLength(2);
    });

    it("deletes a reference and searches again", async () => {
      const { wrapper } = await mountPage();

      await wrapper.find('[data-test="reference-referenced"]').trigger("click");
      await flushPromises();

      expect(DELETE).toHaveBeenCalledWith("/bff/manage/event-references/{id}", {
        params: { path: { id: 77 } },
      });
      expect(notify.success).toHaveBeenCalled();
      expect(searchCalls()).toHaveLength(2);
    });

    it("reports a failed write", async () => {
      POST.mockResolvedValue({ error: { name: "Error", message: "Denied" } });
      const { wrapper } = await mountPage();

      await wrapper.find('[data-test="reference-none"]').trigger("click");
      await flushPromises();

      expect(notify.error).toHaveBeenCalledWith("Denied");
      expect(notify.success).not.toHaveBeenCalled();
    });
  });

  describe("map", () => {
    const place = { name: "Hall", latitude: 51.9, longitude: 10.4 };

    it("is hidden until toggled", async () => {
      const { wrapper } = await mountPage();
      expect(wrapper.find("#event-dates-map").exists()).toBe(false);

      await wrapper.find("#toggle-map-btn").trigger("click");
      await flushPromises();

      expect(wrapper.find("#event-dates-map").exists()).toBe(true);
    });

    it("opens from a place link and flies to the coordinates", async () => {
      current.search = searchResult([item(1, null, place)]);
      const { wrapper } = await mountPage();

      await wrapper.find('[data-test="place"]').trigger("click");
      await flushPromises();

      expect(wrapper.find("#event-dates-map").exists()).toBe(true);
      expect(flyTo).toHaveBeenCalledWith(51.9, 10.4);
    });
  });
});
