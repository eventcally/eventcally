import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import { mountPage } from "../testing";
import OutgoingEventReferencesPage from "./OutgoingEventReferencesPage.vue";

const URL = "/manage/admin_unit/3/outgoing_event_references";
const row = {
  id: 5,
  event_id: 8,
  event_name: "Mein Event",
  organization_id: 4,
  organization_name: "Other Crew",
  created_at: "2026-11-04T10:00:00Z",
};
const page = (items: object[], over = {}) => ({
  data: { items, page: 1, per_page: 50, total: items.length, pages: 1, can_write: false, ...over },
});

describe("OutgoingEventReferencesPage", () => {
  beforeEach(() => {
    GET.mockReset();
    document.body.innerHTML = "";
  });

  it("lists the references with a link to the events and a view event action", async () => {
    GET.mockResolvedValue(page([row]));
    const { wrapper } = await mountPage(OutgoingEventReferencesPage, { organizationId: 3 }, URL);

    expect(GET).toHaveBeenCalledWith("/bff/manage/organizations/{id}/outgoing-event-references", {
      params: { path: { id: 3 }, query: { page: 1 } },
    });
    expect(wrapper.find(".breadcrumb").text()).toContain("Outgoing references");
    expect(wrapper.find("[data-test=instruction] a").attributes("href")).toBe(
      "/manage/admin_unit/3/events",
    );
    expect(wrapper.find("table").text()).toContain("Other Crew");

    await wrapper.find(".row-actions button").trigger("click");
    await flushPromises();
    const items = [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];
    expect(items.map((i) => i.textContent?.trim())).toEqual(["View event"]);
    expect(items[0].getAttribute("href")).toBe("/event/8");
  });

  it("shows no table for an empty list, the error of a failed load and pages", async () => {
    GET.mockResolvedValue(page([]));
    expect(
      (await mountPage(OutgoingEventReferencesPage, { organizationId: 3 }, URL)).wrapper
        .find("table")
        .exists(),
    ).toBe(false);

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(OutgoingEventReferencesPage, { organizationId: 3 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");

    GET.mockResolvedValue(page([row], { total: 120, pages: 3 }));
    const paged = await mountPage(OutgoingEventReferencesPage, { organizationId: 3 }, URL);
    await paged.wrapper.find('button[aria-label="Next page"]').trigger("click");
    await flushPromises();
    expect(paged.router.currentRoute.value.query.page).toBe("2");
  });
});
