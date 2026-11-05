import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import CalendarExportModal from "./CalendarExportModal.vue";

async function mountModal(links: { ics: string; google?: string | null }) {
  const wrapper = mount(CalendarExportModal, {
    props: { links, modelValue: true },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  await flushPromises();
  return wrapper;
}

const hrefs = () =>
  Array.from(document.body.querySelectorAll(".list-group a")).map((a) => a.getAttribute("href"));

describe("CalendarExportModal", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("offers the ics file for every calendar but Google", async () => {
    await mountModal({ ics: "/event/1/ical", google: "https://google.test" });

    expect(hrefs()).toEqual([
      "/event/1/ical",
      "https://google.test",
      "/event/1/ical",
      "/event/1/ical",
      "/event/1/ical",
    ]);
  });

  it("hides Google without a link", async () => {
    await mountModal({ ics: "/event/1/ical", google: null });

    expect(hrefs()).toHaveLength(4);
  });
});
