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
import AppInstallationsPage from "./AppInstallationsPage.vue";

const URL = "/manage/admin_unit/3/app_installations";
const LIST = "/bff/manage/organizations/{id}/app-installations";
const row = (over = {}) => ({ id: 6, app: "Meine App", created_at: "2026-11-04T10:00:00Z", ...over });
const page = (items: object[], over = {}) => ({
  data: { items, page: 1, per_page: 20, total: items.length, pages: 1, can_write: true, ...over },
});
const open = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find(".row-actions button").trigger("click");
  await flushPromises();
};
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];

describe("AppInstallationsPage", () => {
  beforeEach(() => {
    [GET, POST, success].forEach((f) => f.mockReset());
    document.body.innerHTML = "";
  });

  it("lists the installations", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(AppInstallationsPage, { organizationId: 3 }, URL);

    expect(GET).toHaveBeenCalledWith(LIST, { params: { path: { id: 3 }, query: { page: 1 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("App installations");
    expect(wrapper.find("table").text()).toContain("Meine App");
  });

  it("names an installation of an unnamed app by its id", async () => {
    GET.mockResolvedValue(page([row({ app: null })]));
    const { wrapper } = await mountPage(AppInstallationsPage, { organizationId: 3 }, URL);

    expect(wrapper.find("table").text()).toContain("App installation 6");
  });

  it("offers view and uninstall", async () => {
    GET.mockResolvedValue(page([row()]));
    const writer = await mountPage(AppInstallationsPage, { organizationId: 3 }, URL);
    await open(writer.wrapper);
    expect(items().map((i) => i.textContent?.trim())).toEqual(["View", "Delete"]);
    expect(items()[0].getAttribute("href")).toBe("/manage/admin_unit/3/app_installation/6");
  });

  it("offers only view without permission", async () => {
    GET.mockResolvedValue(page([row()], { can_write: false }));
    const reader = await mountPage(AppInstallationsPage, { organizationId: 3 }, URL);
    await open(reader.wrapper);
    expect(items().map((i) => i.textContent?.trim())).toEqual(["View"]);
  });

  it("uninstalls after a plain confirmation, toasts and reloads", async () => {
    GET.mockResolvedValue(page([row()]));
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper } = await mountPage(AppInstallationsPage, { organizationId: 3 }, URL);
    await open(wrapper);
    items()[1].click();
    await flushPromises();
    expect(document.body.textContent).toContain("Do you want to delete 'App installation 6'?");
    expect(document.querySelector(".modal input")).toBeNull();
    document.querySelector<HTMLButtonElement>(".modal .btn-danger")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(`${LIST}/{installation_id}/delete`, {
      params: { path: { id: 3, installation_id: 6 } },
      body: { inline: true },
    });
    expect(success).toHaveBeenCalledWith("Gone");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("goes back a page when the last row of a later page was uninstalled", async () => {
    GET.mockResolvedValueOnce(page([row()], { page: 2, total: 21, pages: 2 }));
    GET.mockResolvedValue(page([], { page: 2, total: 20, pages: 1 }));
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper, router } = await mountPage(
      AppInstallationsPage,
      { organizationId: 3 },
      `${URL}?page=2`,
    );
    await open(wrapper);
    items()[1].click();
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal .btn-danger")!.click();
    await flushPromises();

    expect(router.currentRoute.value.query.page).toBe("1");
  });

  it("shows no table for an empty list and the error of a failed load", async () => {
    GET.mockResolvedValue(page([]));
    const empty = await mountPage(AppInstallationsPage, { organizationId: 3 }, URL);
    expect(empty.wrapper.find("table").exists()).toBe(false);

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(AppInstallationsPage, { organizationId: 3 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });
});
