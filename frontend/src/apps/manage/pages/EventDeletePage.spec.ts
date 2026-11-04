import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));

import { mountPage } from "../testing";
import EventDeleteModal from "../components/EventDeleteModal.vue";
import EventDeletePage from "./EventDeletePage.vue";

const URL = "/manage/admin_unit/3/event/9/delete";
const FORM = "/bff/manage/organizations/{id}/events/{event_id}/delete-form";
const DELETE = "/bff/manage/organizations/{id}/events/{event_id}/delete";
const form = (over = {}) => ({
  data: { id: 9, name: "Jam Session", has_multiple_dates: false, ...over },
});
const assign = vi.fn();

describe("EventDeletePage", () => {
  beforeEach(() => {
    [GET, POST, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
  });

  it("asks for the event and deletes it, then leaves for the list", async () => {
    GET.mockResolvedValue(form());
    POST.mockResolvedValue({
      data: { message: "Event successfully deleted", redirect_url: "/manage/admin_unit/3/events" },
    });
    const { wrapper } = await mountPage(EventDeletePage, { organizationId: 3, id: 9 }, URL);

    expect(GET).toHaveBeenCalledWith(FORM, { params: { path: { id: 3, event_id: 9 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Delete Event");
    expect(wrapper.text()).toContain("Do you want to delete 'Jam Session'?");
    expect(wrapper.text()).not.toContain("multiple dates");

    await wrapper.find("#submit").trigger("click");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(DELETE, {
      params: { path: { id: 3, event_id: 9 } },
      body: { inline: false },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3/events");
  });

  it("warns about several dates and links to the edit page", async () => {
    GET.mockResolvedValue(form({ has_multiple_dates: true }));
    const { wrapper } = await mountPage(EventDeletePage, { organizationId: 3, id: 9 }, URL);

    expect(wrapper.find(".alert-danger").text()).toContain("multiple dates");
    expect(wrapper.find('.alert-danger a[href="/manage/admin_unit/3/event/9/update"]').text()).toBe(
      "Edit event",
    );
  });

  it("shows the error of the load and of the delete", async () => {
    GET.mockResolvedValue({ error: { message: "Not found" } });
    const failed = await mountPage(EventDeletePage, { organizationId: 3, id: 9 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Not found");
    expect(failed.wrapper.find("#submit").exists()).toBe(false);

    GET.mockResolvedValue(form());
    POST.mockResolvedValue({ error: { message: "Kaputt" } });
    const { wrapper } = await mountPage(EventDeletePage, { organizationId: 3, id: 9 }, URL);
    await wrapper.find("#submit").trigger("click");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Kaputt");
    expect(assign).not.toHaveBeenCalled();
  });
});

describe("EventDeleteModal", () => {
  beforeEach(() => [GET, POST].forEach((f) => f.mockReset()));

  it("deletes inline and reports the answer", async () => {
    GET.mockResolvedValue(form());
    POST.mockResolvedValue({
      data: { message: "Event successfully deleted", redirect_url: "/x" },
    });
    const { wrapper } = await mountPage(
      EventDeleteModal,
      { organizationId: 3, eventId: 9, modelValue: true },
      URL,
    );

    expect(document.body.textContent).toContain("Do you want to delete 'Jam Session'?");
    document.querySelector<HTMLButtonElement>("#submit")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(DELETE, {
      params: { path: { id: 3, event_id: 9 } },
      body: { inline: true },
    });
    expect(wrapper.emitted("deleted")).toEqual([
      [{ message: "Event successfully deleted", redirect_url: "/x" }],
    ]);
  });

  it("loads nothing without an event", async () => {
    await mountPage(EventDeleteModal, { organizationId: 3, eventId: null, modelValue: true }, URL);

    expect(GET).not.toHaveBeenCalled();
  });
});
