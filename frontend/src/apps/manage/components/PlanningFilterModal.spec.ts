import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { emptyFilter } from "../planning";

vi.mock("@/shared/api", () => ({ api: { GET: vi.fn() } }));

import PlanningFilterModal from "./PlanningFilterModal.vue";

const categories = [
  { id: 1, name: "Music" },
  { id: 2, name: "Sport" },
];

async function mountModal() {
  const wrapper = mount(PlanningFilterModal, {
    props: {
      categories,
      distances: [{ value: 500, label: "500 m" }],
      filter: emptyFilter(),
      modelValue: true,
    },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  await flushPromises();
  return wrapper;
}

const q = <T extends Element>(selector: string) => document.body.querySelector<T>(selector)!;

describe("PlanningFilterModal", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("applies the edited filter only on Refresh", async () => {
    const wrapper = await mountModal();

    q<HTMLInputElement>("#planning-category-2").click();
    const postal = q<HTMLInputElement>("#planning-postal-code");
    postal.value = "38640";
    postal.dispatchEvent(new Event("input"));
    q<HTMLInputElement>("#planning-exclude-recurring").click();
    await flushPromises();
    expect(wrapper.emitted("apply")).toBeUndefined();

    q<HTMLButtonElement>('[data-test="refresh"]').click();
    await flushPromises();

    expect(wrapper.emitted("apply")![0][0]).toMatchObject({
      category_id: [2],
      postal_code: "38640",
      exclude_recurring: false,
    });
    expect(wrapper.emitted("update:modelValue")![0]).toEqual([false]);
  });

  it("discards edits when closed without Refresh", async () => {
    const wrapper = await mountModal();

    q<HTMLInputElement>("#planning-category-1").click();
    await flushPromises();
    q<HTMLButtonElement>(".modal-footer .btn-outline-secondary").click();
    await flushPromises();

    expect(wrapper.emitted("apply")).toBeUndefined();
  });

  it("renders every category and the min. participants field", async () => {
    await mountModal();

    expect(document.body.querySelectorAll('input[id^="planning-category-"]')).toHaveLength(2);
    expect(q<HTMLInputElement>("#planning-participants").type).toBe("number");
  });
});
