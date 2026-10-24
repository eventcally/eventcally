import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import LinkifiedText from "./LinkifiedText.vue";

describe("LinkifiedText", () => {
  it("renders links as safe anchors", () => {
    const wrapper = mount(LinkifiedText, { props: { text: "Visit https://a.de now" } });

    const link = wrapper.get("a");
    expect(link.attributes("href")).toBe("https://a.de");
    expect(link.attributes("target")).toBe("_blank");
    expect(link.attributes("rel")).toBe("nofollow noopener noreferrer");
    expect(wrapper.text()).toBe("Visit https://a.de now");
  });

  it("renders markup as text", () => {
    const wrapper = mount(LinkifiedText, { props: { text: "<script>alert(1)</script> <b>x</b>" } });

    expect(wrapper.find("script").exists()).toBe(false);
    expect(wrapper.find("b").exists()).toBe(false);
    expect(wrapper.text()).toBe("<script>alert(1)</script> <b>x</b>");
  });

  it("keeps newlines", () => {
    const wrapper = mount(LinkifiedText, { props: { text: "a\nb" } });

    expect(wrapper.text()).toBe("a\nb");
  });
});
