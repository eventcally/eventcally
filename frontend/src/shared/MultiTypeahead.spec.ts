import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import MultiTypeahead from "./MultiTypeahead.vue";

type Option = { id: number; name: string };
const fetchMock = vi.fn();

function mountMulti(modelValue: Option[] = []) {
  const wrapper = mount(MultiTypeahead, {
    props: {
      fetch: fetchMock,
      modelValue,
      inputId: "multi",
      "onUpdate:modelValue": (v: Option[]) => wrapper.setProps({ modelValue: v }),
    },
    global: { plugins: [createI18n({ legacy: false, locale: "en", messages: { en: {} } })] },
  });
  return wrapper;
}

async function search(wrapper: ReturnType<typeof mountMulti>, keyword: string) {
  await wrapper.find("#multi").setValue(keyword);
  vi.advanceTimersByTime(250);
  await flushPromises();
}

describe("MultiTypeahead", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    fetchMock.mockReset().mockResolvedValue([
      { id: 1, name: "Alpha" },
      { id: 2, name: "Alpine" },
    ]);
  });
  afterEach(() => vi.useRealTimers());

  it("adds a pick as a chip and clears the input", async () => {
    const wrapper = mountMulti();
    await search(wrapper, "Al");

    await wrapper.findAll('[data-test="option"]')[1].trigger("click");

    expect(wrapper.props("modelValue")).toEqual([{ id: 2, name: "Alpine" }]);
    expect(wrapper.findAll('[data-test="chip"]').map((c) => c.text())).toEqual(["Alpine"]);
    expect((wrapper.find("#multi").element as HTMLInputElement).value).toBe("");
  });

  it("offers only unselected options", async () => {
    const wrapper = mountMulti([{ id: 1, name: "Alpha" }]);
    await search(wrapper, "Al");

    expect(wrapper.findAll('[data-test="option"]').map((o) => o.text())).toEqual(["Alpine"]);
  });

  it("removes a chip", async () => {
    const wrapper = mountMulti([
      { id: 1, name: "Alpha" },
      { id: 2, name: "Alpine" },
    ]);

    await wrapper.findAll('[data-test="remove"]')[0].trigger("click");

    expect(wrapper.props("modelValue")).toEqual([{ id: 2, name: "Alpine" }]);
  });

  it("skips duplicates", async () => {
    fetchMock.mockResolvedValue([{ id: 1, name: "Alpha" }]);
    const wrapper = mountMulti();
    await search(wrapper, "Al");
    await wrapper.find('[data-test="option"]').trigger("click");
    // The lookup answered before the first pick landed.
    fetchMock.mockResolvedValue([{ id: 1, name: "Alpha" }]);
    const typeahead = wrapper.findComponent({ name: "AppTypeahead" });
    typeahead.vm.$emit("update:modelValue", { id: 1, name: "Alpha" });
    typeahead.vm.$emit("update:modelValue", null);
    await flushPromises();

    expect(wrapper.props("modelValue")).toEqual([{ id: 1, name: "Alpha" }]);
  });
});
