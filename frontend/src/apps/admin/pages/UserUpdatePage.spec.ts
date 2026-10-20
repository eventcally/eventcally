import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
const PUT = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...args: unknown[]) => GET(...args), PUT: (...args: unknown[]) => PUT(...args) },
}));

const success = vi.fn();
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import UserUpdatePage from "./UserUpdatePage.vue";

const detail = {
  user: { id: 7, email: "a@b.de", roles: ["admin"] },
  available_roles: [
    { name: "admin", title: "Administrator" },
    { name: "event_verifier", title: "Event verifier" },
  ],
};

async function mountPage() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: { template: "<div/>" } },
      { path: "/users", name: "users", component: { template: "<div/>" } },
      { path: "/users/:id/update", name: "user-update", component: UserUpdatePage },
    ],
  });
  router.push("/users/7/update");
  await router.isReady();
  const wrapper = mount(UserUpdatePage, {
    props: { id: 7 },
    global: {
      plugins: [router, createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  await flushPromises();
  return { wrapper, router };
}

describe("UserUpdatePage", () => {
  beforeEach(() => {
    GET.mockReset();
    PUT.mockReset();
    success.mockReset();
  });

  it("renders the roles with the current ones checked", async () => {
    GET.mockResolvedValue({ data: detail });
    const { wrapper } = await mountPage();

    expect(GET).toHaveBeenCalledWith("/bff/admin/users/{id}", { params: { path: { id: 7 } } });
    const boxes = wrapper.findAll<HTMLInputElement>('input[type="checkbox"]');
    expect(boxes.map((b) => b.element.checked)).toEqual([true, false]);
    expect(wrapper.text()).toContain("Event verifier");
  });

  it("saves the roles, notifies and navigates to the list", async () => {
    GET.mockResolvedValue({ data: detail });
    PUT.mockResolvedValue({});
    const { wrapper, router } = await mountPage();

    await wrapper.findAll('input[type="checkbox"]')[1].setValue(true);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith("/bff/admin/users/{id}/roles", {
      params: { path: { id: 7 } },
      body: { roles: ["admin", "event_verifier"] },
    });
    expect(success).toHaveBeenCalledWith("User successfully updated");
    expect(router.currentRoute.value.name).toBe("users");
  });

  it("shows an alert when saving fails", async () => {
    GET.mockResolvedValue({ data: detail });
    PUT.mockResolvedValue({
      error: { name: "Unprocessable Entity", message: "m", errors: [{ loc: ["roles"], msg: "Bad role" }] },
    });
    const { wrapper, router } = await mountPage();

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Bad role");
    expect(success).not.toHaveBeenCalled();
    expect(router.currentRoute.value.name).toBe("user-update");
  });

  it("shows an alert and no form when the user cannot be loaded", async () => {
    GET.mockResolvedValue({ error: { name: "Not Found", message: "Not here" } });
    const { wrapper } = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Not here");
    expect(wrapper.find("form").exists()).toBe(false);
  });
});
