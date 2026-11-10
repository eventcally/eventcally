import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login", docsUrl: null } }));
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success: vi.fn(), error: vi.fn() }) }));
const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...a: unknown[]) => GET(...a) } }));

import { makeEvent, noRights } from "../components/eventFixture";
import EventActionsPage from "./EventActionsPage.vue";

async function mountPage() {
  const wrapper = mount(EventActionsPage, {
    props: { id: 4 },
    attachTo: document.body,
    global: {
      plugins: [
        createBootstrap(),
        createI18n({
          legacy: false,
          locale: "en",
          messages: {
            en: {
              "Create another event for %(admin_unit_name)s": "Create another event for {admin_unit_name}",
              "List all events of %(admin_unit_name)s": "List all events of {admin_unit_name}",
            },
          },
        }),
      ],
    },
  });
  await flushPromises();
  return wrapper;
}

const hrefs = (wrapper: Awaited<ReturnType<typeof mountPage>>) =>
  wrapper.findAll("a.list-group-item").map((a) => a.attributes("href"));

describe("EventActionsPage", () => {
  beforeEach(() => {
    GET.mockReset();
    document.body.innerHTML = "";
  });

  it("offers only sharing to an anonymous visitor", async () => {
    GET.mockResolvedValue({ data: makeEvent() });
    const wrapper = await mountPage();

    expect(wrapper.find('a[href="/event/4"]').text()).toBe("Stadtfest");
    expect(hrefs(wrapper)).toEqual([]);

    await wrapper.find("button.list-group-item").trigger("click");
    await flushPromises();
    expect(document.body.querySelector('input[name="shareUrl"]')).not.toBeNull();
  });

  it("offers adding to a calendar and opens the modal", async () => {
    GET.mockResolvedValue({ data: makeEvent({ calendar_organization: { id: 7, name: "Crew" } }) });
    const wrapper = await mountPage();

    await wrapper.find("[data-test=add-to-calendar]").trigger("click");
    await flushPromises();

    expect(GET).toHaveBeenLastCalledWith(
      "/bff/manage/organizations/{id}/events/{event_id}/calendars",
      { params: { path: { id: 7, event_id: 4 } } },
    );
  });

  it("offers no calendar action without a calendar organization", async () => {
    GET.mockResolvedValue({ data: makeEvent() });
    const wrapper = await mountPage();

    expect(wrapper.find("[data-test=add-to-calendar]").exists()).toBe(false);
  });

  it("lists the management actions of an editor", async () => {
    GET.mockResolvedValue({
      data: makeEvent({
        rights: {
          ...noRights,
          can_update_event: true,
          can_duplicate_event: true,
          can_create_event: true,
          can_create_reference_request: true,
          can_reference_event: true,
        },
      }),
    });
    const wrapper = await mountPage();

    expect(hrefs(wrapper)).toEqual([
      "/manage/admin_unit/2/outgoing_event_reference_request/create_for_event/4",
      "/event/4/reference",
      "/manage/admin_unit/2/event/create?template_id=4",
      "/manage/admin_unit/2/event/create",
      "/manage/admin_unit/2/events",
      "/manage/admin_unit/2/event/4/update",
      "/manage/admin_unit/2/event/4/delete",
    ]);
    expect(wrapper.text()).toContain("Create another event for Meine Crew");
  });

  it("shows the load error", async () => {
    GET.mockResolvedValue({ error: { message: "Not found" } });
    const wrapper = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Not found");
  });

  it("falls back to a generic error", async () => {
    GET.mockResolvedValue({ error: undefined });
    const wrapper = await mountPage();

    expect(wrapper.find(".alert-danger").text()).toBe("Error");
  });
});
