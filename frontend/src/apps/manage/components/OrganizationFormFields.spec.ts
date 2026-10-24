import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, ref } from "vue";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

vi.mock("@/shared/ImageCropper.vue", () => ({
  __esModule: true,
  default: defineComponent({ name: "ImageCropper", render: () => null }),
}));

import { emptyOrganizationForm } from "../organizationForm";
import OrganizationFormFields from "./OrganizationFormFields.vue";

function mountFields(props: Record<string, unknown> = {}) {
  const Host = defineComponent({
    components: { OrganizationFormFields },
    setup: () => ({ form: ref(emptyOrganizationForm()), errors: ref({}), props }),
    template:
      '<OrganizationFormFields ref="fields" v-model="form" v-model:errors="errors" :licenses="[]" v-bind="props" />',
  });
  return mount(Host, {
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });
}

describe("OrganizationFormFields", () => {
  beforeEach(() => {
    GET.mockReset();
    vi.useRealTimers();
  });

  it("sends exclude_id with the live name check", async () => {
    vi.useFakeTimers();
    GET.mockResolvedValue({ data: { name_taken: false, short_name_taken: null } });
    const wrapper = mountFields({ excludeId: 3 });

    await wrapper.find("#name").setValue("Freie Crew");
    await vi.advanceTimersByTimeAsync(300);
    await flushPromises();

    expect(GET).toHaveBeenCalledWith("/bff/manage/organizations/name-availability", {
      params: { query: { name: "Freie Crew", exclude_id: 3 } },
    });
  });

  it("does not suggest a short name without the option or when one is set", async () => {
    const wrapper = mountFields();

    await wrapper.find("#name").setValue("Meine Crew");
    await wrapper.find("#name").trigger("blur");

    expect((wrapper.find("#short_name").element as HTMLInputElement).value).toBe("");

    const withOption = mountFields({ suggestShortName: true });
    await withOption.find("#short_name").setValue("eigener");
    await withOption.find("#name").setValue("Meine Crew");
    await withOption.find("#name").trigger("blur");

    expect((withOption.find("#short_name").element as HTMLInputElement).value).toBe("eigener");
  });

  it("marks the suggested short name as valid after the check", async () => {
    vi.useFakeTimers();
    GET.mockResolvedValue({ data: { name_taken: false, short_name_taken: false } });
    const wrapper = mountFields({ suggestShortName: true });

    await wrapper.find("#name").setValue("Meine Crew");
    await wrapper.find("#name").trigger("blur");
    await vi.advanceTimersByTimeAsync(300);
    await flushPromises();

    expect((wrapper.find("#short_name").element as HTMLInputElement).value).toBe("meinecrew");
    expect(wrapper.find("#short_name").classes()).toContain("is-valid");
  });
});
