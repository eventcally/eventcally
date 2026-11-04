import { mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import ReadActions from "./ReadActions.vue";
import type { RowAction } from "./RowActions.vue";

const mountActions = (actions: RowAction[]) =>
  mount(ReadActions, {
    props: { actions },
    attachTo: document.body,
    global: {
      plugins: [
        createBootstrap(),
        createI18n({ legacy: false, locale: "en", messages: { en: {} } }),
      ],
    },
  });

describe("ReadActions", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("opens the actions as links and callbacks", async () => {
    const onClick = vi.fn();
    const wrapper = mountActions([
      { title: "Edit", onClick },
      { title: "View event", href: "/event/4" },
    ]);

    expect(wrapper.text()).toContain("Actions");
    await wrapper.find("button").trigger("click");

    const items = [...document.querySelectorAll<HTMLElement>(".dropdown-item")];
    expect(items.map((i) => i.textContent?.trim())).toEqual(["Edit", "View event"]);
    expect(items[1].getAttribute("href")).toBe("/event/4");
    items[0].click();
    expect(onClick).toHaveBeenCalled();
  });

  it("renders nothing without actions", () => {
    expect(mountActions([]).find("button").exists()).toBe(false);
  });
});
