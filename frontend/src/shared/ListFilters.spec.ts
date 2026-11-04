import { mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import ListFilters from "./ListFilters.vue";

const mountFilters = (active: boolean) =>
  mount(ListFilters, {
    props: { active },
    slots: { default: '<input id="keyword" />' },
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });

describe("ListFilters", () => {
  it("is collapsed until the toggle is clicked", async () => {
    const wrapper = mountFilters(false);
    const toggle = wrapper.find("[data-test=filters-toggle]");

    expect(toggle.attributes("aria-expanded")).toBe("false");
    await toggle.trigger("click");
    expect(toggle.attributes("aria-expanded")).toBe("true");
    expect(wrapper.find("[data-test=filters-reset]").exists()).toBe(false);
  });

  it("is open when a filter is set and emits submit and reset", async () => {
    const wrapper = mountFilters(true);

    expect(wrapper.find("[data-test=filters-toggle]").attributes("aria-expanded")).toBe("true");
    await wrapper.find("form").trigger("submit");
    await wrapper.find("[data-test=filters-reset]").trigger("click");

    expect(wrapper.emitted("submit")).toHaveLength(1);
    expect(wrapper.emitted("reset")).toHaveLength(1);
    expect(wrapper.find("#keyword").exists()).toBe(true);
  });
});
