import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import ApiKeyFormFields from "./ApiKeyFormFields.vue";

const global = {
  plugins: [createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
};

describe("ApiKeyFormFields", () => {
  it("edits the name", async () => {
    const wrapper = mount(ApiKeyFormFields, { props: { name: "Key" }, global });

    await wrapper.find("#name").setValue("Other");

    expect(wrapper.emitted("update:name")).toEqual([["Other"]]);
  });

  it("shows the error", () => {
    const wrapper = mount(ApiKeyFormFields, {
      props: { name: "", errors: { name: "Required" } },
      global,
    });

    expect(wrapper.find("[data-test=field-error]").text()).toBe("Required");
  });
});
