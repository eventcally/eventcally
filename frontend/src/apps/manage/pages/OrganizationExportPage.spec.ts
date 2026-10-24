import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));

import OrganizationExportPage from "./OrganizationExportPage.vue";

const EXPORT_PATH = "/bff/manage/organizations/{id}/export";
const JOB_PATH = "/bff/manage/organizations/{id}/export/jobs/{job_id}";

const none = { data: { file: null } };
const file = {
  data: {
    file: { url: "/manage/admin_unit/3/export/dump/org-3.zip", size: 2048, created_at: "2026-10-24T10:00:00Z" },
  },
};

function route(exportResponse: () => unknown, status: () => unknown = () => ({})) {
  GET.mockImplementation((path: string) =>
    Promise.resolve(path === EXPORT_PATH ? exportResponse() : status()),
  );
}

async function mountPage() {
  const wrapper = mount(OrganizationExportPage, {
    props: { organizationId: 3 },
    global: {
      plugins: [
        createBootstrap(),
        createI18n({ legacy: false, locale: "en", messages: { en: {} } }),
      ],
    },
  });
  await flushPromises();
  return wrapper;
}

describe("OrganizationExportPage", () => {
  beforeEach(() => {
    GET.mockReset();
    POST.mockReset();
  });
  afterEach(() => vi.useRealTimers());

  it("shows that there are no files", async () => {
    route(() => none);
    const wrapper = await mountPage();

    expect(GET).toHaveBeenCalledWith(EXPORT_PATH, { params: { path: { id: 3 } } });
    expect(wrapper.find("[data-test=no-file]").text()).toBe("No files available");
    expect(wrapper.find("[data-test=file]").exists()).toBe(false);
  });

  it("links the file with its date and size", async () => {
    route(() => file);
    const wrapper = await mountPage();

    const item = wrapper.find("[data-test=file]");
    expect(item.find("a").attributes("href")).toBe("/manage/admin_unit/3/export/dump/org-3.zip");
    expect(item.find("a").text()).toBe("All data");
    const badges = item.findAll(".badge");
    expect(badges[0].text()).toContain("2026");
    expect(badges[1].text()).toBe("2KB");
  });

  it("shows a load error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const wrapper = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
    expect(wrapper.find("[data-test=no-file]").exists()).toBe(false);
  });

  it("falls back to a generic load error", async () => {
    GET.mockResolvedValue({});
    const wrapper = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Error");
  });

  it("disables the button while the export runs and reloads the info when done", async () => {
    vi.useFakeTimers();
    let current: unknown = none;
    route(() => current, () => ({ data: { ready: true, successful: true } }));
    POST.mockResolvedValue({ data: { job_id: "org-export-3-x" } });
    const wrapper = await mountPage();

    current = file;
    await wrapper.find("#submit_async").trigger("click");
    await flushPromises();
    await vi.advanceTimersByTimeAsync(0);
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(EXPORT_PATH, { params: { path: { id: 3 } } });
    expect(GET).toHaveBeenCalledWith(JOB_PATH, {
      params: { path: { id: 3, job_id: "org-export-3-x" } },
    });
    expect(wrapper.find("[data-test=file]").exists()).toBe(true);
    expect(wrapper.find("#submit_async").attributes("disabled")).toBeUndefined();
  });

  it("shows a spinner and a disabled button while polling", async () => {
    vi.useFakeTimers();
    route(() => none, () => ({ data: { ready: false, successful: null } }));
    POST.mockResolvedValue({ data: { job_id: "org-export-3-x" } });
    const wrapper = await mountPage();

    await wrapper.find("#submit_async").trigger("click");
    await flushPromises();

    expect(wrapper.find("[data-test=spinner]").exists()).toBe(true);
    expect(wrapper.find("#submit_async").attributes("disabled")).toBeDefined();
  });

  it("reloads right away when there is no job to follow", async () => {
    let current: unknown = none;
    route(() => current)
    POST.mockResolvedValue({ data: { job_id: null } });
    const wrapper = await mountPage();

    current = file;
    await wrapper.find("#submit_async").trigger("click");
    await flushPromises();

    expect(wrapper.find("[data-test=file]").exists()).toBe(true);
  });

  it("shows an alert when the export fails", async () => {
    route(() => none, () => ({ data: { ready: true, successful: false } }));
    POST.mockResolvedValue({ data: { job_id: "org-export-3-x" } });
    const wrapper = await mountPage();

    await wrapper.find("#submit_async").trigger("click");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("The export files could not be created.");
    expect(wrapper.find("#submit_async").attributes("disabled")).toBeUndefined();
  });
});
