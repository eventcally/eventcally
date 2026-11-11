import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login", docsUrl: null } }));
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success: vi.fn(), error: vi.fn() }) }));

import EventDetailView from "./EventDetailView.vue";
import { makeEvent, noRights } from "./eventFixture";

const img = (url: string) => ({ url, copyright_text: null, license_code: null, license_url: null });

async function mountView(event = makeEvent(), props: Record<string, unknown> = {}) {
  const wrapper = mount(EventDetailView, {
    props: { event, start: event.start!, end: event.end, allday: false, ...props },
    attachTo: document.body,
    global: {
      plugins: [
        createBootstrap(),
        createI18n({
          legacy: false,
          locale: "en",
          messages: { en: { "%(count)d event dates": "{count} event dates" } },
        }),
      ],
    },
  });
  await flushPromises();
  return wrapper;
}

describe("EventDetailView", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("renders the header and the property list", async () => {
    const wrapper = await mountView();

    expect(wrapper.find("h1").text()).toContain("Stadtfest");
    expect(wrapper.text()).toContain("Marktplatz, Goslar");
    expect(wrapper.find("img").attributes("src")).toBe("/image/1?s=700");
    expect(wrapper.text()).toContain("© Fotograf");
    expect(wrapper.text()).toContain("5 Euro");
    expect(wrapper.text()).toContain("Music, Art");
    expect(wrapper.text()).toContain("fest, musik");
    expect(wrapper.text()).toContain("6 -");
    expect(wrapper.find('a[href="https://example.com/extern"]').exists()).toBe(true);
    expect(wrapper.find('a[href="https://example.com/fest"]').exists()).toBe(true);
    expect(wrapper.find('a[href="/event/4/report"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("Created at");
  });

  it("hides what the visitor may not see", async () => {
    const wrapper = await mountView();

    expect(wrapper.find("[data-test=event-menu]").exists()).toBe(false);
    expect(wrapper.find("[data-test=reference-requests]").exists()).toBe(false);
    expect(wrapper.find("[data-test=references]").exists()).toBe(false);
    expect(wrapper.find('a[href*="/update"]').exists()).toBe(false);
  });

  it("shows the date count and the list when there are several dates", async () => {
    const event = makeEvent({
      dates: [
        { id: 9, start: "2026-12-01T17:00:00Z", end: null, allday: false },
        { id: 10, start: "2026-12-02T17:00:00Z", end: null, allday: false },
      ],
    });
    const wrapper = await mountView(event);

    expect(wrapper.find('a[href="#event-dates"]').text()).toBe("2 event dates");
    expect(wrapper.findAll("[data-test=dates] a").map((a) => a.attributes("href"))).toEqual([
      "/eventdate/9",
      "/eventdate/10",
    ]);
  });

  it("shows the edit links and the private cards to an editor", async () => {
    const event = makeEvent({
      rating: 70,
      internal_tags: "a,b",
      rights: { ...noRights, can_update_event: true, can_create_reference_request: true, can_reference_event: true },
      references: [{ id: 1, organization: { id: 5, name: "Other Crew", is_verified: true } }],
      reference_requests: [
        { id: 2, review_status: "inbox", review_status_label: "Inbox", organization: { id: 5, name: "Other Crew", is_verified: false } },
        { id: 3, review_status: "verified", review_status_label: "Verified", organization: { id: 6, name: "Third", is_verified: false } },
        { id: 4, review_status: "rejected", review_status_label: "Rejected", organization: { id: 7, name: "Fourth", is_verified: false } },
        { id: 5, review_status: null, review_status_label: null, organization: { id: 8, name: "Fifth", is_verified: false } },
      ],
    });
    const wrapper = await mountView(event);

    expect(wrapper.text()).toContain("7/10");
    expect(wrapper.text()).toContain("a, b");
    expect(wrapper.find('a[href="/manage/admin_unit/2/event/4/update"]').exists()).toBe(true);
    expect(wrapper.find('a[href="/manage/admin_unit/2/event_place/3/update"]').exists()).toBe(true);
    expect(wrapper.find('a[href="/manage/admin_unit/2/event_organizer/7/update"]').exists()).toBe(true);
    expect(wrapper.find('a[href="/manage/admin_unit/2/event_organizer/8/update"]').exists()).toBe(true);
    expect(wrapper.find("[data-test=references]").text()).toContain("Other Crew");
    const pills = wrapper.findAll("[data-test=reference-requests] .badge").map((b) => b.classes());
    expect(pills[0]).toContain("text-bg-info");
    expect(pills[1]).toContain("text-bg-success");
    expect(pills[2]).toContain("text-bg-danger");
    expect(pills).toHaveLength(3);
    expect(
      wrapper.find('a[href="/manage/admin_unit/2/outgoing_event_reference_request/create_for_event/4"]').exists(),
    ).toBe(true);
  });

  it("explains online and mixed events and hides directions when online", async () => {
    const online = await mountView(makeEvent({ attendance_mode: "online" }));
    expect(online.text()).toContain("The event takes place online.");
    expect(online.find('a[href^="http://www.google.com/maps"]').exists()).toBe(false);

    document.body.innerHTML = "";
    const mixed = await mountView(makeEvent({ attendance_mode: "mixed" }));
    expect(mixed.text()).toContain("The event takes place both offline and online.");
    expect(mixed.find("a[href^='http://www.google.com/maps?q=Marktplatz%2C']").exists()).toBe(true);
  });

  it("opens the share and calendar dialogs", async () => {
    const wrapper = await mountView();
    const buttons = wrapper.findAll("button.btn-outline-secondary");

    await buttons.find((b) => b.text().includes("Share"))!.trigger("click");
    await flushPromises();
    expect(document.body.querySelector('input[name="shareUrl"]')).not.toBeNull();

    await buttons.find((b) => b.text().includes("Add to calendar"))!.trigger("click");
    await flushPromises();
    expect(document.body.textContent).toContain("Outlook");
  });

  it("links the public calendars of other organizations for editors", async () => {
    const wrapper = await mountView(
      makeEvent({
        public_calendars: [{ id: 4, name: "Sport", organization: { id: 2, name: "Other Crew" } }],
      }),
    );

    const block = wrapper.find("[data-test=public-calendars]");
    expect(block.text()).toContain("Sport");
    expect(block.text()).toContain("Other Crew");
    expect(block.find("a").attributes("href")).toBe("/calendars/4");

    const none = await mountView(makeEvent({ public_calendars: [] }));
    expect(none.find("[data-test=calendars]").exists()).toBe(false);
  });

  it("puts the calendars into their own box between the reference requests and the dates", async () => {
    const wrapper = await mountView(
      makeEvent({
        rights: { ...makeEvent().rights, can_create_reference_request: true },
        public_calendars: [],
        calendar_organization: { id: 7, name: "Crew" },
      }),
    );

    const boxes = wrapper
      .findAll(".card[data-test]")
      .map((box) => box.attributes("data-test"))
      .filter((name) => ["reference-requests", "calendars", "dates"].includes(name!));
    expect(boxes).toEqual(["reference-requests", "calendars", "dates"]);
    expect(wrapper.find("[data-test=calendars]").text()).toContain("Add to organization calendar");
    expect(wrapper.find("[data-test=public-calendars]").exists()).toBe(false);
  });

  it("shows the property list of a full event", async () => {
    const wrapper = await mountView(
      makeEvent({
        status: "cancelled",
        status_label: "Cancelled",
        ticket_link: "https://tickets.test",
        accessible_for_free: true,
        target_group_origin_label: "Tourists",
        attendance_mode_label: "Mixed",
        registration_required: true,
        booked_up: true,
        expected_participants: 200,
        age_to: 99,
        place: { ...makeEvent().place, photo: img("/image/2?s=240"), url: "place.test" },
        organizer: { ...makeEvent().organizer, logo: img("/image/3?s=120") },
        organization: { ...makeEvent().organization, logo: img("/image/4?s=120"), address: "38640 Goslar" },
      }),
    );

    for (const text of ["Cancelled", "Tourists", "Mixed", "Registration required", "Booked up", "200", "6 - 99", "38640 Goslar"]) {
      expect(wrapper.text()).toContain(text);
    }
    expect(wrapper.find('a[href="https://tickets.test"]').exists()).toBe(true);
    expect(wrapper.find('a[href="https://place.test"]').exists()).toBe(true);
    expect(wrapper.findAll("img").map((i) => i.attributes("src"))).toEqual(
      expect.arrayContaining(["/image/2?s=240", "/image/3?s=120", "/image/4?s=120"]),
    );
  });

  it("falls back to the place name without a city", async () => {
    const wrapper = await mountView(makeEvent({ place: { ...makeEvent().place, city: null } }));

    expect(wrapper.text()).toContain("Marktplatz");
    expect(wrapper.text()).not.toContain("Marktplatz, Goslar");
  });
});
