import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import NameConfirmationForm from "./NameConfirmationForm.vue";

describe("NameConfirmationForm", () => {
  it("emits what was typed and shows the slot", async () => {
    const wrapper = mount(NameConfirmationForm, {
      props: { label: "Name", submitLabel: "Delete" },
      slots: { default: "<p>Really?</p>" },
    });

    expect(wrapper.text()).toContain("Really?");
    await wrapper.find("#name").setValue("Mein Client");
    await wrapper.find("form").trigger("submit");

    expect(wrapper.emitted("submit")).toEqual([["Mein Client"]]);
  });

  it("shows the error of the server and the custom input", () => {
    const wrapper = mount(NameConfirmationForm, {
      props: {
        label: "Email",
        submitLabel: "Go",
        inputId: "email",
        inputType: "email",
        error: "Does not match",
        busy: true,
      },
    });

    expect(wrapper.find("#email").attributes("type")).toBe("email");
    expect(wrapper.find("#email").classes()).toContain("is-invalid");
    expect(wrapper.find("[data-test=field-error]").text()).toBe("Does not match");
    expect(wrapper.find("#submit").attributes("disabled")).toBeDefined();
  });
});
