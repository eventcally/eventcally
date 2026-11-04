import { mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import ConfirmModal from "./ConfirmModal.vue";

const mountModal = (props: Record<string, unknown>) =>
  mount(ConfirmModal, {
    props: { modelValue: true, title: "Delete place", instruction: "Really?", ...props },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: { Cancel: "Cancel" } } })],
    },
  });

describe("ConfirmModal", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("confirms with a plain danger button", async () => {
    const wrapper = mountModal({ confirmTitle: "Delete" });
    await flushPromises();

    expect(document.body.textContent).toContain("Really?");
    const ok = document.querySelector<HTMLButtonElement>(".modal-footer .btn-danger");
    expect(ok?.textContent?.trim()).toBe("Delete");
    ok?.click();
    await flushPromises();

    expect(wrapper.emitted("submit")).toEqual([[undefined]]);
  });

  it("asks for the name and shows the errors", async () => {
    const wrapper = mountModal({
      confirmLabel: "Name",
      error: "Kaputt",
      nameError: "Does not match",
    });
    await flushPromises();

    expect(document.querySelector(".modal-footer")).toBeNull();
    expect(document.querySelector("[data-test=confirm-error]")?.textContent).toContain("Kaputt");
    expect(document.querySelector("[data-test=field-error]")?.textContent).toBe("Does not match");

    const input = document.querySelector<HTMLInputElement>("#name");
    input!.value = "Rathaus";
    input!.dispatchEvent(new Event("input"));
    document
      .querySelector("form")!
      .dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
    await flushPromises();

    expect(wrapper.emitted("submit")).toEqual([["Rathaus"]]);
  });
});
