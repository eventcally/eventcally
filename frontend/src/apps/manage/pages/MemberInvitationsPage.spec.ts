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
const success = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import { mountPage } from "../testing";
import MemberInvitationsPage from "./MemberInvitationsPage.vue";

const URL = "/manage/admin_unit/3/organization_member_invitations";
const LIST = "/bff/manage/organizations/{id}/member-invitations";
const CHOICES = [
  { name: "admin", title: "Administrator" },
  { name: "event_verifier", title: "Event expert" },
];
const row = (over = {}) => ({ id: 8, email: "invited@test.de", roles: ["admin"], ...over });
const page = (items: object[], over = {}) => ({
  data: {
    items,
    page: 1,
    per_page: 50,
    total: items.length,
    pages: 1,
    can_write: true,
    role_choices: CHOICES,
    ...over,
  },
});

const open = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find(".row-actions button").trigger("click");
  await flushPromises();
};
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];

describe("MemberInvitationsPage", () => {
  beforeEach(() => {
    [GET, POST, PUT, success].forEach((f) => f.mockReset());
    document.body.innerHTML = "";
    sessionStorage.clear();
  });

  it("lists the invitations with the create button", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(MemberInvitationsPage, { organizationId: 3 }, URL);

    expect(GET).toHaveBeenCalledWith(LIST, { params: { path: { id: 3 }, query: { page: 1 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Organization member invitations");
    expect(wrapper.find("table").text()).toContain("invited@test.de");
    expect(
      wrapper.find('a[href="/manage/admin_unit/3/organization_member_invitation/create"]').exists(),
    ).toBe(true);
  });

  it("offers no actions and no create button without write permission", async () => {
    GET.mockResolvedValue(page([row()], { can_write: false }));
    const { wrapper } = await mountPage(MemberInvitationsPage, { organizationId: 3 }, URL);

    expect(wrapper.find(".row-actions").exists()).toBe(false);
    expect(wrapper.find("table").text()).toContain("invited@test.de");
    expect(wrapper.find('a[href$="/organization_member_invitation/create"]').exists()).toBe(false);
  });

  it("changes the roles of an invitation in a modal", async () => {
    GET.mockResolvedValue(page([row()]));
    PUT.mockResolvedValue({
      data: { message: "Organization member invitation successfully updated" },
    });
    const { wrapper } = await mountPage(MemberInvitationsPage, { organizationId: 3 }, URL);
    await open(wrapper);
    items()[0].click();
    await flushPromises();

    expect(document.body.textContent).toContain("Update Organization member invitation");
    expect(document.querySelector<HTMLInputElement>("#modal-role-admin")!.checked).toBe(true);
    document.querySelector<HTMLInputElement>("#modal-role-admin")!.click();
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-primary")!.click();
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith(
      "/bff/manage/organizations/{id}/member-invitations/{invitation_id}",
      { params: { path: { id: 3, invitation_id: 8 } }, body: { roles: [] } },
    );
    expect(success).toHaveBeenCalledWith("Organization member invitation successfully updated");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("revokes after a plain confirmation, toasts and reloads", async () => {
    GET.mockResolvedValue(page([row()]));
    POST.mockResolvedValue({ data: { message: "Revoked" }, response: { ok: true } });
    const { wrapper } = await mountPage(MemberInvitationsPage, { organizationId: 3 }, URL);
    await open(wrapper);
    items()[1].click();
    await flushPromises();

    expect(document.body.textContent).toContain(
      "Do you want to delete 'Organization member invitation 8'?",
    );
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(
      "/bff/manage/organizations/{id}/member-invitations/{invitation_id}/delete",
      { params: { path: { id: 3, invitation_id: 8 } } },
    );
    expect(success).toHaveBeenCalledWith("Revoked");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("goes back a page when the last row of a later page was revoked", async () => {
    GET.mockResolvedValueOnce(page([row()], { page: 2, total: 51, pages: 2 }));
    GET.mockResolvedValue(page([], { page: 2, total: 50, pages: 1 }));
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper, router } = await mountPage(
      MemberInvitationsPage,
      { organizationId: 3 },
      `${URL}?page=2`,
    );
    await open(wrapper);
    items()[1].click();
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!.click();
    await flushPromises();

    expect(router.currentRoute.value.query.page).toBe("1");
  });

  it("shows no table for an empty list and the error of a failed load", async () => {
    GET.mockResolvedValue(page([]));
    const empty = await mountPage(MemberInvitationsPage, { organizationId: 3 }, URL);
    expect(empty.wrapper.find("table").exists()).toBe(false);

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(MemberInvitationsPage, { organizationId: 3 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });
});
