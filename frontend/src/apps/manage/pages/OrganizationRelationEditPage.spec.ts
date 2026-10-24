import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({
  boot: { locale: "en", csrfToken: "x", loginUrl: "/login" },
}));

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

import OrganizationRelationEditPage from "./OrganizationRelationEditPage.vue";

const assign = vi.fn();
const MESSAGES = {
  en: {
    "Create %(model_display_name)s": "Create {model_display_name}",
    "Update %(model_display_name)s": "Update {model_display_name}",
  },
};
const BASE = "/bff/manage/organizations/{id}/outgoing-organization-relations";

function relationForm(overrides: Record<string, unknown> = {}) {
  return {
    id: null,
    target: null,
    verify: false,
    auto_verify_event_reference_requests: false,
    can_verify_other: true,
    list_url: "/manage/admin_unit/5/outgoing_organization_relations",
    ...overrides,
  };
}

async function mountPage(
  props: { organizationId: number; id?: number } = { organizationId: 5 },
  data: Record<string, unknown> = relationForm(),
) {
  GET.mockImplementation(async (path: string) =>
    path.endsWith("/organizations")
      ? { data: { items: [{ id: 9, name: "Other Crew" }] } }
      : { data },
  );
  const wrapper = mount(OrganizationRelationEditPage, {
    props,
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: MESSAGES })],
    },
  });
  await flushPromises();
  return wrapper;
}

async function pickOrganization(wrapper: Awaited<ReturnType<typeof mountPage>>) {
  await wrapper.find("#target_admin_unit").setValue("Oth");
  await vi.advanceTimersByTimeAsync(300);
  await flushPromises();
  await wrapper.find("[data-test=option]").trigger("click");
}

describe("OrganizationRelationEditPage", () => {
  beforeEach(() => {
    [GET, POST, PUT, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign, search: "" });
    vi.useRealTimers();
    Element.prototype.scrollIntoView = vi.fn();
  });

  it("loads the empty create form with both switches", async () => {
    const wrapper = await mountPage();

    expect(GET.mock.calls[0]).toEqual([
      `${BASE}/create-form`,
      { params: { path: { id: 5 }, query: {} } },
    ]);
    expect(wrapper.find("#target_admin_unit").exists()).toBe(true);
    expect(wrapper.find("#verify").exists()).toBe(true);
    expect(wrapper.find("#auto_verify_event_reference_requests").exists()).toBe(true);
    expect(wrapper.find("#submit").text()).toBe("Create");
    expect(wrapper.find(".breadcrumb").text()).toContain("Create Outgoing organization relation");
    expect(wrapper.find(".breadcrumb a").attributes("href")).toBe(
      "/manage/admin_unit/5/outgoing_organization_relations",
    );
  });

  it("prefills the create form from the query string", async () => {
    vi.stubGlobal("location", { assign, search: "?target=9&verify=1" });
    const wrapper = await mountPage(
      { organizationId: 5 },
      relationForm({ target: { id: 9, name: "Other Crew" }, verify: true }),
    );

    expect(GET.mock.calls[0][1]).toEqual({
      params: { path: { id: 5 }, query: { target: 9, verify: 1 } },
    });
    expect((wrapper.find("#target_admin_unit").element as HTMLInputElement).value).toBe(
      "Other Crew",
    );
    expect((wrapper.find("#verify").element as HTMLInputElement).checked).toBe(true);
  });

  it("hides the verify switch without the permission", async () => {
    const wrapper = await mountPage(
      { organizationId: 5 },
      relationForm({ can_verify_other: false }),
    );

    expect(wrapper.find("#verify").exists()).toBe(false);
    expect(wrapper.find("#auto_verify_event_reference_requests").exists()).toBe(true);
  });

  it("creates a relation to the picked organization", async () => {
    vi.useFakeTimers();
    POST.mockResolvedValue({ data: { id: 1, redirect_url: "/list" } });
    const wrapper = await mountPage();

    await pickOrganization(wrapper);
    await wrapper.find("#verify").setValue(true);
    await wrapper.find("#auto_verify_event_reference_requests").setValue(true);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(GET).toHaveBeenCalledWith(`${BASE}/organizations`, {
      params: { path: { id: 5 }, query: { keyword: "Oth" } },
    });
    expect(POST).toHaveBeenCalledWith(BASE, {
      params: { path: { id: 5 } },
      body: {
        verify: true,
        auto_verify_event_reference_requests: true,
        target_admin_unit_id: 9,
      },
    });
    expect(assign).toHaveBeenCalledWith("/list");
  });

  it("shows the field error of a missing organization", async () => {
    POST.mockResolvedValue({
      error: {
        errors: [{ loc: ["target_admin_unit_id"], msg: "This field is required." }],
      },
    });
    const wrapper = await mountPage();

    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST.mock.calls[0][1].body.target_admin_unit_id).toBeNull();
    expect(wrapper.find("[data-test=target-error]").text()).toBe("This field is required.");
    expect(assign).not.toHaveBeenCalled();
  });

  it("shows unmatched and generic save errors", async () => {
    POST.mockResolvedValueOnce({
      error: { errors: [{ loc: ["body"], msg: "Broken" }] },
    });
    POST.mockResolvedValueOnce({ error: { message: "Nope" } });
    POST.mockResolvedValueOnce({ error: {} });
    const wrapper = await mountPage();

    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Broken");

    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Nope");

    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Error");
  });

  it("shows the target of an update read-only and saves the switches", async () => {
    PUT.mockResolvedValue({ data: { id: 7, redirect_url: "/list" } });
    const wrapper = await mountPage(
      { organizationId: 5, id: 7 },
      relationForm({
        id: 7,
        target: { id: 9, name: "Other Crew" },
        auto_verify_event_reference_requests: true,
      }),
    );

    expect(GET.mock.calls[0]).toEqual([
      `${BASE}/{relation_id}`,
      { params: { path: { id: 5, relation_id: 7 } } },
    ]);
    expect(wrapper.find("#target_admin_unit").exists()).toBe(false);
    expect(wrapper.find("[data-test=target-name]").text()).toContain("Other Crew");
    expect(wrapper.find("#submit").text()).toBe("Update");
    expect(wrapper.find(".breadcrumb").text()).toContain("Update Outgoing organization relation");

    await wrapper.find("#verify").setValue(true);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith(`${BASE}/{relation_id}`, {
      params: { path: { id: 5, relation_id: 7 } },
      body: { verify: true, auto_verify_event_reference_requests: true },
    });
    expect(assign).toHaveBeenCalledWith("/list");
  });

  it("reports a load error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const wrapper = mount(OrganizationRelationEditPage, {
      props: { organizationId: 5 },
      global: {
        plugins: [
          createBootstrap(),
          createI18n({ legacy: false, locale: "en", messages: MESSAGES }),
        ],
      },
    });
    await flushPromises();
    expect(wrapper.text()).toContain("Forbidden");
    expect(wrapper.find("form").exists()).toBe(false);

    GET.mockResolvedValue({});
    const fallback = mount(OrganizationRelationEditPage, {
      props: { organizationId: 5 },
      global: {
        plugins: [
          createBootstrap(),
          createI18n({ legacy: false, locale: "en", messages: MESSAGES }),
        ],
      },
    });
    await flushPromises();
    expect(fallback.text()).toContain("Error");
  });
});
