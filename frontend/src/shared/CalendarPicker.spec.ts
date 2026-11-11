import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import CalendarPicker from "./CalendarPicker.vue";

const mountPicker = (props: Record<string, unknown> = {}) =>
  mount(CalendarPicker, {
    props: {
      choices: [
        { id: 1, name: "Sport", private: false },
        { id: 2, name: "Intern", private: true },
      ],
      modelValue: [1],
      ...props,
    },
    global: { plugins: [createI18n({ legacy: false, locale: "en", messages: { en: {} } })] },
  });

describe("CalendarPicker", () => {
  it("lists the calendars with a badge for private ones", () => {
    const wrapper = mountPicker();

    expect(wrapper.findAll("input")).toHaveLength(2);
    expect((wrapper.find("#calendar-1").element as HTMLInputElement).checked).toBe(true);
    expect(wrapper.find("label[for=calendar-2]").text()).toContain("Private");
    expect(wrapper.find("label[for=calendar-1]").text()).not.toContain("Private");
  });

  it("emits the selection and shows an error", async () => {
    const wrapper = mountPicker({ idPrefix: "x", error: "Calendar not found" });

    await wrapper.find("#x-2").setValue(true);

    expect(wrapper.emitted("update:modelValue")).toEqual([[[1, 2]]]);
    expect(wrapper.find("[data-test=calendar-error]").text()).toBe("Calendar not found");
  });
});
