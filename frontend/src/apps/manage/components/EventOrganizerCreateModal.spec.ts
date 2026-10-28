import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";
import { createI18n } from "vue-i18n";

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
vi.mock("@/shared/ImageCropper.vue", () => ({
  __esModule: true,
  default: defineComponent({ name: "ImageCropper", render: () => null }),
}));

import EventOrganizerCreateModal from "./EventOrganizerCreateModal.vue";

let mounted: { unmount: () => void } | null = null;

function mountModal() {
  const wrapper = mount(EventOrganizerCreateModal, {
    props: {
      organizationId: 5,
      modelValue: false,
      "onUpdate:modelValue": (v: boolean) => wrapper.setProps({ modelValue: v }),
    },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
      // The lazy modal body renders after the enter transition.
      stubs: { transition: false },
    },
  });
  mounted = wrapper;
  return wrapper;
}

async function open(wrapper: ReturnType<typeof mountModal>) {
  await wrapper.setProps({ modelValue: true });
  await flushPromises();
}

const input = (id: string) => document.body.querySelector<HTMLInputElement>(`#${id}`)!;
const okButton = () =>
  Array.from(document.body.querySelectorAll<HTMLButtonElement>(".modal-footer button")).pop()!;

async function type(id: string, value: string) {
  input(id).value = value;
  input(id).dispatchEvent(new Event("input"));
  await flushPromises();
}

describe("EventOrganizerCreateModal", () => {
  afterEach(() => mounted?.unmount());

  beforeEach(() => {
    GET.mockReset().mockImplementation(async (path: string) =>
      path.endsWith("/name-availability")
        ? { data: { name_taken: false } }
        : { data: { licenses: [{ id: 1, name: "CC0" }] } },
    );
    POST.mockReset();
  });

  it("creates the organizer inline and emits it", async () => {
    POST.mockResolvedValue({ data: { id: 9, redirect_url: "/x" } });
    const wrapper = mountModal();
    await open(wrapper);

    await type("new_organizer-name", "Halle");
    await type("location-city", "Goslar");
    await type("location-postalCode", "38640");
    okButton().click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/manage/organizations/{id}/event-organizers", {
      params: { path: { id: 5 } },
      body: expect.objectContaining({ name: "Halle", inline: true }),
    });
    expect(wrapper.emitted("created")![0]).toEqual([{ id: 9, name: "Halle" }]);
    expect(wrapper.props("modelValue")).toBe(false);
  });

  it("shows the errors of a 422 in the modal", async () => {
    POST.mockResolvedValue({
      error: {
        errors: [
          { loc: ["name"], msg: "Taken" },
          { loc: ["other"], msg: "Other" },
        ],
      },
    });
    const wrapper = mountModal();
    await open(wrapper);

    await type("new_organizer-name", "Halle");
    okButton().click();
    await flushPromises();

    expect(document.body.textContent).toContain("Taken");
    expect(document.body.textContent).toContain("Other");
    expect(wrapper.emitted("created")).toBeUndefined();
  });

  it("shows other errors and resets on close", async () => {
    POST.mockResolvedValue({ error: { message: "Boom" } });
    const wrapper = mountModal();
    await open(wrapper);
    await type("new_organizer-name", "Halle");
    okButton().click();
    await flushPromises();
    expect(document.body.textContent).toContain("Boom");

    await wrapper.setProps({ modelValue: false });
    await open(wrapper);

    expect(document.body.textContent).not.toContain("Boom");
    expect(input("new_organizer-name").value).toBe("");
    // The licenses are loaded once.
    expect(GET.mock.calls.filter(([path]) => path.endsWith("/create-form"))).toHaveLength(1);
  });

  it("reports a load error", async () => {
    GET.mockResolvedValue({ error: {} });
    const wrapper = mountModal();
    await open(wrapper);

    expect(document.body.textContent).toContain("Error");
    expect(okButton().disabled).toBe(true);
  });
});
