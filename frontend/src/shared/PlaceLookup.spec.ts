import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import PlaceLookup from "./PlaceLookup.vue";

const address = {
  street: "Markt 12",
  postalCode: "38640",
  city: "Goslar",
  state: "Niedersachsen",
  latitude: 51.9,
  longitude: 10.4,
};

function mountLookup() {
  return mount(PlaceLookup, {
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
}

async function search(wrapper: ReturnType<typeof mountLookup>) {
  await wrapper.find("#location-google_place").setValue("Goslar");
  await vi.advanceTimersByTimeAsync(300);
  await flushPromises();
}

describe("PlaceLookup", () => {
  beforeEach(() => {
    GET.mockReset();
    vi.useFakeTimers();
  });

  it("emits the address and the main text of the picked place", async () => {
    GET.mockImplementation(async (path: string) =>
      path === "/bff/manage/places"
        ? {
            data: {
              items: [
                { gmaps_id: "abc", text: "Kaiserpfalz, Goslar, Germany", main_text: "Kaiserpfalz" },
              ],
            },
          }
        : { data: address },
    );
    const wrapper = mountLookup();

    await search(wrapper);
    await wrapper.find("[data-test=option]").trigger("click");
    await flushPromises();

    expect(GET).toHaveBeenCalledWith("/bff/manage/places/{gmaps_id}/address", {
      params: { path: { gmaps_id: "abc" } },
    });
    expect(wrapper.emitted("picked")).toEqual([[{ address, main_text: "Kaiserpfalz" }]]);
  });

  it("emits no main text when Google sends none", async () => {
    GET.mockImplementation(async (path: string) =>
      path === "/bff/manage/places"
        ? { data: { items: [{ gmaps_id: "abc", text: "Goslar" }] } }
        : { data: address },
    );
    const wrapper = mountLookup();

    await search(wrapper);
    await wrapper.find("[data-test=option]").trigger("click");
    await flushPromises();

    expect(wrapper.emitted("picked")).toEqual([[{ address, main_text: null }]]);
  });

  it("reports a failed address lookup", async () => {
    GET.mockImplementation(async (path: string) =>
      path === "/bff/manage/places"
        ? { data: { items: [{ gmaps_id: "abc", text: "Goslar" }] } }
        : { error: {} },
    );
    const wrapper = mountLookup();

    await search(wrapper);
    await wrapper.find("[data-test=option]").trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("Error");
    expect(wrapper.emitted("picked")).toBeUndefined();
  });
});
