import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import en from "@/locales/en.json";
import TriStateFilter from "./TriStateFilter.vue";

const i18n = createI18n({ legacy: false, locale: "en", messages: { en } });

describe("TriStateFilter", () => {
  it("selects all by default and reports the choice", async () => {
    const wrapper = mount(TriStateFilter, {
      props: { id: "verify", label: "Verify", modelValue: "" },
      global: { plugins: [i18n] },
    });

    expect(wrapper.find<HTMLInputElement>("#verify-all").element.checked).toBe(true);

    await wrapper.find("#verify-yes").setValue();
    await wrapper.find("#verify-no").setValue();

    expect(wrapper.emitted("update:modelValue")).toEqual([["1"], ["0"]]);
    expect(wrapper.text()).toContain("Verify");
  });
});
