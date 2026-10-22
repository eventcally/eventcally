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

import OrganizerPage from "./OrganizerPage.vue";

const organizer = {
  id: 5,
  name: "Jam Club",
  url: "https://jam.test",
  email: "info@jam.test",
  phone: "0123",
  fax: "0456",
  location: { street: "Main St 1", postal_code: "38640", city: "Goslar" },
  logo_url: "/image/1?s=120",
  organization: { id: 3, name: "Jam Org" },
  ical_url: "http://localhost/organizers/5/ical",
};

async function mountPage() {
  const wrapper = mount(OrganizerPage, {
    props: { id: 5 },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
  await flushPromises();
  return wrapper;
}

describe("OrganizerPage", () => {
  beforeEach(() => {
    GET.mockReset().mockResolvedValue({ data: organizer });
    document.body.innerHTML = "";
  });

  it("loads and renders the organizer", async () => {
    const wrapper = await mountPage();

    expect(GET).toHaveBeenCalledWith("/bff/public/organizers/{id}", {
      params: { path: { id: 5 } },
    });
    expect(wrapper.find("h1").text()).toBe("Jam Club");
    expect(wrapper.find('a[href="mailto:info@jam.test"]').exists()).toBe(true);
    expect(wrapper.find('a[href="tel:0123"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("Main St 1, 38640 Goslar");
    expect(wrapper.find('a[href="/organizations/3"]').text()).toBe("Jam Org");
    expect(wrapper.find('a[href="/eventdates?organizer_id=5"]').exists()).toBe(true);
    expect(wrapper.find("img").attributes("src")).toBe("/image/1?s=120");
  });

  it("hides empty fields", async () => {
    GET.mockResolvedValue({
      data: {
        ...organizer,
        url: null,
        email: null,
        phone: null,
        fax: null,
        location: null,
        logo_url: null,
      },
    });
    const wrapper = await mountPage();

    expect(wrapper.find("img").exists()).toBe(false);
    expect(wrapper.find(".fa-link").exists()).toBe(false);
    expect(wrapper.find(".fa-envelope").exists()).toBe(false);
    expect(wrapper.find(".fa-map-marker").exists()).toBe(false);
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
    expect(input.value).toBe(organizer.ical_url);
  });
});
