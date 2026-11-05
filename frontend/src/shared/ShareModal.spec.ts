import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

const success = vi.fn();
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import ShareModal from "./ShareModal.vue";

const links = {
  url: "http://localhost/event/1",
  facebook: "https://fb.test",
  twitter: "https://tw.test",
  email: "mailto:?subject=x",
  whatsapp: "whatsapp://send",
  telegram: "https://t.me/x",
};

async function mountModal() {
  const wrapper = mount(ShareModal, {
    props: { links, modelValue: true },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  await flushPromises();
  return wrapper;
}

describe("ShareModal", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    success.mockReset();
  });

  it("lists the share targets", async () => {
    await mountModal();

    const hrefs = Array.from(document.body.querySelectorAll(".list-group a")).map((a) => a.getAttribute("href"));
    expect(hrefs).toEqual([links.facebook, links.twitter, links.email, links.whatsapp, links.telegram]);
    expect((document.body.querySelector('input[name="shareUrl"]') as HTMLInputElement).value).toBe(links.url);
  });

  it("copies the link", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
    await mountModal();

    (document.body.querySelector("[data-test=copy-link]") as HTMLElement).click();
    await flushPromises();

    expect(writeText).toHaveBeenCalledWith(links.url);
    expect(success).toHaveBeenCalledWith("Link copied");
  });

  it("falls back to selecting the input without clipboard access", async () => {
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: vi.fn().mockRejectedValue(new Error("no")) },
      configurable: true,
    });
    await mountModal();

    (document.body.querySelector("[data-test=copy-link]") as HTMLElement).click();
    await flushPromises();

    expect(success).not.toHaveBeenCalled();
  });
});
