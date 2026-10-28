import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import LegacyFormLink from "./LegacyFormLink.vue";

describe("LegacyFormLink", () => {
  it("links to the previous form", () => {
    const wrapper = mount(LegacyFormLink, {
      props: { href: "/manage/admin_unit/1/legacy/event/create" },
      global: { plugins: [createI18n({ legacy: false, locale: "en", messages: { en: {} } })] },
    });

    expect(wrapper.text()).toContain("This is the new form.");
    expect(wrapper.find("a").attributes("href")).toBe("/manage/admin_unit/1/legacy/event/create");
    expect(wrapper.find("a").text()).toBe("Open the previous form");
  });
});
