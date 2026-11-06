import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import type { ManageEventDate } from "../manageEventCalendar";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", docsUrl: null } }));

import ManageEventDateModal from "./ManageEventDateModal.vue";

const options = {
  default_date_from: "2030-10-01",
  categories: [],
  statuses: [{ value: 3, name: "cancelled", label: "Cancelled" }],
  public_statuses: [{ value: 1, name: "draft", label: "Draft" }],
  distances: [],
  can_write: true,
  can_request_reference: true,
};

function row(over: Partial<ManageEventDate["event"]> = {}): ManageEventDate {
  return {
    id: 5,
    start: "2030-10-03T10:00:00",
    end: null,
    allday: false,
    event: {
      id: 11,
      name: "Jam",
      is_recurring: false,
      status: "cancelled",
      public_status: "draft",
      organizer_name: "Jam Crew",
      place_label: "Rathaus 38640 Goslar",
      ...over,
    },
  };
}

async function mountModal(value: ManageEventDate, opts = {}) {
  const wrapper = mount(ManageEventDateModal, {
    props: { row: value, organizationId: 3, options: { ...options, ...opts }, modelValue: true },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  await flushPromises();
  return wrapper;
}

const text = () => document.body.textContent ?? "";
const find = (test: string) => document.body.querySelector<HTMLElement>(`[data-test="${test}"]`);

describe("ManageEventDateModal", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("shows the date, statuses, organizer, place and the actions", async () => {
    await mountModal(row());

    expect(text()).toContain("Jam");
    expect(text()).toContain("October 3, 2030");
    expect(text()).toContain("Jam Crew");
    expect(text()).toContain("Rathaus 38640 Goslar");
    expect(find("status")!.textContent).toBe("Cancelled");
    expect(find("status")!.className).toContain("text-bg-danger");
    expect(find("public-status")!.textContent).toBe("Draft");
    expect(find("public-status")!.className).toContain("text-bg-light");
    expect(find("recurring")).toBeNull();
    expect(find("view")!.getAttribute("href")).toBe("/eventdate/5");
    expect(find("edit")!.getAttribute("href")).toBe("/manage/admin_unit/3/event/11/update");
    expect(find("request-reference")).not.toBeNull();
    expect(find("more")!.getAttribute("href")).toBe("/event/11/actions");
  });

  it("notes that the actions of a recurring event apply to all dates", async () => {
    await mountModal(row({ is_recurring: true, status: null, organizer_name: null, place_label: null }));

    expect(find("recurring")).not.toBeNull();
    expect(find("status")).toBeNull();
    expect(document.body.querySelector(".fa-server")).toBeNull();
    expect(document.body.querySelector(".fa-map-marker")).toBeNull();
  });

  it("hides the reference request when it is not allowed", async () => {
    await mountModal(row(), { can_request_reference: false });

    expect(find("request-reference")).toBeNull();
  });

  it("closes and emits the event to delete", async () => {
    const wrapper = await mountModal(row());

    find("delete")!.click();
    await flushPromises();

    expect(wrapper.emitted("delete")).toEqual([[11]]);
    expect(wrapper.emitted("update:modelValue")).toEqual([[false]]);
  });
});
