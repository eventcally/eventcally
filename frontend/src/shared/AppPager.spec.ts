import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import AppPager from "./AppPager.vue";

const i18n = createI18n({ legacy: false, locale: "en", messages: {
    en: { "Page %(page)d of %(pages)d (%(total)d total)": "Page {page} of {pages} ({total} total)" },
  } });

function mountPager(page: number) {
  return mount(AppPager, { props: { page, pages: 42, total: 823 }, global: { plugins: [i18n] } });
}

describe("AppPager", () => {
  it("shows the page and the total", () => {
    expect(mountPager(1).text()).toContain("Page 1 of 42 (823 total)");
  });

  it("emits the next page", async () => {
    const wrapper = mountPager(1);
    await wrapper.findAll("button")[2].trigger("click");
    expect(wrapper.emitted("update:page")).toEqual([[2]]);
  });

  it("emits the last page and ignores clicks beyond the bounds", async () => {
    const wrapper = mountPager(42);
    await wrapper.findAll("button")[3].trigger("click");
    expect(wrapper.emitted("update:page")).toBeUndefined();
    await wrapper.findAll("button")[0].trigger("click");
    expect(wrapper.emitted("update:page")).toEqual([[1]]);
  });
});
