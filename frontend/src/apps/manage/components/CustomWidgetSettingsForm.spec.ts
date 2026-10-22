import { mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import { defaultSettings, type Settings, type WidgetType } from "@/shared/customWidget";
import CustomWidgetSettingsForm from "./CustomWidgetSettingsForm.vue";

function mountForm(type: WidgetType, settings: Settings) {
  return mount(CustomWidgetSettingsForm, {
    props: { type, settings },
    attachTo: document.body,
    global: {
      plugins: [
        createBootstrap(),
        createI18n({ legacy: false, locale: "en", messages: { en: {} } }),
      ],
    },
  });
}

const lastUpdate = (wrapper: ReturnType<typeof mountForm>) =>
  wrapper.emitted("update:settings")!.at(-1)![0] as Record<string, unknown>;

describe("CustomWidgetSettingsForm", () => {
  it("renders the search settings", () => {
    const wrapper = mountForm("search", defaultSettings("search", 1));

    expect(wrapper.text()).toContain("Layout");
    expect(wrapper.text()).toContain("Events per page");
    expect(wrapper.find("#field-layout").exists()).toBe(true);
    expect(wrapper.find("#field-iFrameMinHeight").exists()).toBe(true);
  });

  it("renders the calendar settings", () => {
    const wrapper = mountForm("calendar", defaultSettings("calendar", 1));

    expect(wrapper.find("#field-calendarType").exists()).toBe(true);
    expect(wrapper.find("#field-iFrameHeight").exists()).toBe(true);
    expect(wrapper.find("#field-layout").exists()).toBe(false);
  });

  it("emits the edited settings and keeps the others", async () => {
    const wrapper = mountForm("search", defaultSettings("search", 1));

    await wrapper.find("#field-eventsPerPage").setValue("25");

    expect(lastUpdate(wrapper)).toMatchObject({
      eventsPerPage: 25,
      layout: "card",
      organizationId: 1,
    });
  });

  it("emits checkbox changes", async () => {
    const wrapper = mountForm("search", defaultSettings("search", 1));

    await wrapper.find("input[type=checkbox]").setValue(false);

    expect(lastUpdate(wrapper)).toMatchObject({ showFilter: false });
  });

  it("shows the Styles tab fields depending on the switches", async () => {
    const settings = { ...defaultSettings("search", 1), showPrintButton: true };
    const wrapper = mountForm("search", settings);

    expect(wrapper.find("#field-printButtonTextColor").exists()).toBe(true);
    expect(wrapper.find("#field-linkColor").attributes("type")).toBe("color");

    await wrapper.setProps({ settings: { ...settings, showPrintButton: false, layout: "text" } });

    expect(wrapper.find("#field-printButtonTextColor").exists()).toBe(false);
    expect(wrapper.find("#field-eventBackgroundColor").exists()).toBe(false);
  });
});
