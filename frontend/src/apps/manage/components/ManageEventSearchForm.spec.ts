import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import { emptyFilter } from "../manageEventQuery";
import ManageEventSearchForm from "./ManageEventSearchForm.vue";

const defaults = { date_from: "2030-10-01" };
const options = {
  default_date_from: "2030-10-01",
  categories: [{ id: 3, name: "Music" }],
  statuses: [{ value: 1, name: "scheduled", label: "Scheduled" }],
  public_statuses: [{ value: 1, name: "draft", label: "Draft" }],
  distances: [{ value: 500, label: "500 m" }],
  can_write: true,
  can_request_reference: true,
};

function mountForm(filter = {}, refs: Record<string, unknown> = {}) {
  return mount(ManageEventSearchForm, {
    props: {
      organizationId: 3,
      filter: { ...emptyFilter(defaults), ...filter },
      options,
      organizer: null,
      eventPlace: null,
      ...refs,
    },
    global: { plugins: [createI18n({ legacy: false, locale: "en", messages: { en: {} } })] },
  });
}

const extendedVisible = (wrapper: ReturnType<typeof mountForm>) =>
  (wrapper.find('[data-test="extended"]').element as HTMLElement).style.display !== "none";

describe("ManageEventSearchForm", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    GET.mockReset().mockImplementation((path: string) =>
      Promise.resolve(
        path.endsWith("/event-organizers")
          ? { data: { items: [{ id: 9, name: "Jam Crew" }] } }
          : { data: { items: [{ id: 8, name: "Jam Hall, Goslar" }] } },
      ),
    );
  });
  afterEach(() => vi.useRealTimers());

  const formVisible = (wrapper: ReturnType<typeof mountForm>) =>
    (wrapper.find('[data-test="form"]').element as HTMLElement).style.display !== "none";

  it("is collapsed without active filters and opens with the Filter button", async () => {
    const wrapper = mountForm();
    expect(formVisible(wrapper)).toBe(false);

    await wrapper.find('[data-test="toggle-filter"]').trigger("click");
    expect(formVisible(wrapper)).toBe(true);
  });

  it("starts open when the URL sets a filter", () => {
    expect(formVisible(mountForm({ keyword: "Jam" }))).toBe(true);
    expect(formVisible(mountForm({ sort: "-created_at" }))).toBe(true);
    expect(formVisible(mountForm({ date_from: "2031-01-01" }))).toBe(true);
    expect(formVisible(mountForm({ is_recurring: "1" }))).toBe(true);
  });

  it("starts collapsed and expands on demand", async () => {
    const wrapper = mountForm();
    expect(extendedVisible(wrapper)).toBe(false);

    await wrapper.find("#toggle-search-btn").trigger("click");
    expect(extendedVisible(wrapper)).toBe(true);
  });

  it("starts expanded when an extended filter is set", () => {
    expect(extendedVisible(mountForm({ event_place_id: 5 }))).toBe(true);
  });

  it("shows the name of a preselected place", () => {
    const wrapper = mountForm({ event_place_id: 5 }, { eventPlace: { id: 5, name: "Rathaus" } });
    expect((wrapper.find("#event_place_id").element as HTMLInputElement).value).toBe("Rathaus");
  });

  it("emits the edited filter with the page reset", async () => {
    const wrapper = mountForm({ page: 3 });
    await wrapper.find("#keyword").setValue("Jam");
    await wrapper.find("#is_recurring").setValue("1");
    await wrapper.find("form").trigger("submit");

    const [filter] = wrapper.emitted("search")![0] as [Record<string, unknown>];
    expect(filter).toMatchObject({ keyword: "Jam", is_recurring: "1", page: 1 });
  });

  it("picks an organizer from the lookup of the organization", async () => {
    const wrapper = mountForm();
    await wrapper.find("#organizer_id").setValue("Jam");
    await vi.advanceTimersByTimeAsync(300);
    await flushPromises();

    expect(GET).toHaveBeenCalledWith("/bff/manage/organizations/{id}/event-organizers", {
      params: { path: { id: 3 }, query: { keyword: "Jam" } },
    });
    await wrapper.find('[data-test="option"]').trigger("click");
    await wrapper.find("form").trigger("submit");

    const [filter] = wrapper.emitted("search")![0] as [Record<string, unknown>];
    expect(filter.organizer_id).toBe(9);
  });

  it("resets to the default filter", async () => {
    const wrapper = mountForm({ keyword: "x", category_id: 3 });
    await wrapper.find('[data-test="reset"]').trigger("click");

    expect(wrapper.emitted("search")![0]).toEqual([emptyFilter(defaults)]);
  });
});
