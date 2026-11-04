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

import { mountPage } from "../testing";
import OrganizationOAuth2ClientEditPage from "./OrganizationOAuth2ClientEditPage.vue";

const FORM = "/bff/manage/organizations/{id}/oauth2-clients/form";
const ITEM = "/bff/manage/organizations/{id}/oauth2-clients/{client_id}";
const LIST = "/bff/manage/organizations/{id}/oauth2-clients";
const assign = vi.fn();

const stubGets = (client: object | null = null) =>
  GET.mockImplementation(async (url: string) => {
    if (url === FORM) return { data: { scopes: ["openid", "profile"] } };
    return client ? { data: client } : { error: { message: "Not found" } };
  });

describe("OrganizationOAuth2ClientEditPage", () => {
  beforeEach(() => {
    [GET, POST, PUT, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
  });

  it("creates a client and follows the redirect of the server", async () => {
    stubGets();
    POST.mockResolvedValue({ data: { id: 9, redirect_url: "/manage/admin_unit/3/oauth2_client/9" } });
    const { wrapper } = await mountPage(
      OrganizationOAuth2ClientEditPage,
      { organizationId: 3 },
      "/manage/admin_unit/3/oauth2_client/create",
    );

    expect(GET).toHaveBeenCalledWith(FORM, { params: { path: { id: 3 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Create OAuth2 client");
    await wrapper.find("#client_name").setValue("Neu");
    await wrapper.find("#redirect_uris").setValue("https://a.example\nhttps://b.example");
    await wrapper.find("#scope-1").setValue(true);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(LIST, {
      params: { path: { id: 3 } },
      body: {
        client_name: "Neu",
        redirect_uris: ["https://a.example", "https://b.example"],
        scopes: ["profile"],
      },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3/oauth2_client/9");
  });

  it("loads and updates a client", async () => {
    stubGets({
      id: 5,
      client_name: "Mein Client",
      redirect_uris: ["https://a.example"],
      scopes: ["openid"],
    });
    PUT.mockResolvedValue({ data: { id: 5, redirect_url: "/manage/admin_unit/3/oauth2_client/5" } });
    const { wrapper } = await mountPage(
      OrganizationOAuth2ClientEditPage,
      { organizationId: 3, id: 5 },
      "/manage/admin_unit/3/oauth2_client/5/update",
    );

    expect(wrapper.find(".breadcrumb").text()).toContain("Update OAuth2 client");
    expect((wrapper.find("#client_name").element as HTMLInputElement).value).toBe("Mein Client");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith(ITEM, {
      params: { path: { id: 3, client_id: 5 } },
      body: { client_name: "Mein Client", redirect_uris: ["https://a.example"], scopes: ["openid"] },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3/oauth2_client/5");
  });

  it("shows the field errors and the page error of a failed save", async () => {
    stubGets();
    POST.mockResolvedValueOnce({
      error: {
        errors: [
          { loc: ["client_name"], msg: "Required" },
          { loc: ["other"], msg: "Odd" },
        ],
      },
    });
    const { wrapper } = await mountPage(
      OrganizationOAuth2ClientEditPage,
      { organizationId: 3 },
      "/manage/admin_unit/3/oauth2_client/create",
    );
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".invalid-feedback").text()).toContain("Required");
    expect(wrapper.find(".alert-danger").text()).toBe("Odd");

    POST.mockResolvedValueOnce({ error: { message: "Server error" } });
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Server error");
    expect(assign).not.toHaveBeenCalled();
  });

  it("shows the error when the form or the client cannot be loaded", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const form = await mountPage(
      OrganizationOAuth2ClientEditPage,
      { organizationId: 3 },
      "/manage/admin_unit/3/oauth2_client/create",
    );
    expect(form.wrapper.find(".alert-danger").text()).toBe("Forbidden");
    expect(form.wrapper.find("form").exists()).toBe(false);

    stubGets(null);
    const missing = await mountPage(
      OrganizationOAuth2ClientEditPage,
      { organizationId: 3, id: 5 },
      "/manage/admin_unit/3/oauth2_client/5/update",
    );
    expect(missing.wrapper.find(".alert-danger").text()).toBe("Not found");
  });

  it("ignores a second submit while saving", async () => {
    stubGets();
    let resolve: (v: unknown) => void = () => {};
    POST.mockReturnValue(new Promise((r) => (resolve = r)));
    const { wrapper } = await mountPage(
      OrganizationOAuth2ClientEditPage,
      { organizationId: 3 },
      "/manage/admin_unit/3/oauth2_client/create",
    );
    await wrapper.find("form").trigger("submit");
    await wrapper.find("form").trigger("submit");
    resolve({ error: { message: "x" } });
    await flushPromises();

    expect(POST).toHaveBeenCalledTimes(1);
  });
});
