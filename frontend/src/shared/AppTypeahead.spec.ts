import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import AppTypeahead from "./AppTypeahead.vue";

const fetchMock = vi.fn();

function mountTypeahead(props: Record<string, unknown> = {}) {
  const wrapper = mount(AppTypeahead, {
    props: {
      fetch: fetchMock,
      modelValue: null,
      "onUpdate:modelValue": (v: { id: number; name: string } | null) => wrapper.setProps({ modelValue: v }),
      ...props,
    },
    global: { plugins: [createI18n({ legacy: false, locale: "en", messages: { en: {} } })] },
  });
  return wrapper;
}

describe("AppTypeahead", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    fetchMock.mockReset().mockResolvedValue([
      { id: 1, name: "Alpha" },
      { id: 2, name: "Alpine" },
    ]);
  });
  afterEach(() => vi.useRealTimers());

  it("debounces the lookup", async () => {
    const wrapper = mountTypeahead();
    const input = wrapper.find("input");

    await input.setValue("Al");
    await input.setValue("Alp");
    vi.advanceTimersByTime(249);
    expect(fetchMock).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    await flushPromises();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith("Alp");
    expect(wrapper.findAll('[data-test="option"]')).toHaveLength(2);
  });

  it("picks an option with the mouse", async () => {
    const wrapper = mountTypeahead();
    await wrapper.find("input").setValue("Al");
    vi.advanceTimersByTime(250);
    await flushPromises();

    await wrapper.findAll('[data-test="option"]')[1].trigger("click");

    expect(wrapper.props("modelValue")).toEqual({ id: 2, name: "Alpine" });
    expect((wrapper.find("input").element as HTMLInputElement).value).toBe("Alpine");
    expect(wrapper.find('[data-test="option"]').exists()).toBe(false);
  });

  it("picks with the keyboard", async () => {
    const wrapper = mountTypeahead();
    const input = wrapper.find("input");
    await input.setValue("Al");
    vi.advanceTimersByTime(250);
    await flushPromises();

    await input.trigger("keydown", { key: "ArrowDown" });
    await input.trigger("keydown", { key: "Enter" });

    expect(wrapper.props("modelValue")).toEqual({ id: 1, name: "Alpha" });
  });

  it("drops the value when typing and clears with the button", async () => {
    const wrapper = mountTypeahead({ modelValue: { id: 1, name: "Alpha" } });
    expect((wrapper.find("input").element as HTMLInputElement).value).toBe("Alpha");

    await wrapper.find("input").setValue("Alph");
    expect(wrapper.props("modelValue")).toBeNull();

    await wrapper.find('[data-test="clear"]').trigger("click");
    expect((wrapper.find("input").element as HTMLInputElement).value).toBe("");
    expect(wrapper.props("modelValue")).toBeNull();
  });

  it("follows a value set by the parent", async () => {
    const wrapper = mountTypeahead();

    await wrapper.setProps({ modelValue: { id: 3, name: "Gamma" } });
    expect((wrapper.find("input").element as HTMLInputElement).value).toBe("Gamma");

    await wrapper.setProps({ modelValue: null });
    expect((wrapper.find("input").element as HTMLInputElement).value).toBe("");
  });

  it("clears the text when the parent clears a picked value", async () => {
    const wrapper = mountTypeahead();
    await wrapper.find("input").setValue("Al");
    vi.advanceTimersByTime(250);
    await flushPromises();
    await wrapper.findAll('[data-test="option"]')[0].trigger("click");

    await wrapper.setProps({ modelValue: null });

    expect((wrapper.find("input").element as HTMLInputElement).value).toBe("");
  });

  it("shows a hint when nothing was found", async () => {
    fetchMock.mockResolvedValue([]);
    const wrapper = mountTypeahead();
    await wrapper.find("input").setValue("zzz");
    vi.advanceTimersByTime(250);
    await flushPromises();

    expect(wrapper.find('[data-test="no-results"]').exists()).toBe(true);
  });

  it("is disabled without a clear button", () => {
    const wrapper = mountTypeahead({ disabled: true, modelValue: { id: 1, name: "Alpha" } });

    expect(wrapper.find("input").attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-test="clear"]').exists()).toBe(false);
  });
});
