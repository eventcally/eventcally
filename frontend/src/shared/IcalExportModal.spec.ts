import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

const bootMock = vi.hoisted(() => ({ boot: { docsUrl: null as string | null } }));
vi.mock("@/shared/boot", () => bootMock);

const success = vi.fn();
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import IcalExportModal from "./IcalExportModal.vue";

const url = "http://localhost/organizers/5/ical";

async function mountModal() {
  const wrapper = mount(IcalExportModal, {
    props: { url, modelValue: true },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  await flushPromises();
  return wrapper;
}

function buttons() {
  return Array.from(document.body.querySelectorAll<HTMLElement>(".modal-footer a, .modal-footer button"));
}

describe("IcalExportModal", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    success.mockReset();
    bootMock.boot.docsUrl = null;
  });

  it("renders the url and a download link", async () => {
    await mountModal();

    const input = document.body.querySelector('input[name="icalUrl"]') as HTMLInputElement;
    expect(input.value).toBe(url);
    const download = buttons().find((b) => b.textContent?.trim() === "Download");
    expect(download?.getAttribute("href")).toBe(url);
  });

  it("copies the url to the clipboard", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
    await mountModal();

    buttons().find((b) => b.textContent?.trim() === "Copy link")?.click();
    await flushPromises();

    expect(writeText).toHaveBeenCalledWith(url);
    expect(success).toHaveBeenCalledWith("Link copied");
  });

  it("hides the docs button without docsUrl and shows it with", async () => {
    await mountModal();
    expect(buttons().some((b) => b.textContent?.trim() === "Docs")).toBe(false);

    document.body.innerHTML = "";
    bootMock.boot.docsUrl = "https://docs.test";
    await mountModal();
    const docs = buttons().find((b) => b.textContent?.trim() === "Docs");
    expect(docs?.getAttribute("href")).toBe("https://docs.test/goto/ical-calendar");
  });
});
