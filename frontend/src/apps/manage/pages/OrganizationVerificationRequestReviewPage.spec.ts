import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));

import OrganizationVerificationRequestReviewPage from "./OrganizationVerificationRequestReviewPage.vue";

const assign = vi.fn();
const BASE = "/bff/manage/organizations/{id}/incoming-verification-requests/{request_id}";
const PARAMS = { params: { path: { id: 3, request_id: 9 } } };

function review(overrides: Record<string, unknown> = {}) {
  return {
    id: 9,
    review_status: "inbox",
    organization: {
      id: 2,
      name: "Other Crew",
      is_verified: true,
      logo_url: "/image/9?s=120",
      url: "crew.example",
      email: "crew@example.com",
      address: "38640 Goslar",
      description: "We do things.\nTogether.",
    },
    members: [
      { email: "a@example.com", roles: ["Admin", "Event expert"] },
      { email: "b@example.com", roles: [] },
    ],
    auto_verify_description: "If all upcoming reference requests of Other Crew should be verified automatically.",
    rejection_reasons: [
      { value: 0, label: "No reason" },
      { value: 6, label: "Irrelevant" },
    ],
    list_url: "/manage/admin_unit/3/incoming_organization_verification_requests",
    ...overrides,
  };
}

async function mountPage() {
  const wrapper = mount(OrganizationVerificationRequestReviewPage, {
    props: { organizationId: 3, id: 9 },
    attachTo: document.body,
    global: {
      plugins: [
        createBootstrap(),
        createI18n({
          legacy: false,
          locale: "en",
          messages: {
            en: { "Review %(model_display_name)s": "Review {model_display_name}", Cancel: "Cancel" },
          },
        }),
      ],
    },
  });
  await flushPromises();
  return wrapper;
}

const body = (selector: string) => document.body.querySelector<HTMLElement>(selector);

describe("OrganizationVerificationRequestReviewPage", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    [GET, POST, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
  });

  it("shows the organization, its members and the breadcrumb", async () => {
    GET.mockResolvedValue({ data: review() });
    const wrapper = await mountPage();

    expect(GET).toHaveBeenCalledWith(`${BASE}/review`, PARAMS);
    const organization = wrapper.get("[data-test=organization-card]");
    expect(organization.text()).toContain("Other Crew");
    expect(organization.find(".fa-check-circle").exists()).toBe(true);
    expect(organization.get("img").attributes("src")).toBe("/image/9?s=120");
    expect(organization.text()).toContain("crew@example.com");
    expect(organization.text()).toContain("38640 Goslar");
    expect(organization.text()).toContain("We do things.");

    const members = wrapper.findAll("[data-test=members-card] li");
    expect(members.map((m) => m.text())).toEqual([
      "a@example.comAdmin, Event expert",
      "b@example.com",
    ]);
    expect(wrapper.get(".breadcrumb a").attributes("href")).toBe(
      "/manage/admin_unit/3/incoming_organization_verification_requests",
    );
  });

  it("omits the optional parts of an organization", async () => {
    GET.mockResolvedValue({
      data: review({
        organization: { id: 2, name: "Plain", is_verified: false },
        members: [],
      }),
    });
    const wrapper = await mountPage();

    const organization = wrapper.get("[data-test=organization-card]");
    expect(organization.find("img").exists()).toBe(false);
    expect(organization.find(".fa-check-circle").exists()).toBe(false);
    expect(wrapper.findAll("[data-test=members-card] li")).toHaveLength(0);
  });

  it("shows the load error", async () => {
    GET.mockResolvedValue({ error: { message: "Not found" } });
    const wrapper = await mountPage();

    expect(wrapper.get(".alert-danger").text()).toBe("Not found");
    expect(wrapper.find("[data-test=decision]").exists()).toBe(false);
  });

  it("accepts with the auto-verify switch", async () => {
    GET.mockResolvedValue({ data: review() });
    POST.mockResolvedValue({ data: { redirect_url: "/list" } });
    const wrapper = await mountPage();

    await wrapper.get("[data-test=accept]").trigger("click");
    await flushPromises();
    expect(body("#rating")).toBeNull();
    expect(document.body.textContent).toContain(
      "If all upcoming reference requests of Other Crew should be verified automatically.",
    );
    (body("#auto_verify") as HTMLInputElement).click();
    await flushPromises();
    body("[data-test=accept-confirm]")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(`${BASE}/approve`, { ...PARAMS, body: { auto_verify: true } });
    expect(assign).toHaveBeenCalledWith("/list");
  });

  it("rejects without a reason, then with one", async () => {
    GET.mockResolvedValue({ data: review() });
    POST.mockResolvedValue({ error: { message: "Boom" } });
    const wrapper = await mountPage();

    await wrapper.get("[data-test=reject]").trigger("click");
    await flushPromises();
    body("[data-test=reject-confirm]")!.click();
    await flushPromises();
    expect(POST).toHaveBeenLastCalledWith(`${BASE}/reject`, {
      ...PARAMS,
      body: { rejection_reason: null },
    });
    expect(body("[data-test=reject-error]")!.textContent).toContain("Boom");

    POST.mockResolvedValue({ data: { redirect_url: "/list" } });
    const select = body("#rejection_reason") as HTMLSelectElement;
    select.value = "6";
    select.dispatchEvent(new Event("change"));
    await flushPromises();
    body("[data-test=reject-confirm]")!.click();
    await flushPromises();

    expect(POST.mock.calls[1][1].body).toEqual({ rejection_reason: 6 });
    expect(assign).toHaveBeenCalledWith("/list");
  });

  it("falls back to a generic error", async () => {
    GET.mockResolvedValue({ data: review() });
    POST.mockResolvedValue({ error: {} });
    const wrapper = await mountPage();

    await wrapper.get("[data-test=accept]").trigger("click");
    await flushPromises();
    body("[data-test=accept-confirm]")!.click();
    await flushPromises();

    expect(body("[data-test=accept-error]")!.textContent).toContain("Error");
  });
});
