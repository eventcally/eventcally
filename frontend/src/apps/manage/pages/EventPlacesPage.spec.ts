import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
const success = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import { mountPage } from "../testing";
import EventPlacesPage from "./EventPlacesPage.vue";

const URL = "/manage/admin_unit/3/event_places";
const LIST = "/bff/manage/organizations/{id}/event-places/list";
const row = (over = {}) => ({
  id: 8,
  name: "Rathaus",
  location: "Markt 1, 38640 Goslar",
  has_coordinates: true,
  has_photo: false,
  number_of_events: 3,
  last_modified_at: "2026-11-04T10:00:00Z",
  ...over,
});
const page = (items: object[], over = {}) => ({
  data: { items, page: 1, per_page: 50, total: items.length, pages: 1, can_write: true, ...over },
});
const items = () => [...document.querySelectorAll<HTMLElement>(".dropdown-item")];

describe("EventPlacesPage", () => {
  beforeEach(() => [GET, POST, success].forEach((f) => f.mockReset()));

  it("lists the places with their columns and the actions", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(EventPlacesPage, { organizationId: 3 }, URL);

    expect(GET).toHaveBeenCalledWith(LIST, {
      params: { path: { id: 3 }, query: { page: 1, sort: "name", keyword: undefined } },
    });
    expect(wrapper.find(".breadcrumb").text()).toContain("Places");
    expect(wrapper.find("table").text()).toContain("Markt 1, 38640 Goslar");
    // Coordinates yes, photo no.
    expect(wrapper.findAll("table .fa-check-circle")).toHaveLength(1);
    expect(wrapper.find('a[href="/manage/admin_unit/3/event_place/create"]').text()).toContain(
      "Create Place",
    );

    await wrapper.find(".row-actions button").trigger("click");
    expect(items().map((i) => i.textContent?.trim())).toEqual(["Edit", "Delete", "View events"]);
    expect(items()[0].getAttribute("href")).toBe("/manage/admin_unit/3/event_place/8/update");
    expect(items()[2].getAttribute("href")).toBe("/manage/admin_unit/3/events?event_place_id=8");
  });

  it("only offers viewing the events without write permission", async () => {
    GET.mockResolvedValue(page([row({ has_photo: true })], { can_write: false }));
    const { wrapper } = await mountPage(EventPlacesPage, { organizationId: 3 }, URL);

    await wrapper.find(".row-actions button").trigger("click");
    expect(items().map((i) => i.textContent?.trim())).toEqual(["View events"]);
    expect(wrapper.find('a[href$="/create"]').exists()).toBe(false);
    expect(wrapper.findAll("table .fa-check-circle")).toHaveLength(2);
  });

  it("searches, sorts and shows the error and the empty list", async () => {
    GET.mockResolvedValue(page([]));
    const { wrapper, router } = await mountPage(
      EventPlacesPage,
      { organizationId: 3 },
      `${URL}?keyword=Rat&sort=-number_of_events`,
    );

    expect(wrapper.find("table").exists()).toBe(false);
    expect(GET.mock.calls[0][1].params.query).toEqual({
      page: 1,
      sort: "-number_of_events",
      keyword: "Rat",
    });
    await wrapper.find("[data-test=filters-reset]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({});

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(EventPlacesPage, { organizationId: 3 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });

  it("deletes after typing the name", async () => {
    GET.mockResolvedValue(page([row()]));
    POST.mockResolvedValue({ data: { message: "Place successfully deleted" }, response: { ok: true } });
    const { wrapper } = await mountPage(EventPlacesPage, { organizationId: 3 }, URL);

    await wrapper.find(".row-actions button").trigger("click");
    items()[1].click();
    await flushPromises();
    const input = document.querySelector<HTMLInputElement>("#name")!;
    input.value = "Rathaus";
    input.dispatchEvent(new Event("input"));
    document
      .querySelector("[data-test=confirmation-form]")!
      .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(
      "/bff/manage/organizations/{id}/event-places/{place_id}/delete",
      { params: { path: { id: 3, place_id: 8 } }, body: { name: "Rathaus" } },
    );
    expect(success).toHaveBeenCalledWith("Place successfully deleted");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("goes back a page when the last row of a later page was deleted", async () => {
    GET.mockResolvedValueOnce(page([row()], { page: 2, total: 51, pages: 2 }));
    GET.mockResolvedValue(page([], { page: 2, total: 50, pages: 1 }));
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper, router } = await mountPage(EventPlacesPage, { organizationId: 3 }, `${URL}?page=2`);

    await wrapper.find(".row-actions button").trigger("click");
    items()[1].click();
    await flushPromises();
    const input = document.querySelector<HTMLInputElement>("#name")!;
    input.value = "Rathaus";
    input.dispatchEvent(new Event("input"));
    document
      .querySelector("[data-test=confirmation-form]")!
      .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    await flushPromises();

    expect(router.currentRoute.value.query.page).toBe("1");
  });
});
