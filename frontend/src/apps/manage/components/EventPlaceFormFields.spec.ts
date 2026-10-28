import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";
import { createI18n } from "vue-i18n";
import { emptyLocation, type EventPlaceFormValue } from "../eventPlaceForm";

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
vi.mock("@/shared/ImageCropper.vue", () => ({
  __esModule: true,
  default: defineComponent({ name: "ImageCropper", render: () => null }),
}));

import EventPlaceFormFields from "./EventPlaceFormFields.vue";

function mountFields(form: Partial<EventPlaceFormValue> = {}) {
  const wrapper = mount(EventPlaceFormFields, {
    props: {
      organizationId: 5,
      licenses: [],
      idPrefix: "new_event_place-",
      modelValue: { name: "", url: "", description: "", location: emptyLocation(), photo: null, ...form },
      errors: { "photo.copyright_text": "Required" },
      "onUpdate:modelValue": (v: EventPlaceFormValue) => wrapper.setProps({ modelValue: v }),
    },
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  return wrapper;
}

describe("EventPlaceFormFields", () => {
  it("prefixes the input ids for a modal", async () => {
    const wrapper = mountFields({
      photo: { image_base64: "data:image/png;base64,x", copyright_text: null, license_id: null },
    });
    await flushPromises();

    expect(wrapper.find("#new_event_place-name").exists()).toBe(true);
    expect(wrapper.find("#new_event_place-url").exists()).toBe(true);
    expect(wrapper.find("#new_event_place-description").exists()).toBe(true);
    expect(wrapper.find("#new_event_place-photo-copyright_text").exists()).toBe(true);
    expect(wrapper.text()).toContain("Required");
  });

  it("updates the value and checks the name", async () => {
    vi.useFakeTimers();
    GET.mockResolvedValue({ data: { name_taken: true } });
    const wrapper = mountFields();

    await wrapper.find("#new_event_place-name").setValue("Halle");
    await wrapper.find("#new_event_place-description").setValue("Text");
    vi.advanceTimersByTime(300);
    await flushPromises();
    vi.useRealTimers();

    expect(wrapper.props("modelValue")).toMatchObject({ name: "Halle", description: "Text" });
    expect(wrapper.text()).toContain("A place already exists with this name.");
  });
});
