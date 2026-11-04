import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({
  boot: { base: "/", locale: "en", csrfToken: "x", loginUrl: "/login" },
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

import { mountPage } from "../testing";
import MembershipLeavePage from "./MembershipLeavePage.vue";

const assign = vi.fn();

beforeEach(() => {
  [GET, POST, PUT, assign].forEach((f) => f.mockReset());
  vi.stubGlobal("location", { assign });
  document.body.innerHTML = "";
  sessionStorage.clear();
});

const membership = (over = {}) => ({
  data: {
    id: 10,
    organization_id: 7,
    organization_name: "Andere Crew",
    can_leave: true,
    ...over,
  },
});

describe("MembershipLeavePage", () => {
  it("asks for the organization name and leaves with a full page load", async () => {
    GET.mockResolvedValue(membership());
    POST.mockResolvedValue({
      data: { redirect_url: "/user/organization_members" },
    });
    const { wrapper } = await mountPage(
      MembershipLeavePage,
      { id: 10 },
      "/user/organization_member/10/delete",
    );

    expect(wrapper.text()).toContain("Do you want to leave organization Andere Crew?");
    await wrapper.find("#name").setValue("Andere Crew");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/user/memberships/{id}/leave", {
      params: { path: { id: 10 } },
      body: { name: "Andere Crew" },
    });
    expect(assign).toHaveBeenCalledWith("/user/organization_members");
  });

  it("shows a mismatch and other refusals", async () => {
    GET.mockResolvedValue(membership());
    POST.mockResolvedValue({
      error: {
        errors: [
          { loc: ["name"], msg: "Does not match" },
          { loc: ["x"], msg: "Odd" },
        ],
      },
    });
    const { wrapper } = await mountPage(
      MembershipLeavePage,
      { id: 10 },
      "/user/organization_member/10/delete",
    );
    await wrapper.find("#name").setValue("Falsch");
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find("[data-test=field-error]").text()).toBe("Does not match");
    expect(wrapper.find(".alert-danger").text()).toBe("Odd");

    POST.mockResolvedValue({
      error: { message: "Last remaining administrator" },
    });
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(wrapper.find(".alert-danger").text()).toBe("Last remaining administrator");
    expect(assign).not.toHaveBeenCalled();
  });

  it("does not offer leaving to the last administrator and shows a failed load", async () => {
    GET.mockResolvedValue(membership({ can_leave: false }));
    const { wrapper } = await mountPage(
      MembershipLeavePage,
      { id: 10 },
      "/user/organization_member/10/delete",
    );
    expect(wrapper.find("#submit").attributes("disabled")).toBeDefined();

    GET.mockResolvedValue({ error: { message: "Gone" } });
    const failed = await mountPage(
      MembershipLeavePage,
      { id: 10 },
      "/user/organization_member/10/delete",
    );
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Gone");
  });
});
