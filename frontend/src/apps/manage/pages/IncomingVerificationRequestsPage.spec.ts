import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import { mountPage } from "../testing";
import IncomingVerificationRequestsPage from "./IncomingVerificationRequestsPage.vue";

const URL = "/manage/admin_unit/3/incoming_organization_verification_requests";
const LIST = "/bff/manage/organizations/{id}/incoming-verification-requests";
const row = (over = {}) => ({
  id: 7,
  organization_id: 4,
  organization_name: "Andere Crew",
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
    ],
    ...over,
  },
});

const open = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find(".row-actions button").trigger("click");
  await flushPromises();
};
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];

describe("IncomingVerificationRequestsPage", () => {
  beforeEach(() => {
    GET.mockReset();
    document.body.innerHTML = "";
  });

  it("lists the requests with their status badge", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(IncomingVerificationRequestsPage, { organizationId: 3 }, URL);

    expect(GET).toHaveBeenCalledWith(LIST, {
      params: { path: { id: 3 }, query: { page: 1, review_status: undefined } },
    });
    expect(wrapper.find(".breadcrumb").text()).toContain("Incoming verification requests");
    expect(wrapper.find("table").text()).toContain("Andere Crew");
    expect(wrapper.find("table .badge").text()).toBe("Inbox");
    expect(wrapper.find("table").text()).toContain("Nov 4, 2026");
  });

  it("offers review and view organization", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(IncomingVerificationRequestsPage, { organizationId: 3 }, URL);
    await open(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual([
      "Review request",
      "View organization",
    ]);
    expect(items()[0].getAttribute("href")).toBe(
      "/manage/admin_unit/3/incoming_organization_verification_request/7/review",
    );
    expect(items()[1].getAttribute("href")).toBe("/organizations/4");
  });

  it("offers no review for a verified request", async () => {
    GET.mockResolvedValue(page([row({ can_review: false })]));
    const { wrapper } = await mountPage(IncomingVerificationRequestsPage, { organizationId: 3 }, URL);
    await open(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual(["View organization"]);
  });

  it("filters by review status through the route query", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper, router } = await mountPage(
      IncomingVerificationRequestsPage,
      { organizationId: 3 },
      `${URL}?review_status=3`,
    );

    expect(GET).toHaveBeenCalledWith(LIST, {
      params: { path: { id: 3 }, query: { page: 1, review_status: 3 } },
    });

    await wrapper.find("#review_status").setValue(1);
    await wrapper.find("[data-test=filters-form]").trigger("submit");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({ review_status: "1" });

    await wrapper.find("#review_status").setValue(-1);
    await wrapper.find("[data-test=filters-form]").trigger("submit");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({});

    await router.push(`${URL}?review_status=3`);
    await flushPromises();
    await wrapper.find("[data-test=filters-reset]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query).toEqual({});
  });

  it("shows no table for an empty list, the error of a failed load and pages", async () => {
    GET.mockResolvedValue(page([]));
    const empty = await mountPage(IncomingVerificationRequestsPage, { organizationId: 3 }, URL);
    expect(empty.wrapper.find("table").exists()).toBe(false);

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(IncomingVerificationRequestsPage, { organizationId: 3 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");

    GET.mockResolvedValue(page([row()], { total: 120, pages: 3 }));
    const paged = await mountPage(IncomingVerificationRequestsPage, { organizationId: 3 }, URL);
    await paged.wrapper.find('button[aria-label="Next page"]').trigger("click");
    await flushPromises();
    expect(paged.router.currentRoute.value.query.page).toBe("2");
  });
});
