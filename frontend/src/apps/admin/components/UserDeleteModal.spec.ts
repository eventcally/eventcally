import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const DELETE = vi.fn();
vi.mock("@/shared/api", () => ({ api: { DELETE: (...args: unknown[]) => DELETE(...args) } }));

const success = vi.fn();
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import UserDeleteModal from "./UserDeleteModal.vue";

const user = { id: 7, email: "Other@Test.de" };

function mountModal() {
  return mount(UserDeleteModal, {
    props: { user, modelValue: true },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
}

const okButton = () => document.body.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!;
const emailInput = () => document.body.querySelector<HTMLInputElement>("#delete-user-email")!;

async function type(value: string) {
  emailInput().value = value;
  emailInput().dispatchEvent(new Event("input"));
  await flushPromises();
}

describe("UserDeleteModal", () => {
  beforeEach(() => {
    DELETE.mockReset();
    success.mockReset();
  });
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("enables OK only when the typed email matches, ignoring case", async () => {
    const wrapper = mountModal();
    await flushPromises();

    expect(okButton().disabled).toBe(true);
    await type("nope@test.de");
    expect(okButton().disabled).toBe(true);
    await type("  other@test.DE ");
    expect(okButton().disabled).toBe(false);
    wrapper.unmount();
  });

  it("deletes, notifies and emits deleted", async () => {
    DELETE.mockResolvedValue({});
    const wrapper = mountModal();
    await flushPromises();
    await type("other@test.de");

    okButton().click();
    await flushPromises();

    expect(DELETE).toHaveBeenCalledWith("/bff/admin/users/{id}", {
      params: { path: { id: 7 } },
      body: { email: "other@test.de" },
    });
    expect(success).toHaveBeenCalledWith("User successfully deleted");
    expect(wrapper.emitted("deleted")).toHaveLength(1);
    wrapper.unmount();
  });

  it("shows the field error and does not emit when the server rejects", async () => {
    DELETE.mockResolvedValue({
      error: { name: "Unprocessable Entity", message: "m", errors: [{ loc: ["email"], msg: "No match" }] },
    });
    const wrapper = mountModal();
    await flushPromises();
    await type("other@test.de");

    okButton().click();
    await flushPromises();

    expect(document.body.querySelector(".modal .alert-danger")?.textContent).toBe("No match");
    expect(success).not.toHaveBeenCalled();
    expect(wrapper.emitted("deleted")).toBeUndefined();
    wrapper.unmount();
  });
});
