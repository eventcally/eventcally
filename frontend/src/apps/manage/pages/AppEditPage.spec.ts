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
import AppEditPage from "./AppEditPage.vue";

const FORM = "/bff/manage/organizations/{id}/apps/form";
const VALUES = "/bff/manage/organizations/{id}/apps/{app_id}/form";
const ITEM = "/bff/manage/organizations/{id}/apps/{app_id}";
const LIST = "/bff/manage/organizations/{id}/apps";
const assign = vi.fn();

const options = {
  scopes: ["openid", "profile"],
  app_permissions: [
    { permission: "events:read", label: "Read Events" },
    { permission: "events:write", label: "Write Events" },
  ],
  event_types: ["app.installed", "app.updated"],
};
const values = (over = {}) => ({
  client_name: "Meine App",
  redirect_uris: ["https://a.example"],
  scopes: ["openid"],
  app_permissions: ["events:read"],
  homepage_url: "https://home.example",
  setup_url: null,
  description: "Eine App",
  webhook: { url: "https://hook.example", secret: "geheim", disabled: true, event_types: ["app.updated"] },
  ...over,
});
const stubGets = (loaded: object | null = null) =>
  GET.mockImplementation(async (url: string) => {
    if (url === FORM) return { data: options };
    return loaded ? { data: loaded } : { error: { message: "Not found" } };
  });

describe("AppEditPage", () => {
  beforeEach(() => {
    [GET, POST, PUT, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
  });

  it("creates an app and follows the redirect of the server", async () => {
    stubGets();
    POST.mockResolvedValue({ data: { id: 9, redirect_url: "/manage/admin_unit/3/app/9" } });
    const { wrapper } = await mountPage(
      AppEditPage,
      { organizationId: 3 },
      "/manage/admin_unit/3/app/create",
    );

    expect(GET).toHaveBeenCalledWith(FORM, { params: { path: { id: 3 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Create App");
    await wrapper.find("#client_name").setValue("Neu");
    await wrapper.find("#redirect_uris").setValue("https://a.example\nhttps://b.example");
    await wrapper.find("#scope-1").setValue(true);
    await wrapper.find("#permission-1").setValue(true);
    await wrapper.find("#homepage_url").setValue("https://home.example");
    await wrapper.find("#description").setValue("Text");
    await wrapper.find("#webhook_url").setValue("https://hook.example");
    await wrapper.find("#webhook_secret").setValue("s");
    await wrapper.find("#webhook_disabled").setValue(true);
    await wrapper.find("#event-type-0").setValue(true);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(LIST, {
      params: { path: { id: 3 } },
      body: {
        client_name: "Neu",
        redirect_uris: ["https://a.example", "https://b.example"],
        scopes: ["profile"],
        app_permissions: ["events:write"],
        homepage_url: "https://home.example",
        setup_url: "",
        description: "Text",
        webhook: {
          url: "https://hook.example",
          secret: "s",
          disabled: true,
          event_types: ["app.installed"],
        },
      },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3/app/9");
  });

  it("loads and updates an app", async () => {
    stubGets(values());
    PUT.mockResolvedValue({ data: { id: 5, redirect_url: "/manage/admin_unit/3/app/5" } });
    const { wrapper } = await mountPage(
      AppEditPage,
      { organizationId: 3, id: 5 },
      "/manage/admin_unit/3/app/5/update",
    );

    expect(GET).toHaveBeenCalledWith(VALUES, { params: { path: { id: 3, app_id: 5 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Update App");
    expect((wrapper.find("#client_name").element as HTMLInputElement).value).toBe("Meine App");
    expect((wrapper.find("#webhook_secret").element as HTMLInputElement).value).toBe("geheim");
    expect((wrapper.find("#webhook_disabled").element as HTMLInputElement).checked).toBe(true);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith(ITEM, {
      params: { path: { id: 3, app_id: 5 } },
      body: {
        client_name: "Meine App",
        redirect_uris: ["https://a.example"],
        scopes: ["openid"],
        app_permissions: ["events:read"],
        homepage_url: "https://home.example",
        setup_url: "",
        description: "Eine App",
        webhook: {
          url: "https://hook.example",
          secret: "geheim",
          disabled: true,
          event_types: ["app.updated"],
        },
      },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3/app/5");
  });

  it("loads an app without a webhook or optional values", async () => {
    stubGets({
      client_name: "Meine App",
      app_permissions: ["events:read"],
      webhook: { disabled: false, event_types: [] },
    });
    const { wrapper } = await mountPage(
      AppEditPage,
      { organizationId: 3, id: 5 },
      "/manage/admin_unit/3/app/5/update",
    );

    expect((wrapper.find("#webhook_url").element as HTMLInputElement).value).toBe("");
    expect((wrapper.find("#redirect_uris").element as HTMLTextAreaElement).value).toBe("");
  });

  it("shows the field errors and the page error of a failed save", async () => {
    stubGets();
    POST.mockResolvedValueOnce({
      error: {
        errors: [
          { loc: ["client_name"], msg: "Required" },
          { loc: ["webhook", "url"], msg: "Too long" },
          { loc: ["other"], msg: "Odd" },
        ],
      },
    });
    const { wrapper } = await mountPage(
      AppEditPage,
      { organizationId: 3 },
      "/manage/admin_unit/3/app/create",
    );
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    const errors = wrapper.findAll(".invalid-feedback").map((e) => e.text());
    expect(errors).toEqual(expect.arrayContaining(["Required", "Too long"]));
    expect(wrapper.find(".alert-danger").text()).toBe("Odd");

    POST.mockResolvedValueOnce({ error: { message: "Server error" } });
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Server error");
    expect(assign).not.toHaveBeenCalled();
  });

  it("shows the error when the choices or the app cannot be loaded", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const form = await mountPage(AppEditPage, { organizationId: 3 }, "/manage/admin_unit/3/app/create");
    expect(form.wrapper.find(".alert-danger").text()).toBe("Forbidden");
    expect(form.wrapper.find("form").exists()).toBe(false);

    stubGets(null);
    const missing = await mountPage(
      AppEditPage,
      { organizationId: 3, id: 5 },
      "/manage/admin_unit/3/app/5/update",
    );
    expect(missing.wrapper.find(".alert-danger").text()).toBe("Not found");
  });

  it("ignores a second submit while saving", async () => {
    stubGets();
    let resolve: (v: unknown) => void = () => {};
    POST.mockReturnValue(new Promise((r) => (resolve = r)));
    const { wrapper } = await mountPage(AppEditPage, { organizationId: 3 }, "/manage/admin_unit/3/app/create");
    await wrapper.find("form").trigger("submit");
    await wrapper.find("form").trigger("submit");
    resolve({ error: { message: "x" } });
    await flushPromises();

    expect(POST).toHaveBeenCalledTimes(1);
  });
});
