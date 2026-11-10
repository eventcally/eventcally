import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

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

import { mountPage } from "../testing";
import CalendarEditPage from "./CalendarEditPage.vue";

const assign = vi.fn();
const BASE = "/bff/manage/organizations/{id}/calendars";

const form = (over = {}) => ({ id: null, name: "", description: null, private: false, ...over });

function answers(data: object, taken = false) {
  GET.mockImplementation(async (path: string) =>
    path.endsWith("/name-availability") ? { data: { name_taken: taken } } : { data },
  );
}

describe("CalendarEditPage", () => {
  beforeEach(() => {
    [GET, POST, PUT, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
    vi.useRealTimers();
  });

  it("creates a calendar and follows the redirect", async () => {
    answers(form());
    POST.mockResolvedValue({ data: { id: 5, redirect_url: "/manage/admin_unit/3/calendars" } });
    const { wrapper } = await mountPage(CalendarEditPage, { organizationId: 3 }, "/x");

    expect(GET).toHaveBeenCalledWith(`${BASE}/create-form`, { params: { path: { id: 3 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Create Calendar");

    await wrapper.find("#name").setValue("Sport");
    await wrapper.find("#description").setValue("Text");
    await wrapper.find("#private").setValue(true);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(BASE, {
      params: { path: { id: 3 } },
      body: { name: "Sport", description: "Text", private: true, inline: false },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3/calendars");
  });

  it("loads and updates a calendar", async () => {
    answers(form({ id: 4, name: "Sport", description: "Alt", private: true }));
    PUT.mockResolvedValue({ data: { id: 4, redirect_url: "/manage/admin_unit/3/calendars" } });
    const { wrapper } = await mountPage(CalendarEditPage, { organizationId: 3, id: 4 }, "/x");

    expect((wrapper.find("#name").element as HTMLInputElement).value).toBe("Sport");
    expect((wrapper.find("#private").element as HTMLInputElement).checked).toBe(true);
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith(`${BASE}/{calendar_id}`, {
      params: { path: { id: 3, calendar_id: 4 } },
      body: { name: "Sport", description: "Alt", private: true, inline: false },
    });
  });

  it("shows a taken name while typing", async () => {
    answers(form(), true);
    const { wrapper } = await mountPage(CalendarEditPage, { organizationId: 3 }, "/x");

    await wrapper.find("#name").setValue("Sport");
    await new Promise((resolve) => setTimeout(resolve, 400));
    await flushPromises();

    expect(wrapper.text()).toContain("A calendar already exists with this name.");
    expect(GET).toHaveBeenLastCalledWith(`${BASE}/name-availability`, {
      params: { path: { id: 3 }, query: { name: "Sport", exclude_id: undefined } },
    });
  });

  it("maps field errors of the server and shows other errors", async () => {
    answers(form());
    POST.mockResolvedValueOnce({
      error: { errors: [{ loc: ["name"], msg: "A calendar already exists with this name." }] },
    });
    const { wrapper } = await mountPage(CalendarEditPage, { organizationId: 3 }, "/x");
    await wrapper.find("#name").setValue("Sport");
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=field-error]").text()).toBe(
      "A calendar already exists with this name.",
    );

    POST.mockResolvedValueOnce({ error: { message: "Boom" } });
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Boom");
    expect(assign).not.toHaveBeenCalled();
  });

  it("shows the error of a failed load", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const { wrapper } = await mountPage(CalendarEditPage, { organizationId: 3 }, "/x");

    expect(wrapper.find(".alert-danger").text()).toBe("Forbidden");
    expect(wrapper.find("form").exists()).toBe(false);
  });
});
