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
import CalendarsPage from "./CalendarsPage.vue";

const URL = "/manage/admin_unit/3/calendars";
const LIST = "/bff/manage/organizations/{id}/calendars/list";
const row = (over = {}) => ({
  id: 4,
  name: "Sport",
  description: null,
  private: false,
  number_of_events: 2,
  last_modified_at: "2026-11-04T10:00:00Z",
  public_url: "/calendars/4",
  ...over,
});
const page = (items: object[], over = {}) => ({
  data: { items, page: 1, per_page: 50, total: items.length, pages: 1, can_write: true, ...over },
});

const open = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find(".row-actions button").trigger("click");
  await flushPromises();
};
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];
const titles = () => items().map((i) => i.textContent?.trim());

describe("CalendarsPage", () => {
  beforeEach(() => {
    [GET, POST, success].forEach((f) => f.mockReset());
    document.body.innerHTML = "";
    sessionStorage.clear();
  });

  it("lists the calendars and offers create", async () => {
    GET.mockResolvedValue(page([row({ private: true, public_url: null })]));
    const { wrapper } = await mountPage(CalendarsPage, { organizationId: 3 }, URL);

    expect(GET).toHaveBeenCalledWith(LIST, {
      params: { path: { id: 3 }, query: { page: 1, sort: "name", keyword: undefined } },
    });
    expect(wrapper.find(".breadcrumb").text()).toContain("Calendars");
    expect(wrapper.find("table .fa-check-circle").exists()).toBe(true);
    expect(wrapper.find('a[href="/manage/admin_unit/3/calendar/create"]').text()).toContain(
      "Create Calendar",
    );
  });

  it("offers show only for public calendars, plus events, edit and delete", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(CalendarsPage, { organizationId: 3 }, URL);
    await open(wrapper);

    expect(titles()).toEqual(["Show", "View events", "Edit", "Delete"]);
    expect(items()[0].getAttribute("href")).toBe("/calendars/4");
    expect(items()[1].getAttribute("href")).toBe("/manage/admin_unit/3/events?calendar_id=4");
    expect(items()[2].getAttribute("href")).toBe("/manage/admin_unit/3/calendar/4/update");
  });

  it("hides show for private calendars and write actions without the right", async () => {
    GET.mockResolvedValue(page([row({ private: true, public_url: null })], { can_write: false }));
    const { wrapper } = await mountPage(CalendarsPage, { organizationId: 3 }, URL);
    await open(wrapper);

    expect(titles()).toEqual(["View events"]);
    expect(wrapper.find('a[href$="/create"]').exists()).toBe(false);
  });

  it("shows the error of a failed load and nothing for an empty list", async () => {
    GET.mockResolvedValue(page([]));
    expect((await mountPage(CalendarsPage, { organizationId: 3 }, URL)).wrapper.find("table").exists()).toBe(
      false,
    );

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(CalendarsPage, { organizationId: 3 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });

  it("mirrors the filters in the URL", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper, router } = await mountPage(
      CalendarsPage,
      { organizationId: 3 },
      `${URL}?keyword=Sp&sort=-number_of_events`,
    );

    expect((wrapper.find("#keyword").element as HTMLInputElement).value).toBe("Sp");
    await wrapper.find("#keyword").setValue("Mu");
    await wrapper.find("#sort").setValue("-last_modified_at");
    await wrapper.find("[data-test=filters-form]").trigger("submit");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ keyword: "Mu", sort: "-last_modified_at" });

    await wrapper.find("[data-test=filters-reset]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({});
  });

  it("deletes after typing the name and reloads", async () => {
    GET.mockResolvedValue(page([row()]));
    POST.mockResolvedValue({ data: { message: "Calendar successfully deleted" }, response: { ok: true } });
    const { wrapper } = await mountPage(CalendarsPage, { organizationId: 3 }, URL);
    await open(wrapper);
    items()[3].click();
    await flushPromises();

    const input = document.querySelector<HTMLInputElement>("#name")!;
    input.value = "Sport";
    input.dispatchEvent(new Event("input"));
    document
      .querySelector("[data-test=confirmation-form]")!
      .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(
      "/bff/manage/organizations/{id}/calendars/{calendar_id}/delete",
      { params: { path: { id: 3, calendar_id: 4 } }, body: { name: "Sport" } },
    );
    expect(success).toHaveBeenCalledWith("Calendar successfully deleted");
    expect(GET).toHaveBeenCalledTimes(2);
  });
});
