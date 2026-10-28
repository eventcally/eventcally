import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
vi.mock("@/shared/api", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
  },
}));
vi.mock("vue-router", () => ({
  RouterLink: defineComponent({ name: "RouterLink", render: () => null }),
}));
vi.mock("@/shared/ImageCropper.vue", () => ({
  __esModule: true,
  default: defineComponent({ name: "ImageCropper", render: () => null }),
}));

function modalStub(name: string) {
  return {
    __esModule: true,
    default: defineComponent({
      name,
      props: ["modelValue", "organizationId", "show"],
      emits: ["update:modelValue", "update:show", "created"],
      render: () => null,
    }),
  };
}
vi.mock("../components/EventPlaceCreateModal.vue", () => modalStub("EventPlaceCreateModal"));
vi.mock("../components/EventOrganizerCreateModal.vue", () => modalStub("EventOrganizerCreateModal"));
vi.mock("../components/RecurrenceRuleModal.vue", () => modalStub("RecurrenceRuleModal"));

import EventEditPage from "./EventEditPage.vue";

const assign = vi.fn();
const MESSAGES = {
  en: {
    "Create %(model_display_name)s": "Create {model_display_name}",
    "Update %(model_display_name)s": "Update {model_display_name}",
  },
};

function eventForm(overrides: Record<string, unknown> = {}) {
  return {
    id: null,
    name: "",
    description: null,
    date_definitions: [{ start: "2030-12-31T14:00:00", end: null, allday: false, recurrence_rule: null }],
    status: null,
    public_status: 2,
    status_choices: [],
    public_status_choices: [],
    organizer: null,
    event_place: null,
    co_organizers: [],
    category_ids: [3],
    category_choices: [
      { id: 3, name: "Other" },
      { id: 4, name: "Music" },
    ],
    custom_category_sets: [{ id: 7, label: "Region", selected: [] }],
    photo: null,
    licenses: [],
    external_link: null,
    ticket_link: null,
    tags: null,
    internal_tags: null,
    kid_friendly: false,
    accessible_for_free: false,
    registration_required: false,
    booked_up: false,
    age_from: null,
    age_to: null,
    expected_participants: null,
    price_info: null,
    target_group_origin: 1,
    target_group_origin_choices: [{ value: 1, label: "Both" }],
    attendance_mode: 1,
    attendance_mode_choices: [{ value: 1, label: "Offline" }],
    rating: 50,
    rating_choices: [
      { value: 0, label: "0" },
      { value: 50, label: "5" },
    ],
    reference_request_choices: [
      { id: 11, name: "Harzinfo" },
      { id: 12, name: "Kultur" },
    ],
    reference_request_ids: [11],
    can_create_place: true,
    can_create_organizer: true,
    ...overrides,
  };
}

const LOOKUP_ITEMS = [{ id: 21, name: "Found" }];

async function mountPage(props: Record<string, unknown> = { organizationId: 5 }, data: unknown = eventForm()) {
  GET.mockImplementation(async (path: string) =>
    path.endsWith("/form") || path.endsWith("/create-form")
      ? { data }
      : { data: { items: LOOKUP_ITEMS } },
  );
  const wrapper = mount(EventEditPage, {
    props: props as { organizationId: number },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: MESSAGES })],
    },
  });
  await flushPromises();
  return wrapper;
}

async function pick(wrapper: Awaited<ReturnType<typeof mountPage>>, inputId: string, keyword = "Fo") {
  await wrapper.find(`#${inputId}`).setValue(keyword);
  vi.advanceTimersByTime(250);
  await flushPromises();
  const option = wrapper
    .findAll('[data-test="option"]')
    .find((o) => o.element.closest(".app-typeahead")?.querySelector(`#${inputId}`));
  await option!.trigger("click");
}

describe("EventEditPage", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    GET.mockReset();
    POST.mockReset();
    PUT.mockReset();
    assign.mockReset();
    vi.stubGlobal("location", { ...window.location, assign });
    // jsdom has no layout: the page scrolls to the first invalid field.
    Element.prototype.scrollIntoView = vi.fn();
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    document.body.innerHTML = "";
  });

  it("loads the create form from a template and links the previous form", async () => {
    const wrapper = await mountPage({ organizationId: 5, templateId: 9 });

    expect(GET).toHaveBeenCalledWith("/bff/manage/organizations/{id}/events/create-form", {
      params: { path: { id: 5 }, query: { template_id: 9 } },
    });
    expect(wrapper.find('[data-test="legacy-form-link"] a').attributes("href")).toBe(
      "/manage/admin_unit/5/legacy/event/create?template_id=9",
    );
    expect(wrapper.text()).toContain("Create Event");
    expect(wrapper.find("#status").exists()).toBe(false);
    expect(wrapper.find("#reference_request_admin_unit_id-11").element).toHaveProperty("checked", true);
  });

  it("creates the event with every button's public status", async () => {
    POST.mockResolvedValue({ data: { id: 3, redirect_url: "/event/3/actions" } });
    const wrapper = await mountPage();

    await wrapper.find("#name").setValue("Stadtfest");
    await pick(wrapper, "organizer");
    await pick(wrapper, "event_place");
    await pick(wrapper, "co_organizers");
    await pick(wrapper, "custom_categories-set_7");
    await pick(wrapper, "categories", "mus");
    await wrapper.find("#reference_request_admin_unit_id-12").setValue(true);
    await wrapper.find("#reference_request_admin_unit_id-11").setValue(false);

    await wrapper.find("#submit_planned").trigger("click");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/manage/organizations/{id}/events", {
      params: { path: { id: 5 } },
      body: expect.objectContaining({
        name: "Stadtfest",
        public_status: 3,
        organizer_id: 21,
        event_place_id: 21,
        co_organizer_ids: [21],
        category_ids: [3, 4],
        custom_category_ids: [21],
        reference_request_ids: [12],
        date_definitions: [{ start: "2030-12-31T14:00", end: null, allday: false, recurrence_rule: null }],
      }),
    });
    expect(assign).toHaveBeenCalledWith("/event/3/actions");

    await wrapper.find("#submit_draft").trigger("click");
    expect(wrapper.find("#submit_draft").attributes("disabled")).toBeDefined();
  });

  it("publishes with the main button", async () => {
    POST.mockResolvedValue({ data: { id: 3, redirect_url: "/x" } });
    const wrapper = await mountPage();

    await wrapper.find("#submit").trigger("click");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST.mock.calls[0][1].body.public_status).toBe(2);
  });

  it("loads and updates an event with status and edit links", async () => {
    PUT.mockResolvedValue({ data: { id: 8, redirect_url: "/manage/admin_unit/5/events" } });
    const wrapper = await mountPage(
      { organizationId: 5, id: 8 },
      eventForm({
        id: 8,
        status: 2,
        public_status: 3,
        status_choices: [
          { value: 1, label: "Scheduled" },
          { value: 2, label: "Cancelled" },
        ],
        public_status_choices: [
          { value: 2, label: "Published" },
          { value: 3, label: "Planned" },
        ],
        organizer: { id: 1, name: "Org" },
        event_place: { id: 2, name: "Place" },
        photo: { image_base64: "data:image/png;base64,x", copyright_text: "Me", license_id: null },
      }),
    );

    expect(GET).toHaveBeenCalledWith("/bff/manage/organizations/{id}/events/{event_id}/form", {
      params: { path: { id: 5, event_id: 8 } },
    });
    expect(wrapper.find('[data-test="legacy-form-link"] a').attributes("href")).toBe(
      "/manage/admin_unit/5/legacy/event/8/update",
    );
    expect(wrapper.find('[data-test="organizer-edit"]').attributes("href")).toBe(
      "/manage/admin_unit/5/event_organizer/1/update",
    );
    expect(wrapper.find('[data-test="event_place-edit"]').attributes("href")).toBe(
      "/manage/admin_unit/5/event_place/2/update",
    );
    expect(wrapper.find('[data-test="reference-requests"]').exists()).toBe(false);

    await wrapper.find("#status").setValue("1");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith("/bff/manage/organizations/{id}/events/{event_id}", {
      params: { path: { id: 5, event_id: 8 } },
      body: expect.objectContaining({
        status: 1,
        public_status: 3,
        organizer_id: 1,
        photo: { image_base64: null, copyright_text: "Me", license_id: null },
      }),
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/5/events");
  });

  it("maps the field errors of a 422", async () => {
    POST.mockResolvedValue({
      error: {
        errors: [
          { loc: ["organizer_id"], msg: "Organizer required" },
          { loc: ["date_definitions", "0", "start"], msg: "Start late" },
          { loc: ["date_definitions"], msg: "No dates" },
          { loc: ["unknown"], msg: "Something else" },
        ],
      },
    });
    const wrapper = await mountPage();

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.text()).toContain("Organizer required");
    expect(wrapper.text()).toContain("Start late");
    expect(wrapper.text()).toContain("No dates");
    expect(wrapper.find(".alert-danger").text()).toBe("Something else");
    expect(Element.prototype.scrollIntoView).toHaveBeenCalled();
    expect(assign).not.toHaveBeenCalled();
  });

  it("shows other save errors", async () => {
    PUT.mockResolvedValue({ error: {} });
    const wrapper = await mountPage({ organizationId: 5, id: 8 }, eventForm({ id: 8 }));

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Error");
  });

  it("reports a load error", async () => {
    GET.mockResolvedValue({ error: { message: "Gone" } });
    const wrapper = mount(EventEditPage, {
      props: { organizationId: 5 },
      global: {
        plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: MESSAGES })],
      },
    });
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Gone");
    expect(wrapper.find("form").exists()).toBe(false);
  });

  it("adds and removes dates", async () => {
    const wrapper = await mountPage();

    await wrapper.find("#add-date-definition-btn").trigger("click");
    expect(wrapper.find("#date_definitions-1-start").element).toHaveProperty("value", "2030-12-31");

    await wrapper.find('[data-test="date_definitions-1-remove"]').trigger("click");
    expect(wrapper.find("#date_definitions-1-start").exists()).toBe(false);
  });

  it("adds a date to a form without dates", async () => {
    const wrapper = await mountPage({ organizationId: 5 }, eventForm({ date_definitions: [] }));

    await wrapper.find("#add-date-definition-btn").trigger("click");

    expect(wrapper.find("#date_definitions-0-start").exists()).toBe(true);
  });

  it("selects a place or organizer created in the modal", async () => {
    const wrapper = await mountPage();

    await wrapper.find("#event_place-new-btn").trigger("click");
    const placeModal = wrapper.findComponent({ name: "EventPlaceCreateModal" });
    expect(placeModal.props("modelValue")).toBe(true);
    placeModal.vm.$emit("created", { id: 31, name: "Neue Halle" });
    await wrapper.find("#organizer-new-btn").trigger("click");
    wrapper.findComponent({ name: "EventOrganizerCreateModal" }).vm.$emit("created", { id: 32, name: "Neuer Verein" });
    await flushPromises();

    expect(wrapper.find("#event_place").element).toHaveProperty("value", "Neue Halle");
    expect(wrapper.find("#organizer").element).toHaveProperty("value", "Neuer Verein");
  });

  it("hides the new buttons without the permissions", async () => {
    const wrapper = await mountPage(
      { organizationId: 5 },
      eventForm({ can_create_place: false, can_create_organizer: false, reference_request_choices: [] }),
    );

    expect(wrapper.find("#event_place-new-btn").exists()).toBe(false);
    expect(wrapper.find("#organizer-new-btn").exists()).toBe(false);
    expect(wrapper.find('[data-test="reference-requests"]').exists()).toBe(false);
  });
});
