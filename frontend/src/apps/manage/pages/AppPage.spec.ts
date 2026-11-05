import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
const success = vi.hoisted(() => vi.fn());
const failure = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: failure }) }));

import { mountPage } from "../testing";
import AppPage from "./AppPage.vue";

const URL = "/manage/admin_unit/3/app/5";
const READ = "/bff/manage/organizations/{id}/apps/{app_id}";
const key = (over = {}) => ({ id: 8, kid: "kid-1", checksum: "abc", ...over });
const app = (over = {}) => ({
  id: 5,
  client_id: "cid",
  client_secret: "secret",
  client_name: "Meine App",
  client_uri: null,
  scope: "openid",
  scopes: ["openid"],
  redirect_uris: ["https://a.example"],
  grant_types: ["authorization_code"],
  response_types: ["code"],
  token_endpoint_auth_method: ["none"],
  app_permissions: ["Read Events"],
  homepage_url: "https://home.example",
  setup_url: null,
  webhook_url: "https://hook.example",
  description: "Eine App",
  keys: [key()],
  can_read_keys: true,
  can_write_keys: true,
  can_read_deliveries: true,
  audit: { created_at: "2026-11-04T10:00:00Z", created_by_label: "me@test.de" },
  can_write: true,
  ...over,
});
const mountIt = () => mountPage(AppPage, { organizationId: 3, id: 5 }, URL, { Cancel: "Cancel" });
// The dropdown menus are teleported to the body: first the actions, then the key rows.
const items = (menu = 0) => [
  ...(document.querySelectorAll(".dropdown-menu")[menu]?.querySelectorAll<HTMLAnchorElement>(".dropdown-item") ?? []),
];
// Both confirm modals are in the body: first the app, then the key.
const typeName = async (name: string, modal = 0) => {
  const dialog = document.querySelectorAll(".modal")[modal];
  const input = dialog.querySelector<HTMLInputElement>("input")!;
  input.value = name;
  input.dispatchEvent(new Event("input"));
  await flushPromises();
  dialog.querySelector<HTMLButtonElement>("button[type=submit]")!.click();
  await flushPromises();
};

describe("AppPage", () => {
  const assign = vi.fn();
  const createObjectURL = vi.fn(() => "blob:pem");
  const revokeObjectURL = vi.fn();

  beforeEach(() => {
    [GET, POST, success, failure, assign, createObjectURL, revokeObjectURL].forEach((f) =>
      f.mockReset(),
    );
    createObjectURL.mockReturnValue("blob:pem");
    vi.stubGlobal("location", { assign });
    vi.stubGlobal("URL", { createObjectURL, revokeObjectURL });
    document.body.innerHTML = "";
  });

  it("shows the app, the keys and the link to the deliveries", async () => {
    GET.mockResolvedValue({ data: app() });
    const { wrapper } = await mountIt();

    expect(GET).toHaveBeenCalledWith(READ, { params: { path: { id: 3, app_id: 5 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Meine App");
    expect(wrapper.text()).toContain("secret");
    expect(wrapper.text()).toContain("Read Events");
    expect(wrapper.find('a[href="https://hook.example"]').exists()).toBe(true);
    expect(wrapper.find("[data-test=keys]").text()).toContain("kid-1");
    expect(wrapper.find("[data-test=keys]").text()).toContain("abc");
    expect(wrapper.find("[data-test=deliveries-link]").attributes("href")).toBe(
      "/manage/admin_unit/3/app/5/webhook_deliveries",
    );
  });

  it("names an app without a name by its id", async () => {
    GET.mockResolvedValue({ data: app({ client_name: null }) });
    const { wrapper } = await mountIt();

    expect(wrapper.find(".breadcrumb").text()).toContain("OAuth2 client 5");
  });

  it("hides what the permissions do not allow", async () => {
    GET.mockResolvedValue({
      data: app({
        can_write: false,
        can_read_keys: false,
        can_write_keys: false,
        can_read_deliveries: false,
        keys: [],
      }),
    });
    const { wrapper } = await mountIt();

    expect(wrapper.find("button.dropdown-toggle").exists()).toBe(false);
    expect(wrapper.find("[data-test=keys]").exists()).toBe(false);
    expect(wrapper.find("[data-test=deliveries-link]").exists()).toBe(false);
  });

  it("lists keys read only without the write permission", async () => {
    GET.mockResolvedValue({ data: app({ can_write_keys: false }) });
    const { wrapper } = await mountIt();

    expect(wrapper.find("[data-test=create-key]").exists()).toBe(false);
    expect(wrapper.find("[data-test=keys] .row-actions").exists()).toBe(false);
    expect(wrapper.find("[data-test=keys]").text()).toContain("kid-1");
  });

  it("shows the error of a failed load", async () => {
    GET.mockResolvedValue({ error: { message: "Not found" } });
    const { wrapper } = await mountIt();

    expect(wrapper.find(".alert-danger").text()).toBe("Not found");
  });

  it("offers edit and delete", async () => {
    GET.mockResolvedValue({ data: app() });
    const { wrapper } = await mountIt();
    await wrapper.find("button.dropdown-toggle").trigger("click");
    await flushPromises();

    expect(items().map((i) => i.textContent?.trim())).toEqual(["Edit", "Delete"]);
    expect(items()[0].getAttribute("href")).toBe("/manage/admin_unit/3/app/5/update");
  });

  it("deletes the app after the typed name and goes back to the list", async () => {
    GET.mockResolvedValue({ data: app() });
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper } = await mountIt();
    await wrapper.find("button.dropdown-toggle").trigger("click");
    await flushPromises();
    items()[1].click();
    await flushPromises();
    await typeName("Meine App");

    expect(POST).toHaveBeenCalledWith(`${READ}/delete`, {
      params: { path: { id: 3, app_id: 5 } },
      body: { name: "Meine App", inline: false },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3/apps");
  });

  it("creates a key, downloads the private key once and reloads the keys", async () => {
    GET.mockResolvedValueOnce({ data: app({ keys: [] }) });
    GET.mockResolvedValue({ data: app() });
    POST.mockResolvedValue({ data: { id: 8, kid: "kid-1", private_pem: "PEM" } });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    const { wrapper } = await mountIt();

    await wrapper.find("[data-test=create-key]").trigger("click");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(`${READ}/keys`, { params: { path: { id: 3, app_id: 5 } } });
    expect(createObjectURL).toHaveBeenCalledTimes(1);
    expect(click).toHaveBeenCalledTimes(1);
    expect(wrapper.find("[data-test=pem-warning]").text()).toContain(
      "Please download the private key. It will only be available once.",
    );
    expect(success).toHaveBeenCalled();
    expect(wrapper.find("[data-test=keys]").text()).toContain("kid-1");

    await wrapper.find("[data-test=pem-warning] button").trigger("click");
    expect(createObjectURL).toHaveBeenCalledTimes(2);
    click.mockRestore();
  });

  it("toasts the error of a failed key creation", async () => {
    GET.mockResolvedValue({ data: app() });
    POST.mockResolvedValue({ error: { message: "Limit" } });
    const { wrapper } = await mountIt();

    await wrapper.find("[data-test=create-key]").trigger("click");
    await flushPromises();

    expect(failure).toHaveBeenCalledWith("Limit");
    expect(wrapper.find("[data-test=pem-warning]").exists()).toBe(false);
  });

  it("deletes a key after the typed KID and reloads", async () => {
    GET.mockResolvedValue({ data: app() });
    POST.mockResolvedValue({ data: { message: "Key gone" }, response: { ok: true } });
    const { wrapper } = await mountIt();
    await wrapper.find("[data-test=keys] .row-actions button").trigger("click");
    await flushPromises();
    items(1)[0].click();
    await flushPromises();
    expect(document.body.textContent).toContain("Do you want to delete 'App key 8'?");
    await typeName("kid-1", 1);

    expect(POST).toHaveBeenCalledWith(`${READ}/keys/{key_id}/delete`, {
      params: { path: { id: 3, app_id: 5, key_id: 8 } },
      body: { name: "kid-1", inline: true },
    });
    expect(success).toHaveBeenCalledWith("Key gone");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("shows a wrong KID inside the modal", async () => {
    GET.mockResolvedValue({ data: app() });
    POST.mockResolvedValue({
      error: { errors: [{ loc: ["name"], msg: "Does not match" }] },
      response: { ok: false },
    });
    const { wrapper } = await mountIt();
    await wrapper.find("[data-test=keys] .row-actions button").trigger("click");
    await flushPromises();
    items(1)[0].click();
    await flushPromises();
    await typeName("falsch", 1);

    expect(document.body.textContent).toContain("Does not match");
    expect(GET).toHaveBeenCalledTimes(1);
  });
});
