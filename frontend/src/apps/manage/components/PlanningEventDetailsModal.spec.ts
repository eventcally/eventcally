import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import type { CalendarEventProps } from "../planning";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", docsUrl: null } }));

import PlanningEventDetailsModal from "./PlanningEventDetailsModal.vue";

function dateProps(over: Record<string, unknown> = {}): CalendarEventProps {
  return {
    kind: "date",
    row: {
      id: 5,
      start: "2026-10-03T10:00:00",
      end: null,
      allday: false,
      event: {
        id: 1,
        name: "Jam",
        status: "scheduled",
        public_status: "planned",
        booked_up: null,
        attendance_mode: "offline",
        has_status_info: true,
        organization_name: "Org",
        organizer_name: "Organizer",
        place_name: "Hall",
        ...over,
      },
    },
  };
}

async function mountModal(selected: CalendarEventProps) {
  const wrapper = mount(PlanningEventDetailsModal, {
    props: { selected, modelValue: true },
    attachTo: document.body,
    global: {
      plugins: [
        createBootstrap(),
        createI18n({
          legacy: false,
          locale: "en",
          messages: { en: { "EventPublicStatus.planned": "Planned" } },
        }),
      ],
    },
  });
  await flushPromises();
  return wrapper;
}

const text = () => document.body.textContent ?? "";

describe("PlanningEventDetailsModal", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("shows organization, organizer, place, pills and the view link", async () => {
    await mountModal(dateProps());

    expect(text()).toContain("Jam");
    expect(text()).toContain("October 3, 2026");
    expect(text()).toContain("Org");
    expect(text()).toContain("Organizer");
    expect(text()).toContain("Hall");
    expect(text()).toContain("Planned");
    const view = document.body.querySelector<HTMLAnchorElement>('[data-test="view"]')!;
    expect(view.getAttribute("href")).toBe("/eventdate/5");
    expect(view.target).toBe("_blank");
  });

  it("hides the organizer when it equals the organization", async () => {
    await mountModal(dateProps({ organizer_name: "Org" }));

    expect(document.body.querySelector(".fa-server")).toBeNull();
  });

  it("shows description, location and source of an external item", async () => {
    await mountModal({
      kind: "external",
      calendar: { title: "Holidays", url: "http://h" },
      item: {
        name: "Holiday",
        start: "2026-10-12",
        end: null,
        allday: true,
        location: "Somewhere",
        description: "Day off",
      },
    });

    expect(text()).toContain("Holiday");
    expect(text()).toContain("Somewhere");
    expect(text()).toContain("Day off");
    expect(text()).toContain("Holidays");
    expect(document.body.querySelector('[data-test="view"]')).toBeNull();
  });
});
