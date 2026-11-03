import { flushPromises } from "@vue/test-utils";
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
import OrganizationInvitationPage from "./OrganizationInvitationPage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

const invitation = {
  data: { id: 2, organization_id: 8, organization_name: "Dritte Crew" },
};
const URL = "/user/organization_invitation/2/negotiate";

describe("OrganizationInvitationPage", () => {
  it("links to the organization creation", async () => {
    GET.mockResolvedValue(invitation);
    const { wrapper } = await mountPage(OrganizationInvitationPage, { id: 2 }, URL);

    expect(wrapper.text()).toContain("Dritte Crew invited you to create an organization.");
    expect(wrapper.find("#accept").attributes("href")).toBe(
      "/manage/organization/create?invitation_id=2",
    );
  });

  it("declines with a full page load", async () => {
    GET.mockResolvedValue(invitation);
    POST.mockResolvedValue({
      data: { redirect_url: "/user/organization_invitations" },
    });
    const { wrapper } = await mountPage(OrganizationInvitationPage, { id: 2 }, URL);

    await wrapper.find("#decline").trigger("click");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/user/organization-invitations/{id}/decline", {
      params: { path: { id: 2 } },
    });
    expect(assign).toHaveBeenCalledWith("/user/organization_invitations");
  });

  it("shows a refusal and a failed load", async () => {
    GET.mockResolvedValueOnce(invitation);
    POST.mockResolvedValue({ error: { message: "Forbidden" } });
    const { wrapper } = await mountPage(OrganizationInvitationPage, { id: 2 }, URL);
    await wrapper.find("#decline").trigger("click");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");

    GET.mockResolvedValue({ error: { message: "Gone" } });
    const failed = await mountPage(OrganizationInvitationPage, { id: 2 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Gone");
  });
});
