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

import { mountPage } from "../testing";
import MemberInvitationsPage from "./MemberInvitationsPage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

describe("MemberInvitationsPage", () => {
  it("lists the invitations with a link to each", async () => {
    GET.mockResolvedValue({
      data: {
        items: [{ id: 2, organization_id: 8, organization_name: "Dritte Crew" }],
        page: 1,
        per_page: 20,
        total: 1,
        pages: 1,
      },
    });
    const { wrapper } = await mountPage(
      MemberInvitationsPage,
      {},
      "/user/organization_member_invitations",
    );

    expect(wrapper.text()).toContain("Dritte Crew");
    expect(wrapper.find('a[href="/user/organization_member_invitation/2/negotiate"]').text()).toBe(
      "View",
    );
  });

  it("shows the error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const { wrapper } = await mountPage(
      MemberInvitationsPage,
      {},
      "/user/organization_member_invitations",
    );

    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });
});
