import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import { emptyFilter } from "../eventDateQuery";
import EventDateSearchForm from "./EventDateSearchForm.vue";

const defaults = { date_from: "2030-10-01" };
const baseOptions = {
  default_date_from: "2030-10-01",
  categories: [{ id: 3, name: "Music" }],
  distances: [{ value: 500, label: "500 m" }],
  sorts: [
    { value: "start", label: "Earliest start first" },
    { value: "-created_at", label: "Newest first" },
  ],
  organization: null,
  organizer: null,
  referencing_organization: null,
  calendar_organization: null,
  calendars: [] as { id: number; name: string; organization: { id: number; name: string } }[],
};

function mountForm(filter = {}, options: Record<string, unknown> = {}) {
  return mount(EventDateSearchForm, {
    props: { filter: { ...emptyFilter(defaults), ...filter }, options: { ...baseOptions, ...options } },
    global: { plugins: [createI18n({ legacy: false, locale: "en", messages: { en: {} } })] },
  });
}

const extendedVisible = (wrapper: ReturnType<typeof mountForm>) =>
  (wrapper.find('[data-test="extended"]').element as HTMLElement).style.display !== "none";

describe("EventDateSearchForm", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    GET.mockReset().mockImplementation((path: string) =>
      Promise.resolve(
        path === "/bff/public/organizations"
          ? { data: { items: [{ id: 7, name: "Jam Org" }] } }
          : path === "/bff/public/calendars"
            ? { data: { items: [{ id: 5, name: "Sport", organization: { id: 7, name: "Jam Org" } }] } }
            : { data: { items: [{ id: 9, name: "Jam Crew" }] } },
      ),
    );
  });
  afterEach(() => vi.useRealTimers());

  it("starts collapsed without extended filters and expands on demand", async () => {
    const wrapper = mountForm();
    expect(extendedVisible(wrapper)).toBe(false);

    await wrapper.find("#toggle-search-btn").trigger("click");

    expect(extendedVisible(wrapper)).toBe(true);
  });

  it("labels the toggle by its state", async () => {
    const wrapper = mountForm();
    const toggle = wrapper.find("#toggle-search-btn");
    expect(toggle.text()).toBe("More filters");

    await toggle.trigger("click");

    expect(toggle.text()).toBe("Fewer filters");
  });

  it("shows the filtered calendars with their organization and picks more", async () => {
    const wrapper = mountForm(
      { calendar_id: [4] },
      { calendars: [{ id: 4, name: "Feste", organization: { id: 8, name: "Stadt" } }] },
    );
    expect(extendedVisible(wrapper)).toBe(true);
    expect(wrapper.findAll('[data-test="chip"]').map((chip) => chip.text())).toEqual([
      "Feste (Stadt)",
    ]);

    await wrapper.find("#calendar_id").setValue("Spo");
    vi.advanceTimersByTime(250);
    await flushPromises();
    expect(GET).toHaveBeenLastCalledWith("/bff/public/calendars", {
      params: { query: { keyword: "Spo", per_page: 10 } },
    });
    expect(wrapper.find('[data-test="option"]').text()).toContain("Sport (Jam Org)");
    await wrapper.find('[data-test="option"]').trigger("click");

    await wrapper.find("form").trigger("submit");
    expect(wrapper.emitted("search")![0][0]).toMatchObject({ calendar_id: [4, 5] });
  });

  it("starts expanded when an extended filter is set", () => {
    expect(extendedVisible(mountForm({ tag: "live" }))).toBe(true);
  });

  it("submits the draft on page 1", async () => {
    const wrapper = mountForm({ page: 4 });

    await wrapper.find("#keyword").setValue("jam");
    await wrapper.find("form").trigger("submit");

    expect(wrapper.emitted("search")).toHaveLength(1);
    expect(wrapper.emitted("search")![0][0]).toMatchObject({ keyword: "jam", page: 1 });
  });

  it("emits toggle-map", async () => {
    const wrapper = mountForm();

    await wrapper.find("#toggle-map-btn").trigger("click");

    expect(wrapper.emitted("toggle-map")).toHaveLength(1);
  });

  it("shows the not-referenced checkbox only for a referencing organization", () => {
    expect(mountForm().find('[data-test="not-referenced"]').exists()).toBe(false);
    expect(
      mountForm({}, { referencing_organization: { id: 1, name: "Mine" } })
        .find('[data-test="not-referenced"]')
        .exists(),
    ).toBe(true);
  });

  it("fills the pickers from the options and disables the organizer without an organization", () => {
    const without = mountForm();
    expect((without.find("#organizer_id").element as HTMLInputElement).disabled).toBe(true);

    const wrapper = mountForm(
      { admin_unit_id: 7, organizer_id: 9 },
      { organization: { id: 7, name: "Jam Org" }, organizer: { id: 9, name: "Jam Crew" } },
    );
    expect((wrapper.find("#admin_unit_id").element as HTMLInputElement).value).toBe("Jam Org");
    expect((wrapper.find("#organizer_id").element as HTMLInputElement).value).toBe("Jam Crew");
    expect((wrapper.find("#organizer_id").element as HTMLInputElement).disabled).toBe(false);
  });

  it("picks an organization, then searches its organizers", async () => {
    const wrapper = mountForm({ tag: "x" });

    await wrapper.find("#admin_unit_id").setValue("Ja");
    vi.advanceTimersByTime(250);
    await flushPromises();
    await wrapper.find('[data-test="option"]').trigger("click");

    expect((wrapper.find("#organizer_id").element as HTMLInputElement).disabled).toBe(false);

    await wrapper.find("#organizer_id").setValue("Cr");
    vi.advanceTimersByTime(250);
    await flushPromises();
    expect(GET).toHaveBeenLastCalledWith("/bff/public/organizations/{id}/organizers", {
      params: { path: { id: 7 }, query: { keyword: "Cr", per_page: 5 } },
    });
    await wrapper.findAll('[data-test="option"]')[0].trigger("click");

    await wrapper.find("form").trigger("submit");
    expect(wrapper.emitted("search")![0][0]).toMatchObject({ admin_unit_id: 7, organizer_id: 9 });
  });

  it("clears the organizer when the organization changes", async () => {
    const wrapper = mountForm(
      { admin_unit_id: 7, organizer_id: 9 },
      { organization: { id: 7, name: "Jam Org" }, organizer: { id: 9, name: "Jam Crew" } },
    );

    await wrapper.find("#admin_unit_id").setValue("Other");
    await flushPromises();

    expect((wrapper.find("#organizer_id").element as HTMLInputElement).value).toBe("");
    expect((wrapper.find("#organizer_id").element as HTMLInputElement).disabled).toBe(true);
    await wrapper.find("form").trigger("submit");
    expect(wrapper.emitted("search")![0][0]).toMatchObject({
      admin_unit_id: null,
      organizer_id: null,
    });
  });

  it("resets the draft when the applied filter changes", async () => {
    const wrapper = mountForm({ keyword: "jam" });
    await wrapper.find("#keyword").setValue("changed");

    await wrapper.setProps({ filter: { ...emptyFilter(defaults), keyword: "other" } });

    expect((wrapper.find("#keyword").element as HTMLInputElement).value).toBe("other");
  });
});
