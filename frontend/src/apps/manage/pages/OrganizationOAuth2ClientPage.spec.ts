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
import OrganizationOAuth2ClientPage from "./OrganizationOAuth2ClientPage.vue";

const URL = "/manage/admin_unit/3/oauth2_client/5";
const READ = "/bff/manage/organizations/{id}/oauth2-clients/{client_id}";
const client = (over = {}) => ({
  id: 5,
  client_id: "cid",
  client_secret: "csecret",
  client_name: "Mein Client",
  client_uri: null,
  scope: "openid profile",
  scopes: ["openid", "profile"],
  redirect_uris: ["https://example.com/cb"],
  grant_types: ["authorization_code"],
  response_types: ["code"],
  token_endpoint_auth_method: ["none"],
  audit: { created_at: "2026-11-04T10:00:00Z", created_by_label: "me@test.de" },
  can_write: true,
  ...over,
});
const mountIt = () => mountPage(OrganizationOAuth2ClientPage, { organizationId: 3, id: 5 }, URL);
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];
const openActions = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find("button.dropdown-toggle").trigger("click");
  await flushPromises();
};

describe("OrganizationOAuth2ClientPage", () => {
  const assign = vi.fn();

  beforeEach(() => {
    [GET, POST, success, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
    document.body.innerHTML = "";
  });

  it("shows the client details", async () => {
    GET.mockResolvedValue({ data: client() });
    const { wrapper } = await mountIt();

    expect(GET).toHaveBeenCalledWith(READ, { params: { path: { id: 3, client_id: 5 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Mein Client");
    expect(wrapper.find("[data-test=oauth2-client-details]").text()).toContain("csecret");
  });

  it("titles a client without a name by its id", async () => {
    GET.mockResolvedValue({ data: client({ client_name: null }) });
    const { wrapper } = await mountIt();

    expect(wrapper.find(".breadcrumb").text()).toContain("OAuth2 client 5");
  });

  it("offers edit and delete", async () => {
    GET.mockResolvedValue({ data: client() });
    const { wrapper } = await mountIt();
    await openActions(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual(["Edit", "Delete"]);
    expect(items()[0].getAttribute("href")).toBe("/manage/admin_unit/3/oauth2_client/5/update");
  });

  it("offers no actions without permission", async () => {
    GET.mockResolvedValue({ data: client({ can_write: false }) });
    const reader = await mountIt();
    expect(reader.wrapper.find("button.dropdown-toggle").exists()).toBe(false);
  });

  it("shows the error of a failed load", async () => {
    GET.mockResolvedValue({ error: { message: "Not found" } });
    const { wrapper } = await mountIt();

    expect(wrapper.find(".alert-danger").text()).toBe("Not found");
  });

  it("deletes after the typed name and leaves for the list", async () => {
    GET.mockResolvedValue({ data: client() });
    POST.mockResolvedValue({ data: { message: "Gone", redirect_url: "/x" }, response: { ok: true } });
    const { wrapper } = await mountIt();
    await openActions(wrapper);
    items()[1].click();
    await flushPromises();

    expect(document.body.textContent).toContain("Do you want to delete 'Mein Client'?");
    const input = document.querySelector<HTMLInputElement>(".modal input")!;
    input.value = "Mein Client";
    input.dispatchEvent(new Event("input"));
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal button[type=submit]")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(`${READ}/delete`, {
      params: { path: { id: 3, client_id: 5 } },
      body: { name: "Mein Client", inline: false },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3/oauth2_clients");
  });
});
