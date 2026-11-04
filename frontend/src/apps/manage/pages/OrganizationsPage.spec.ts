import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import { mountPage } from "../testing";
import OrganizationsPage from "./OrganizationsPage.vue";

const overview = (over = {}) => ({
  data: {
    invitations: [{ id: 1, name: "Crew A", url: "/user/organization_member_invitation/1" }],
    organization_invitations: [
      { id: 2, name: "Crew B", url: "/user/organization_invitation/2" },
    ],
    organizations: [
      { id: 3, name: "Meine Crew" },
      { id: 4, name: "Other Crew" },
    ],
    docs_url: "https://docs.example/goto/organization-create",
    can_create: true,
    invite_organization_id: 3,
    ...over,
  },
});

describe("OrganizationsPage", () => {
  beforeEach(() => GET.mockReset());

  it("lists the invitations and organizations with the actions", async () => {
    GET.mockResolvedValue(overview());
    const { wrapper } = await mountPage(OrganizationsPage, {}, "/manage/admin_units");

    expect(GET).toHaveBeenCalledWith("/bff/manage/organizations");
    const text = wrapper.text();
    expect(text).toContain("Invitations");
    expect(text).toContain("Organization invitations");
    expect(wrapper.find('[data-test="invitations"] a').attributes("href")).toBe(
      "/user/organization_member_invitation/1",
    );
    expect(wrapper.find('[data-test="organization-invitations"] a').text()).toBe("Crew B");

    const organizations = wrapper.findAll('[data-test="organizations"] a');
    expect(organizations.map((a) => a.text())).toEqual(["Meine Crew", "Other Crew"]);
    expect(organizations[0].attributes("href")).toBe("/manage/admin_unit/3");

    const docs = wrapper.find('a[target="_blank"]');
    expect(docs.attributes("href")).toBe("https://docs.example/goto/organization-create");
    expect(wrapper.find('a[href="/manage/organization/create"]').text()).toContain(
      "Create organization",
    );
    expect(wrapper.find('a[href="/manage/admin_unit/3/organization_invitation/create"]').text()).toContain(
      "Invite organization",
    );
  });

  it("hides what is not offered", async () => {
    GET.mockResolvedValue(
      overview({
        invitations: [],
        organization_invitations: [],
        docs_url: null,
        can_create: false,
        invite_organization_id: null,
      }),
    );
    const { wrapper } = await mountPage(OrganizationsPage, {}, "/manage/admin_units");

    expect(wrapper.find('[data-test="invitations"]').exists()).toBe(false);
    expect(wrapper.find('[data-test="organization-invitations"]').exists()).toBe(false);
    expect(wrapper.find('a[target="_blank"]').exists()).toBe(false);
    expect(wrapper.text()).not.toContain("Create organization");
    expect(wrapper.text()).not.toContain("Invite organization");
  });

  it("shows the error of the load", async () => {
    GET.mockResolvedValue({ error: { message: "Kaputt" } });
    const { wrapper } = await mountPage(OrganizationsPage, {}, "/manage/admin_units");

    expect(wrapper.find(".alert-danger").text()).toBe("Kaputt");
  });
});
