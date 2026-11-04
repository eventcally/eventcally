import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import { mountPage } from "../testing";
import OutgoingEventReferenceRequestPage from "./OutgoingEventReferenceRequestPage.vue";

const URL = "/manage/admin_unit/3/outgoing_event_reference_request/5";
const request = (over = {}) => ({
  id: 5,
  event_id: 8,
  event_name: "Mein Event",
  review_status: 3,
  review_status_label: "Rejected",
  rejection_reason_label: "Irrelevant",
  organization_id: 4,
  organization_name: "Other Crew",
  audit: { created_at: "2026-11-04T10:00:00Z" },
  ...over,
});
const mountIt = () => mountPage(OutgoingEventReferenceRequestPage, { organizationId: 3, id: 5 }, URL);

describe("OutgoingEventReferenceRequestPage", () => {
  beforeEach(() => {
    GET.mockReset();
    document.body.innerHTML = "";
  });

  it("shows the event, the status, the rejection reason and the organization", async () => {
    GET.mockResolvedValue({ data: request() });
    const { wrapper } = await mountIt();

    expect(GET).toHaveBeenCalledWith(
      "/bff/manage/organizations/{id}/outgoing-event-reference-requests/{request_id}",
      { params: { path: { id: 3, request_id: 5 } } },
    );
    expect(wrapper.find(".breadcrumb").text()).toContain("Outgoing reference requests");
    expect(wrapper.find(".breadcrumb").text()).toContain("Event reference request 5");
    expect(wrapper.find("dl a").attributes("href")).toBe("/event/8");
    expect(wrapper.find("dl .badge.text-bg-danger").text()).toBe("Rejected");
    expect(wrapper.find("dl").text()).toContain("Irrelevant");
    expect(wrapper.find("dl").text()).toContain("Other Crew");
    expect(wrapper.find("[data-test=audit]").exists()).toBe(true);
  });

  it("hides the rejection reason of a request without one", async () => {
    GET.mockResolvedValue({ data: request({ rejection_reason_label: null, review_status: 1 }) });
    const { wrapper } = await mountIt();

    expect(wrapper.find("dl").text()).not.toContain("Rejection reason");
  });

  it("shows the error of a failed load", async () => {
    GET.mockResolvedValue({ error: { message: "Not found" } });
    const { wrapper } = await mountIt();

    expect(wrapper.find(".alert-danger").text()).toBe("Not found");
    expect(wrapper.find("dl").exists()).toBe(false);
  });
});
