import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));

const route = { query: {} as Record<string, string> };
vi.mock("vue-router", () => ({
  useRoute: () => route,
  RouterLink: defineComponent({ name: "RouterLink", render: () => null }),
}));

// The cropper has its own spec (and needs a canvas).
vi.mock("@/shared/ImageCropper.vue", () => ({
  __esModule: true,
  default: defineComponent({ name: "ImageCropper", render: () => null }),
}));

import OrganizationCreatePage from "./OrganizationCreatePage.vue";

const assign = vi.fn();
const MESSAGES = { en: { "Relation to %(admin_unit_name)s": "Relation to {admin_unit_name}" } };

function createForm(overrides: Record<string, unknown> = {}) {
  return {
    name: "",
    invitation_id: null,
    relation: null,
    licenses: [{ id: 1, name: "CC0 (Zero)" }],
    ...overrides,
  };
}

async function mountPage(data: Record<string, unknown> = createForm(), availability = false) {
  GET.mockImplementation(async (path: string) =>
    path.endsWith("/create-form")
      ? { data }
      : { data: { name_taken: availability, short_name_taken: availability } },
  );
  const wrapper = mount(OrganizationCreatePage, {
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: MESSAGES })],
      stubs: { AppBreadcrumb: true },
    },
  });
  await flushPromises();
  return wrapper;
}

async function fillRequired(wrapper: ReturnType<typeof mount>) {
  await wrapper.find("#name").setValue("Neue Crew");
  await wrapper.find("#short_name").setValue("neuecrew");
  await wrapper.find("#location-postalCode").setValue("38640");
  await wrapper.find("#location-city").setValue("Goslar");
}

describe("OrganizationCreatePage", () => {
  beforeEach(() => {
    [GET, POST, assign].forEach((f) => f.mockReset());
    route.query = {};
    vi.stubGlobal("location", { assign });
    vi.useRealTimers();
  });

  it("loads the empty form without relation card", async () => {
    const wrapper = await mountPage();

    expect(GET.mock.calls[0][0]).toBe("/bff/manage/organizations/create-form");
    expect(GET.mock.calls[0][1]).toEqual({ params: { query: { invitation_id: undefined } } });
    expect((wrapper.find("#name").element as HTMLInputElement).value).toBe("");
    expect(wrapper.find("[data-test=relation]").exists()).toBe(false);
    expect(wrapper.find("#submit").text()).toBe("Create");
  });

  it("reports a load error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const wrapper = mount(OrganizationCreatePage, {
      global: {
        plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: MESSAGES })],
        stubs: { AppBreadcrumb: true },
      },
    });
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
    expect(wrapper.find("form").exists()).toBe(false);
  });

  it("falls back to a generic message when the load error has none", async () => {
    GET.mockResolvedValue({});
    const wrapper = mount(OrganizationCreatePage, {
      global: {
        plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: MESSAGES })],
        stubs: { AppBreadcrumb: true },
      },
    });
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Error");
  });

  it("prefills the invitation, suggests the short name and checks both names", async () => {
    route.query = { invitation_id: "7" };
    const wrapper = await mountPage(
      createForm({ name: "Invited Organization", invitation_id: 7 }),
    );
    await flushPromises();

    expect(GET.mock.calls[0][1]).toEqual({ params: { query: { invitation_id: 7 } } });
    expect((wrapper.find("#name").element as HTMLInputElement).value).toBe("Invited Organization");
    expect((wrapper.find("#short_name").element as HTMLInputElement).value).toBe(
      "invitedorganization",
    );
  });

  it("suggests a short name when leaving the name field", async () => {
    const wrapper = await mountPage();

    await wrapper.find("#name").setValue("Zürich Bühne");
    await wrapper.find("#name").trigger("blur");

    expect((wrapper.find("#short_name").element as HTMLInputElement).value).toBe("zuerichbuehne");
  });

  it("shows the relation card with the verification checked by default", async () => {
    const wrapper = await mountPage(
      createForm({
        relation: { organization_name: "Meine Crew", can_verify: true, can_auto_verify: true },
      }),
    );

    expect(wrapper.find("[data-test=relation]").text()).toContain("Relation to Meine Crew");
    expect((wrapper.find("#embedded_relation-verify").element as HTMLInputElement).checked).toBe(true);
    expect(
      (wrapper.find("#embedded_relation-auto_verify_event_reference_requests").element as HTMLInputElement)
        .checked,
    ).toBe(false);
  });

  it("offers only the allowed relation options", async () => {
    const wrapper = await mountPage(
      createForm({
        relation: { organization_name: "Meine Crew", can_verify: false, can_auto_verify: true },
      }),
    );

    expect(wrapper.find("#embedded_relation-verify").exists()).toBe(false);
    expect(wrapper.find("#embedded_relation-auto_verify_event_reference_requests").exists()).toBe(true);
  });

  it("creates the organization and follows the redirect", async () => {
    POST.mockResolvedValue({ data: { id: 5, verified: true, redirect_url: "/manage/admin_unit/5" } });
    const wrapper = await mountPage(
      createForm({
        invitation_id: null,
        relation: { organization_name: "Meine Crew", can_verify: true, can_auto_verify: true },
      }),
    );
    await fillRequired(wrapper);
    await wrapper.find("#embedded_relation-auto_verify_event_reference_requests").setValue(true);

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    const [path, options] = POST.mock.calls[0];
    expect(path).toBe("/bff/manage/organizations");
    expect(options.body).toMatchObject({
      name: "Neue Crew",
      short_name: "neuecrew",
      location: { postalCode: "38640", city: "Goslar" },
      logo: null,
      invitation_id: null,
      relation_verify: true,
      relation_auto_verify_event_reference_requests: true,
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/5");
  });

  it("sends no relation flags without a relation card and keeps the invitation", async () => {
    POST.mockResolvedValue({ data: { id: 5, verified: false, redirect_url: "/x" } });
    const wrapper = await mountPage(createForm({ name: "Invited Organization", invitation_id: 7 }));
    await wrapper.find("#location-postalCode").setValue("38640");
    await wrapper.find("#location-city").setValue("Goslar");

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST.mock.calls[0][1].body).toMatchObject({
      invitation_id: 7,
      relation_verify: false,
      relation_auto_verify_event_reference_requests: false,
    });
  });

  it("shows the field errors of a 422 and the unmatched ones in an alert", async () => {
    Element.prototype.scrollIntoView = vi.fn();
    POST.mockResolvedValue({
      error: {
        errors: [
          { loc: ["name"], msg: "Name is already taken" },
          { loc: ["somewhere"], msg: "Odd" },
        ],
      },
    });
    const wrapper = await mountPage();
    await fillRequired(wrapper);

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find("#name").classes()).toContain("is-invalid");
    expect(wrapper.text()).toContain("Name is already taken");
    expect(wrapper.find(".alert-danger").text()).toBe("Odd");
    expect(Element.prototype.scrollIntoView).toHaveBeenCalled();
    expect(assign).not.toHaveBeenCalled();
    expect(wrapper.find("#submit").attributes("disabled")).toBeUndefined();
  });

  it("shows other save errors in an alert", async () => {
    POST.mockResolvedValue({ error: { message: "Boom" } });
    const wrapper = await mountPage();
    await fillRequired(wrapper);

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Boom");
  });

  it("falls back to a generic message for an unknown save error", async () => {
    POST.mockResolvedValue({ error: {} });
    const wrapper = await mountPage();
    await fillRequired(wrapper);

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Error");
  });

  it("ignores a second submit while saving", async () => {
    POST.mockReturnValue(new Promise(() => {}));
    const wrapper = await mountPage();
    await fillRequired(wrapper);

    await wrapper.find("form").trigger("submit");
    await wrapper.find("form").trigger("submit");

    expect(POST).toHaveBeenCalledTimes(1);
  });
});
