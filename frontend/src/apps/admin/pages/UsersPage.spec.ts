import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...args: unknown[]) => GET(...args) } }));

import UsersPage from "./UsersPage.vue";

function mountPage() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: { template: "<div/>" } },
      { path: "/users", name: "users", component: UsersPage },
    ],
  });
  router.push("/users");
  return router.isReady().then(() =>
    mount(UsersPage, {
      global: {
        plugins: [router, createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
      },
    }),
  );
}

describe("UsersPage", () => {
  beforeEach(() => GET.mockReset());

  it("lists users with legacy edit and delete links", async () => {
    GET.mockResolvedValue({
      data: {
        items: [{ id: 7, email: "a@b.de", roles: [], created_at: null }],
        page: 1,
        per_page: 20,
        total: 1,
        pages: 1,
      },
    });
    const wrapper = await mountPage();
    await flushPromises();

    expect(wrapper.text()).toContain("a@b.de");
    expect(wrapper.find('a[href="/admin/user/7/update"]').exists()).toBe(true);
    expect(wrapper.find('a[href="/admin/user/7/delete"]').exists()).toBe(true);
  });

  it("shows an error alert when the request fails", async () => {
    GET.mockResolvedValue({ error: { name: "Forbidden", message: "No access" } });
    const wrapper = await mountPage();
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("No access");
  });
});
