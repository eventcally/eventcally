import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import type { Component } from "vue";
import { createI18n } from "vue-i18n";
import { createMemoryHistory, createRouter } from "vue-router";
import en from "@/locales/en.json";
import { routes } from "./router";

/** Mounts a page of the user app on a memory router at `url`, like the entry would. */
export async function mountPage(
  component: Component,
  props: Record<string, unknown> = {},
  url = "/profile",
  messages: Record<string, string> = {},
) {
  const router = createRouter({ history: createMemoryHistory(), routes });
  router.push(url);
  await router.isReady();
  const wrapper = mount(component, {
    props,
    attachTo: document.body,
    global: {
      plugins: [
        router,
        createBootstrap(),
        createI18n({
          legacy: false,
          locale: "en",
          messages: { en: { ...en, ...messages } },
        }),
      ],
    },
  });
  await flushPromises();
  return { wrapper, router };
}
