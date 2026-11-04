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
import OrganizationRelationsPage from "./OrganizationRelationsPage.vue";

const URL = "/manage/admin_unit/3/outgoing_organization_relations";
const LIST = "/bff/manage/organizations/{id}/outgoing-organization-relations";
const DELETE = `${LIST}/{relation_id}/delete`;
const row = (over = {}) => ({
  id: 6,
  organization_id: 4,
  organization_name: "Andere Crew",
  verify: true,
  auto_verify_event_reference_requests: false,
  last_modified_at: "2026-11-04T10:00:00Z",
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
    can_verify_other: true,
    ...over,
  },
});
const query = (over = {}) => ({
  page: 1,
  sort: "name",
  keyword: undefined,
  verify: undefined,
  auto_verify_event_reference_requests: undefined,
  ...over,
});

const open = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find(".row-actions button").trigger("click");
  await flushPromises();
};
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];

describe("OrganizationRelationsPage", () => {
  beforeEach(() => {
    [GET, POST, success].forEach((f) => f.mockReset());
    document.body.innerHTML = "";
    sessionStorage.clear();
  });

  it("lists the relations with the create button", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(OrganizationRelationsPage, { organizationId: 3 }, URL);

    expect(GET).toHaveBeenCalledWith(LIST, { params: { path: { id: 3 }, query: query() } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Outgoing organization relations");
    expect(wrapper.find("table").text()).toContain("Andere Crew");
    expect(wrapper.find("table").text()).toContain("Verify other organization");
    expect(wrapper.find("table").text()).toContain("Nov 4, 2026");
    expect(wrapper.find("table .fa-check-circle").exists()).toBe(true);
    expect(
      wrapper.find('a[href="/manage/admin_unit/3/outgoing_organization_relation/create"]').exists(),
    ).toBe(true);
  });

  it("hides the verify column and filter when the organization cannot verify others", async () => {
    GET.mockResolvedValue(page([row({ verify: false })], { can_verify_other: false }));
    const { wrapper } = await mountPage(OrganizationRelationsPage, { organizationId: 3 }, URL);

    expect(wrapper.find("table").text()).not.toContain("Verify other organization");
    expect(wrapper.find("[data-test=verify-filter]").exists()).toBe(false);
    expect(wrapper.find("[data-test=auto-verify-filter]").exists()).toBe(true);
  });

  it("offers edit and delete", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(OrganizationRelationsPage, { organizationId: 3 }, URL);
    await open(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual(["Edit", "Delete"]);
    expect(items()[0].getAttribute("href")).toBe(
      "/manage/admin_unit/3/outgoing_organization_relation/6/update",
    );
  });

  it("offers no actions and no create button without write permission", async () => {
    GET.mockResolvedValue(page([row()], { can_write: false }));
    const readOnly = await mountPage(OrganizationRelationsPage, { organizationId: 3 }, URL);

    expect(readOnly.wrapper.find(".row-actions").exists()).toBe(false);
    expect(readOnly.wrapper.find("table").text()).toContain("Andere Crew");
    expect(readOnly.wrapper.find('a[href$="/outgoing_organization_relation/create"]').exists()).toBe(
      false,
    );
  });

  it("filters through the route query", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper, router } = await mountPage(
      OrganizationRelationsPage,
      { organizationId: 3 },
      `${URL}?keyword=an&verify=1&auto_verify_event_reference_requests=0&sort=-last_modified_at`,
    );

    expect(GET).toHaveBeenCalledWith(LIST, {
      params: {
        path: { id: 3 },
        query: query({
          sort: "-last_modified_at",
          keyword: "an",
          verify: true,
          auto_verify_event_reference_requests: false,
        }),
      },
    });
    // A set filter opens the collapse and offers the reset.
    expect(wrapper.find("[data-test=filters-reset]").exists()).toBe(true);

    await wrapper.find("#keyword").setValue("be");
    await wrapper.find("#verify-no").setValue();
    await wrapper.find("#auto-verify-all").setValue();
    await wrapper.find("[data-test=filters-form]").trigger("submit");
    await flushPromises();

    expect(router.currentRoute.value.query).toEqual({
      keyword: "be",
      verify: "0",
      sort: "-last_modified_at",
    });

    await wrapper.find("[data-test=filters-reset]").trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.query).toEqual({});
  });

  it("ignores unknown filter values", async () => {
    GET.mockResolvedValue(page([row()]));
    await mountPage(OrganizationRelationsPage, { organizationId: 3 }, `${URL}?verify=x&sort=y`);

    expect(GET).toHaveBeenCalledWith(LIST, { params: { path: { id: 3 }, query: query() } });
  });

  it("shows no table for an empty list, the error of a failed load and pages", async () => {
    GET.mockResolvedValue(page([]));
    const empty = await mountPage(OrganizationRelationsPage, { organizationId: 3 }, URL);
    expect(empty.wrapper.find("table").exists()).toBe(false);

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(OrganizationRelationsPage, { organizationId: 3 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");

    GET.mockResolvedValue(page([row()], { total: 120, pages: 3 }));
    const paged = await mountPage(OrganizationRelationsPage, { organizationId: 3 }, URL);
    await paged.wrapper.find('button[aria-label="Next page"]').trigger("click");
    await flushPromises();
    expect(paged.router.currentRoute.value.query.page).toBe("2");
  });

  it("deletes after a plain confirmation, toasts and reloads", async () => {
    GET.mockResolvedValue(page([row()]));
    POST.mockResolvedValue({
      data: { message: "Outgoing organization relation successfully deleted" },
      response: { ok: true },
    });
    const { wrapper } = await mountPage(OrganizationRelationsPage, { organizationId: 3 }, URL);
    await open(wrapper);
    items()[1].click();
    await flushPromises();

    expect(document.body.textContent).toContain("Do you want to delete 'Organization relation 6'?");
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(DELETE, {
      params: { path: { id: 3, relation_id: 6 } },
    });
    expect(success).toHaveBeenCalledWith("Outgoing organization relation successfully deleted");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("goes back a page when the last row of a later page was deleted", async () => {
    GET.mockResolvedValueOnce(page([row()], { page: 2, total: 51, pages: 2 }));
    GET.mockResolvedValue(page([], { page: 2, total: 50, pages: 1 }));
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper, router } = await mountPage(
      OrganizationRelationsPage,
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
});
