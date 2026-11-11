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

import { mountPage } from "../testing";
import IncomingEventReferencePage from "./IncomingEventReferencePage.vue";

const URL = "/manage/admin_unit/3/incoming_event_reference/5";
const READ = "/bff/manage/organizations/{id}/incoming-event-references/{reference_id}";
const MESSAGES = { Cancel: "Cancel" };
const reference = (over = {}) => ({
  id: 5,
  event_id: 8,
  event_name: "Mein Event",
  rating: 70,
  rating_text: "7/10",
  rating_choices: [
    { value: 50, label: "5 (Default)" },
    { value: 70, label: "7" },
  ],
  audit: { created_at: "2026-11-04T10:00:00Z", created_by_label: "me@test.de" },
  can_write: true,
  can_assign_calendars: false,
  ...over,
});
const mountIt = () => mountPage(IncomingEventReferencePage, { organizationId: 3, id: 5 }, URL, MESSAGES);
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];
const openActions = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find("button.dropdown-toggle").trigger("click");
  await flushPromises();
};

describe("IncomingEventReferencePage", () => {
  const assign = vi.fn();

  beforeEach(() => {
    [GET, POST, PUT, success, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
    document.body.innerHTML = "";
  });

  it("shows the event, the rating and the audit line", async () => {
    GET.mockResolvedValue({ data: reference() });
    const { wrapper } = await mountIt();

    expect(GET).toHaveBeenCalledWith(READ, { params: { path: { id: 3, reference_id: 5 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Incoming references");
    expect(wrapper.find(".breadcrumb").text()).toContain("Event reference 5");
    expect(wrapper.find("dl a").attributes("href")).toBe("/event/8");
    expect(wrapper.find("dl").text()).toContain("7/10");
    expect(wrapper.find("[data-test=audit]").text()).toContain("by me@test.de");
  });

  it("offers edit, delete and view event", async () => {
    GET.mockResolvedValue({ data: reference() });
    const { wrapper } = await mountIt();
    await openActions(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual(["Edit", "Delete", "View event"]);
    expect(items()[2].getAttribute("href")).toBe("/event/8");
  });

  it("offers the calendars when the user may assign them", async () => {
    GET.mockImplementation(async (path: string) =>
      path.endsWith("/calendars")
        ? { data: { choices: [], selected_ids: [] } }
        : { data: reference({ can_assign_calendars: true }) },
    );
    const { wrapper } = await mountIt();
    await openActions(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual([
      "Edit",
      "Delete",
      "Calendars…",
      "View event",
    ]);
    items()[2].click();
    await flushPromises();

    expect(GET).toHaveBeenLastCalledWith(
      "/bff/manage/organizations/{id}/events/{event_id}/calendars",
      { params: { path: { id: 3, event_id: 8 } } },
    );
  });

  it("offers only the event without write permission", async () => {
    GET.mockResolvedValue({ data: reference({ can_write: false }) });
    const { wrapper } = await mountIt();
    await openActions(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual(["View event"]);
  });

  it("shows the error of a failed load", async () => {
    GET.mockResolvedValue({ error: { message: "Not found" } });
    const { wrapper } = await mountIt();

    expect(wrapper.find(".alert-danger").text()).toBe("Not found");
    expect(wrapper.find("dl").exists()).toBe(false);
  });

  it("edits the rating in a modal that starts with the rating (default without one)", async () => {
    GET.mockResolvedValue({ data: reference({ rating: null }) });
    PUT.mockResolvedValue({ data: { message: "Incoming reference successfully updated" } });
    const { wrapper } = await mountIt();
    await openActions(wrapper);
    items()[0].click();
    await flushPromises();

    const select = document.querySelector<HTMLSelectElement>("#rating")!;
    expect(select.value).toBe("50");
    select.value = "70";
    select.dispatchEvent(new Event("change"));
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-primary")!.click();
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith(READ, {
      params: { path: { id: 3, reference_id: 5 } },
      body: { rating: 70 },
    });
    expect(success).toHaveBeenCalledWith("Incoming reference successfully updated");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("shows the error of a failed rating update inside the modal", async () => {
    GET.mockResolvedValue({ data: reference() });
    PUT.mockResolvedValue({ error: { message: "Database error" } });
    const { wrapper } = await mountIt();
    await openActions(wrapper);
    items()[0].click();
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-primary")!.click();
    await flushPromises();

    expect(document.querySelector("[data-test=rating-error]")?.textContent?.trim()).toBe("Database error");
    expect(success).not.toHaveBeenCalled();
  });

  it("deletes after a plain confirmation and leaves for the list", async () => {
    GET.mockResolvedValue({ data: reference() });
    POST.mockResolvedValue({
      data: { message: "deleted", redirect_url: "/manage/admin_unit/3/incoming_event_references" },
      response: { ok: true },
    });
    const { wrapper } = await mountIt();
    await openActions(wrapper);
    items()[1].click();
    await flushPromises();

    expect(document.body.textContent).toContain("Do you want to delete 'Event reference 5'?");
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(`${READ}/delete`, {
      params: { path: { id: 3, reference_id: 5 } },
      body: { inline: false },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3/incoming_event_references");
  });

  it("shows the error of a failed delete inside the modal and stays", async () => {
    GET.mockResolvedValue({ data: reference() });
    POST.mockResolvedValue({ error: { message: "Database error" }, response: { ok: false } });
    const { wrapper } = await mountIt();
    await openActions(wrapper);
    items()[1].click();
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!.click();
    await flushPromises();

    expect(document.querySelector("[data-test=confirm-error]")?.textContent?.trim()).toBe(
      "Database error",
    );
    expect(assign).not.toHaveBeenCalled();
  });
});
