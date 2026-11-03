import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import TosAcceptLabel from "./TosAcceptLabel.vue";

const messages = {
  "I read and accept %(tos_open)sTerms of Service%(tos_close)s and %(privacy_open)sPrivacy%(privacy_close)s.":
    "I read and accept {tos_open}Terms of Service{tos_close} and {privacy_open}Privacy{privacy_close}.",
  "I read and accept %(privacy_open)sPrivacy%(privacy_close)s.":
    "I read and accept {privacy_open}Privacy{privacy_close}.",
};

function mountLabel(hasTos: boolean, en = messages) {
  return mount(TosAcceptLabel, {
    props: { hasTos },
    global: {
      plugins: [createI18n({ legacy: false, locale: "en", messages: { en } })],
    },
  });
}

describe("TosAcceptLabel", () => {
  it("links the terms and the privacy policy", () => {
    const wrapper = mountLabel(true);

    expect(wrapper.text()).toBe("I read and accept Terms of Service and Privacy.");
    expect(wrapper.findAll("a").map((a) => [a.text(), a.attributes("href")])).toEqual([
      ["Terms of Service", "/tos"],
      ["Privacy", "/privacy"],
    ]);
  });

  it("links only the privacy policy without terms", () => {
    const wrapper = mountLabel(false);

    expect(wrapper.text()).toBe("I read and accept Privacy.");
    expect(wrapper.findAll("a").map((a) => a.attributes("href"))).toEqual(["/privacy"]);
  });

  it("never renders markup of a translation", () => {
    const wrapper = mountLabel(false, {
      "I read and accept %(tos_open)sTerms of Service%(tos_close)s and %(privacy_open)sPrivacy%(privacy_close)s.":
        "",
      "I read and accept %(privacy_open)sPrivacy%(privacy_close)s.":
        "<b>bold</b> {privacy_open}<i>Privacy</i>{privacy_close}",
    });

    expect(wrapper.find("b").exists()).toBe(false);
    expect(wrapper.find("i").exists()).toBe(false);
    expect(wrapper.text()).toContain("<b>bold</b>");
    expect(wrapper.find("a").text()).toBe("<i>Privacy</i>");
  });
});
