import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

const success = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import { setFlash } from "../flash";
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
        createI18n({ legacy: false, locale: "en", messages: { en: {} } }),
      ],
    },
  });
  await flushPromises();
  return { wrapper, router };
}

const listCalls = () =>
  GET.mock.calls.filter(([path]) => path === "/bff/manage/organizations/{id}/events");

describe("ManageEventsPage", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    success.mockReset();
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

  it("shows the flash message of a legacy action", async () => {
    setFlash("Event deleted");
    await mountPage();

    expect(success).toHaveBeenCalledWith("Event deleted");
  });
});
