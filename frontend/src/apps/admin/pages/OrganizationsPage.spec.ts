import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...args: unknown[]) => GET(...args) } }));

import OrganizationsPage from "./OrganizationsPage.vue";

const row = { id: 5, name: "Alpha Crew", is_verified: true, created_at: null, deletion_requested_at: null };
const result = (items = [row]) => ({
  data: { items, page: 1, per_page: 20, total: items.length, pages: 1 },
});

async function mountPage(url = "/organizations") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: { template: "<div/>" } },
      { path: "/organizations", name: "organizations", component: OrganizationsPage },
      { path: "/organizations/:id/update", name: "organization-update", component: { template: "<div/>" } },
    ],
  });
  router.push(url);
  await router.isReady();
  const wrapper = mount(OrganizationsPage, {
    global: {
      plugins: [router, createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  await flushPromises();
  return { wrapper, router };
}

describe("OrganizationsPage", () => {
  beforeEach(() => GET.mockReset());
  afterEach(() => vi.useRealTimers());

  it("lists organizations with manage, view, edit and delete actions", async () => {
    GET.mockResolvedValue(result());
    const { wrapper } = await mountPage();

    expect(wrapper.text()).toContain("Alpha Crew");
    expect(wrapper.text()).toContain("Yes");
    expect(wrapper.find('a[href="/manage/admin_unit/5"]').exists()).toBe(true);
    expect(wrapper.find('a[href="/organizations/5"]').exists()).toBe(true);
    expect(wrapper.find('a[href="/organizations/5/update"]').exists()).toBe(true);
    expect(wrapper.find("button.btn-link").text()).toBe("Delete");
  });

  it("shows the empty state", async () => {
    GET.mockResolvedValue(result([]));
    const { wrapper } = await mountPage();

    expect(wrapper.text()).toContain("No organizations found");
  });

  it("loads with the keyword from the URL", async () => {
    GET.mockResolvedValue(result());
    const { wrapper } = await mountPage("/organizations?keyword=alp");

    expect(GET).toHaveBeenCalledWith("/bff/admin/organizations", {
      params: { query: { page: 1, keyword: "alp" } },
    });
    expect((wrapper.find("input[type=search]").element as HTMLInputElement).value).toBe("alp");
  });

  it("debounces the search into the URL and drops the page", async () => {
    GET.mockResolvedValue(result());
    const { wrapper, router } = await mountPage("/organizations?page=2");
    GET.mockClear();

    vi.useFakeTimers();
    await wrapper.find("input[type=search]").setValue("a");
    await wrapper.find("input[type=search]").setValue("alp");
    vi.advanceTimersByTime(299);
    expect(router.currentRoute.value.query.keyword).toBeUndefined();
    vi.advanceTimersByTime(1);
    vi.useRealTimers();
    await flushPromises();

    expect(router.currentRoute.value.query).toEqual({ keyword: "alp" });
    expect(GET).toHaveBeenCalledTimes(1);
    expect(GET).toHaveBeenCalledWith("/bff/admin/organizations", {
      params: { query: { page: 1, keyword: "alp" } },
    });
  });

  it("opens the delete modal for the row and reloads after deleting", async () => {
    GET.mockResolvedValue(result());
    const { wrapper } = await mountPage();

    await wrapper.find("button.btn-link").trigger("click");
    await flushPromises();
    const modal = wrapper.findComponent({ name: "OrganizationDeleteModal" });
    expect(modal.props("organization")).toEqual(expect.objectContaining({ id: 5, name: "Alpha Crew" }));
    expect(modal.props("modelValue")).toBe(true);

    GET.mockClear();
    modal.vm.$emit("deleted");
    await flushPromises();
    expect(GET).toHaveBeenCalledTimes(1);
  });

  it("shows an error alert when the request fails", async () => {
    GET.mockResolvedValue({ error: { name: "Forbidden", message: "No access" } });
    const { wrapper } = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("No access");
  });
});
