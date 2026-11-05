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
const failure = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: failure }) }));

import { mountPage } from "../testing";
import AppInstallationPage from "./AppInstallationPage.vue";

const URL = "/manage/admin_unit/3/app_installation/5";
const READ = "/bff/manage/organizations/{id}/app-installations/{installation_id}";
const installation = (over = {}) => ({
  id: 5,
  app: "Meine App",
  permissions: ["Read Events"],
  requested_permissions: ["Read Events"],
  needs_permission_update: false,
  created_at: "2026-11-04T10:00:00Z",
  audit: { created_at: "2026-11-04T10:00:00Z", created_by_label: "me@test.de" },
  can_write: true,
  ...over,
});
const mountIt = () => mountPage(AppInstallationPage, { organizationId: 3, id: 5 }, URL);
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];

describe("AppInstallationPage", () => {
  const assign = vi.fn();

  beforeEach(() => {
    [GET, POST, PUT, success, failure, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
    document.body.innerHTML = "";
  });

  it("shows the installation without the accept section", async () => {
    GET.mockResolvedValue({ data: installation() });
    const { wrapper } = await mountIt();

    expect(GET).toHaveBeenCalledWith(READ, { params: { path: { id: 3, installation_id: 5 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("App installation 5");
    expect(wrapper.text()).toContain("Meine App");
    expect(wrapper.text()).toContain("Read Events");
    expect(wrapper.find("[data-test=accept-permissions]").exists()).toBe(false);
  });

  it("offers to accept the permissions the app requests now", async () => {
    GET.mockResolvedValue({
      data: installation({
        requested_permissions: ["Read Events", "Write Events"],
        needs_permission_update: true,
      }),
    });
    PUT.mockResolvedValue({ data: { message: "Updated" } });
    const { wrapper } = await mountIt();

    const section = wrapper.find("[data-test=accept-permissions]");
    expect(section.text()).toContain("Write Events");
    await section.find("button").trigger("click");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith(`${READ}/permissions`, {
      params: { path: { id: 3, installation_id: 5 } },
    });
    expect(success).toHaveBeenCalledWith("Updated");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("toasts the error of a failed accept", async () => {
    GET.mockResolvedValue({
      data: installation({ needs_permission_update: true }),
    });
    PUT.mockResolvedValue({ error: { message: "Nope" } });
    const { wrapper } = await mountIt();

    await wrapper.find("[data-test=accept]").trigger("click");
    await flushPromises();

    expect(failure).toHaveBeenCalledWith("Nope");
  });

  it("hides the actions and the accept section without permission", async () => {
    GET.mockResolvedValue({
      data: installation({ can_write: false, needs_permission_update: true }),
    });
    const { wrapper } = await mountIt();

    expect(wrapper.find("button.dropdown-toggle").exists()).toBe(false);
    expect(wrapper.find("[data-test=accept-permissions]").exists()).toBe(false);
  });

  it("uninstalls after a plain confirmation and goes back to the list", async () => {
    GET.mockResolvedValue({ data: installation() });
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper } = await mountIt();
    await wrapper.find("button.dropdown-toggle").trigger("click");
    await flushPromises();
    expect(items().map((i) => i.textContent?.trim())).toEqual(["Delete"]);
    items()[0].click();
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal .btn-danger")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(`${READ}/delete`, {
      params: { path: { id: 3, installation_id: 5 } },
      body: { inline: false },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3/app_installations");
  });

  it("shows the error of a failed load", async () => {
    GET.mockResolvedValue({ error: { message: "Not found" } });
    const { wrapper } = await mountIt();

    expect(wrapper.find(".alert-danger").text()).toBe("Not found");
  });
});
