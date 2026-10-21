import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import TypeToConfirmModal from "./TypeToConfirmModal.vue";

function mountModal(confirm: (input: string) => Promise<void>, subject: string | null = "Alpha Crew") {
  return mount(TypeToConfirmModal, {
    props: { title: "T", okTitle: "Go", subject, label: "Name", inputId: "x-input", confirm, modelValue: true },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
}

const okButton = () => document.body.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!;

async function type(value: string) {
  const input = document.body.querySelector<HTMLInputElement>("#x-input")!;
  input.value = value;
  input.dispatchEvent(new Event("input"));
  await flushPromises();
}

describe("TypeToConfirmModal", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("enables OK only for a trimmed, case-insensitive match", async () => {
    const wrapper = mountModal(vi.fn());
    await flushPromises();

    expect(okButton().disabled).toBe(true);
    await type("alpha");
    expect(okButton().disabled).toBe(true);
    await type("  ALPHA crew ");
    expect(okButton().disabled).toBe(false);
    wrapper.unmount();
  });

  it("keeps OK disabled without a subject", async () => {
    const wrapper = mountModal(vi.fn(), null);
    await flushPromises();
    await type("");

    expect(okButton().disabled).toBe(true);
    wrapper.unmount();
  });

  it("confirms with the trimmed input and emits done", async () => {
    const confirm = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountModal(confirm);
    await flushPromises();
    await type(" alpha crew ");

    okButton().click();
    await flushPromises();

    expect(confirm).toHaveBeenCalledWith("alpha crew");
    expect(wrapper.emitted("done")).toHaveLength(1);
    wrapper.unmount();
  });

  it("shows the thrown message inline and does not emit done", async () => {
    const wrapper = mountModal(vi.fn().mockRejectedValue(new Error("Nope")));
    await flushPromises();
    await type("Alpha Crew");

    okButton().click();
    await flushPromises();

    expect(document.body.querySelector(".modal .alert-danger")?.textContent).toBe("Nope");
    expect(wrapper.emitted("done")).toBeUndefined();
    wrapper.unmount();
  });
});
