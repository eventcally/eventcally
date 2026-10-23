import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

// jsdom has no canvas: the real crop is covered by the e2e suite.
const state = vi.hoisted(() => ({
  options: {} as Record<string, (...args: unknown[]) => void>,
  imageData: { naturalWidth: 600, naturalHeight: 500 },
  instance: null as null | Record<string, ReturnType<typeof vi.fn>>,
}));

vi.mock("cropperjs/dist/cropper.css", () => ({}));
vi.mock("cropperjs", () => ({
  default: class {
    constructor(_el: unknown, options: Record<string, (...args: unknown[]) => void>) {
      state.options = options;
      state.instance = {
        getImageData: vi.fn(() => state.imageData),
        getCroppedCanvas: vi.fn(() => ({ toDataURL: (mime: string) => `data:${mime};cropped` })),
        setData: vi.fn(),
        zoom: vi.fn(),
        rotate: vi.fn(),
        destroy: vi.fn(),
      };
      return state.instance as unknown as object;
    }
  },
}));

import ImageCropper from "./ImageCropper.vue";

async function mountCropper(props: Record<string, unknown> = {}) {
  const wrapper = mount(ImageCropper, {
    props: { src: "data:image/png;base64,AAAA", show: true, ...props },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({
        legacy: false,
        locale: "en",
        messages: {
          en: {
            "The resolution is too low. At least %(width)sx%(height)spx.":
              "The resolution is too low. At least {width}x{height}px.",
          },
        },
      })],
    },
  });
  await flushPromises();
  // BModal emits `shown` after its transition, which jsdom does not run.
  wrapper.findComponent({ name: "BModal" }).vm.$emit("shown");
  await flushPromises();
  return wrapper;
}

function click(selector: string) {
  (document.body.querySelector(selector) as HTMLElement).click();
}

describe("ImageCropper", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    state.imageData = { naturalWidth: 600, naturalHeight: 500 };
  });

  it("emits the cropped data URI in the given mime type", async () => {
    const wrapper = await mountCropper({ mimeType: "image/jpeg" });

    wrapper.findComponent({ name: "BModal" }).vm.$emit("ok", { preventDefault() {} });

    expect(wrapper.emitted("cropped")?.[0]).toEqual(["data:image/jpeg;cropped"]);
  });

  it("rejects a source below the minimum resolution and closes", async () => {
    state.imageData = { naturalWidth: 100, naturalHeight: 500 };
    const wrapper = await mountCropper();

    state.options.ready();
    await flushPromises();

    expect(wrapper.emitted("error")?.[0][0]).toBe("The resolution is too low. At least 320x320px.");
    expect(wrapper.emitted("update:show")?.[0]).toEqual([false]);
  });

  it("accepts a source of the minimum resolution", async () => {
    state.imageData = { naturalWidth: 320, naturalHeight: 320 };
    const wrapper = await mountCropper();

    state.options.ready();

    expect(wrapper.emitted("error")).toBeUndefined();
  });

  it("keeps the crop box at the minimum size", async () => {
    await mountCropper();

    state.options.crop({ detail: { width: 100, height: 500 } });
    expect(state.instance?.setData).toHaveBeenCalledWith({ width: 320, height: 500 });

    state.instance?.setData.mockClear();
    state.options.crop({ detail: { width: 400, height: 400 } });
    expect(state.instance?.setData).not.toHaveBeenCalled();
  });

  it("zooms and rotates", async () => {
    await mountCropper();

    click("[data-test=zoom-in]");
    click("[data-test=zoom-out]");
    click("[data-test=rotate-left]");
    click("[data-test=rotate-right]");

    expect(state.instance?.zoom).toHaveBeenNthCalledWith(1, 0.1);
    expect(state.instance?.zoom).toHaveBeenNthCalledWith(2, -0.1);
    expect(state.instance?.rotate).toHaveBeenNthCalledWith(1, -90);
    expect(state.instance?.rotate).toHaveBeenNthCalledWith(2, 90);
  });

  it("destroys the cropper when the dialog is hidden", async () => {
    const wrapper = await mountCropper();

    wrapper.findComponent({ name: "BModal" }).vm.$emit("hidden");

    expect(state.instance?.destroy).toHaveBeenCalled();
  });
});
