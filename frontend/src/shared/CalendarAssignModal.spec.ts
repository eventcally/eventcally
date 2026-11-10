import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

const GET = vi.fn();
const PUT = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a) },
}));
const success = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import CalendarAssignModal from "./CalendarAssignModal.vue";

const PATH = "/bff/manage/organizations/{id}/events/{event_id}/calendars";

function mountModal() {
  const wrapper = mount(CalendarAssignModal, {
    props: {
      organizationId: 3,
      eventId: 9,
      modelValue: false,
      "onUpdate:modelValue": (v: boolean) => wrapper.setProps({ modelValue: v }),
    },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
      stubs: { transition: false },
    },
  });
  return wrapper;
}

async function open(wrapper: ReturnType<typeof mountModal>) {
  await wrapper.setProps({ modelValue: true });
  await flushPromises();
}

const ok = () =>
  Array.from(document.body.querySelectorAll<HTMLButtonElement>(".modal-footer button")).pop()!;

describe("CalendarAssignModal", () => {
  beforeEach(() => {
    [GET, PUT, success].forEach((f) => f.mockReset());
    document.body.innerHTML = "";
  });

  it("loads the calendars of the event and saves the selection", async () => {
    GET.mockResolvedValue({
      data: {
        choices: [
          { id: 1, name: "Sport", private: false },
          { id: 2, name: "Intern", private: true },
        ],
        selected_ids: [1],
      },
    });
    PUT.mockResolvedValue({ data: { message: "Calendars successfully saved" } });
    const wrapper = mountModal();
    await open(wrapper);

    expect(GET).toHaveBeenCalledWith(PATH, { params: { path: { id: 3, event_id: 9 } } });
    expect((document.querySelector("#assign-calendar-1") as HTMLInputElement).checked).toBe(true);

    (document.querySelector("#assign-calendar-2") as HTMLInputElement).click();
    await flushPromises();
    ok().click();
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith(PATH, {
      params: { path: { id: 3, event_id: 9 } },
      body: { calendar_ids: [1, 2] },
    });
    expect(success).toHaveBeenCalledWith("Calendars successfully saved");
    expect(wrapper.emitted("saved")).toHaveLength(1);
    expect(wrapper.props("modelValue")).toBe(false);
  });

  it("points to the calendar management when there are none", async () => {
    GET.mockResolvedValue({ data: { choices: [], selected_ids: [] } });
    await open(mountModal());

    expect(document.querySelector("[data-test=no-calendars] a")?.getAttribute("href")).toBe(
      "/manage/admin_unit/3/calendar/create",
    );
    expect(ok().disabled).toBe(true);
  });

  it("shows load and save errors and keeps the modal open", async () => {
    GET.mockResolvedValueOnce({ error: { message: "Forbidden" } });
    const wrapper = mountModal();
    await open(wrapper);
    expect(document.querySelector("[data-test=calendar-modal-error]")?.textContent).toContain(
      "Forbidden",
    );

    GET.mockResolvedValue({ data: { choices: [{ id: 1, name: "Sport", private: false }], selected_ids: [] } });
    PUT.mockResolvedValue({ error: { message: "Calendar not found" } });
    await wrapper.setProps({ modelValue: false });
    await open(wrapper);
    ok().click();
    await flushPromises();

    expect(document.querySelector("[data-test=calendar-modal-error]")?.textContent).toContain(
      "Calendar not found",
    );
    expect(success).not.toHaveBeenCalled();
    expect(wrapper.props("modelValue")).toBe(true);
  });
});
