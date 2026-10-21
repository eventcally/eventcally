import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { createMemoryHistory, createRouter } from "vue-router";
import en from "@/locales/en.json";
import de from "@/locales/de.json";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
const PUT = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...args: unknown[]) => GET(...args), PUT: (...args: unknown[]) => PUT(...args) },
}));

const success = vi.fn();
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import OrganizationUpdatePage from "./OrganizationUpdatePage.vue";

const detail = {
  id: 7,
  name: "Alpha Crew",
  is_verified: true,
  incoming_reference_requests_allowed: true,
  can_create_other: false,
  can_invite_other: false,
  can_verify_other: false,
  audit: {
    created_at: "2026-01-02T10:00:00Z",
    created_by_label: "a@b.de",
    updated_at: null,
    updated_by_label: null,
  },
};

const mounted: { unmount: () => void }[] = [];

async function mountPage(locale = "en") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: { template: "<div/>" } },
      { path: "/organizations", name: "organizations", component: { template: "<div/>" } },
      { path: "/organizations/:id/update", name: "organization-update", component: OrganizationUpdatePage },
    ],
  });
  router.push("/organizations/7/update");
  await router.isReady();
  const wrapper = mount(OrganizationUpdatePage, {
    props: { id: 7 },
    global: {
      plugins: [router, createBootstrap(), createI18n({ legacy: false, locale, messages: { en, de } })],
    },
  });
  mounted.push(wrapper);
  await flushPromises();
  return { wrapper, router };
}

const box = (wrapper: Awaited<ReturnType<typeof mountPage>>["wrapper"], key: string) =>
  wrapper.find<HTMLInputElement>(`#org-${key}`);

describe("OrganizationUpdatePage", () => {
  beforeEach(() => {
    GET.mockReset();
    PUT.mockReset();
    success.mockReset();
  });
  afterEach(() => mounted.splice(0).forEach((w) => w.unmount()));

  it("reflects the loaded state in the switches and links out", async () => {
    GET.mockResolvedValue({ data: structuredClone(detail) });
    const { wrapper } = await mountPage();

    expect(GET).toHaveBeenCalledWith("/bff/admin/organizations/{id}", { params: { path: { id: 7 } } });
    expect(wrapper.find("h1").text()).toContain("Alpha Crew");
    expect(wrapper.find("h1").text()).toContain("Verified");
    expect(box(wrapper, "incoming_reference_requests_allowed").element.checked).toBe(true);
    expect(box(wrapper, "can_invite_other").element.checked).toBe(false);
    expect(wrapper.find('a[href="/manage/admin_unit/7"]').exists()).toBe(true);
    expect(wrapper.find('a[href="/organizations/7"]').exists()).toBe(true);
  });

  it("saves a toggled switch on its own and takes the server state", async () => {
    GET.mockResolvedValue({ data: structuredClone(detail) });
    PUT.mockResolvedValue({
      data: {
        ...detail,
        can_invite_other: true,
        audit: { ...detail.audit, updated_at: "2026-02-03T10:00:00Z", updated_by_label: "admin@b.de" },
      },
    });
    const { wrapper } = await mountPage();

    await box(wrapper, "can_invite_other").setValue(true);
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith("/bff/admin/organizations/{id}/settings/{key}", {
      params: { path: { id: 7, key: "can_invite_other" } },
      body: { value: true },
    });
    expect(success).toHaveBeenCalledWith("Organization successfully updated");
    expect(box(wrapper, "can_invite_other").element.checked).toBe(true);
    expect(wrapper.text()).toContain("admin@b.de");
  });

  it("disables a switch while its own request is pending", async () => {
    GET.mockResolvedValue({ data: structuredClone(detail) });
    let resolve!: (v: unknown) => void;
    PUT.mockReturnValue(new Promise((r) => (resolve = r)));
    const { wrapper } = await mountPage();

    await box(wrapper, "can_invite_other").setValue(true);
    await flushPromises();
    expect(box(wrapper, "can_invite_other").element.disabled).toBe(true);
    expect(box(wrapper, "can_create_other").element.disabled).toBe(false);

    resolve({ data: { ...detail, can_invite_other: true } });
    await flushPromises();
    expect(box(wrapper, "can_invite_other").element.disabled).toBe(false);
  });

  it("reverts the switch and shows the error when saving fails", async () => {
    GET.mockResolvedValue({ data: structuredClone(detail) });
    PUT.mockResolvedValue({ error: { name: "Forbidden", message: "No access" } });
    const { wrapper } = await mountPage();

    await box(wrapper, "can_invite_other").setValue(true);
    await flushPromises();

    expect(box(wrapper, "can_invite_other").element.checked).toBe(false);
    expect(wrapper.find(".alert-danger").text()).toBe("No access");
    expect(success).not.toHaveBeenCalled();
  });

  it("interpolates the audit line from the real messages", async () => {
    GET.mockResolvedValue({ data: structuredClone(detail) });
    const en1 = await mountPage("en");
    expect(en1.wrapper.find("p.small").text()).toMatch(/^Created at .+ by a@b\.de\.$/);

    const de1 = await mountPage("de");
    expect(de1.wrapper.find("p.small").text()).toMatch(/a@b\.de/);
    expect(de1.wrapper.find("p.small").text()).not.toContain("%(");
  });

  it("shows the load error and no form", async () => {
    GET.mockResolvedValue({ error: { name: "Not Found", message: "Not found" } });
    const { wrapper } = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Not found");
    expect(wrapper.find("input[type=checkbox]").exists()).toBe(false);
  });

  it("navigates to the list after deleting", async () => {
    GET.mockResolvedValue({ data: structuredClone(detail) });
    const { wrapper, router } = await mountPage();

    wrapper.findComponent({ name: "OrganizationDeleteModal" }).vm.$emit("deleted");
    await flushPromises();

    expect(router.currentRoute.value.name).toBe("organizations");
  });
});
