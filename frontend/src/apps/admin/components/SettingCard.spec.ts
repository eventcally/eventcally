import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

const success = vi.fn();
vi.mock("@/shared/notify", () => ({
  useNotify: () => ({ success, error: vi.fn() }),
}));

import SettingCard from "./SettingCard.vue";

function mountCard(props: Record<string, unknown> = {}) {
  return mount(SettingCard, {
    props: {
      label: "Legal notice",
      inputId: "s",
      value: null,
      save: vi.fn(),
      ...props,
    },
    slots: { help: '<p class="help">Example</p>' },
    global: {
      plugins: [
        createBootstrap(),
        createI18n({ legacy: false, locale: "en", messages: { en: {} } }),
      ],
    },
  });
}

const editButton = (w: ReturnType<typeof mountCard>) =>
  w.findAll("button").find((b) => b.text() === "Edit")!;

describe("SettingCard", () => {
  beforeEach(() => success.mockReset());

  it("shows a plain-text preview without rendering the HTML", () => {
    const wrapper = mountCard({
      value: "<p>Hello <b>world</b></p><script>x()</script>",
    });

    expect(wrapper.text()).toContain("Hello world");
    expect(wrapper.find("b").exists()).toBe(false);
    expect(wrapper.find("script").exists()).toBe(false);
  });

  it("separates block elements in the preview", () => {
    const wrapper = mountCard({ value: "<h2>Impressum</h2><p>Musterstraße 1</p>" });

    expect(wrapper.find(".setting-preview").text()).toBe("Impressum Musterstraße 1");
  });

  it("truncates long previews", () => {
    const wrapper = mountCard({ value: "a".repeat(300) });

    expect(wrapper.find(".setting-preview").text()).toBe(`${"a".repeat(200)}…`);
  });

  it("shows 'Not specified' when empty", () => {
    expect(mountCard().text()).toContain("Not specified");
  });

  it("renders the help slot only while editing", async () => {
    const wrapper = mountCard();
    expect(wrapper.find(".help").exists()).toBe(false);

    await editButton(wrapper).trigger("click");

    expect(wrapper.find(".help").exists()).toBe(true);
  });

  it("saves the draft, closes, emits saved and toasts", async () => {
    const save = vi.fn().mockResolvedValue("Impressum");
    const wrapper = mountCard({ save });

    await editButton(wrapper).trigger("click");
    await wrapper.find("textarea").setValue("Impressum");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(save).toHaveBeenCalledWith("Impressum");
    expect(wrapper.emitted("saved")).toEqual([["Impressum"]]);
    expect(success).toHaveBeenCalledWith("Settings successfully updated");
    expect(wrapper.find("textarea").exists()).toBe(false);
  });

  it("saves a blank draft as null", async () => {
    const save = vi.fn().mockResolvedValue(null);
    const wrapper = mountCard({ save, value: "old" });

    await editButton(wrapper).trigger("click");
    await wrapper.find("textarea").setValue("   ");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(save).toHaveBeenCalledWith(null);
  });

  it("keeps the editor open and shows the message when saving fails", async () => {
    const save = vi.fn().mockRejectedValue(new Error("Bad JSON"));
    const wrapper = mountCard({ save });

    await editButton(wrapper).trigger("click");
    await wrapper.find("textarea").setValue("{");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Bad JSON");
    expect(wrapper.find("textarea").exists()).toBe(true);
    expect(success).not.toHaveBeenCalled();
    expect(wrapper.emitted("saved")).toBeUndefined();
  });

  it("discards the draft on cancel", async () => {
    const save = vi.fn();
    const wrapper = mountCard({ save, value: "old" });

    await editButton(wrapper).trigger("click");
    await wrapper.find("textarea").setValue("new");
    await wrapper
      .findAll("button")
      .find((b) => b.text() === "Cancel")!
      .trigger("click");

    expect(save).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain("old");
    await editButton(wrapper).trigger("click");
    expect(wrapper.find<HTMLTextAreaElement>("textarea").element.value).toBe("old");
  });
});
