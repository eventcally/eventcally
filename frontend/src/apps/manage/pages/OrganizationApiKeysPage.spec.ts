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
import OrganizationApiKeysPage from "./OrganizationApiKeysPage.vue";

const URL = "/manage/admin_unit/3/api_keys";
const LIST = "/bff/manage/organizations/{id}/api-keys";
const row = (over = {}) => ({ id: 6, name: "Mein API Key", created_at: "2026-11-04T10:00:00Z", ...over });
const page = (items: object[], over = {}) => ({
  data: { items, page: 1, per_page: 20, total: items.length, pages: 1, can_write: true, ...over },
});
const open = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find(".row-actions button").trigger("click");
  await flushPromises();
};
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];

describe("OrganizationApiKeysPage", () => {
  beforeEach(() => {
    [GET, POST, success].forEach((f) => f.mockReset());
    document.body.innerHTML = "";
  });

  it("lists the keys, sorted by name, with the create button", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(OrganizationApiKeysPage, { organizationId: 3 }, URL);

    expect(GET).toHaveBeenCalledWith(LIST, {
      params: { path: { id: 3 }, query: { page: 1, sort: "name" } },
    });
    expect(wrapper.find(".breadcrumb").text()).toContain("API keys");
    expect(wrapper.find("table").text()).toContain("Mein API Key");
    expect(wrapper.find('a[href="/manage/admin_unit/3/api_key/create"]').exists()).toBe(true);
  });

  it("offers only the view action and no create button without permission", async () => {
    GET.mockResolvedValue(page([row()], { can_write: false }));
    const { wrapper } = await mountPage(OrganizationApiKeysPage, { organizationId: 3 }, URL);
    await open(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual(["View"]);
    expect(items()[0].getAttribute("href")).toBe("/manage/admin_unit/3/api_key/6");
    expect(wrapper.find('a[href$="/api_key/create"]').exists()).toBe(false);
  });

  it("sorts by the last created through the filters", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper, router } = await mountPage(OrganizationApiKeysPage, { organizationId: 3 }, URL);

    await wrapper.find("[data-test=filters-toggle]").trigger("click");
    await wrapper.find("#sort").setValue("-created_at");
    await wrapper.find("[data-test=filters-form]").trigger("submit");
    await flushPromises();

    expect(router.currentRoute.value.query.sort).toBe("-created_at");
    expect(GET).toHaveBeenLastCalledWith(LIST, {
      params: { path: { id: 3 }, query: { page: 1, sort: "-created_at" } },
    });

    await wrapper.find("[data-test=filters-reset]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.query.sort).toBeUndefined();
  });

  it("ignores an unknown sort of the URL", async () => {
    GET.mockResolvedValue(page([row()]));
    await mountPage(OrganizationApiKeysPage, { organizationId: 3 }, `${URL}?sort=bogus`);

    expect(GET).toHaveBeenCalledWith(LIST, {
      params: { path: { id: 3 }, query: { page: 1, sort: "name" } },
    });
  });

  it("deletes after the typed name, toasts and reloads", async () => {
    GET.mockResolvedValue(page([row()]));
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper } = await mountPage(OrganizationApiKeysPage, { organizationId: 3 }, URL);
    await open(wrapper);
    items()[1].click();
    await flushPromises();

    expect(document.body.textContent).toContain("Do you want to delete 'Mein API Key'?");
    const input = document.querySelector<HTMLInputElement>(".modal input")!;
    input.value = "Mein API Key";
    input.dispatchEvent(new Event("input"));
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal button[type=submit]")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/manage/organizations/{id}/api-keys/{api_key_id}/delete", {
      params: { path: { id: 3, api_key_id: 6 } },
      body: { name: "Mein API Key", inline: true },
    });
    expect(success).toHaveBeenCalledWith("Gone");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("shows a name mismatch inside the modal", async () => {
    GET.mockResolvedValue(page([row()]));
    POST.mockResolvedValue({
      error: { errors: [{ loc: ["name"], msg: "Does not match" }] },
      response: { ok: false },
    });
    const { wrapper } = await mountPage(OrganizationApiKeysPage, { organizationId: 3 }, URL);
    await open(wrapper);
    items()[1].click();
    await flushPromises();
    const input = document.querySelector<HTMLInputElement>(".modal input")!;
    input.value = "wrong";
    input.dispatchEvent(new Event("input"));
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal button[type=submit]")!.click();
    await flushPromises();

    expect(document.querySelector(".modal")?.textContent).toContain("Does not match");
    expect(success).not.toHaveBeenCalled();
  });

  it("goes back a page when the last row of a later page was deleted", async () => {
    GET.mockResolvedValueOnce(page([row()], { page: 2, total: 21, pages: 2 }));
    GET.mockResolvedValue(page([], { page: 2, total: 20, pages: 1 }));
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper, router } = await mountPage(
      OrganizationApiKeysPage,
      { organizationId: 3 },
      `${URL}?page=2`,
    );
    await open(wrapper);
    items()[1].click();
    await flushPromises();
    const input = document.querySelector<HTMLInputElement>(".modal input")!;
    input.value = "Mein API Key";
    input.dispatchEvent(new Event("input"));
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal button[type=submit]")!.click();
    await flushPromises();

    expect(router.currentRoute.value.query.page).toBe("1");
  });

  it("shows no table for an empty list and the error of a failed load", async () => {
    GET.mockResolvedValue(page([]));
    const empty = await mountPage(OrganizationApiKeysPage, { organizationId: 3 }, URL);
    expect(empty.wrapper.find("table").exists()).toBe(false);

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(OrganizationApiKeysPage, { organizationId: 3 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });
});
