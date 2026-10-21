import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import NewsletterConfirmModal from "./NewsletterConfirmModal.vue";

async function mountModal() {
  const wrapper = mount(NewsletterConfirmModal, {
    props: { modelValue: false },
    attachTo: document.body,
    global: {
      plugins: [
        createBootstrap(),
        createI18n({
          legacy: false,
          locale: "en",
          messages: { en: { "Send to %(count)d recipients?": "Send to {count} recipients?" } },
        }),
      ],
    },
  });
  await wrapper.setProps({ modelValue: true });
  await flushPromises();
  return wrapper;
}

const body = () => document.body.querySelector(".modal-body")!.textContent!.trim();
const ok = () => document.body.querySelector<HTMLButtonElement>(".modal-footer .btn-primary")!;

describe("NewsletterConfirmModal", () => {
  beforeEach(() => GET.mockReset());
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("asks with the recipient count and confirms", async () => {
    GET.mockResolvedValue({ data: { recipient_count: 7 } });
    const wrapper = await mountModal();

    expect(body()).toBe("Send to 7 recipients?");
    ok().click();
    await flushPromises();

    expect(wrapper.emitted("confirm")).toHaveLength(1);
  });

  it("disables OK without recipients", async () => {
    GET.mockResolvedValue({ data: { recipient_count: 0 } });
    await mountModal();

    expect(body()).toBe("There are no recipients.");
    expect(ok().disabled).toBe(true);
  });

  it("shows a load error and keeps OK disabled", async () => {
    GET.mockResolvedValue({ error: { name: "Forbidden", message: "Nope" } });
    await mountModal();

    expect(body()).toBe("Nope");
    expect(ok().disabled).toBe(true);
  });
});
