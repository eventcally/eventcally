import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
const PUT = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), PUT: (...a: unknown[]) => PUT(...a) },
}));

const success = vi.fn();
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

// The cropper has its own spec (and needs a canvas).
vi.mock("@/shared/ImageCropper.vue", () => ({
  __esModule: true,
  default: defineComponent({ name: "ImageCropper", render: () => null }),
}));

import { setFlash, takeFlash } from "../flash";
import OrganizationSettingsPage from "./OrganizationSettingsPage.vue";

const reload = vi.fn();

function settings(overrides: Record<string, unknown> = {}) {
  return {
    id: 3,
    name: "Meine Crew",
    short_name: "meinecrew",
    description: "Hi",
    location: { street: "Markt 1", postalCode: "38640", city: "Goslar", state: "", latitude: 51.9, longitude: null },
    logo: null,
    url: "https://example.org",
    email: null,
    phone: null,
    fax: null,
    can_verify_other: false,
    verification_requests: null,
    licenses: [{ id: 1, name: "CC0 (Zero)" }],
    deletion_requested_at: null,
    ...overrides,
  };
}

async function mountPage(data = settings()) {
  GET.mockImplementation(async (path: string) =>
    path.endsWith("/settings") ? { data } : { data: { name_taken: false, short_name_taken: null } },
  );
  const wrapper = mount(OrganizationSettingsPage, {
    props: { organizationId: 3 },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  await flushPromises();
  return wrapper;
}

const value = (wrapper: ReturnType<typeof mount>, selector: string) =>
  (wrapper.find(selector).element as HTMLInputElement).value;

describe("OrganizationSettingsPage", () => {
  beforeEach(() => {
    [GET, PUT, reload, success].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { reload });
    vi.useRealTimers();
    sessionStorage.clear();
  });

  it("fills the form from the settings", async () => {
    const wrapper = await mountPage();

    expect(value(wrapper, "#name")).toBe("Meine Crew");
    expect(value(wrapper, "#short_name")).toBe("meinecrew");
    expect(value(wrapper, "#description")).toBe("Hi");
    expect(value(wrapper, "#location-city")).toBe("Goslar");
    expect(value(wrapper, "#location-latitude")).toBe("51.9");
    expect(value(wrapper, "#additional_information-url")).toBe("https://example.org");
    expect(wrapper.find("[data-test=verification-requests]").exists()).toBe(false);
    expect(wrapper.find("[data-test=delete]").attributes("href")).toBe(
      "/manage/admin_unit/3/request-deletion",
    );
  });

  it("reports a load error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const wrapper = mount(OrganizationSettingsPage, {
      props: { organizationId: 3 },
      global: { plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })] },
    });
    await flushPromises();

    expect(wrapper.text()).toContain("Forbidden");
    expect(wrapper.find("form").exists()).toBe(false);
  });

  it("falls back to a generic message when the load error has none", async () => {
    GET.mockResolvedValue({});
    const wrapper = mount(OrganizationSettingsPage, {
      props: { organizationId: 3 },
      global: { plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })] },
    });
    await flushPromises();

    expect(wrapper.text()).toContain("Error");
  });

  it("shows the deletion notice instead of the delete button", async () => {
    const wrapper = await mountPage(settings({ deletion_requested_at: "2026-10-23T10:00:00" }));

    expect(wrapper.text()).toContain("The organization is scheduled for deletion.");
    expect(wrapper.find("a.alert-link").attributes("href")).toBe("/manage/admin_unit/3/cancel-deletion");
    expect(wrapper.find("[data-test=delete]").exists()).toBe(false);
  });

  it("shows the stored logo and keeps it unchanged on save", async () => {
    const wrapper = await mountPage(
      settings({
        logo: { image_base64: "data:image/png;base64,AAAA", copyright_text: "Me", license_id: 1 },
      }),
    );
    PUT.mockResolvedValue({ response: { ok: true } });

    expect(wrapper.find("[data-test=preview]").attributes("src")).toBe("data:image/png;base64,AAAA");
    expect(value(wrapper, "#logo-copyright_text")).toBe("Me");

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT.mock.calls[0][1].body.logo).toEqual({
      image_base64: null,
      copyright_text: "Me",
      license_id: 1,
    });
  });

  it("removes the logo", async () => {
    const wrapper = await mountPage(
      settings({ logo: { image_base64: "data:image/png;base64,AAAA", copyright_text: "Me", license_id: null } }),
    );
    PUT.mockResolvedValue({ response: { ok: true } });

    await wrapper.find("[data-test=remove]").trigger("click");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT.mock.calls[0][1].body.logo).toBeNull();
  });

  it("saves, sets the flash message and reloads", async () => {
    const wrapper = await mountPage();
    PUT.mockResolvedValue({ response: { ok: true } });

    await wrapper.find("#name").setValue("Neue Crew");
    await wrapper.find("#location-city").setValue("Bad Harzburg");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    const [path, options] = PUT.mock.calls[0];
    expect(path).toBe("/bff/manage/organizations/{id}/settings");
    expect(options.params.path.id).toBe(3);
    expect(options.body).toMatchObject({
      name: "Neue Crew",
      short_name: "meinecrew",
      location: { city: "Bad Harzburg", postalCode: "38640" },
      logo: null,
      verification_requests: null,
    });
    expect(takeFlash()).toBe("Organization successfully updated");
    expect(reload).toHaveBeenCalled();
  });

  it("sends the verification requests of an organization that may verify", async () => {
    const wrapper = await mountPage(
      settings({
        can_verify_other: true,
        verification_requests: { allowed: false, text: null, postal_codes: ["12345"] },
      }),
    );
    PUT.mockResolvedValue({ response: { ok: true } });

    await wrapper.find("#verification-allowed").setValue(true);
    await wrapper.find("#verification-text").setValue("Please verify");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT.mock.calls[0][1].body.verification_requests).toEqual({
      allowed: true,
      text: "Please verify",
      postal_codes: ["12345"],
    });
  });

  it("shows the field errors of a 422 and the unmatched ones in an alert", async () => {
    const wrapper = await mountPage();
    PUT.mockResolvedValue({
      response: { ok: false },
      error: {
        message: "Unprocessable",
        errors: [
          { loc: ["name"], msg: "Name is already taken" },
          { loc: ["location", "city"], msg: "This field is required." },
          { loc: ["logo", "copyright_text"], msg: "Hidden" },
          { loc: ["body"], msg: "Something else" },
        ],
      },
    });
    wrapper.element.scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = vi.fn();

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find("#name").classes()).toContain("is-invalid");
    expect(wrapper.text()).toContain("Name is already taken");
    expect(wrapper.find("#location-city").classes()).toContain("is-invalid");
    expect(wrapper.find("[role=alert]").text()).toContain("Something else");
    expect(reload).not.toHaveBeenCalled();
    expect(Element.prototype.scrollIntoView).toHaveBeenCalled();
  });

  it("shows other save errors in an alert", async () => {
    const wrapper = await mountPage();
    PUT.mockResolvedValue({ response: { ok: false }, error: { message: "Boom" } });

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find("[role=alert]").text()).toBe("Boom");
  });

  it("falls back to a generic message for an unknown save error", async () => {
    const wrapper = await mountPage();
    PUT.mockResolvedValue({ response: { ok: false }, error: {} });

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find("[role=alert]").text()).toBe("Error");
  });

  it("ignores a second submit while saving", async () => {
    const wrapper = await mountPage();
    PUT.mockReturnValue(new Promise(() => {}));

    await wrapper.find("form").trigger("submit");
    await wrapper.find("form").trigger("submit");

    expect(PUT).toHaveBeenCalledTimes(1);
  });

  describe("live name check", () => {
    const availability = () =>
      GET.mock.calls.filter(([path]) => path.endsWith("/name-availability"));

    it("marks a taken name and a taken short name", async () => {
      vi.useFakeTimers();
      const wrapper = await mountPage();
      GET.mockImplementation(async () => ({ data: { name_taken: true, short_name_taken: true } }));

      await wrapper.find("#name").setValue("Andere Crew");
      await wrapper.find("#short_name").setValue("anderecrew");
      await vi.advanceTimersByTimeAsync(300);
      await flushPromises();

      expect(wrapper.find("#name").classes()).toContain("is-invalid");
      expect(wrapper.find("#short_name").classes()).toContain("is-invalid");
      expect(wrapper.text()).toContain("Name is already taken");
      expect(wrapper.text()).toContain("Short name is already taken");
    });

    it("marks a free name as valid", async () => {
      vi.useFakeTimers();
      const wrapper = await mountPage();
      GET.mockImplementation(async () => ({ data: { name_taken: false, short_name_taken: false } }));

      await wrapper.find("#name").setValue("Freie Crew");
      await wrapper.find("#short_name").setValue("freiecrew");
      await vi.advanceTimersByTimeAsync(300);
      await flushPromises();

      expect(wrapper.find("#name").classes()).toContain("is-valid");
      expect(wrapper.find("#short_name").classes()).toContain("is-valid");
    });

    it("does not check the unchanged, too short or malformed values", async () => {
      vi.useFakeTimers();
      const wrapper = await mountPage();
      GET.mockClear();

      await wrapper.find("#name").setValue("abc");
      await wrapper.find("#short_name").setValue("bad name!");
      await wrapper.find("#name").setValue("Meine Crew");
      await vi.advanceTimersByTimeAsync(500);

      expect(availability()).toHaveLength(0);
    });

    it("ignores a response for a value that was edited meanwhile", async () => {
      vi.useFakeTimers();
      const wrapper = await mountPage();
      GET.mockImplementation(async () => ({ data: { name_taken: true, short_name_taken: null } }));

      await wrapper.find("#name").setValue("Andere Crew");
      await vi.advanceTimersByTimeAsync(300);
      await wrapper.find("#name").setValue("Wieder frei");
      await flushPromises();

      expect(wrapper.find("#name").classes()).not.toContain("is-invalid");
    });

    it("ignores a failed check", async () => {
      vi.useFakeTimers();
      const wrapper = await mountPage();
      GET.mockImplementation(async () => ({ error: {} }));

      await wrapper.find("#name").setValue("Andere Crew");
      await vi.advanceTimersByTimeAsync(300);
      await flushPromises();

      expect(wrapper.find("#name").classes()).not.toContain("is-invalid");
    });
  });

  it("shows the flash message of the previous save", async () => {
    setFlash("Organization successfully updated");

    await mountPage();

    expect(success).toHaveBeenCalledWith("Organization successfully updated");
  });
});
