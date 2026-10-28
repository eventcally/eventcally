import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";
import { createI18n } from "vue-i18n";
import { newDateDefinition, type DateDefinitionValue } from "../eventForm";

vi.mock("./RecurrenceRuleModal.vue", () => ({
  __esModule: true,
  default: defineComponent({
    name: "RecurrenceRuleModal",
    props: ["show", "modelValue", "start", "idPrefix", "organizationId"],
    emits: ["update:modelValue", "update:show"],
    render: () => null,
  }),
}));

import EventDateDefinitionFields from "./EventDateDefinitionFields.vue";

function mountCard(value: Partial<DateDefinitionValue> = {}, props: Record<string, unknown> = {}) {
  const wrapper = mount(EventDateDefinitionFields, {
    props: {
      organizationId: 5,
      index: 1,
      removable: false,
      modelValue: { ...newDateDefinition({ date: "2030-12-31", time: "14:00" }), ...value },
      "onUpdate:modelValue": (v: DateDefinitionValue) => wrapper.setProps({ modelValue: v }),
      ...props,
    },
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  return wrapper;
}

const value = (wrapper: ReturnType<typeof mountCard>) => wrapper.props("modelValue") as DateDefinitionValue;

describe("EventDateDefinitionFields", () => {
  it("edits the start and shows the end three hours later", async () => {
    const wrapper = mountCard();

    await wrapper.find("#date_definitions-1-start").setValue("2031-01-02");
    await wrapper.find("#date_definitions-1-start-time").setValue("10:00");
    await wrapper.find('[data-test="date_definitions-1-end-show"]').trigger("click");

    expect(value(wrapper)).toMatchObject({
      startDate: "2031-01-02",
      startTime: "10:00",
      endShown: true,
      endDate: "2031-01-02",
      endTime: "13:00",
    });

    await wrapper.find("#date_definitions-1-end").setValue("2031-01-03");
    await wrapper.find("#date_definitions-1-end-time").setValue("11:00");
    expect(value(wrapper)).toMatchObject({ endDate: "2031-01-03", endTime: "11:00" });
  });

  it("all-day opens the end at the end of the day and hides the times", async () => {
    const wrapper = mountCard();

    await wrapper.find("#date_definitions-1-allday").setValue(true);

    expect(value(wrapper)).toMatchObject({ allday: true, endShown: true, endDate: "2030-12-31", endTime: "23:59" });
    expect(wrapper.find("#date_definitions-1-start-time").exists()).toBe(false);
    expect(wrapper.find("#date_definitions-1-end-time").exists()).toBe(false);

    await wrapper.find("#date_definitions-1-allday").setValue(false);
    expect(value(wrapper)).toMatchObject({ allday: false, endShown: true });
  });

  it("hiding the end clears it and turns off all-day", async () => {
    const wrapper = mountCard({ allday: true, endShown: true, endDate: "2030-12-31", endTime: "23:59" });

    await wrapper.find('[data-test="date_definitions-1-end-hide"]').trigger("click");

    expect(value(wrapper)).toMatchObject({ endShown: false, endDate: "", endTime: "", allday: false });
  });

  it("shows the errors", () => {
    const wrapper = mountCard({ endShown: true }, { errors: { start: "Too late", end: "Too long" } });

    expect(wrapper.text()).toContain("Too late");
    expect(wrapper.text()).toContain("Too long");
  });

  it("opens the recurrence editor and takes its rule", async () => {
    const wrapper = mountCard();
    const modal = wrapper.findComponent({ name: "RecurrenceRuleModal" });

    await wrapper.find("#date_definitions-1-recc-button").trigger("click");
    expect(modal.props("show")).toBe(true);
    expect(modal.props("start")).toBe("2030-12-31");
    expect(modal.props("idPrefix")).toBe("date_definitions-1-");

    modal.vm.$emit("update:modelValue", "RRULE:FREQ=DAILY;COUNT=7");
    await flushPromises();

    expect(value(wrapper).recurrenceRule).toBe("RRULE:FREQ=DAILY;COUNT=7");
    expect(wrapper.find('[data-test="date_definitions-1-recurrence-summary"]').text()).toContain(
      "ends after",
    );
    expect(wrapper.find("#date_definitions-1-recc-button").text()).toContain("Edit recurrence");

    await wrapper.find('[data-test="date_definitions-1-recc-remove"]').trigger("click");
    expect(value(wrapper).recurrenceRule).toBeNull();
  });

  it("shows an unknown rule as it is", () => {
    const wrapper = mountCard({ recurrenceRule: "RRULE:FREQ=DAILY;BYHOUR=3" });

    expect(wrapper.find('[data-test="date_definitions-1-recurrence-summary"]').text()).toBe(
      "RRULE:FREQ=DAILY;BYHOUR=3",
    );
  });

  it("can be removed when there are more dates", async () => {
    const single = mountCard();
    expect(single.find('[data-test="date_definitions-1-remove"]').exists()).toBe(false);

    const wrapper = mountCard({}, { removable: true });
    await wrapper.find('[data-test="date_definitions-1-remove"]').trigger("click");
    expect(wrapper.emitted("remove")).toHaveLength(1);
  });
});
