import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";
import { createI18n } from "vue-i18n";
import type { EventOrganizerFormValue } from "../eventOrganizerForm";
import { emptyLocation } from "../eventPlaceForm";

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
vi.mock("@/shared/ImageCropper.vue", () => ({
  __esModule: true,
  default: defineComponent({ name: "ImageCropper", render: () => null }),
}));

import EventOrganizerFormFields from "./EventOrganizerFormFields.vue";

function mountFields(form: Partial<EventOrganizerFormValue> = {}) {
  const wrapper = mount(EventOrganizerFormFields, {
    props: {
      organizationId: 5,
      licenses: [],
      idPrefix: "new_organizer-",
      modelValue: {
        name: "",
        url: "",
        email: "",
        phone: "",
        fax: "",
        location: emptyLocation(),
        logo: null,
        ...form,
      },
      errors: { email: "Invalid" },
      "onUpdate:modelValue": (v: EventOrganizerFormValue) => wrapper.setProps({ modelValue: v }),
    },
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  return wrapper;
}

describe("EventOrganizerFormFields", () => {
  it("prefixes the input ids for a modal", async () => {
    const wrapper = mountFields({
      logo: { image_base64: "data:image/png;base64,x", copyright_text: null, license_id: null },
    });
    await flushPromises();

    for (const field of ["name", "url", "email", "phone", "fax", "logo-copyright_text"]) {
      expect(wrapper.find(`#new_organizer-${field}`).exists()).toBe(true);
    }
    expect(wrapper.text()).toContain("Invalid");
  });

  it("updates the value and marks a free name", async () => {
    vi.useFakeTimers();
    GET.mockResolvedValue({ data: { name_taken: false } });
    const wrapper = mountFields();

    await wrapper.find("#new_organizer-name").setValue("Verein");
    await wrapper.find("#new_organizer-phone").setValue("123");
    vi.advanceTimersByTime(300);
    await flushPromises();
    vi.useRealTimers();

    expect(wrapper.props("modelValue")).toMatchObject({ name: "Verein", phone: "123" });
    expect(wrapper.find("#new_organizer-name").classes()).toContain("is-valid");
  });
});
