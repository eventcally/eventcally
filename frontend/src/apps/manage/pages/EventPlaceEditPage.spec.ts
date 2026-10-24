import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
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

// The cropper has its own spec (and needs a canvas).
vi.mock("@/shared/ImageCropper.vue", () => ({
  __esModule: true,
  default: defineComponent({ name: "ImageCropper", render: () => null }),
}));

import EventPlaceEditPage from "./EventPlaceEditPage.vue";

const assign = vi.fn();
const MESSAGES = {
  en: {
    "Create %(model_display_name)s": "Create {model_display_name}",
    "Update %(model_display_name)s": "Update {model_display_name}",
  },
};

const emptyLocation = {
  street: null,
  postalCode: null,
  city: null,
  state: null,
  latitude: null,
  longitude: null,
};

function placeForm(overrides: Record<string, unknown> = {}) {
  return {
    id: null,
    name: "",
    url: null,
    description: null,
    location: emptyLocation,
    photo: null,
    licenses: [{ id: 1, name: "CC0 (Zero)" }],
    ...overrides,
  };
}

async function mountPage(
  props: { organizationId: number; id?: number } = { organizationId: 5 },
  data: Record<string, unknown> = placeForm(),
  taken = false,
) {
  GET.mockImplementation(async (path: string) =>
    path.endsWith("/name-availability") ? { data: { name_taken: taken } } : { data },
  );
  const wrapper = mount(EventPlaceEditPage, {
    props,
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: MESSAGES })],
    },
  });
  await flushPromises();
  return wrapper;
}

describe("EventPlaceEditPage", () => {
  beforeEach(() => {
    [GET, POST, PUT, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
    vi.useRealTimers();
  });

  it("loads the empty create form with optional location", async () => {
    const wrapper = await mountPage();

    expect(GET.mock.calls[0]).toEqual([
      "/bff/manage/organizations/{id}/event-places/create-form",
      { params: { path: { id: 5 } } },
    ]);
    expect((wrapper.find("#name").element as HTMLInputElement).value).toBe("");
    expect(wrapper.find("#submit").text()).toBe("Create place");
    expect(wrapper.find("[data-test=place-lookup]").exists()).toBe(true);
    expect(wrapper.findAll("#location-google_place")).toHaveLength(1);
    expect(wrapper.find("#location-postalCode").attributes("required")).toBeUndefined();
    expect(wrapper.find(".breadcrumb").text()).toContain("Create Place");
    expect(wrapper.find(".breadcrumb a").attributes("href")).toBe("/manage/admin_unit/5/event_places");
  });

  it("loads the place of an update with its stored photo", async () => {
    const wrapper = await mountPage(
      { organizationId: 5, id: 8 },
      placeForm({
        id: 8,
        name: "Kaiserpfalz",
        url: "https://example.org",
        description: "Alt",
        location: { ...emptyLocation, street: "Markt 1", latitude: 51.9 },
        photo: { image_base64: "data:image/png;base64,AAAA", copyright_text: "Me", license_id: 1 },
      }),
    );

    expect(GET.mock.calls[0]).toEqual([
      "/bff/manage/organizations/{id}/event-places/{place_id}",
      { params: { path: { id: 5, place_id: 8 } } },
    ]);
    expect((wrapper.find("#name").element as HTMLInputElement).value).toBe("Kaiserpfalz");
    expect((wrapper.find("#url").element as HTMLInputElement).value).toBe("https://example.org");
    expect((wrapper.find("#location-street").element as HTMLInputElement).value).toBe("Markt 1");
    expect((wrapper.find("#location-latitude").element as HTMLInputElement).value).toBe("51.9");
    expect(wrapper.find("[data-test=preview]").attributes("src")).toBe("data:image/png;base64,AAAA");
    expect(wrapper.find("#submit").text()).toBe("Update place");
    expect(wrapper.find(".breadcrumb").text()).toContain("Update Place");
  });

  it("reports a load error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const wrapper = mount(EventPlaceEditPage, {
      props: { organizationId: 5 },
      global: {
        plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: MESSAGES })],
      },
    });
    await flushPromises();

    expect(wrapper.text()).toContain("Forbidden");
    expect(wrapper.find("form").exists()).toBe(false);
  });

  it("falls back to a generic load error", async () => {
    GET.mockResolvedValue({});
    const wrapper = mount(EventPlaceEditPage, {
      props: { organizationId: 5 },
      global: {
        plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: MESSAGES })],
      },
    });
    await flushPromises();

    expect(wrapper.text()).toContain("Error");
  });

  it("checks the name live and ignores the unchanged name", async () => {
    vi.useFakeTimers();
    const wrapper = await mountPage({ organizationId: 5, id: 8 }, placeForm({ id: 8, name: "Alt" }), true);
    GET.mockClear();

    await wrapper.find("#name").setValue("Alt");
    await vi.advanceTimersByTimeAsync(300);
    expect(GET).not.toHaveBeenCalled();

    await wrapper.find("#name").setValue("Neu");
    await vi.advanceTimersByTimeAsync(300);
    await flushPromises();

    expect(GET).toHaveBeenCalledWith(
      "/bff/manage/organizations/{id}/event-places/name-availability",
      { params: { path: { id: 5 }, query: { name: "Neu", exclude_id: 8 } } },
    );
    expect(wrapper.find("#name").classes()).toContain("is-invalid");
    expect(wrapper.text()).toContain("A place already exists with this name.");
  });

  it("marks a free name as valid", async () => {
    vi.useFakeTimers();
    const wrapper = await mountPage();

    await wrapper.find("#name").setValue("Frei");
    await vi.advanceTimersByTimeAsync(300);
    await flushPromises();

    expect(wrapper.find("#name").classes()).toContain("is-valid");
  });

  it("ignores a stale availability answer", async () => {
    vi.useFakeTimers();
    const wrapper = await mountPage({ organizationId: 5 }, placeForm(), true);

    await wrapper.find("#name").setValue("Erst");
    await vi.advanceTimersByTimeAsync(300);
    await wrapper.find("#name").setValue("Dann");
    await flushPromises();

    expect(wrapper.find("#name").classes()).not.toContain("is-invalid");
  });

  it("fills the address and overwrites the name with a picked Google place", async () => {
    vi.useFakeTimers();
    const address = {
      street: "Kaiserbleek 6",
      postalCode: "38640",
      city: "Goslar",
      state: "Niedersachsen",
      latitude: 51.9,
      longitude: 10.4,
    };
    const wrapper = await mountPage();
    GET.mockImplementation(async (path: string) => {
      if (path === "/bff/manage/places") {
        return { data: { items: [{ gmaps_id: "abc", text: "Kaiserpfalz, Goslar", main_text: "Kaiserpfalz" }] } };
      }
      if (path.endsWith("/name-availability")) return { data: { name_taken: false } };
      return { data: address };
    });

    await wrapper.find("#name").setValue("Eigener Name");
    await wrapper.find("#location-google_place").setValue("Kaiser");
    await vi.advanceTimersByTimeAsync(300);
    await flushPromises();
    await wrapper.find("[data-test=option]").trigger("click");
    await flushPromises();
    await vi.advanceTimersByTimeAsync(300);
    await flushPromises();

    expect((wrapper.find("#name").element as HTMLInputElement).value).toBe("Kaiserpfalz");
    expect((wrapper.find("#location-street").element as HTMLInputElement).value).toBe("Kaiserbleek 6");
    expect((wrapper.find("#location-city").element as HTMLInputElement).value).toBe("Goslar");
    expect(GET).toHaveBeenCalledWith(
      "/bff/manage/organizations/{id}/event-places/name-availability",
      { params: { path: { id: 5 }, query: { name: "Kaiserpfalz", exclude_id: undefined } } },
    );
  });

  it("keeps the name when Google sends no main text", async () => {
    vi.useFakeTimers();
    const wrapper = await mountPage();
    GET.mockImplementation(async (path: string) =>
      path === "/bff/manage/places"
        ? { data: { items: [{ gmaps_id: "abc", text: "Goslar" }] } }
        : { data: { ...emptyLocation, city: "Goslar", street: "", postalCode: "", state: "" } },
    );

    await wrapper.find("#name").setValue("Eigener Name");
    await wrapper.find("#location-google_place").setValue("Gos");
    await vi.advanceTimersByTimeAsync(300);
    await flushPromises();
    await wrapper.find("[data-test=option]").trigger("click");
    await flushPromises();

    expect((wrapper.find("#name").element as HTMLInputElement).value).toBe("Eigener Name");
    expect((wrapper.find("#location-city").element as HTMLInputElement).value).toBe("Goslar");
  });

  it("creates the place and follows the redirect", async () => {
    POST.mockResolvedValue({ data: { id: 9, redirect_url: "/manage/admin_unit/5/event_places" } });
    const wrapper = await mountPage();

    await wrapper.find("#name").setValue("Neuer Ort");
    await wrapper.find("#url").setValue("https://example.org");
    await wrapper.find("#description").setValue("Text");
    await wrapper.find("#location-city").setValue("Goslar");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/manage/organizations/{id}/event-places", {
      params: { path: { id: 5 } },
      body: {
        name: "Neuer Ort",
        url: "https://example.org",
        description: "Text",
        location: {
          street: "",
          postalCode: "",
          city: "Goslar",
          state: "",
          latitude: null,
          longitude: null,
        },
        photo: null,
      },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/5/event_places");
  });

  it("updates the place and keeps the stored photo", async () => {
    PUT.mockResolvedValue({ data: { id: 8, redirect_url: "/manage/admin_unit/5/event_places" } });
    const wrapper = await mountPage(
      { organizationId: 5, id: 8 },
      placeForm({
        id: 8,
        name: "Alt",
        photo: { image_base64: "data:image/png;base64,AAAA", copyright_text: "Me", license_id: null },
      }),
    );

    await wrapper.find("#name").setValue("Neu");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    const call = PUT.mock.calls[0];
    expect(call[0]).toBe("/bff/manage/organizations/{id}/event-places/{place_id}");
    expect(call[1].params).toEqual({ path: { id: 5, place_id: 8 } });
    expect(call[1].body.name).toBe("Neu");
    expect(call[1].body.photo).toEqual({ image_base64: null, copyright_text: "Me", license_id: null });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/5/event_places");
  });

  it("maps the field errors of a 422", async () => {
    POST.mockResolvedValue({
      error: {
        errors: [
          { loc: ["name"], msg: "A place already exists with this name." },
          { loc: ["photo", "copyright_text"], msg: "This field is required." },
          { loc: ["location", "postalCode"], msg: "Too long" },
          { loc: ["other"], msg: "Unknown" },
        ],
      },
    });
    const wrapper = await mountPage();
    wrapper.element.scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = vi.fn();

    await wrapper.find("#name").setValue("Neuer Ort");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find("#name").classes()).toContain("is-invalid");
    expect(wrapper.find("#location-postalCode").classes()).toContain("is-invalid");
    expect(wrapper.text()).toContain("A place already exists with this name.");
    expect(wrapper.find("[role=alert]").text()).toContain("Unknown");
    expect(assign).not.toHaveBeenCalled();
    expect(wrapper.find("#submit").attributes("disabled")).toBeUndefined();
  });

  it("shows other save errors", async () => {
    POST.mockResolvedValue({ error: { message: "Server down" } });
    const wrapper = await mountPage();

    await wrapper.find("#name").setValue("Neuer Ort");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find("[role=alert]").text()).toBe("Server down");

    POST.mockResolvedValue({});
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find("[role=alert]").text()).toBe("Error");
  });
});
