import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({
  boot: { locale: "en", csrfToken: "x", loginUrl: "/login" },
}));

const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { POST: (...args: unknown[]) => POST(...args) },
}));

const success = vi.fn();
vi.mock("@/shared/notify", () => ({
  useNotify: () => ({ success, error: vi.fn() }),
}));

import ResetTosModal from "./ResetTosModal.vue";

function mountModal() {
  return mount(ResetTosModal, {
    props: { modelValue: true },
    attachTo: document.body,
    global: {
      plugins: [
        createBootstrap(),
        createI18n({ legacy: false, locale: "en", messages: { en: {} } }),
      ],
    },
  });
}

const okButton = () => document.body.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!;

describe("ResetTosModal", () => {
  beforeEach(() => {
    POST.mockReset();
    success.mockReset();
  });
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("posts the reset and toasts", async () => {
    POST.mockResolvedValue({});
    const wrapper = mountModal();
    await flushPromises();

    okButton().click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/admin/settings/reset-tos-accepted");
    expect(success).toHaveBeenCalledWith("Acceptance of terms of service and privacy reset");
    expect(wrapper.emitted("update:modelValue")).toEqual([[false]]);
    wrapper.unmount();
  });

  it("keeps the error inline and stays open when the server rejects", async () => {
    POST.mockResolvedValue({ error: { name: "Forbidden", message: "No way" } });
    const wrapper = mountModal();
    await flushPromises();

    okButton().click();
    await flushPromises();

    expect(document.body.querySelector(".modal .alert-danger")?.textContent).toBe("No way");
    expect(success).not.toHaveBeenCalled();
    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
    wrapper.unmount();
  });
});
