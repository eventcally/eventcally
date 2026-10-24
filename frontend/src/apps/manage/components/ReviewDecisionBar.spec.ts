import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import ReviewDecisionBar from "./ReviewDecisionBar.vue";

const reasons = [
  { value: 0, label: "No reason" },
  { value: 4, label: "Irrelevant" },
];

async function mountBar(props: Record<string, unknown> = {}) {
  const wrapper = mount(ReviewDecisionBar, {
    props: {
      acceptLabel: "Accept",
      rejectLabel: "Reject",
      rejectionReasons: reasons,
      busy: false,
      error: null,
      ...props,
    },
    slots: { "accept-fields": '<input id="slot-field" />' },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: { Cancel: "Cancel" } } })],
    },
  });
  await flushPromises();
  return wrapper;
}

const body = (selector: string) => document.body.querySelector<HTMLElement>(selector);

describe("ReviewDecisionBar", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("shows both decisions with the labels", async () => {
    const wrapper = await mountBar();

    expect(wrapper.get("[data-test=accept]").classes()).toContain("btn-success");
    expect(wrapper.get("[data-test=accept]").text()).toBe("Accept…");
    expect(wrapper.get("[data-test=reject]").classes()).toContain("btn-danger");
    expect(wrapper.get("[data-test=reject]").text()).toBe("Reject…");
  });

  it("accepts from the modal with the page's fields", async () => {
    const wrapper = await mountBar();

    await wrapper.get("[data-test=accept]").trigger("click");
    await flushPromises();
    expect(body("#slot-field")).not.toBeNull();
    body("[data-test=accept-confirm]")!.click();

    expect(wrapper.emitted("accept")).toHaveLength(1);
  });

  it("rejects without a reason by default", async () => {
    const wrapper = await mountBar();

    await wrapper.get("[data-test=reject]").trigger("click");
    await flushPromises();
    body("[data-test=reject-confirm]")!.click();

    expect(wrapper.emitted("reject")![0]).toEqual([null]);
  });

  it("rejects with the chosen reason", async () => {
    const wrapper = await mountBar();

    await wrapper.get("[data-test=reject]").trigger("click");
    await flushPromises();
    const select = body("#rejection_reason") as HTMLSelectElement;
    select.value = "4";
    select.dispatchEvent(new Event("change"));
    await flushPromises();
    body("[data-test=reject-confirm]")!.click();

    expect(wrapper.emitted("reject")![0]).toEqual([4]);
  });

  it("shows the server error inside the open modal only", async () => {
    const wrapper = await mountBar({ error: "Already verified" });
    expect(body("[data-test=accept-error]")).toBeNull();
    expect(body("[data-test=reject-error]")).toBeNull();

    await wrapper.get("[data-test=reject]").trigger("click");
    await flushPromises();

    expect(body("[data-test=reject-error]")!.textContent).toContain("Already verified");
    expect(body("[data-test=accept-error]")).toBeNull();
  });

  it("asks the page to clear the error when a modal opens", async () => {
    const wrapper = await mountBar();

    await wrapper.get("[data-test=accept]").trigger("click");
    await flushPromises();

    expect(wrapper.emitted("reset")).toBeTruthy();
  });

  it("disables the confirmations while busy", async () => {
    const wrapper = await mountBar({ busy: true });

    await wrapper.get("[data-test=accept]").trigger("click");
    await flushPromises();

    expect(body("[data-test=accept-confirm]")!.hasAttribute("disabled")).toBe(true);
  });
});
