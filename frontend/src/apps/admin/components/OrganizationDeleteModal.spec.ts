import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const DELETE = vi.fn();
vi.mock("@/shared/api", () => ({ api: { DELETE: (...args: unknown[]) => DELETE(...args) } }));

const success = vi.fn();
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import OrganizationDeleteModal from "./OrganizationDeleteModal.vue";

function mountModal() {
  return mount(OrganizationDeleteModal, {
    props: { organization: { id: 3, name: "Alpha Crew" }, modelValue: true },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
}

const okButton = () => document.body.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!;

async function type(value: string) {
  const input = document.body.querySelector<HTMLInputElement>("#delete-organization-name")!;
  input.value = value;
  input.dispatchEvent(new Event("input"));
  await flushPromises();
}

describe("OrganizationDeleteModal", () => {
  beforeEach(() => {
    DELETE.mockReset();
    success.mockReset();
  });
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("enables OK only when the name matches, ignoring case", async () => {
    const wrapper = mountModal();
    await flushPromises();

    expect(okButton().disabled).toBe(true);
    await type("alpha crew");
    expect(okButton().disabled).toBe(false);
    wrapper.unmount();
  });

  it("deletes with the trimmed name, notifies and emits deleted", async () => {
    DELETE.mockResolvedValue({});
    const wrapper = mountModal();
    await flushPromises();
    await type(" alpha crew ");

    okButton().click();
    await flushPromises();

    expect(DELETE).toHaveBeenCalledWith("/bff/admin/organizations/{id}", {
      params: { path: { id: 3 } },
      body: { name: "alpha crew" },
    });
    expect(success).toHaveBeenCalledWith("Organization successfully deleted");
    expect(wrapper.emitted("deleted")).toHaveLength(1);
    wrapper.unmount();
  });

  it("shows the server's field error inline", async () => {
    DELETE.mockResolvedValue({
      error: { name: "Unprocessable Entity", message: "m", errors: [{ loc: ["name"], msg: "No match" }] },
    });
    const wrapper = mountModal();
    await flushPromises();
    await type("Alpha Crew");

    okButton().click();
    await flushPromises();

    expect(document.body.querySelector(".modal .alert-danger")?.textContent).toBe("No match");
    expect(wrapper.emitted("deleted")).toBeUndefined();
    wrapper.unmount();
  });
});
