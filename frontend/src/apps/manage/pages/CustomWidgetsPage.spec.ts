import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";
import { createMemoryHistory, createRouter } from "vue-router";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
const DELETE = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), DELETE: (...a: unknown[]) => DELETE(...a) },
}));

const success = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import { setFlash } from "../flash";
import CustomWidgetsPage from "./CustomWidgetsPage.vue";

const page = (items: { id: number; name: string; widget_type: string }[], over = {}) => ({
  data: { items, page: 1, per_page: 20, total: items.length, pages: 1, can_write: true, ...over },
});
const rows = [
  { id: 4, name: "Mein Widget", widget_type: "search" },
  { id: 5, name: "Kalender", widget_type: "calendar" },
];

async function mountPage(url = "/manage/admin_unit/3/custom-widgets") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: "/manage/admin_unit/:organizationId/custom-widgets",
        name: "custom-widgets",
        component: CustomWidgetsPage,
      },
    ],
  });
  router.push(url);
  await router.isReady();
  const wrapper = mount(CustomWidgetsPage, {
    props: { organizationId: 3 },
    attachTo: document.body,
    global: {
      plugins: [
        router,
        createBootstrap(),
        createI18n({ legacy: false, locale: "en", messages: { en: {} } }),
      ],
    },
  });
  await flushPromises();
  return { wrapper, router };
}

describe("CustomWidgetsPage", () => {
  beforeEach(() => {
    GET.mockReset();
    DELETE.mockReset();
    success.mockReset();
    document.body.innerHTML = "";
  });

  it("lists the widgets with their type and the actions", async () => {
    GET.mockResolvedValue(page(rows));
    const { wrapper } = await mountPage();

    expect(GET).toHaveBeenCalledWith("/bff/manage/organizations/{id}/custom-widgets", {
      params: { path: { id: 3 }, query: { page: 1 } },
    });
    expect(wrapper.text()).toContain("Mein Widget");
    expect(wrapper.text()).toContain("Search");
    expect(wrapper.text()).toContain("Calendar");
    expect(wrapper.find('a[href="/manage/admin_unit/3/custom-widgets/create"]').exists()).toBe(
      true,
    );
    expect(wrapper.find('a[href="/manage/admin_unit/3/custom-widgets/4/update"]').exists()).toBe(
      true,
    );
  });

  it("hides add and delete without write permission", async () => {
    GET.mockResolvedValue(page(rows, { can_write: false }));
    const { wrapper } = await mountPage();

    expect(wrapper.find('a[href$="/create"]').exists()).toBe(false);
    expect(wrapper.text()).not.toContain("Delete");
    expect(wrapper.text()).toContain("Installation");
    expect(wrapper.text()).toContain("Edit");
  });

  it("shows the empty state", async () => {
    GET.mockResolvedValue(page([]));
    const { wrapper } = await mountPage();

    expect(wrapper.text()).toContain("No widgets found");
  });

  it("shows the error", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const { wrapper } = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });

  it("shows the installation snippets of the widget", async () => {
    GET.mockResolvedValue(page(rows));
    const { wrapper } = await mountPage();

    await wrapper.findAll("button.btn-link")[0].trigger("click");
    await flushPromises();

    const header = document.querySelector<HTMLTextAreaElement>('[data-test="install-header"]');
    const body = document.querySelector<HTMLTextAreaElement>('[data-test="install-body"]');
    expect(header?.value).toContain(`${location.origin}/static/widget-loader.js`);
    expect(body?.value).toBe('<div class="eventcally-widget" data-widget-id="4"></div>');
  });

  it("deletes after the confirmation and reloads", async () => {
    GET.mockResolvedValue(page(rows));
    DELETE.mockResolvedValue({});
    const { wrapper } = await mountPage();

    // Row 0: Installation, Delete -> the second link button.
    await wrapper.findAll("button.btn-link")[1].trigger("click");
    await flushPromises();
    expect(document.body.textContent).toContain("Do you really want to delete the widget?");
    expect(DELETE).not.toHaveBeenCalled();

    const ok = [...document.querySelectorAll<HTMLButtonElement>(".modal-footer button")].find(
      (b) => b.textContent?.trim() === "Delete",
    );
    ok?.click();
    await flushPromises();

    expect(DELETE).toHaveBeenCalledWith("/bff/manage/custom-widgets/{id}", {
      params: { path: { id: 4 } },
    });
    expect(success).toHaveBeenCalledWith("Widget successfully deleted");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("shows the message the editor left before the redirect", async () => {
    GET.mockResolvedValue(page(rows));
    setFlash("Widget successfully saved");
    await mountPage();

    expect(success).toHaveBeenCalledWith("Widget successfully saved");
  });
});
