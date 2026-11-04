import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const POST = vi.fn();
vi.mock("@/shared/api", () => ({ api: { POST: (...a: unknown[]) => POST(...a) } }));

import { mountPage } from "../testing";
import OrganizationDeletionPage from "./OrganizationDeletionPage.vue";

const assign = vi.fn();
const DELETION = "/bff/manage/organizations/{id}/deletion";

async function submit(wrapper: Awaited<ReturnType<typeof mountPage>>["wrapper"], name: string) {
  await wrapper.find("#name").setValue(name);
  await wrapper.find("form").trigger("submit");
  await flushPromises();
}

describe("OrganizationDeletionPage", () => {
  beforeEach(() => {
    [POST, assign].forEach((f) => f.mockReset());
    vi.stubGlobal("location", { assign });
  });

  it("requests the deletion with the typed name and leaves", async () => {
    POST.mockResolvedValue({ data: { redirect_url: "/manage/admin_unit/3" } });
    const { wrapper } = await mountPage(
      OrganizationDeletionPage,
      { organizationId: 3, mode: "request" },
      "/manage/admin_unit/3/request-deletion",
    );

    expect(wrapper.find(".breadcrumb").text()).toContain("Delete Organization");
    expect(wrapper.find('[data-test="instruction"]').text()).toContain("not deleted immediately");
    expect(wrapper.find("label").text()).toContain("Name of organization");
    expect(wrapper.find("#submit").text()).toBe("Request deletion");

    await submit(wrapper, "Meine Crew");

    expect(POST).toHaveBeenCalledWith(DELETION, {
      params: { path: { id: 3 } },
      body: { name: "Meine Crew" },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3");
  });

  it("cancels the deletion", async () => {
    POST.mockResolvedValue({ data: { redirect_url: "/manage/admin_unit/3" } });
    const { wrapper } = await mountPage(
      OrganizationDeletionPage,
      { organizationId: 3, mode: "cancel" },
      "/manage/admin_unit/3/cancel-deletion",
    );

    expect(wrapper.find(".breadcrumb").text()).toContain("Cancel deletion");
    expect(wrapper.find('[data-test="instruction"]').exists()).toBe(false);
    expect(wrapper.find("#submit").text()).toBe("Cancel deletion");

    await submit(wrapper, "Meine Crew");

    expect(POST).toHaveBeenCalledWith(`${DELETION}/cancel`, {
      params: { path: { id: 3 } },
      body: { name: "Meine Crew" },
    });
    expect(assign).toHaveBeenCalledWith("/manage/admin_unit/3");
  });

  it("shows a mismatch at the field and other errors above the form", async () => {
    POST.mockResolvedValue({
      error: {
        errors: [
          { loc: ["name"], msg: "Entered name does not match organization name" },
          { loc: ["other"], msg: "Also wrong" },
        ],
      },
    });
    const { wrapper } = await mountPage(
      OrganizationDeletionPage,
      { organizationId: 3, mode: "request" },
      "/manage/admin_unit/3/request-deletion",
    );
    await submit(wrapper, "wrong");

    expect(wrapper.find('[data-test="field-error"]').text()).toBe(
      "Entered name does not match organization name",
    );
    expect(wrapper.find(".alert-danger").text()).toBe("Also wrong");
    expect(assign).not.toHaveBeenCalled();

    POST.mockResolvedValue({ error: { message: "Kaputt" } });
    await submit(wrapper, "wrong");
    expect(wrapper.find(".alert-danger").text()).toBe("Kaputt");
  });
});
