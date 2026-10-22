import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import EventWarningPills from "./EventWarningPills.vue";

function render(event: Record<string, unknown>) {
  return mount(EventWarningPills, {
    props: { event },
    global: {
      plugins: [
        createI18n({
          legacy: false,
          locale: "en",
          messages: {
            en: {
              "EventPublicStatus.planned": "Planned",
              "EventPublicStatus.draft": "Draft",
              "EventStatus.cancelled": "Cancelled",
              "Booked up": "Booked up",
              "EventAttendanceMode.mixed": "Online and offline",
            },
          },
        }),
      ],
    },
  });
}

describe("EventWarningPills", () => {
  it("renders nothing for a plain published event", () => {
    const wrapper = render({
      public_status: "published",
      status: "scheduled",
      attendance_mode: "offline",
    });
    expect(wrapper.findAll(".badge")).toHaveLength(0);
  });

  it("renders a pill per warning", () => {
    const wrapper = render({
      public_status: "planned",
      status: "cancelled",
      booked_up: true,
      attendance_mode: "mixed",
    });
    expect(wrapper.findAll(".badge").map((b) => b.text())).toEqual([
      "Planned",
      "Cancelled",
      "Booked up",
      "Online and offline",
    ]);
  });

  it("renders the draft pill", () => {
    expect(render({ public_status: "draft" }).text()).toBe("Draft");
  });
});
