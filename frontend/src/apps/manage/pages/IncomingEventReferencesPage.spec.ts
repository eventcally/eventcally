import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
vi.mock("@/shared/api", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
  },
}));
const success = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import { setFlash } from "@/shared/flash";
import { mountPage } from "../testing";
import IncomingEventReferencesPage from "./IncomingEventReferencesPage.vue";

const URL = "/manage/admin_unit/3/incoming_event_references";
const LIST = "/bff/manage/organizations/{id}/incoming-event-references";
const MESSAGES = { Cancel: "Cancel" };
const row = (over = {}) => ({
  id: 5,
  event_id: 8,
  event_name: "Mein Event",
  organization_id: 4,
  organization_name: "Other Crew",
  rating: 70,
  created_at: "2026-11-04T10:00:00Z",
  ...over,
});
const page = (items: object[], over = {}) => ({
  data: {
    items,
    page: 1,
    per_page: 50,
    total: items.length,
    pages: 1,
    can_write: true,
    rating_choices: [
      { value: 50, label: "5 (Default)" },
      { value: 70, label: "7" },
    ],
    ...over,
  },
});

const open = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find(".row-actions button").trigger("click");
  await flushPromises();
};
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];

describe("IncomingEventReferencesPage", () => {
  beforeEach(() => {
    [GET, POST, PUT, success].forEach((f) => f.mockReset());
    document.body.innerHTML = "";
    sessionStorage.clear();
  });

  it("lists the references with the instruction and its search link", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(IncomingEventReferencesPage, { organizationId: 3 }, URL, MESSAGES);

    expect(GET).toHaveBeenCalledWith(LIST, { params: { path: { id: 3 }, query: { page: 1 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Incoming references");
    expect(wrapper.find("[data-test=instruction]").text()).toContain(
      'select "Reference event" on an event page',
    );
    expect(wrapper.find("[data-test=instruction] a").attributes("href")).toBe("/eventdates");
    expect(wrapper.find("table").text()).toContain("Other Crew");
    expect(wrapper.find("table").text()).toContain("Nov 4, 2026");
  });

  it("offers view, edit, delete and view event", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(IncomingEventReferencesPage, { organizationId: 3 }, URL, MESSAGES);
    await open(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual([
      "View",
      "Edit",
      "Delete",
      "View event",
    ]);
    expect(items()[0].getAttribute("href")).toBe("/manage/admin_unit/3/incoming_event_reference/5");
    expect(items()[3].getAttribute("href")).toBe("/event/8");
  });

  it("offers neither edit nor delete without write permission", async () => {
    GET.mockResolvedValue(page([row()], { can_write: false }));
    const { wrapper } = await mountPage(IncomingEventReferencesPage, { organizationId: 3 }, URL, MESSAGES);
    await open(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual(["View", "View event"]);
  });

  it("shows no table for an empty list, the error of a failed load and pages", async () => {
    GET.mockResolvedValue(page([]));
    const empty = await mountPage(IncomingEventReferencesPage, { organizationId: 3 }, URL, MESSAGES);
    expect(empty.wrapper.find("table").exists()).toBe(false);

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(IncomingEventReferencesPage, { organizationId: 3 }, URL, MESSAGES);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");

    GET.mockResolvedValue(page([row()], { total: 120, pages: 3 }));
    const paged = await mountPage(IncomingEventReferencesPage, { organizationId: 3 }, URL, MESSAGES);
    await paged.wrapper.find('button[aria-label="Next page"]').trigger("click");
    await flushPromises();
    expect(paged.router.currentRoute.value.query.page).toBe("2");
  });

  it("edits the rating in a modal and reloads", async () => {
    GET.mockResolvedValue(page([row()]));
    PUT.mockResolvedValue({ data: { message: "Incoming reference successfully updated" } });
    const { wrapper } = await mountPage(IncomingEventReferencesPage, { organizationId: 3 }, URL, MESSAGES);
    await open(wrapper);
    items()[1].click();
    await flushPromises();

    const select = document.querySelector<HTMLSelectElement>("#rating")!;
    expect(select.value).toBe("70");
    select.value = "50";
    select.dispatchEvent(new Event("change"));
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-primary")!.click();
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith(
      "/bff/manage/organizations/{id}/incoming-event-references/{reference_id}",
      { params: { path: { id: 3, reference_id: 5 } }, body: { rating: 50 } },
    );
    expect(success).toHaveBeenCalledWith("Incoming reference successfully updated");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("deletes after a plain confirmation, toasts and reloads", async () => {
    GET.mockResolvedValue(page([row()]));
    POST.mockResolvedValue({
      data: { message: "Incoming reference successfully deleted", redirect_url: "/x" },
      response: { ok: true },
    });
    const { wrapper } = await mountPage(IncomingEventReferencesPage, { organizationId: 3 }, URL, MESSAGES);
    await open(wrapper);
    items()[2].click();
    await flushPromises();

    expect(document.body.textContent).toContain("Do you want to delete 'Event reference 5'?");
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(
      "/bff/manage/organizations/{id}/incoming-event-references/{reference_id}/delete",
      { params: { path: { id: 3, reference_id: 5 } }, body: { inline: true } },
    );
    expect(success).toHaveBeenCalledWith("Incoming reference successfully deleted");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("goes back a page when the last row of a later page was deleted", async () => {
    GET.mockResolvedValueOnce(page([row()], { page: 2, total: 51, pages: 2 }));
    GET.mockResolvedValue(page([], { page: 2, total: 50, pages: 1 }));
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper, router } = await mountPage(
      IncomingEventReferencesPage,
      { organizationId: 3 },
      `${URL}?page=2`,
      MESSAGES,
    );
    await open(wrapper);
    items()[2].click();
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!.click();
    await flushPromises();

    expect(router.currentRoute.value.query.page).toBe("1");
  });

  it("shows the message a previous page left", async () => {
    GET.mockResolvedValue(page([]));
    setFlash("Incoming reference successfully deleted");
    await mountPage(IncomingEventReferencesPage, { organizationId: 3 }, URL, MESSAGES);

    expect(success).toHaveBeenCalledWith("Incoming reference successfully deleted");
  });
});
