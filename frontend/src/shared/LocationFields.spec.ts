import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import LocationFields, { type LocationValue } from "./LocationFields.vue";

const empty: LocationValue = {
  street: "",
  postalCode: "",
  city: "",
  state: "",
  latitude: null,
  longitude: null,
};

function mountFields(modelValue: LocationValue = empty, errors: Record<string, string> = {}) {
  const wrapper: ReturnType<typeof mount> = mount(LocationFields, {
    props: {
      modelValue,
      errors,
      // A real parent feeds the value back; without it every change starts from the original.
      "onUpdate:modelValue": (value: LocationValue) => wrapper.setProps({ modelValue: value }),
    },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  return wrapper;
}

describe("LocationFields", () => {
  beforeEach(() => {
    GET.mockReset();
    vi.useRealTimers();
  });

  it("updates the model per field and parses coordinates", async () => {
    const wrapper = mountFields();

    await wrapper.find("#location-street").setValue("Markt 1");
    await wrapper.find("#location-state").setValue("Niedersachsen");
    await wrapper.find("#location-postalCode").setValue("38640");
    await wrapper.find("#location-city").setValue("Goslar");
    await wrapper.find("#location-latitude").setValue("51.9");
    await wrapper.find("#location-longitude").setValue("");

    expect((wrapper.props() as { modelValue: unknown }).modelValue).toEqual({
      street: "Markt 1",
      state: "Niedersachsen",
      postalCode: "38640",
      city: "Goslar",
      latitude: 51.9,
      longitude: null,
    });
  });

  it("fills the fields from a picked Google place", async () => {
    vi.useFakeTimers();
    const address = {
      street: "Markt 12",
      postalCode: "38640",
      city: "Goslar",
      state: "Niedersachsen",
      latitude: 51.9,
      longitude: 10.4,
    };
    GET.mockImplementation(async (path: string) =>
      path === "/bff/manage/places"
        ? { data: { items: [{ gmaps_id: "abc", text: "Goslar, Germany" }] } }
        : { data: address },
    );
    const wrapper = mountFields();

    await wrapper.find("#location-google_place").setValue("Goslar");
    await vi.advanceTimersByTimeAsync(300);
    await flushPromises();
    await wrapper.find("[data-test=option]").trigger("click");
    await flushPromises();

    expect(GET).toHaveBeenCalledWith("/bff/manage/places/{gmaps_id}/address", {
      params: { path: { gmaps_id: "abc" } },
    });
    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual([address]);
  });

  it("reports a failed address lookup", async () => {
    vi.useFakeTimers();
    GET.mockImplementation(async (path: string) =>
      path === "/bff/manage/places"
        ? { data: { items: [{ gmaps_id: "abc", text: "Goslar" }] } }
        : { error: {} },
    );
    const wrapper = mountFields();

    await wrapper.find("#location-google_place").setValue("Goslar");
    await vi.advanceTimersByTimeAsync(300);
    await flushPromises();
    await wrapper.find("[data-test=option]").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("Error");
    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
  });

  it("works without suggestions", async () => {
    vi.useFakeTimers();
    GET.mockResolvedValue({ error: {} });
    const wrapper = mountFields();

    await wrapper.find("#location-google_place").setValue("x");
    await vi.advanceTimersByTimeAsync(300);
    await flushPromises();

    expect(wrapper.find("[data-test=no-results]").exists()).toBe(true);
  });

  it("shows the errors of the fields", () => {
    const wrapper = mountFields(empty, {
      city: "This field is required.",
      postalCode: "Too long",
      street: "S",
      state: "T",
      latitude: "La",
      longitude: "Lo",
    });

    for (const id of ["city", "postalCode", "street", "state", "latitude", "longitude"]) {
      expect(wrapper.find(`#location-${id}`).classes()).toContain("is-invalid");
    }
    expect(wrapper.text()).toContain("This field is required.");
  });
});
