import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import InstructionText from "./InstructionText.vue";
import { LINK_CLOSE, LINK_OPEN } from "./instruction";

const text = `Find it through the ${LINK_OPEN}search${LINK_CLOSE} now.`;

describe("InstructionText", () => {
  it("links the marked part to a page", () => {
    const wrapper = mount(InstructionText, { props: { text, href: "/eventdates" } });

    expect(wrapper.find("a").attributes("href")).toBe("/eventdates");
    expect(wrapper.find("a").text()).toBe("search");
    expect(wrapper.text()).toBe("Find it through the search now.");
  });

  it("links to a route", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: "/events", name: "events", component: { render: () => null } }],
    });
    const wrapper = mount(InstructionText, {
      props: { text, to: { name: "events" } },
      global: { plugins: [router] },
    });

    expect(wrapper.find("a").attributes("href")).toBe("/events");
  });

  it("shows a text without a link as it is and never renders markup", () => {
    const wrapper = mount(InstructionText, { props: { text: "Plain <b>text</b>" } });

    expect(wrapper.find("a").exists()).toBe(false);
    expect(wrapper.find("b").exists()).toBe(false);
    expect(wrapper.text()).toBe("Plain <b>text</b>");
  });
});
