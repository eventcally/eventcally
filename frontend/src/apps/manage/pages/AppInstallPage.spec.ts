import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));

import { mountPage } from "../testing";
import AppInstallPage from "./AppInstallPage.vue";

const URL = "/manage/admin_unit/3/app_installations/install/8";
const app = (over = {}) => ({
  id: 8,
  client_name: "Meine App",
  homepage_url: "https://home.example",
  description: "Eine App",
  permissions: ["Read Events", "Write Events"],
  ...over,
});
const mountIt = () => mountPage(AppInstallPage, { organizationId: 3, appId: 8 }, URL);

describe("AppInstallPage", () => {
  const assign = vi.fn();

  beforeEach(() => {
    [GET, POST, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
  });

  it("shows the app and the permissions it gets, all fixed", async () => {
    GET.mockResolvedValue({ data: app() });
    const { wrapper } = await mountIt();

    expect(GET).toHaveBeenCalledWith("/bff/manage/organizations/{id}/installable-apps/{app_id}", {
      params: { path: { id: 3, app_id: 8 } },
    });
    expect(wrapper.find(".breadcrumb").text()).toContain("Create App installation");
    expect(wrapper.text()).toContain("Do you want to install 'Meine App'?");
    expect(wrapper.text()).toContain("Eine App");
    expect(wrapper.find('a[href="https://home.example"]').exists()).toBe(true);

    const boxes = wrapper.findAll<HTMLInputElement>("input[type=checkbox]");
    expect(boxes).toHaveLength(2);
    expect(boxes.every((b) => b.element.disabled)).toBe(true);
    expect(wrapper.text()).toContain("Write Events");
  });

  it("installs and follows the redirect of the server", async () => {
    GET.mockResolvedValue({ data: app() });
    POST.mockResolvedValue({ data: { id: 4, redirect_url: "/manage/admin_unit/3/app_installation/4" } });
    const { wrapper } = await mountIt();
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/manage/organizations/{id}/app-installations", {
      params: { path: { id: 3 } },
      body: { app_id: 8 },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3/app_installation/4");
  });

  it("shows the error of a failed install and ignores a second submit while installing", async () => {
    GET.mockResolvedValue({ data: app({ client_name: null, homepage_url: null }) });
    let resolve: (v: unknown) => void = () => {};
    POST.mockReturnValue(new Promise((r) => (resolve = r)));
    const { wrapper } = await mountIt();
    await wrapper.find("form").trigger("submit");
    await wrapper.find("form").trigger("submit");
    resolve({ error: { message: "Already installed" } });
    await flushPromises();

    expect(POST).toHaveBeenCalledTimes(1);
    expect(wrapper.find(".alert-danger").text()).toBe("Already installed");
    expect(assign).not.toHaveBeenCalled();
  });

  it("shows the error of a failed load", async () => {
    GET.mockResolvedValue({ error: { message: "Not found" } });
    const { wrapper } = await mountIt();

    expect(wrapper.find(".alert-danger").text()).toBe("Not found");
    expect(wrapper.find("form").exists()).toBe(false);
  });
});
