import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

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
import OrganizationInvitationEditPage from "./OrganizationInvitationEditPage.vue";

const BASE = "/bff/manage/organizations/{id}/organization-invitations";
const assign = vi.fn();

const invitationForm = (over: Record<string, unknown> = {}) => ({
  id: null,
  email: "",
  admin_unit_name: "",
  relation_verify: false,
  relation_auto_verify_event_reference_requests: false,
  can_verify_other: true,
  audit: null,
  list_url: "/manage/admin_unit/5/organization_invitations",
  ...over,
});

const mount = (props: { organizationId: number; id?: number } = { organizationId: 5 }, data = {}) => {
  GET.mockResolvedValue({ data: invitationForm(data) });
  return mountPage(OrganizationInvitationEditPage, props, "/manage/admin_unit/5/organization_invitation/create");
};

describe("OrganizationInvitationEditPage", () => {
  beforeEach(() => {
    [GET, POST, PUT, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
    Element.prototype.scrollIntoView = vi.fn();
  });

  it("loads the empty create form with both switches", async () => {
    const { wrapper } = await mount();

    expect(GET).toHaveBeenCalledWith(`${BASE}/create-form`, { params: { path: { id: 5 } } });
    expect(wrapper.find("#email").exists()).toBe(true);
    expect(wrapper.find("#relation_verify").exists()).toBe(true);
    expect(wrapper.find("#relation_auto_verify_event_reference_requests").exists()).toBe(true);
    expect(wrapper.find("[data-test=email-read]").exists()).toBe(false);
    expect(wrapper.find("#submit").text()).toBe("Create");
    expect(wrapper.find(".breadcrumb").text()).toContain("Create Organization invitation");
  });

  it("hides the verify switch without the permission", async () => {
    const { wrapper } = await mount({ organizationId: 5 }, { can_verify_other: false });

    expect(wrapper.find("#relation_verify").exists()).toBe(false);
    expect(wrapper.find("#relation_auto_verify_event_reference_requests").exists()).toBe(true);
  });

  it("creates an invitation and leaves for the list", async () => {
    POST.mockResolvedValue({ data: { id: 1, redirect_url: "/list" } });
    const { wrapper } = await mount();

    await wrapper.find("#email").setValue("orginv@test.de");
    await wrapper.find("#admin_unit_name").setValue("Neue Crew");
    await wrapper.find("#relation_verify").setValue(true);
    await wrapper.find("#relation_auto_verify_event_reference_requests").setValue(true);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(BASE, {
      params: { path: { id: 5 } },
      body: {
        email: "orginv@test.de",
        admin_unit_name: "Neue Crew",
        relation_verify: true,
        relation_auto_verify_event_reference_requests: true,
      },
    });
    expect(assign).toHaveBeenCalledWith("/list");
  });

  it("shows the email read-only and the audit line on update and saves the fields", async () => {
    PUT.mockResolvedValue({ data: { id: 7, redirect_url: "/list" } });
    const { wrapper } = await mount(
      { organizationId: 5, id: 7 },
      {
        id: 7,
        email: "orginv@test.de",
        admin_unit_name: "Eingeladene Crew",
        relation_verify: true,
        audit: { created_at: "2026-11-04T10:00:00Z", created_by_label: "me@test.de" },
      },
    );

    expect(GET).toHaveBeenCalledWith(`${BASE}/{invitation_id}`, {
      params: { path: { id: 5, invitation_id: 7 } },
    });
    expect(wrapper.find("#email").exists()).toBe(false);
    expect(wrapper.find("[data-test=email-read]").text()).toContain("orginv@test.de");
    expect(wrapper.find("[data-test=audit]").text()).toContain("me@test.de");
    expect((wrapper.find("#admin_unit_name").element as HTMLInputElement).value).toBe(
      "Eingeladene Crew",
    );
    expect(wrapper.find("#submit").text()).toBe("Update");
    expect(wrapper.find(".breadcrumb").text()).toContain("Update Organization invitation");

    await wrapper.find("#admin_unit_name").setValue("Neu");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith(`${BASE}/{invitation_id}`, {
      params: { path: { id: 5, invitation_id: 7 } },
      body: {
        admin_unit_name: "Neu",
        relation_verify: true,
        relation_auto_verify_event_reference_requests: false,
      },
    });
    expect(assign).toHaveBeenCalledWith("/list");
  });

  it("shows the field errors, unmatched and generic errors", async () => {
    POST.mockResolvedValueOnce({
      error: {
        errors: [
          { loc: ["email"], msg: "Not an email" },
          { loc: ["admin_unit_name"], msg: "Too short" },
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
    expect(wrapper.find("[data-test=name-error]").text()).toBe("Too short");
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
    const { wrapper } = await mountPage(
      OrganizationInvitationEditPage,
      { organizationId: 5 },
      "/manage/admin_unit/5/organization_invitation/create",
    );
    expect(wrapper.text()).toContain("Forbidden");
    expect(wrapper.find("form").exists()).toBe(false);

    GET.mockResolvedValue({});
    const fallback = await mountPage(
      OrganizationInvitationEditPage,
      { organizationId: 5 },
      "/manage/admin_unit/5/organization_invitation/create",
    );
    expect(fallback.wrapper.text()).toContain("Error");
  });
});
