import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, h } from "vue";
import { scrollToTop, trackAnalytics, useWidgetSettings, usePageViewTracking } from "./bridge";

function host<T>(setup: () => T) {
  let result!: T;
  const wrapper = mount(
    defineComponent({
      setup() {
        result = setup();
        return () => h("div");
      },
    }),
  );
  return { wrapper, result };
}

const send = (data: object) =>
  window.dispatchEvent(new CustomEvent("eventcally:settings", { detail: data }));

describe("bridge", () => {
  beforeEach(() => {
    window.__eventcallyWidget = { settings: null, ready: false };
    window.parentIFrame = { sendMessage: vi.fn(), scrollToOffset: vi.fn() };
    window.scrollTo = vi.fn() as unknown as typeof window.scrollTo;
  });
  afterEach(() => {
    delete window.__eventcallyWidget;
    delete window.parentIFrame;
  });

  describe("useWidgetSettings", () => {
    it("is null until settings arrive, then merges later messages key by key", () => {
      const { wrapper, result } = host(() => useWidgetSettings<{ a: number; b: number }>());
      expect(result.value).toBeNull();

      send({ a: 1, b: 2 });
      expect(result.value).toEqual({ a: 1, b: 2 });

      send({ b: 3 });
      expect(result.value).toEqual({ a: 1, b: 3 });
      wrapper.unmount();
    });

    it("starts from the settings buffered before the app mounted", () => {
      window.__eventcallyWidget = { settings: { a: 1 }, ready: false };
      const { result } = host(() => useWidgetSettings<{ a: number }>());

      expect(result.value).toEqual({ a: 1 });
    });

    it("stops listening after unmount", () => {
      const { wrapper, result } = host(() => useWidgetSettings<{ a: number }>());
      wrapper.unmount();
      send({ a: 1 });

      expect(result.value).toBeNull();
    });
  });

  describe("trackAnalytics", () => {
    it("sends the analytics message to the parent", () => {
      trackAnalytics({ event: "linkClick", url: "http://x/eventdate/1" });

      expect(window.parentIFrame!.sendMessage).toHaveBeenCalledWith({
        type: "EVENTCALLY_ANALYTICS_EVENT",
        data: { event: "linkClick", url: "http://x/eventdate/1" },
      });
    });

    it("does nothing outside an iframe", () => {
      delete window.parentIFrame;
      expect(() => trackAnalytics({ event: "linkClick", url: "x" })).not.toThrow();
    });
  });

  it("scrolls the page and the parent to the top", () => {
    scrollToTop();

    expect(window.scrollTo).toHaveBeenCalledWith(0, 0);
    expect(window.parentIFrame!.scrollToOffset).toHaveBeenCalledWith(0, 0);
  });

  describe("usePageViewTracking", () => {
    it("reports once when the widget is already ready at mount", () => {
      window.__eventcallyWidget!.ready = true;
      host(() => usePageViewTracking());

      expect(window.parentIFrame!.sendMessage).toHaveBeenCalledTimes(1);
      expect(window.parentIFrame!.sendMessage).toHaveBeenCalledWith({
        type: "EVENTCALLY_ANALYTICS_EVENT",
        data: { event: "pageView", url: document.location.href },
      });
    });

    it("reports the URL it is given", () => {
      window.__eventcallyWidget!.ready = true;
      host(() => usePageViewTracking(() => "http://x/p?"));

      expect(window.parentIFrame!.sendMessage).toHaveBeenCalledWith({
        type: "EVENTCALLY_ANALYTICS_EVENT",
        data: { event: "pageView", url: "http://x/p?" },
      });
    });

    it("waits for the ready event and reports only once", () => {
      host(() => usePageViewTracking());
      expect(window.parentIFrame!.sendMessage).not.toHaveBeenCalled();

      window.__eventcallyWidget!.ready = true;
      window.dispatchEvent(new CustomEvent("eventcally:ready"));
      window.dispatchEvent(new CustomEvent("eventcally:ready"));

      expect(window.parentIFrame!.sendMessage).toHaveBeenCalledTimes(1);
    });
  });
});
