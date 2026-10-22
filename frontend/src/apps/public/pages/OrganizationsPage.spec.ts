import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", base: "/" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import OrganizationsPage from "./OrganizationsPage.vue";

const result = (items: unknown[], pages = 1) => ({
  data: { items, page: 1, per_page: 10, total: items.length, pages },
});
const rows = [
  { id: 1, name: "Jam Org", short_name: "jam", is_verified: true },
  { id: 2, name: "Other Org", short_name: null, is_verified: false },
];

async function mountPage() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/organizations", name: "organizations", component: OrganizationsPage },
      { path: "/organizations/:id", name: "organization", component: { template: "<div />" } },
    ],
  });
  const wrapper = mount(OrganizationsPage, {
    global: {
      plugins: [
        router,
        createBootstrap(),
        createI18n({ legacy: false, locale: "en", messages: { en: {} } }),
      ],
    },
  });
  await flushPromises();
  return wrapper;
}

describe("OrganizationsPage", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    GET.mockReset().mockResolvedValue(result(rows));
  });
  afterEach(() => vi.useRealTimers());

  it("renders the rows with links, verified icon and short name", async () => {
    const wrapper = await mountPage();

    expect(GET).toHaveBeenCalledWith("/bff/public/organizations", {
      params: { query: { page: 1, per_page: 10, keyword: undefined } },
    });
    const links = wrapper.findAll("a.list-group-item");
    expect(links).toHaveLength(2);
    expect(links[0].attributes("href")).toBe("/organizations/1");
    expect(links[0].find(".fa-check-circle").exists()).toBe(true);
    expect(links[0].text()).toContain("@jam");
    expect(links[1].find(".fa-check-circle").exists()).toBe(false);
  });

  it("searches debounced and starts on page 1", async () => {
    const wrapper = await mountPage();
    GET.mockClear();

    await wrapper.find("input[type=search]").setValue("  jam ");
    expect(GET).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(300);
    await flushPromises();

    expect(GET).toHaveBeenCalledTimes(1);
    expect(GET).toHaveBeenCalledWith("/bff/public/organizations", {
      params: { query: { page: 1, per_page: 10, keyword: "jam" } },
    });
  });

  it("changes the page with the pager", async () => {
    GET.mockResolvedValue(result(rows, 3));
    const wrapper = await mountPage();
    GET.mockClear();

    await wrapper.find('button[aria-label="Next page"]').trigger("click");
    await flushPromises();

    expect(GET).toHaveBeenCalledWith("/bff/public/organizations", {
      params: { query: { page: 2, per_page: 10, keyword: undefined } },
    });
  });

  it("shows the empty state", async () => {
    GET.mockResolvedValue(result([]));
    const wrapper = await mountPage();

    expect(wrapper.text()).toContain("No organizations found");
  });

  it("shows the error when loading fails", async () => {
    GET.mockResolvedValue({ error: { name: "Error", message: "Boom" } });
    const wrapper = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Boom");
  });
});
