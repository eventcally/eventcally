import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en" } }));

import ReviewEventCards from "./ReviewEventCards.vue";

const organization = {
  id: 2,
  name: "Other Crew",
  is_verified: true,
  logo_url: "/image/9?s=120",
  url: "crew.example",
  email: "crew@example.com",
  phone: "0123",
  fax: "0456",
  address: "Markt 1, 38640 Goslar",
};

function event(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    name: "Concert",
    start: "2026-10-24T09:42:00",
    end: null,
    allday: false,
    category_names: [],
    custom_categories: [],
    co_organizers: [],
    report_url: "/event/1/report",
    created_at: "2026-10-24T09:42:00",
    updated_at: null,
    organization,
    ...overrides,
  };
}

const full = event({
  public_status: "planned",
  status: "cancelled",
  attendance_mode: "mixed",
  booked_up: true,
  status_label: "Cancelled",
  target_group_origin_label: "Tourists",
  attendance_mode_label: "Online and offline",
  photo_url: "/image/1?s=700",
  description: "See https://example.org/info. <b>bold</b>",
  price_info: "5 EUR",
  external_link: "example.org",
  ticket_link: "https://tickets.example",
  category_names: ["Music", "Other"],
  custom_categories: [{ label: "Set A", names: ["One", "Two"] }],
  tags: "a,b",
  kid_friendly: true,
  accessible_for_free: true,
  age_from: 6,
  age_to: null,
  registration_required: true,
  expected_participants: 120,
  updated_at: "2026-10-25T10:00:00",
  place: {
    name: "Hall",
    photo_url: "/image/2?s=300",
    description: "Big",
    url: "hall.example",
    address: "Markt 2, 38640 Goslar",
    directions_url: "http://www.google.com/maps?q=Hall",
  },
  organizer: { name: "Main", logo_url: "/image/3?s=120", url: "main.example", email: "m@example.com" },
  co_organizers: [{ name: "Co", phone: "999" }],
});

function render(e: Record<string, unknown>, dates: { id: number; start: string }[] = []) {
  return mount(ReviewEventCards, {
    props: { event: e as never, dates },
    global: {
      plugins: [createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
}

describe("ReviewEventCards", () => {
  it("renders all cards of a fully populated event in order", () => {
    const wrapper = render(full, [
      { id: 5, start: "2026-10-24T09:42:00" },
      { id: 6, start: "2026-10-31T09:42:00" },
    ]);

    const cards = wrapper.findAll(".card").map((c) => c.attributes("data-test"));
    expect(cards).toEqual([
      "event-card",
      "place-card",
      "organizer-card",
      "organization-card",
      "dates-card",
    ]);

    const eventCard = wrapper.get("[data-test=event-card]");
    expect(eventCard.text()).toContain("Concert");
    // No translations are loaded, so the pills show their msgids.
    expect(eventCard.text()).toContain("EventPublicStatus.planned");
    expect(eventCard.get("img").attributes("src")).toBe("/image/1?s=700");
    expect(eventCard.get("[data-test=event-props]").text()).toContain("5 EUR");
    expect(eventCard.get("[data-test=event-props]").text()).toContain("Music, Other");
    expect(eventCard.get("[data-test=event-props]").text()).toContain("One, Two");
    expect(eventCard.get("[data-test=event-props]").text()).toContain("a, b");
    expect(eventCard.get("[data-test=event-props]").text()).toContain("6 -");
    expect(eventCard.get("[data-test=event-props]").text()).toContain("120");
    expect(eventCard.text()).toContain("Cancelled");
    expect(eventCard.text()).toContain("Tourists");

    const hrefs = eventCard.findAll("a").map((a) => a.attributes("href"));
    expect(hrefs).toContain("https://example.org/info");
    expect(hrefs).toContain("https://tickets.example");
    expect(hrefs).toContain("#event-dates");
    expect(hrefs).toContain("/event/1/report");
  });

  it("links the description safely and keeps markup as text", () => {
    const wrapper = render(full);

    const description = wrapper.get("[data-test=event-card] .my-4[style*='pre-wrap']");
    expect(description.find("b").exists()).toBe(false);
    expect(description.text()).toContain("<b>bold</b>");
    expect(description.get("a").attributes("rel")).toBe("nofollow noopener noreferrer");
  });

  it("adds a scheme to links without one", () => {
    const wrapper = render(full);

    const hrefs = wrapper.findAll("a").map((a) => a.attributes("href"));
    expect(hrefs).toContain("https://example.org");
    expect(hrefs).toContain("https://hall.example");
    expect(hrefs).toContain("https://main.example");
    expect(hrefs).toContain("mailto:m@example.com");
  });

  it("shows the place, its directions and the online text", () => {
    const wrapper = render(full);

    const place = wrapper.get("[data-test=place-card]");
    expect(place.text()).toContain("Hall");
    expect(place.text()).toContain("Markt 2, 38640 Goslar");
    expect(place.get("a.btn").attributes("href")).toBe("http://www.google.com/maps?q=Hall");
    expect(place.text()).toContain("The event takes place both offline and online.");
  });

  it("lists the organizer and the co-organizers", () => {
    const wrapper = render(full);

    const text = wrapper.get("[data-test=organizer-card]").text();
    expect(text).toContain("Main");
    expect(text).toContain("Co");
    expect(text).toContain("999");
  });

  it("shows the organization with its contact lines and verified badge", () => {
    const wrapper = render(full);

    const card = wrapper.get("[data-test=organization-card]");
    expect(card.text()).toContain("Other Crew");
    expect(card.find(".fa-check-circle").exists()).toBe(true);
    expect(card.get("img").attributes("src")).toBe("/image/9?s=120");
    expect(card.text()).toContain("crew@example.com");
    expect(card.text()).toContain("Markt 1, 38640 Goslar");
  });

  it("shows the audit lines, with the update only when it differs", () => {
    expect(render(full).get("[data-test=event-audit]").text()).toContain("Last updated at");
    expect(render(event()).get("[data-test=event-audit]").text()).not.toContain("Last updated at");
  });

  it("hides every optional part of a minimal event", () => {
    const wrapper = render(event({ organization: { id: 2, name: "Plain", is_verified: false } }));

    expect(wrapper.find("[data-test=organizer-card]").exists()).toBe(false);
    expect(wrapper.find("[data-test=dates-card]").exists()).toBe(false);
    expect(wrapper.find("[data-test=event-props]").text()).toBe("");
    expect(wrapper.find("[data-test=event-card] img").exists()).toBe(false);
    expect(wrapper.find("[data-test=place-card] .card-title").exists()).toBe(false);
    expect(wrapper.find("[data-test=organization-card] .fa-check-circle").exists()).toBe(false);
    expect(wrapper.find("a[href='#event-dates']").exists()).toBe(false);
  });

  it("lists the event dates as links", () => {
    const wrapper = render(event(), [{ id: 5, start: "2026-10-24T09:42:00" }]);

    const links = wrapper.findAll("[data-test=dates-card] a");
    expect(links.map((a) => a.attributes("href"))).toEqual(["/eventdate/5"]);
    // Only one date: no "N event dates" link.
    expect(wrapper.find("a[href='#event-dates']").exists()).toBe(false);
  });
});
