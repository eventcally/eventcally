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

import { setFlash } from "@/shared/flash";
import { mountPage } from "../testing";
import EventOrganizersPage from "./EventOrganizersPage.vue";

const URL = "/manage/admin_unit/3/event_organizers";
const row = (over = {}) => ({
  id: 4,
  name: "Mein Veranstalter",
  location: "38640 Goslar",
  phone: null,
  email: null,
  url: null,
  has_logo: true,
  number_of_events: 2,
  last_modified_at: "2026-11-04T10:00:00Z",
  ...over,
});
const page = (items: object[], over = {}) => ({
  data: { items, page: 1, per_page: 50, total: items.length, pages: 1, can_write: true, ...over },
});
const LIST = "/bff/manage/organizations/{id}/event-organizers/list";
const MESSAGES = { Cancel: "Cancel" };

const open = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find(".row-actions button").trigger("click");
  await flushPromises();
};
const items = () =>
  [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")].map((i) => i);

describe("EventOrganizersPage", () => {
  beforeEach(() => {
    [GET, POST, success].forEach((f) => f.mockReset());
    document.body.innerHTML = "";
    sessionStorage.clear();
  });

  it("lists the organizers sorted by name", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(EventOrganizersPage, { organizationId: 3 }, URL, MESSAGES);

    expect(GET).toHaveBeenCalledWith(LIST, {
      params: { path: { id: 3 }, query: { page: 1, sort: "name", keyword: undefined } },
    });
    expect(wrapper.find(".breadcrumb").text()).toContain("Event organizers");
    expect(wrapper.find("table").text()).toContain("38640 Goslar");
    expect(wrapper.find("table .fa-check-circle").exists()).toBe(true);
    expect(wrapper.find('a[href="/manage/admin_unit/3/event_organizer/create"]').text()).toContain(
      "Create Event organizer",
    );
  });

  it("offers view, edit, delete and view events", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(EventOrganizersPage, { organizationId: 3 }, URL, MESSAGES);
    await open(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual([
      "View",
      "Edit",
      "Delete",
      "View events",
    ]);
    expect(items()[0].getAttribute("href")).toBe("/organizers/4");
    expect(items()[1].getAttribute("href")).toBe("/manage/admin_unit/3/event_organizer/4/update");
    expect(items()[3].getAttribute("href")).toBe("/manage/admin_unit/3/events?organizer_id=4");
  });

  it("offers neither create, edit nor delete without write permission", async () => {
    GET.mockResolvedValue(page([row()], { can_write: false }));
    const { wrapper } = await mountPage(EventOrganizersPage, { organizationId: 3 }, URL, MESSAGES);
    await open(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual(["View", "View events"]);
    expect(wrapper.find('a[href$="/create"]').exists()).toBe(false);
  });

  it("shows no table for an empty list and the error of a failed load", async () => {
    GET.mockResolvedValue(page([]));
    const empty = await mountPage(EventOrganizersPage, { organizationId: 3 }, URL, MESSAGES);
    expect(empty.wrapper.find("table").exists()).toBe(false);

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(EventOrganizersPage, { organizationId: 3 }, URL, MESSAGES);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });

  it("reads the filters from the URL and mirrors them back", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper, router } = await mountPage(
      EventOrganizersPage,
      { organizationId: 3 },
      `${URL}?keyword=Mein&sort=-number_of_events&page=2`,
      MESSAGES,
    );

    expect(GET).toHaveBeenCalledWith(LIST, {
      params: {
        path: { id: 3 },
        query: { page: 2, sort: "-number_of_events", keyword: "Mein" },
      },
    });
    expect((wrapper.find("#keyword").element as HTMLInputElement).value).toBe("Mein");
    expect(wrapper.find("[data-test=filters-toggle]").attributes("aria-expanded")).toBe("true");

    await wrapper.find("#keyword").setValue("Neu");
    await wrapper.find("#sort").setValue("-last_modified_at");
    await wrapper.find("[data-test=filters-form]").trigger("submit");
    await flushPromises();

    expect(router.currentRoute.value.query).toEqual({
      keyword: "Neu",
      sort: "-last_modified_at",
    });
    expect(GET).toHaveBeenLastCalledWith(LIST, {
      params: {
        path: { id: 3 },
        query: { page: 1, sort: "-last_modified_at", keyword: "Neu" },
      },
    });

    await wrapper.find("[data-test=filters-reset]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({});
  });

  it("falls back to the name sort for an unknown sort and pages through the list", async () => {
    GET.mockResolvedValue(page([row()], { total: 120, pages: 3 }));
    const { wrapper, router } = await mountPage(
      EventOrganizersPage,
      { organizationId: 3 },
      `${URL}?sort=bogus`,
      MESSAGES,
    );

    expect(GET.mock.calls[0][1].params.query.sort).toBe("name");
    await wrapper.find('button[aria-label="Next page"]').trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.page).toBe("2");
  });

  it("deletes after typing the name, toasts and reloads", async () => {
    GET.mockResolvedValue(page([row()]));
    POST.mockResolvedValue({ data: { message: "Event organizer successfully deleted" }, response: { ok: true } });
    const { wrapper } = await mountPage(EventOrganizersPage, { organizationId: 3 }, URL, MESSAGES);
    await open(wrapper);
    items()[2].click();
    await flushPromises();

    expect(document.body.textContent).toContain("Do you want to delete 'Mein Veranstalter'?");
    const input = document.querySelector<HTMLInputElement>("#name")!;
    input.value = "Mein Veranstalter";
    input.dispatchEvent(new Event("input"));
    document
      .querySelector("[data-test=confirmation-form]")!
      .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(
      "/bff/manage/organizations/{id}/event-organizers/{organizer_id}/delete",
      { params: { path: { id: 3, organizer_id: 4 } }, body: { name: "Mein Veranstalter" } },
    );
    expect(success).toHaveBeenCalledWith("Event organizer successfully deleted");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("shows the mismatch inside the modal", async () => {
    GET.mockResolvedValue(page([row()]));
    POST.mockResolvedValue({
      error: { errors: [{ loc: ["name"], msg: "Entered name does not match organizer name" }] },
      response: { ok: false },
    });
    const { wrapper } = await mountPage(EventOrganizersPage, { organizationId: 3 }, URL, MESSAGES);
    await open(wrapper);
    items()[2].click();
    await flushPromises();

    const input = document.querySelector<HTMLInputElement>("#name")!;
    input.value = "x";
    input.dispatchEvent(new Event("input"));
    document
      .querySelector("[data-test=confirmation-form]")!
      .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    await flushPromises();

    expect(document.querySelector("[data-test=field-error]")?.textContent).toBe(
      "Entered name does not match organizer name",
    );
    expect(success).not.toHaveBeenCalled();
  });

  it("goes back a page when the last row of a later page was deleted", async () => {
    GET.mockResolvedValueOnce(page([row()], { page: 2, total: 51, pages: 2 }));
    GET.mockResolvedValue(page([], { page: 2, total: 50, pages: 1 }));
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper, router } = await mountPage(
      EventOrganizersPage,
      { organizationId: 3 },
      `${URL}?page=2`,
      MESSAGES,
    );
    await open(wrapper);
    items()[2].click();
    await flushPromises();
    const input = document.querySelector<HTMLInputElement>("#name")!;
    input.value = "Mein Veranstalter";
    input.dispatchEvent(new Event("input"));
    document
      .querySelector("[data-test=confirmation-form]")!
      .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    await flushPromises();

    expect(router.currentRoute.value.query.page).toBe("1");
  });

  it("shows the message a previous page left", async () => {
    GET.mockResolvedValue(page([]));
    setFlash("Event organizer successfully created");
    await mountPage(EventOrganizersPage, { organizationId: 3 }, URL, MESSAGES);

    expect(success).toHaveBeenCalledWith("Event organizer successfully created");
  });
});
