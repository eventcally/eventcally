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
import MemberInvitationPage from "./MemberInvitationPage.vue";

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
const URL = "/user/organization_member_invitation/2/negotiate";

describe("MemberInvitationPage", () => {
  it("asks and accepts with a full page load", async () => {
    GET.mockResolvedValue(invitation);
    POST.mockResolvedValue({ data: { redirect_url: "/manage/admin_unit/8" } });
    const { wrapper } = await mountPage(MemberInvitationPage, { id: 2 }, URL);

    expect(wrapper.text()).toContain("Would you like to accept the invitation from Dritte Crew?");
    await wrapper.find("#accept").trigger("click");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/user/member-invitations/{id}/accept", {
      params: { path: { id: 2 } },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/8");
  });

  it("declines", async () => {
    GET.mockResolvedValue(invitation);
    POST.mockResolvedValue({ data: { redirect_url: "/manage" } });
    const { wrapper } = await mountPage(MemberInvitationPage, { id: 2 }, URL);

    await wrapper.find("#decline").trigger("click");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/user/member-invitations/{id}/decline", {
      params: { path: { id: 2 } },
    });
    expect(assign).toHaveBeenCalledWith("/manage");
  });

  it("shows a refusal and a failed load", async () => {
    GET.mockResolvedValueOnce(invitation);
    POST.mockResolvedValue({ error: { message: "Forbidden" } });
    const { wrapper } = await mountPage(MemberInvitationPage, { id: 2 }, URL);
    await wrapper.find("#accept").trigger("click");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
    expect(assign).not.toHaveBeenCalled();

    GET.mockResolvedValue({ error: { message: "Gone" } });
    const failed = await mountPage(MemberInvitationPage, { id: 2 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Gone");
  });
});
