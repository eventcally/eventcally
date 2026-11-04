import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import { mountPage } from "../testing";
import IncomingEventReferenceRequestsPage from "../pages/IncomingEventReferenceRequestsPage.vue";
import OutgoingEventReferenceRequestsPage from "../pages/OutgoingEventReferenceRequestsPage.vue";

const IN = "/manage/admin_unit/3/incoming_event_reference_requests";
const OUT = "/manage/admin_unit/3/outgoing_event_reference_requests";
const IN_URL = "/bff/manage/organizations/{id}/incoming-event-reference-requests";
const OUT_URL = "/bff/manage/organizations/{id}/outgoing-event-reference-requests";
const MESSAGES = { Cancel: "Cancel" };

const row = (over = {}) => ({
  id: 5,
  event_id: 8,
  event_name: "Mein Event",
  organization_id: 4,
  organization_name: "Other Crew",
  review_status: 1,
  review_status_label: "Inbox",
  created_at: "2026-11-04T10:00:00Z",
  can_review: true,
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
    review_status_choices: [
      { value: -1, label: "All" },
      { value: 1, label: "Inbox" },
      { value: 3, label: "Rejected" },
    ],
    ...over,
  },
});
const open = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find(".row-actions button").trigger("click");
  await flushPromises();
};
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];

describe("incoming reference requests", () => {
  beforeEach(() => {
    GET.mockReset();
    document.body.innerHTML = "";
  });

  it("lists the requests with the status, review and view event actions", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(IncomingEventReferenceRequestsPage, { organizationId: 3 }, IN, MESSAGES);

    expect(GET).toHaveBeenCalledWith(IN_URL, {
      params: { path: { id: 3 }, query: { page: 1, review_status: undefined } },
    });
    expect(wrapper.find(".breadcrumb").text()).toContain("Incoming reference requests");
    expect(wrapper.find("[data-test=instruction]").text()).toContain(
      "Here you will find requests from other organizations",
    );
    expect(wrapper.find("[data-test=instruction] a").exists()).toBe(false);
    expect(wrapper.find("table .badge.text-bg-info").text()).toBe("Inbox");

    await open(wrapper);
    expect(items().map((i) => i.textContent?.trim())).toEqual(["Review request", "View event"]);
    expect(items()[0].getAttribute("href")).toBe(
      "/manage/admin_unit/3/incoming_event_reference_request/5/review",
    );
    expect(items()[1].getAttribute("href")).toBe("/event/8");
  });

  it("does not offer a review of a verified request", async () => {
    GET.mockResolvedValue(page([row({ can_review: false })]));
    const { wrapper } = await mountPage(IncomingEventReferenceRequestsPage, { organizationId: 3 }, IN, MESSAGES);
    await open(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual(["View event"]);
  });

  it("reads the status filter from the URL and mirrors it back", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper, router } = await mountPage(
      IncomingEventReferenceRequestsPage,
      { organizationId: 3 },
      `${IN}?review_status=3&page=2`,
      MESSAGES,
    );

    expect(GET).toHaveBeenCalledWith(IN_URL, {
      params: { path: { id: 3 }, query: { page: 2, review_status: 3 } },
    });
    expect(wrapper.find("[data-test=filters-toggle]").attributes("aria-expanded")).toBe("true");
    expect((wrapper.find("#review_status").element as HTMLSelectElement).value).toBe("3");

    await wrapper.find("#review_status").setValue(1);
    await wrapper.find("[data-test=filters-form]").trigger("submit");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ review_status: "1" });

    await wrapper.find("#review_status").setValue(-1);
    await wrapper.find("[data-test=filters-form]").trigger("submit");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({});

    await router.push(`${IN}?review_status=3`);
    await flushPromises();
    await wrapper.find("[data-test=filters-reset]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({});
  });

  it("shows no table for an empty list, the error of a failed load and pages", async () => {
    GET.mockResolvedValue(page([]));
    const empty = await mountPage(IncomingEventReferenceRequestsPage, { organizationId: 3 }, IN, MESSAGES);
    expect(empty.wrapper.find("table").exists()).toBe(false);

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(IncomingEventReferenceRequestsPage, { organizationId: 3 }, IN, MESSAGES);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");

    GET.mockResolvedValue(page([row()], { total: 120, pages: 3 }));
    const paged = await mountPage(IncomingEventReferenceRequestsPage, { organizationId: 3 }, IN, MESSAGES);
    await paged.wrapper.find('button[aria-label="Next page"]').trigger("click");
    await flushPromises();
    expect(paged.router.currentRoute.value.query.page).toBe("2");
  });
});

describe("outgoing reference requests", () => {
  beforeEach(() => {
    GET.mockReset();
    document.body.innerHTML = "";
  });

  it("lists the requests with the events link and a view action", async () => {
    GET.mockResolvedValue(page([row({ review_status: 3, review_status_label: "Rejected" })], { can_write: false }));
    const { wrapper } = await mountPage(OutgoingEventReferenceRequestsPage, { organizationId: 3 }, OUT, MESSAGES);

    expect(GET).toHaveBeenCalledWith(OUT_URL, {
      params: { path: { id: 3 }, query: { page: 1, review_status: undefined } },
    });
    expect(wrapper.find(".breadcrumb").text()).toContain("Outgoing reference requests");
    expect(wrapper.find("[data-test=instruction]").text()).toContain(
      'select "Request reference" on one of your event pages',
    );
    expect(wrapper.find("[data-test=instruction] a").attributes("href")).toBe(
      "/manage/admin_unit/3/events",
    );
    expect(wrapper.find("table .badge.text-bg-danger").text()).toBe("Rejected");

    await open(wrapper);
    expect(items().map((i) => i.textContent?.trim())).toEqual(["View"]);
    expect(items()[0].getAttribute("href")).toBe(
      "/manage/admin_unit/3/outgoing_event_reference_request/5",
    );
  });
});
