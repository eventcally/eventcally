import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({
  boot: { base: "/", locale: "en", csrfToken: "x", loginUrl: "/login" },
}));

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
vi.mock("@/shared/notify", () => ({
  useNotify: () => ({ success, error: vi.fn() }),
}));

import { setFlash } from "@/shared/flash";
import { mountPage } from "../testing";
import OrganizationInvitationsPage from "./OrganizationInvitationsPage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign, success].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

describe("OrganizationInvitationsPage", () => {
  it("lists the invitations with a link to each", async () => {
    GET.mockResolvedValue({
      data: {
        items: [
          {
            id: 2,
            organization_id: 8,
            organization_name: "Dritte Crew",
            name: "Neue Crew",
            created_at: "2026-11-03T14:41:00Z",
          },
        ],
        page: 1,
        per_page: 20,
        total: 1,
        pages: 1,
      },
    });
    const { wrapper } = await mountPage(
      OrganizationInvitationsPage,
      {},
      "/user/organization_invitations",
    );

    expect(wrapper.text()).toContain("Dritte Crew");
    expect(wrapper.text()).toContain("Neue Crew");
    expect(wrapper.find('a[href="/user/organization_invitation/2/negotiate"]').text()).toBe("View");
  });

  it("shows the message of a decline and the error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    setFlash("Invitation successfully declined");
    const { wrapper } = await mountPage(
      OrganizationInvitationsPage,
      {},
      "/user/organization_invitations",
    );

    expect(success).toHaveBeenCalledWith("Invitation successfully declined");
    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });
});
