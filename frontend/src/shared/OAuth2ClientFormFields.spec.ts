import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import OAuth2ClientFormFields from "./OAuth2ClientFormFields.vue";

const global = {
  plugins: [createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
};
const props = {
  clientName: "Client",
  redirectUris: "a\nb",
  scopes: ["openid"],
  scopeChoices: ["openid", "profile"],
};

describe("OAuth2ClientFormFields", () => {
  it("offers a checkbox per scope and checks the chosen ones", () => {
    const wrapper = mount(OAuth2ClientFormFields, { props, global });

    expect(wrapper.find<HTMLInputElement>("#scope-0").element.checked).toBe(true);
    expect(wrapper.find<HTMLInputElement>("#scope-1").element.checked).toBe(false);
    expect(wrapper.find<HTMLTextAreaElement>("#redirect_uris").element.value).toBe("a\nb");
  });

  it("adds and removes scopes", async () => {
    const wrapper = mount(OAuth2ClientFormFields, { props, global });

    await wrapper.find("#scope-1").setValue(true);
    await wrapper.find("#scope-0").setValue(false);

    expect(wrapper.emitted("update:scopes")).toEqual([[["openid", "profile"]], [["profile"]]]);
  });

  it("edits the name and the redirect URIs", async () => {
    const wrapper = mount(OAuth2ClientFormFields, { props, global });

    await wrapper.find("#client_name").setValue("New");
    await wrapper.find("#redirect_uris").setValue("c");

    expect(wrapper.emitted("update:clientName")).toEqual([["New"]]);
    expect(wrapper.emitted("update:redirectUris")).toEqual([["c"]]);
  });

  it("shows the errors", () => {
    const wrapper = mount(OAuth2ClientFormFields, {
      props: {
        ...props,
        errors: { client_name: "Required", scopes: "Invalid" },
      },
      global,
    });

    expect(wrapper.findAll("[data-test=field-error]").map((e) => e.text())).toEqual([
      "Required",
      "Invalid",
    ]);
  });
});
