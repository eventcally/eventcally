import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import EventDateCard from "./EventDateCard.vue";

function eventDate(overrides: Record<string, unknown> = {}) {
  return {
    id: 5,
    start: "2030-10-03T10:00:00+02:00",
    end: null,
    allday: false,
    event: {
      id: 11,
      name: "Jam Session",
      description_preview: "Bring an instrument",
      status: null,
      public_status: "published",
      booked_up: false,
      attendance_mode: null,
      organization: { id: 1, name: "Jam Org" },
      organizer_name: "Jam Crew",
      place: { name: "Stadthalle", latitude: 51.9, longitude: 10.4 },
      photo: null,
      reference: null,
      ...overrides,
    },
  };
}

function mountCard(event: Record<string, unknown> = {}, props: Record<string, unknown> = {}) {
  return mount(EventDateCard, {
    props: { eventDate: eventDate(event), locale: "en", ...props },
    global: { plugins: [createI18n({ legacy: false, locale: "en", messages: { en: {} } })] },
  });
}

describe("EventDateCard", () => {
  it("links the title to the event date and shows the preview", () => {
    const wrapper = mountCard();

    expect(wrapper.find("a.text-body").attributes("href")).toBe("/eventdate/5");
    expect(wrapper.text()).toContain("Jam Session");
    expect(wrapper.text()).toContain("Bring an instrument");
    expect(wrapper.attributes("id")).toBe("event_card_5");
  });

  it("hides the organization when it equals the organizer", () => {
    expect(mountCard().find('[data-test="organization"]').exists()).toBe(true);
    expect(
      mountCard({ organizer_name: "Jam Org" }).find('[data-test="organization"]').exists(),
    ).toBe(false);
  });

  it("emits fly-to only for a place with coordinates", async () => {
    const wrapper = mountCard();
    await wrapper.find('[data-test="place"]').trigger("click");
    expect(wrapper.emitted("fly-to")).toEqual([[51.9, 10.4]]);

    const without = mountCard({ place: { name: "Somewhere", latitude: null, longitude: null } });
    expect(without.find('[data-test="place"]').exists()).toBe(false);
    expect(without.text()).toContain("Somewhere");
  });

  it("shows the photo with copyright and license", () => {
    const wrapper = mountCard({
      photo: {
        url_200: "/img?s=200",
        url_500: "/img?s=500",
        copyright_text: "Jane",
        license_code: "CC0",
        license_url: "https://license.test",
      },
    });

    expect(wrapper.find("img").attributes("src")).toBe("/img?s=200");
    expect(wrapper.find('[data-test="copyright"]').text()).toContain("© Jane");
    expect(wrapper.find('[data-test="copyright"] a').attributes("href")).toBe("https://license.test");
  });

  it("has no footer without a reference state", () => {
    expect(mountCard().find(".card-footer").exists()).toBe(false);
  });

  it("disables the button for an own event", () => {
    const wrapper = mountCard({ reference: { state: "own", reference_id: null } });

    expect(wrapper.find('[data-test="reference-own"]').attributes("disabled")).toBeDefined();
  });

  it("references an event that is not referenced", async () => {
    const wrapper = mountCard({ reference: { state: "none", reference_id: null } });

    await wrapper.find('[data-test="reference-none"]').trigger("click");

    expect(wrapper.emitted("reference")).toEqual([[11]]);
    expect(wrapper.text()).toContain("Not referenced");
  });

  it("deletes the reference of a referenced event", async () => {
    const wrapper = mountCard({ reference: { state: "referenced", reference_id: 77 } });

    await wrapper.find('[data-test="reference-referenced"]').trigger("click");

    expect(wrapper.emitted("unreference")).toEqual([[77]]);
    expect(wrapper.text()).toContain("Referenced");
  });

  it("blocks the button while busy", () => {
    const wrapper = mountCard(
      { reference: { state: "none", reference_id: null } },
      { busy: true },
    );

    expect(wrapper.find('[data-test="reference-none"]').attributes("disabled")).toBeDefined();
  });
});
