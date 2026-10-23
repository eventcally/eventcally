import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { describe, expect, it, vi } from "vitest";
import { defineComponent, h } from "vue";
import { createI18n } from "vue-i18n";

// The cropper itself is covered by its own spec.
vi.mock("./ImageCropper.vue", () => ({
  __esModule: true,
  default: defineComponent({
    name: "ImageCropper",
    props: ["show", "src", "mimeType", "minWidth", "minHeight"],
    emits: ["cropped", "error", "update:show"],
    setup: (props) => () =>
      h("div", { class: "cropper-stub", "data-show": String(props.show), "data-src": props.src, "data-mime": props.mimeType }),
  }),
}));

import ImageField from "./ImageField.vue";

const licenses = [{ id: 1, name: "CC0 (Zero)" }];

function mountField(props: Record<string, unknown> = {}) {
  const wrapper: ReturnType<typeof mount> = mount(ImageField, {
    props: {
      licenses,
      modelValue: null,
      preview: null,
      // A real parent feeds the values back.
      "onUpdate:modelValue": (value: unknown) => wrapper.setProps({ modelValue: value }),
      "onUpdate:preview": (value: unknown) => wrapper.setProps({ preview: value }),
      ...props,
    },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  return wrapper;
}

/** The cropper is a lazy chunk: wait until it is rendered. */
async function cropper(wrapper: ReturnType<typeof mountField>) {
  await vi.waitFor(() => expect(wrapper.find(".cropper-stub").exists()).toBe(true));
  return wrapper.findComponent({ name: "ImageCropper" });
}

function pickFile(wrapper: ReturnType<typeof mountField>, file: File) {
  const input = wrapper.find("[data-test=file]").element as HTMLInputElement;
  Object.defineProperty(input, "files", { value: [file], configurable: true });
  return wrapper.find("[data-test=file]").trigger("change");
}

describe("ImageField", () => {
  it("shows the dropzone without an image", () => {
    const wrapper = mountField();

    expect(wrapper.find("[data-test=dropzone]").exists()).toBe(true);
    expect(wrapper.find("[data-test=preview]").exists()).toBe(false);
    expect(wrapper.find("#logo-copyright_text").exists()).toBe(false);
  });

  it("opens the cropper with the chosen file", async () => {
    const wrapper = mountField();

    await pickFile(wrapper, new File(["x"], "logo.png", { type: "image/png" }));
    await cropper(wrapper);
    await vi.waitFor(() => expect(wrapper.find(".cropper-stub").attributes("data-show")).toBe("true"));

    expect(wrapper.find(".cropper-stub").attributes("data-mime")).toBe("image/png");
    expect(wrapper.find(".cropper-stub").attributes("data-src")).toMatch(/^data:image\/png/);
  });

  it("rejects a file that is no image", async () => {
    const wrapper = mountField();

    await pickFile(wrapper, new File(["x"], "doc.txt", { type: "text/plain" }));

    expect(wrapper.find("[data-test=image-error]").text()).toBe("Please choose an image file.");
  });

  it("takes a dropped file", async () => {
    const wrapper = mountField();

    await wrapper.find("[data-test=dropzone]").trigger("drop", {
      dataTransfer: { files: [new File(["x"], "logo.png", { type: "image/png" })] },
    });
    await vi.waitFor(() => expect(wrapper.find(".cropper-stub").attributes("data-show")).toBe("true"));
  });

  it("stores the cropped image and keeps the copyright and license", async () => {
    const wrapper = mountField();

    (await cropper(wrapper)).vm.$emit("cropped", "data:image/png;base64,CROP");
    await flushPromises();

    expect(wrapper.emitted("update:preview")?.[0]).toEqual(["data:image/png;base64,CROP"]);
    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual([
      { image_base64: "data:image/png;base64,CROP", copyright_text: null, license_id: null },
    ]);
  });

  it("edits the copyright text and the license of a stored image", async () => {
    const stored = { image_base64: null, copyright_text: "Me", license_id: null };
    const wrapper = mountField({ modelValue: stored, preview: "data:image/jpeg;base64,AAAA" });

    expect(wrapper.find("[data-test=preview]").attributes("src")).toBe("data:image/jpeg;base64,AAAA");
    await wrapper.find("#logo-copyright_text").setValue("You");
    expect((wrapper.props() as { modelValue: unknown }).modelValue).toMatchObject({ copyright_text: "You" });
    await wrapper.find("#logo-license").setValue("1");
    await wrapper.find("#logo-copyright_text").setValue("");

    expect((wrapper.props() as { modelValue: unknown }).modelValue).toEqual({
      image_base64: null,
      copyright_text: null,
      license_id: 1,
    });
  });

  it("re-opens the cropper for the preview with its mime type", async () => {
    const wrapper = mountField({
      modelValue: { image_base64: null, copyright_text: "Me", license_id: null },
      preview: "data:image/jpeg;base64,AAAA",
    });

    await wrapper.find("[data-test=edit]").trigger("click");
    await cropper(wrapper);

    expect(wrapper.find(".cropper-stub").attributes("data-mime")).toBe("image/jpeg");
    expect(wrapper.find(".cropper-stub").attributes("data-show")).toBe("true");
  });

  it("removes the image", async () => {
    const wrapper = mountField({
      modelValue: { image_base64: null, copyright_text: "Me", license_id: null },
      preview: "data:image/png;base64,AAAA",
    });

    await wrapper.find("[data-test=remove]").trigger("click");

    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual([null]);
    expect(wrapper.emitted("update:preview")?.[0]).toEqual([null]);
  });

  it("shows the errors of the sub-fields", () => {
    const wrapper = mountField({
      modelValue: { image_base64: "data:x", copyright_text: "", license_id: null },
      preview: "data:image/png;base64,AAAA",
      errors: { image_base64: "Too small", copyright_text: "This field is required." },
    });

    expect(wrapper.find("[data-test=image-error]").text()).toBe("Too small");
    expect(wrapper.text()).toContain("This field is required.");
  });
});
