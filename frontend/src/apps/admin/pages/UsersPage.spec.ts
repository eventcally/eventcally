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
      { path: "/users/:id/update", name: "user-update", component: { template: "<div/>" } },
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

  it("lists users with an edit link and a delete button", async () => {
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
    expect(wrapper.find('a[href="/users/7/update"]').exists()).toBe(true);
    expect(wrapper.find("button.btn-link").text()).toBe("Delete");
  });

  it("opens the delete modal for the row", async () => {
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

    await wrapper.find("button.btn-link").trigger("click");
    await flushPromises();

    expect(wrapper.findComponent({ name: "UserDeleteModal" }).props("user")).toEqual(
      expect.objectContaining({ id: 7, email: "a@b.de" }),
    );
    expect(wrapper.findComponent({ name: "UserDeleteModal" }).props("modelValue")).toBe(true);
  });

  it("shows an error alert when the request fails", async () => {
    GET.mockResolvedValue({ error: { name: "Forbidden", message: "No access" } });
    const wrapper = await mountPage();
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("No access");
  });
});
