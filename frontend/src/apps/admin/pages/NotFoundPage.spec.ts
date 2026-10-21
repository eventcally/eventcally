import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import { createMemoryHistory, createRouter } from "vue-router";
import NotFoundPage from "./NotFoundPage.vue";

describe("NotFoundPage", () => {
  it("shows the message and links back to the admin home", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/", name: "home", component: { template: "<div/>" } }],
    });
    const wrapper = mount(NotFoundPage, {
      global: {
        plugins: [
          router,
          createBootstrap(),
          createI18n({
            legacy: false,
            locale: "en",
            messages: { en: { Admin: "Admin" } },
          }),
        ],
      },
    });
    await flushPromises();

    expect(wrapper.text()).toContain("The requested resource was not found");
    expect(wrapper.find('a[href="/"]').text()).toBe("Admin");
  });
});
