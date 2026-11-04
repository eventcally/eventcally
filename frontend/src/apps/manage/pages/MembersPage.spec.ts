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
import MembersPage from "./MembersPage.vue";

const URL = "/manage/admin_unit/3/organization_members";
const LIST = "/bff/manage/organizations/{id}/members";
const CHOICES = [
  { name: "admin", title: "Administrator" },
  { name: "event_verifier", title: "Event expert" },
];
const row = (over = {}) => ({
  id: 6,
  email: "member@test.de",
  roles: [CHOICES[1]],
  is_current_user: false,
  leave_url: null,
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
    can_invite: true,
    role_choices: CHOICES,
    ...over,
  },
});

const open = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find(".row-actions button").trigger("click");
  await flushPromises();
};
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];

describe("MembersPage", () => {
  beforeEach(() => {
    [GET, POST, PUT, success].forEach((f) => f.mockReset());
    document.body.innerHTML = "";
    sessionStorage.clear();
  });

  it("lists the members with their roles and the invite button", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(MembersPage, { organizationId: 3 }, URL);

    expect(GET).toHaveBeenCalledWith(LIST, { params: { path: { id: 3 }, query: { page: 1 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Organization members");
    expect(wrapper.find("table").text()).toContain("member@test.de");
    expect(wrapper.find("table").text()).toContain("Event expert");
    expect(
      wrapper.find('a[href="/manage/admin_unit/3/organization_member_invitation/create"]').exists(),
    ).toBe(true);
  });

  it("offers no actions and no invite button without permission", async () => {
    GET.mockResolvedValue(page([row()], { can_write: false, can_invite: false }));
    const { wrapper } = await mountPage(MembersPage, { organizationId: 3 }, URL);

    expect(wrapper.find(".row-actions").exists()).toBe(false);
    expect(wrapper.find("table").text()).toContain("member@test.de");
    expect(wrapper.find('a[href$="/organization_member_invitation/create"]').exists()).toBe(false);
  });

  it("changes the roles in a modal", async () => {
    GET.mockResolvedValue(page([row()]));
    PUT.mockResolvedValue({ data: { message: "Organization member successfully updated" } });
    const { wrapper } = await mountPage(MembersPage, { organizationId: 3 }, URL);
    await open(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual(["Edit", "Delete"]);
    items()[0].click();
    await flushPromises();

    expect(document.querySelector("[data-test=roles-modal-email]")?.textContent).toBe(
      "member@test.de",
    );
    const checked = () =>
      [...document.querySelectorAll<HTMLInputElement>(".modal [data-test=roles] input")].map(
        (box) => box.checked,
      );
    expect(checked()).toEqual([false, true]);

    document.querySelector<HTMLInputElement>("#modal-role-admin")!.click();
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-primary")!.click();
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith("/bff/manage/organizations/{id}/members/{member_id}", {
      params: { path: { id: 3, member_id: 6 } },
      body: { roles: ["event_verifier", "admin"] },
    });
    expect(success).toHaveBeenCalledWith("Organization member successfully updated");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("shows the error of a failed role change inside the modal", async () => {
    GET.mockResolvedValue(page([row()]));
    PUT.mockResolvedValue({ error: { message: "Forbidden" } });
    const { wrapper } = await mountPage(MembersPage, { organizationId: 3 }, URL);
    await open(wrapper);
    items()[0].click();
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-primary")!.click();
    await flushPromises();

    expect(document.querySelector("[data-test=roles-modal-error]")?.textContent?.trim()).toBe(
      "Forbidden",
    );
    expect(success).not.toHaveBeenCalled();
  });

  it("removes a member after a plain confirmation, toasts and reloads", async () => {
    GET.mockResolvedValue(page([row()]));
    POST.mockResolvedValue({
      data: { message: "Organization member successfully deleted" },
      response: { ok: true },
    });
    const { wrapper } = await mountPage(MembersPage, { organizationId: 3 }, URL);
    await open(wrapper);
    items()[1].click();
    await flushPromises();

    expect(document.body.textContent).toContain("Do you want to delete 'member@test.de'?");
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/manage/organizations/{id}/members/{member_id}/delete", {
      params: { path: { id: 3, member_id: 6 } },
    });
    expect(success).toHaveBeenCalledWith("Organization member successfully deleted");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("links the own membership to the page that leaves the organization", async () => {
    GET.mockResolvedValue(
      page([row({ is_current_user: true, leave_url: "/user/organization_member/6/delete" })]),
    );
    const { wrapper } = await mountPage(MembersPage, { organizationId: 3 }, URL);
    await open(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual(["Edit", "Delete"]);
    expect(items()[1].getAttribute("href")).toBe("/user/organization_member/6/delete");
  });

  it("goes back a page when the last row of a later page was removed", async () => {
    GET.mockResolvedValueOnce(page([row()], { page: 2, total: 51, pages: 2 }));
    GET.mockResolvedValue(page([], { page: 2, total: 50, pages: 1 }));
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper, router } = await mountPage(MembersPage, { organizationId: 3 }, `${URL}?page=2`);
    await open(wrapper);
    items()[1].click();
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!.click();
    await flushPromises();

    expect(router.currentRoute.value.query.page).toBe("1");
  });

  it("shows no table for an empty list, the error of a failed load and pages", async () => {
    GET.mockResolvedValue(page([]));
    const empty = await mountPage(MembersPage, { organizationId: 3 }, URL);
    expect(empty.wrapper.find("table").exists()).toBe(false);

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(MembersPage, { organizationId: 3 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");

    GET.mockResolvedValue(page([row()], { total: 120, pages: 3 }));
    const paged = await mountPage(MembersPage, { organizationId: 3 }, URL);
    await paged.wrapper.find('button[aria-label="Next page"]').trigger("click");
    await flushPromises();
    expect(paged.router.currentRoute.value.query.page).toBe("2");
  });
});
