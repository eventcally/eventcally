import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";
import { defaultSettings } from "@/shared/customWidget";
import CustomWidgetPreview from "./CustomWidgetPreview.vue";

const sendMessage = vi.fn();
const resize = vi.fn();
const removeListeners = vi.fn();
const iFrameResize = vi.fn();

beforeEach(() => {
  [sendMessage, resize, removeListeners, iFrameResize].forEach((f) => f.mockReset());
  iFrameResize.mockImplementation((_options, el: HTMLIFrameElement) => {
    el.iFrameResizer = { sendMessage, resize, removeListeners };
    return [];
  });
  window.iFrameResize = iFrameResize;
});
afterEach(() => {
  delete window.iFrameResize;
});

async function mountPreview(props = {}) {
  const wrapper = mount(CustomWidgetPreview, {
    props: { type: "search", settings: defaultSettings("search", 1), size: "100%", ...props },
  });
  await nextTick();
  await nextTick();
  return wrapper;
}

describe("CustomWidgetPreview", () => {
  it("loads the widget page and initialises iframeResizer with the size options", async () => {
    const wrapper = await mountPreview();

    expect(wrapper.find("iframe").attributes("src")).toBe("/custom_widget/search");
    expect(iFrameResize).toHaveBeenCalledTimes(1);
    expect(iFrameResize.mock.calls[0][0]).toMatchObject({
      autoResize: true,
      minHeight: 400,
      maxHeight: "Infinity",
      scrolling: "omit",
    });
  });

  it("does not send before the iframe is initialised", async () => {
    const wrapper = await mountPreview();
    await wrapper.setProps({ settings: { ...defaultSettings("search", 1), linkColor: "#123456" } });
    await nextTick();

    expect(sendMessage).not.toHaveBeenCalled();
  });

  it("sends the settings once the iframe is initialised", async () => {
    await mountPreview();
    iFrameResize.mock.calls[0][0].onInit();

    expect(sendMessage).toHaveBeenCalledWith({
      type: "EVENTCALLY_WIDGET_SETTINGS_UPDATE_EVENT",
      data: expect.objectContaining({ layout: "card", organizationId: 1 }),
    });
  });

  it("sends changed settings live without remounting", async () => {
    const wrapper = await mountPreview();
    iFrameResize.mock.calls[0][0].onInit();
    const settings = { ...defaultSettings("search", 1), linkColor: "#123456" };
    await wrapper.setProps({ settings });
    await nextTick();

    expect(sendMessage).toHaveBeenLastCalledWith({
      type: "EVENTCALLY_WIDGET_SETTINGS_UPDATE_EVENT",
      data: expect.objectContaining({ linkColor: "#123456" }),
    });
    expect(iFrameResize).toHaveBeenCalledTimes(1);
  });

  it("remounts the iframe when a size option changes", async () => {
    const wrapper = await mountPreview();
    const first = wrapper.find("iframe").element;
    await wrapper.setProps({ settings: { ...defaultSettings("search", 1), iFrameMinHeight: 600 } });
    await nextTick();
    await nextTick();

    expect(removeListeners).toHaveBeenCalled();
    expect(iFrameResize).toHaveBeenCalledTimes(2);
    expect(iFrameResize.mock.calls[1][0].minHeight).toBe(600);
    expect(wrapper.find("iframe").element).not.toBe(first);
  });

  it("never sends through a torn-down iframe while the type changes", async () => {
    const wrapper = await mountPreview();
    iFrameResize.mock.calls[0][0].onInit();
    sendMessage.mockClear();
    // iframeResizer throws once its listeners are removed.
    removeListeners.mockImplementation(() => {
      sendMessage.mockImplementation(() => {
        throw new TypeError("torn down");
      });
    });

    await wrapper.setProps({ type: "calendar", settings: defaultSettings("calendar", 1) });
    await nextTick();
    await nextTick();

    expect(sendMessage).not.toHaveBeenCalled();
  });

  it("remounts for another widget type", async () => {
    const wrapper = await mountPreview();
    await wrapper.setProps({ type: "calendar", settings: defaultSettings("calendar", 1) });
    await nextTick();
    await nextTick();

    expect(wrapper.find("iframe").attributes("src")).toBe("/custom_widget/calendar");
    expect(iFrameResize).toHaveBeenCalledTimes(2);
  });

  it("resizes when the preview size changes and cleans up on unmount", async () => {
    const wrapper = await mountPreview();
    await wrapper.setProps({ size: "400px" });
    await nextTick();
    expect(resize).toHaveBeenCalled();

    removeListeners.mockClear();
    wrapper.unmount();
    expect(removeListeners).toHaveBeenCalled();
  });
});
