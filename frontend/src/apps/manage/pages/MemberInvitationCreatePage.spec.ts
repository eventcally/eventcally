import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));

import { mountPage } from "../testing";
import MemberInvitationCreatePage from "./MemberInvitationCreatePage.vue";

const URL = "/manage/admin_unit/5/organization_member_invitation/create";
const FORM = "/bff/manage/organizations/{id}/member-invitations";
const form = {
  role_choices: [
    { name: "admin", title: "Administrator" },
    { name: "event_verifier", title: "Event expert" },
  ],
  list_url: "/manage/admin_unit/5/organization_member_invitations",
};
const assign = vi.fn();

const mount = () => mountPage(MemberInvitationCreatePage, { organizationId: 5 }, URL);

describe("MemberInvitationCreatePage", () => {
  beforeEach(() => {
    [GET, POST, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
    Element.prototype.scrollIntoView = vi.fn();
    GET.mockResolvedValue({ data: form });
  });

  it("loads the form with the roles", async () => {
    const { wrapper } = await mount();

    expect(GET).toHaveBeenCalledWith(`${FORM}/create-form`, { params: { path: { id: 5 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Organization member invitations");
    expect(wrapper.find(".breadcrumb").text()).toContain("Create Organization member invitation");
    expect(wrapper.findAll("[data-test=roles] input")).toHaveLength(2);
    expect(wrapper.find("#submit").text()).toBe("Create");
  });

  it("creates the invitation and leaves for the list", async () => {
    POST.mockResolvedValue({ data: { id: 1, redirect_url: "/list" } });
    const { wrapper } = await mount();

    await wrapper.find("#email").setValue("invited@test.de");
    await wrapper.find("#role-admin").setValue(true);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(FORM, {
      params: { path: { id: 5 } },
      body: { email: "invited@test.de", roles: ["admin"] },
    });
    expect(assign).toHaveBeenCalledWith("/list");
  });

  it("shows the field errors, unmatched and generic errors", async () => {
    POST.mockResolvedValueOnce({
      error: {
        errors: [
          { loc: ["email"], msg: "Not an email" },
          { loc: ["roles"], msg: "Not a valid choice" },
          { loc: ["body"], msg: "Broken" },
        ],
      },
    });
    POST.mockResolvedValueOnce({ error: { message: "Nope" } });
    POST.mockResolvedValueOnce({ error: {} });
    const { wrapper } = await mount();

    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=email-error]").text()).toBe("Not an email");
    expect(wrapper.find("[data-test=roles-error]").text()).toBe("Not a valid choice");
    expect(wrapper.find(".alert-danger").text()).toBe("Broken");

    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Nope");

    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Error");
    expect(assign).not.toHaveBeenCalled();
  });

  it("reports a load error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const { wrapper } = await mount();
    expect(wrapper.text()).toContain("Forbidden");
    expect(wrapper.find("form").exists()).toBe(false);

    GET.mockResolvedValue({});
    const fallback = await mount();
    expect(fallback.wrapper.text()).toContain("Error");
  });
});
