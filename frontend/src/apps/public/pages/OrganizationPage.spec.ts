import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({
  boot: { locale: "en", csrfToken: "x", loginUrl: "/login", docsUrl: null },
}));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success: vi.fn(), error: vi.fn() }) }));

import OrganizationPage from "./OrganizationPage.vue";

const organization = {
  id: 5,
  name: "Jam Org",
  short_name: "jam",
  url: "https://jam.test",
  email: "info@jam.test",
  phone: "0123",
  fax: "0456",
  description: "Line 1\nLine 2",
  is_verified: true,
  location: { street: "Main St 1", postal_code: "38640", city: "Goslar" },
  logo_url: "/image/1?s=120",
  ical_url: "http://localhost/organizations/5/ical",
  relation: null,
};

const messages = {
  "%(source)s verifies %(target)s": "{source} verifies {target}",
  "%(source)s verifies reference requests from %(target)s automatically":
    "{source} verifies reference requests from {target} automatically",
  "There is no relation from %(source)s to %(target)s":
    "There is no relation from {source} to {target}",
  "%(organization)s is not verified": "{organization} is not verified",
  "Verify %(organization)s": "Verify {organization}",
};

const source = { id: 9, name: "Verifier" };

async function mountPage() {
  const wrapper = mount(OrganizationPage, {
    props: { id: 5 },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: messages } })],
    },
  });
  await flushPromises();
  return wrapper;
}

describe("OrganizationPage", () => {
  beforeEach(() => {
    GET.mockReset().mockResolvedValue({ data: organization });
    document.body.innerHTML = "";
  });

  it("loads and renders the organization", async () => {
    const wrapper = await mountPage();

    expect(GET).toHaveBeenCalledWith("/bff/public/organizations/{id}", {
      params: { path: { id: 5 } },
    });
    expect(wrapper.find("h1").text()).toBe("Jam Org");
    expect(wrapper.find("h1 .fa-check-circle").exists()).toBe(true);
    expect(wrapper.text()).toContain("@jam");
    expect(wrapper.find('a[href="mailto:info@jam.test"]').exists()).toBe(true);
    expect(wrapper.find('a[href="tel:0123"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("Main St 1, 38640 Goslar");
    expect(wrapper.text()).toContain("Line 1");
    expect(wrapper.find('a[href="/eventdates?admin_unit_id=5"]').exists()).toBe(true);
    expect(wrapper.find("img").attributes("src")).toBe("/image/1?s=120");
    expect(wrapper.find('[data-testid="relation"]').exists()).toBe(false);
  });

  it("hides empty fields", async () => {
    GET.mockResolvedValue({
      data: {
        ...organization,
        short_name: null,
        url: null,
        email: null,
        phone: null,
        fax: null,
        description: null,
        is_verified: false,
        location: null,
        logo_url: null,
      },
    });
    const wrapper = await mountPage();

    expect(wrapper.find("img").exists()).toBe(false);
    expect(wrapper.find("h1 .fa-check-circle").exists()).toBe(false);
    expect(wrapper.find(".fa-link").exists()).toBe(false);
    expect(wrapper.find(".fa-envelope").exists()).toBe(false);
    expect(wrapper.find(".fa-map-marker").exists()).toBe(false);
  });

  it("shows an existing relation with an edit link", async () => {
    GET.mockResolvedValue({
      data: {
        ...organization,
        relation: {
          source,
          relation_id: 3,
          verify: true,
          auto_verify_event_reference_requests: true,
          edit_url: "/manage/admin_unit/9/outgoing_organization_relation/3/update",
        },
      },
    });
    const wrapper = await mountPage();
    const card = wrapper.find('[data-testid="relation"]');

    expect(card.text()).toContain("Verifier verifies Jam Org");
    expect(card.text()).toContain("Verifier verifies reference requests from Jam Org automatically");
    expect(card.find("a").attributes("href")).toBe(
      "/manage/admin_unit/9/outgoing_organization_relation/3/update",
    );
  });

  it("offers to create a relation to a verified organization", async () => {
    GET.mockResolvedValue({
      data: {
        ...organization,
        relation: { source, create_url: "/manage/admin_unit/9/outgoing_organization_relation/create?target=5&verify=1" },
      },
    });
    const wrapper = await mountPage();
    const card = wrapper.find('[data-testid="relation"]');

    expect(card.text()).toContain("There is no relation from Verifier to Jam Org");
    expect(card.find(".border-warning").exists()).toBe(false);
    expect(card.find("a").attributes("href")).toContain("create?target=5&verify=1");
  });

  it("offers to verify an unverified organization", async () => {
    GET.mockResolvedValue({
      data: {
        ...organization,
        is_verified: false,
        relation: { source, create_url: "/create?target=5&verify=1" },
      },
    });
    const wrapper = await mountPage();
    const card = wrapper.find('[data-testid="relation"]');

    expect(card.find(".border-warning").exists()).toBe(true);
    expect(card.text()).toContain("Jam Org is not verified");
    expect(card.find("a").text()).toBe("Verify Jam Org");
  });

  it("shows the error when loading fails", async () => {
    GET.mockResolvedValue({ error: { name: "Not Found", message: "Not Found" } });
    const wrapper = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Not Found");
    expect(wrapper.find("h1").exists()).toBe(false);
  });

  it("opens the iCal popup", async () => {
    const wrapper = await mountPage();

    await wrapper.find("button.list-group-item").trigger("click");
    await flushPromises();

    const input = document.body.querySelector('input[name="icalUrl"]') as HTMLInputElement;
    expect(input.value).toBe(organization.ical_url);
  });
});
