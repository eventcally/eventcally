import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach } from "vitest";
import { defineComponent, type Component } from "vue";
import { createI18n } from "vue-i18n";
import { createMemoryHistory, createRouter } from "vue-router";
import en from "@/locales/en.json";

const Blank = defineComponent({ render: () => null });
const base = "/manage/admin_unit/:organizationId(\\d+)";

/** The routes the list / delete pages link to, with blank components. */
export const testRoutes = [
  { path: `${base}/event_organizers`, name: "event-organizers", component: Blank },
  { path: `${base}/event_organizer/create`, name: "event-organizer-create", component: Blank },
  { path: `${base}/event_organizer/:id/update`, name: "event-organizer-update", component: Blank },
  { path: `${base}/event_places`, name: "event-places", component: Blank },
  { path: `${base}/event_place/create`, name: "event-place-create", component: Blank },
  { path: `${base}/event_place/:id/update`, name: "event-place-update", component: Blank },
  { path: `${base}/events`, name: "manage-events", component: Blank },
  { path: `${base}/event/:id/update`, name: "event-update", component: Blank },
  { path: `${base}/event/:id/delete`, name: "event-delete", component: Blank },
];

const mounted: { unmount: () => void }[] = [];

// Teleported dropdowns and modals live in `document.body`: unmount after every test.
afterEach(() => {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount());
  document.body.innerHTML = "";
});

/** Mounts a page of the manage app on a memory router at `url`. */
export async function mountPage(
  component: Component,
  props: Record<string, unknown>,
  url: string,
  messages: Record<string, string> = {},
) {
  const router = createRouter({ history: createMemoryHistory(), routes: testRoutes });
  router.push(url);
  await router.isReady();
  const wrapper = mount(component, {
    props,
    attachTo: document.body,
    global: {
      plugins: [
        router,
        createBootstrap(),
        createI18n({ legacy: false, locale: "en", messages: { en: { ...en, ...messages } } }),
      ],
    },
  });
  mounted.push(wrapper);
  await flushPromises();
  return { wrapper, router };
}
