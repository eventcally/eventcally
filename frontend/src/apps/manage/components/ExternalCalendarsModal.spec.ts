import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import ExternalCalendarsModal from "./ExternalCalendarsModal.vue";

const calendars = [
  { title: "Holidays", url: "http://h", active: true },
  { title: "School", url: "http://s", active: false },
];

async function mountModal() {
  const wrapper = mount(ExternalCalendarsModal, {
    props: { calendars, modelValue: true },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  await flushPromises();
  return wrapper;
}

const boxes = () =>
  Array.from(document.body.querySelectorAll<HTMLInputElement>('input[type="checkbox"]'));

describe("ExternalCalendarsModal", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("lists the calendars with the active ones checked", async () => {
    await mountModal();

    expect(boxes().map((b) => b.checked)).toEqual([true, false]);
    expect(document.body.textContent).toContain("Holidays");
    expect(document.body.textContent).toContain("http://s");
  });

  it("emits the active set on close", async () => {
    const wrapper = await mountModal();

    boxes()[1].click();
    await flushPromises();
    document.body.querySelector<HTMLButtonElement>(".modal-footer button")!.click();
    await flushPromises();

    expect(wrapper.emitted("apply")![0]).toEqual([["http://h", "http://s"]]);
  });
});
