import { mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import EventMenu from "./EventMenu.vue";

const none = {
  can_duplicate_event: false,
  can_verify_event: false,
  can_reference_event: false,
  can_create_reference_request: false,
  can_create_event: false,
  can_view_actions: false,
  can_update_event: false,
};

async function mountMenu(rights: typeof none) {
  const wrapper = mount(EventMenu, {
    props: { eventId: 4, organizationId: 2, rights },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  if (wrapper.find("button").exists()) await wrapper.find("button").trigger("click");
  return wrapper;
}

const items = () =>
  Array.from(document.body.querySelectorAll<HTMLElement>(".dropdown-item")).map((i) => [
    i.textContent?.trim(),
    i.getAttribute("href"),
  ]);

describe("EventMenu", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("is hidden without any right", async () => {
    const wrapper = await mountMenu(none);

    expect(wrapper.find("[data-test=event-menu]").exists()).toBe(false);
  });

  it("only offers more for a signed-in visitor", async () => {
    await mountMenu({ ...none, can_view_actions: true });

    expect(items()).toEqual([["More…", "/event/4/actions"]]);
  });

  it("offers everything to an editor", async () => {
    await mountMenu({
      ...none,
      can_update_event: true,
      can_duplicate_event: true,
      can_create_reference_request: true,
      can_reference_event: true,
      can_view_actions: true,
    });

    expect(items().map(([, href]) => href)).toEqual([
      "/manage/admin_unit/2/event/4/update",
      "/manage/admin_unit/2/event/4/delete",
      "/manage/admin_unit/2/event/create?template_id=4",
      "/manage/admin_unit/2/outgoing_event_reference_request/create_for_event/4",
      "/event/4/reference",
      "/event/4/actions",
    ]);
  });
});
