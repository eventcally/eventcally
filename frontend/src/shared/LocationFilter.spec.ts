import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import LocationFilter from "./LocationFilter.vue";

const distances = [
  { value: 500, label: "500 m" },
  { value: 5000, label: "5 km" },
];

function mountFilter(props: Record<string, unknown> = {}) {
  const wrapper = mount(LocationFilter, {
    props: {
      distances,
      coordinate: "",
      name: "",
      distance: null,
      "onUpdate:coordinate": (v: string) => wrapper.setProps({ coordinate: v }),
      "onUpdate:name": (v: string) => wrapper.setProps({ name: v }),
      "onUpdate:distance": (v: number | null) => wrapper.setProps({ distance: v }),
      ...props,
    },
    global: {
      plugins: [createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  return wrapper;
}

describe("LocationFilter public scope", () => {
  it("uses the anonymous place routes", async () => {
    vi.useFakeTimers();
    GET.mockReset().mockImplementation((path: string) =>
      Promise.resolve(
        path === "/bff/public/places"
          ? { data: { items: [{ gmaps_id: "abc", text: "Goslar, Germany" }] } }
          : { data: { latitude: 51.9, longitude: 10.4 } },
      ),
    );
    const wrapper = mountFilter({ scope: "public" });
    await wrapper.find("input").setValue("Gosl");
    vi.advanceTimersByTime(250);
    await flushPromises();
    expect(GET).toHaveBeenCalledWith("/bff/public/places", { params: { query: { keyword: "Gosl" } } });

    await wrapper.find('[data-test="suggestion"]').trigger("click");
    await flushPromises();

    expect(GET).toHaveBeenLastCalledWith("/bff/public/places/{gmaps_id}/coordinate", {
      params: { path: { gmaps_id: "abc" } },
    });
    expect(wrapper.props("coordinate")).toBe("51.9,10.4");
    vi.useRealTimers();
  });
});

describe("LocationFilter", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    GET.mockReset().mockImplementation((path: string) =>
      Promise.resolve(
        path === "/bff/manage/places"
          ? { data: { items: [{ gmaps_id: "abc", text: "Goslar, Germany", main_text: "Goslar" }] } }
          : { data: { latitude: 51.9, longitude: 10.4 } },
      ),
    );
  });

  afterEach(() => {
    vi.useRealTimers();
    Reflect.deleteProperty(navigator, "geolocation");
  });

  it("debounces the suggestion lookup", async () => {
    const wrapper = mountFilter();
    const input = wrapper.find("input");

    await input.setValue("Gos");
    await input.setValue("Gosl");
    vi.advanceTimersByTime(249);
    expect(GET).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    await flushPromises();

    expect(GET).toHaveBeenCalledTimes(1);
    expect(GET).toHaveBeenCalledWith("/bff/manage/places", { params: { query: { keyword: "Gosl" } } });
    expect(wrapper.findAll('[data-test="suggestion"]')).toHaveLength(1);
  });

  it("looks up the coordinate of the picked suggestion", async () => {
    const wrapper = mountFilter();
    await wrapper.find("input").setValue("Gosl");
    vi.advanceTimersByTime(250);
    await flushPromises();

    await wrapper.find('[data-test="suggestion"]').trigger("click");
    await flushPromises();

    expect(GET).toHaveBeenLastCalledWith("/bff/manage/places/{gmaps_id}/coordinate", {
      params: { path: { gmaps_id: "abc" } },
    });
    expect(wrapper.props("coordinate")).toBe("51.9,10.4");
    expect(wrapper.props("name")).toBe("Goslar, Germany");
    expect(wrapper.find("select").attributes("disabled")).toBeUndefined();
  });

  it("picks with the keyboard", async () => {
    const wrapper = mountFilter();
    const input = wrapper.find("input");
    await input.setValue("Gosl");
    vi.advanceTimersByTime(250);
    await flushPromises();

    await input.trigger("keydown", { key: "ArrowDown" });
    await input.trigger("keydown", { key: "Enter" });
    await flushPromises();

    expect(wrapper.props("coordinate")).toBe("51.9,10.4");
  });

  it("shows a hint when nothing was found", async () => {
    GET.mockResolvedValue({ data: { items: [] } });
    const wrapper = mountFilter();
    await wrapper.find("input").setValue("zzz");
    vi.advanceTimersByTime(250);
    await flushPromises();

    expect(wrapper.find('[data-test="no-results"]').exists()).toBe(true);
  });

  it("disables the distance without a coordinate and clears everything", async () => {
    const wrapper = mountFilter({ coordinate: "1,2", name: "Somewhere", distance: 500 });
    expect(wrapper.find("select").attributes("disabled")).toBeUndefined();

    await wrapper.find('[data-test="clear"]').trigger("click");

    expect(wrapper.props("coordinate")).toBe("");
    expect(wrapper.props("name")).toBe("");
    expect(wrapper.props("distance")).toBeNull();
    expect(wrapper.find("select").attributes("disabled")).toBeDefined();
  });

  it("uses the browser location", async () => {
    Object.defineProperty(navigator, "geolocation", {
      configurable: true,
      value: {
        getCurrentPosition: (ok: (p: unknown) => void) =>
          ok({ coords: { latitude: 52.1, longitude: 9.9 } }),
      },
    });
    const wrapper = mountFilter();

    await wrapper.find('[data-test="locate"]').trigger("click");

    expect(wrapper.props("coordinate")).toBe("52.1,9.9");
    expect(wrapper.props("name")).toBe("Current location");
  });

  it("hides the location button without geolocation support", () => {
    expect(mountFilter().find('[data-test="locate"]').exists()).toBe(false);
  });
});
