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
import OrganizationOAuth2ClientsPage from "./OrganizationOAuth2ClientsPage.vue";

const URL = "/manage/admin_unit/3/oauth2_clients";
const LIST = "/bff/manage/organizations/{id}/oauth2-clients";
const row = (over = {}) => ({ id: 6, client_name: "Mein Client", ...over });
const page = (items: object[], over = {}) => ({
  data: { items, page: 1, per_page: 20, total: items.length, pages: 1, can_write: true, ...over },
});
const open = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find(".row-actions button").trigger("click");
  await flushPromises();
};
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];
const typeName = async (name: string) => {
  const input = document.querySelector<HTMLInputElement>(".modal input")!;
  input.value = name;
  input.dispatchEvent(new Event("input"));
  await flushPromises();
  document.querySelector<HTMLButtonElement>(".modal button[type=submit]")!.click();
  await flushPromises();
};

describe("OrganizationOAuth2ClientsPage", () => {
  beforeEach(() => {
    [GET, POST, success].forEach((f) => f.mockReset());
    document.body.innerHTML = "";
  });

  it("lists the clients with the create button", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(OrganizationOAuth2ClientsPage, { organizationId: 3 }, URL);

    expect(GET).toHaveBeenCalledWith(LIST, { params: { path: { id: 3 }, query: { page: 1 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("OAuth2 clients");
    expect(wrapper.find("table").text()).toContain("Mein Client");
    expect(wrapper.find('a[href="/manage/admin_unit/3/oauth2_client/create"]').exists()).toBe(true);
  });

  it("names a client without a name by its id", async () => {
    GET.mockResolvedValue(page([row({ client_name: null })]));
    const { wrapper } = await mountPage(OrganizationOAuth2ClientsPage, { organizationId: 3 }, URL);

    expect(wrapper.find("table").text()).toContain("OAuth2 client 6");
  });

  it("offers view, edit and delete", async () => {
    GET.mockResolvedValue(page([row()]));
    const writer = await mountPage(OrganizationOAuth2ClientsPage, { organizationId: 3 }, URL);
    await open(writer.wrapper);
    expect(items().map((i) => i.textContent?.trim())).toEqual(["View", "Edit", "Delete"]);
    expect(items()[0].getAttribute("href")).toBe("/manage/admin_unit/3/oauth2_client/6");
    expect(items()[1].getAttribute("href")).toBe("/manage/admin_unit/3/oauth2_client/6/update");
  });

  it("offers only the view action and no create button without permission", async () => {
    GET.mockResolvedValue(page([row()], { can_write: false }));
    const reader = await mountPage(OrganizationOAuth2ClientsPage, { organizationId: 3 }, URL);
    await open(reader.wrapper);
    expect(items().map((i) => i.textContent?.trim())).toEqual(["View"]);
    expect(reader.wrapper.find('a[href$="/oauth2_client/create"]').exists()).toBe(false);
  });

  it("deletes after the typed name, toasts and reloads", async () => {
    GET.mockResolvedValue(page([row()]));
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper } = await mountPage(OrganizationOAuth2ClientsPage, { organizationId: 3 }, URL);
    await open(wrapper);
    items()[2].click();
    await flushPromises();
    expect(document.body.textContent).toContain("Do you want to delete 'Mein Client'?");
    await typeName("Mein Client");

    expect(POST).toHaveBeenCalledWith(`${LIST}/{client_id}/delete`, {
      params: { path: { id: 3, client_id: 6 } },
      body: { name: "Mein Client", inline: true },
    });
    expect(success).toHaveBeenCalledWith("Gone");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("goes back a page when the last row of a later page was deleted", async () => {
    GET.mockResolvedValueOnce(page([row()], { page: 2, total: 21, pages: 2 }));
    GET.mockResolvedValue(page([], { page: 2, total: 20, pages: 1 }));
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper, router } = await mountPage(
      OrganizationOAuth2ClientsPage,
      { organizationId: 3 },
      `${URL}?page=2`,
    );
    await open(wrapper);
    items()[2].click();
    await flushPromises();
    await typeName("Mein Client");

    expect(router.currentRoute.value.query.page).toBe("1");
  });

  it("shows no table for an empty list and the error of a failed load", async () => {
    GET.mockResolvedValue(page([]));
    const empty = await mountPage(OrganizationOAuth2ClientsPage, { organizationId: 3 }, URL);
    expect(empty.wrapper.find("table").exists()).toBe(false);

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(OrganizationOAuth2ClientsPage, { organizationId: 3 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });
});
