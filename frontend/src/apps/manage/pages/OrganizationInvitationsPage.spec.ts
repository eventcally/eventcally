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
import OrganizationInvitationsPage from "./OrganizationInvitationsPage.vue";

const URL = "/manage/admin_unit/3/organization_invitations";
const LIST = "/bff/manage/organizations/{id}/organization-invitations";
const row = (over = {}) => ({
  id: 9,
  email: "orginv@test.de",
  admin_unit_name: "Invited Organization",
  created_at: "2026-11-04T10:00:00Z",
  ...over,
});
const page = (items: object[], over = {}) => ({
  data: {
    items,
    page: 1,
    per_page: 50,
    total: items.length,
    pages: 1,
    can_write: true,
    ...over,
  },
});

const open = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find(".row-actions button").trigger("click");
  await flushPromises();
};
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];

describe("OrganizationInvitationsPage", () => {
  beforeEach(() => {
    [GET, POST, success].forEach((f) => f.mockReset());
    document.body.innerHTML = "";
    sessionStorage.clear();
  });

  it("lists the invitations with the create button", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(OrganizationInvitationsPage, { organizationId: 3 }, URL);

    expect(GET).toHaveBeenCalledWith(LIST, { params: { path: { id: 3 }, query: { page: 1 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Organization invitations");
    expect(wrapper.find("table").text()).toContain("orginv@test.de");
    expect(wrapper.find("table").text()).toContain("Invited Organization");
    expect(wrapper.find("table").text()).toContain("Nov 4, 2026");
    expect(
      wrapper.find('a[href="/manage/admin_unit/3/organization_invitation/create"]').exists(),
    ).toBe(true);
  });

  it("offers edit and revoke", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(OrganizationInvitationsPage, { organizationId: 3 }, URL);
    await open(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual(["Edit", "Delete"]);
    expect(items()[0].getAttribute("href")).toBe(
      "/manage/admin_unit/3/organization_invitation/9/update",
    );
  });

  it("offers no actions and no create button without write permission", async () => {
    GET.mockResolvedValue(page([row()], { can_write: false }));
    const { wrapper } = await mountPage(OrganizationInvitationsPage, { organizationId: 3 }, URL);

    expect(wrapper.find(".row-actions").exists()).toBe(false);
    expect(wrapper.find("table").text()).toContain("orginv@test.de");
    expect(wrapper.find('a[href$="/organization_invitation/create"]').exists()).toBe(false);
  });

  it("revokes after a plain confirmation, toasts and reloads", async () => {
    GET.mockResolvedValue(page([row()]));
    POST.mockResolvedValue({ data: { message: "Revoked" }, response: { ok: true } });
    const { wrapper } = await mountPage(OrganizationInvitationsPage, { organizationId: 3 }, URL);
    await open(wrapper);
    items()[1].click();
    await flushPromises();

    expect(document.body.textContent).toContain(
      "Do you want to delete 'Organization invitation 9'?",
    );
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(
      "/bff/manage/organizations/{id}/organization-invitations/{invitation_id}/delete",
      { params: { path: { id: 3, invitation_id: 9 } } },
    );
    expect(success).toHaveBeenCalledWith("Revoked");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("goes back a page when the last row of a later page was revoked", async () => {
    GET.mockResolvedValueOnce(page([row()], { page: 2, total: 51, pages: 2 }));
    GET.mockResolvedValue(page([], { page: 2, total: 50, pages: 1 }));
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper, router } = await mountPage(
      OrganizationInvitationsPage,
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
    const empty = await mountPage(OrganizationInvitationsPage, { organizationId: 3 }, URL);
    expect(empty.wrapper.find("table").exists()).toBe(false);

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(OrganizationInvitationsPage, { organizationId: 3 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });
});
