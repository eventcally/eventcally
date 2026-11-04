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
import OutgoingVerificationRequestPage from "./OutgoingVerificationRequestPage.vue";

const URL = "/manage/admin_unit/3/outgoing_organization_verification_request/7";
const READ = "/bff/manage/organizations/{id}/outgoing-verification-requests/{request_id}";
const read = (over = {}) => ({
  data: {
    id: 7,
    organization_id: 4,
    organization_name: "Andere Crew",
    review_status: 3,
    review_status_label: "Rejected",
    rejection_reason_label: "Unknown",
    audit: { created_at: "2026-11-04T10:00:00Z", created_by_label: "me@test.de" },
    can_write: true,
    ...over,
  },
});

const assign = vi.fn();

describe("OutgoingVerificationRequestPage", () => {
  beforeEach(() => {
    [GET, POST, success, assign].forEach((f) => f.mockReset());
    document.body.innerHTML = "";
    vi.stubGlobal("location", { ...window.location, assign });
  });

  it("shows the request with its status, reason and audit line", async () => {
    GET.mockResolvedValue(read());
    const { wrapper } = await mountPage(
      OutgoingVerificationRequestPage,
      { organizationId: 3, id: 7 },
      URL,
    );

    expect(GET).toHaveBeenCalledWith(READ, { params: { path: { id: 3, request_id: 7 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Outgoing verification requests");
    expect(wrapper.find(".breadcrumb .active").text()).toBe("Organization verification request 7");
    expect(wrapper.find("dl").text()).toContain("Andere Crew");
    expect(wrapper.find("dl .badge").text()).toBe("Rejected");
    expect(wrapper.find("dl").text()).toContain("Unknown");
    expect(wrapper.text()).toContain("me@test.de");
  });

  it("hides the rejection reason and the actions without them", async () => {
    GET.mockResolvedValue(read({ rejection_reason_label: null, can_write: false }));
    const { wrapper } = await mountPage(
      OutgoingVerificationRequestPage,
      { organizationId: 3, id: 7 },
      URL,
    );

    expect(wrapper.find("dl").text()).not.toContain("Rejection reason");
    expect(wrapper.text()).not.toContain("Actions");
  });

  it("shows the error of a failed load", async () => {
    GET.mockResolvedValue({ error: { message: "Not found" } });
    const { wrapper } = await mountPage(
      OutgoingVerificationRequestPage,
      { organizationId: 3, id: 7 },
      URL,
    );

    expect(wrapper.find(".alert-danger").text()).toBe("Not found");
  });

  it("withdraws through the modal and goes back to the list", async () => {
    GET.mockResolvedValue(read());
    POST.mockResolvedValue({
      data: { message: "Gone", redirect_url: "/list" },
      response: { ok: true },
    });
    const { wrapper } = await mountPage(
      OutgoingVerificationRequestPage,
      { organizationId: 3, id: 7 },
      URL,
    );

    await wrapper.find(".dropdown-toggle").trigger("click");
    await flushPromises();
    [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")]
      .find((i) => i.textContent?.trim() === "Delete")!
      .click();
    await flushPromises();

    expect(document.body.textContent).toContain(
      "Do you want to delete 'Organization verification request 7'?",
    );
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(
      "/bff/manage/organizations/{id}/outgoing-verification-requests/{request_id}/withdraw",
      { params: { path: { id: 3, request_id: 7 } }, body: { inline: false } },
    );
    expect(assign).toHaveBeenCalledWith(
      "/manage/admin_unit/3/outgoing_organization_verification_requests",
    );
  });
});
