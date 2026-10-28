import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import LabeledField from "./LabeledField.vue";

describe("LabeledField", () => {
  it("renders the label, description, input and error", () => {
    const wrapper = mount(LabeledField, {
      props: { label: "Name", labelFor: "name", description: "Help", error: "Bad", required: true },
      slots: { default: '<input id="name" />' },
    });

    expect(wrapper.find("label").text()).toBe("Name *");
    expect(wrapper.find("label").attributes("for")).toBe("name");
    expect(wrapper.find(".form-text").text()).toBe("Help");
    expect(wrapper.find("#name").exists()).toBe(true);
    expect(wrapper.find('[data-test="field-error"]').text()).toBe("Bad");
  });

  it("hides the label and leaves out empty parts", () => {
    const wrapper = mount(LabeledField, { props: { label: "Place", hideLabel: true } });

    expect(wrapper.find("label").classes()).toContain("visually-hidden");
    expect(wrapper.find(".form-text").exists()).toBe(false);
    expect(wrapper.find('[data-test="field-error"]').exists()).toBe(false);
  });
});
