import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

const bootMock = vi.hoisted(() => ({
  base: "/",
  locale: "en",
  csrfToken: "x",
  docsUrl: "https://docs.test" as string | null,
}));
vi.mock("@/shared/boot", () => ({ boot: bootMock }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
const success = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import { mountPage } from "../testing";
import OutgoingVerificationRequestsPage from "./OutgoingVerificationRequestsPage.vue";

const URL = "/manage/admin_unit/3/outgoing_organization_verification_requests";
const LIST = "/bff/manage/organizations/{id}/outgoing-verification-requests";
const VERIFIERS = "/bff/manage/organizations/{id}/verifier-organizations";
const row = (over = {}) => ({
  id: 7,
  organization_id: 4,
  organization_name: "Andere Crew",
  review_status: 1,
  review_status_label: "Inbox",
  created_at: "2026-11-04T10:00:00Z",
  can_review: false,
  ...over,
});
const page = (items: object[], over = {}) => ({
  data: {
    items,
    page: 1,
    per_page: 50,
    total: items.length,
    pages: 1,
    can_write: true,
    suggest_create: false,
    ...over,
  },
});
const verifiers = {
  data: {
    items: [],
    page: 1,
    per_page: 20,
    total: 0,
    pages: 0,
    can_write: true,
    organization_name: "Meine Crew",
    postal_code: "38640",
  },
};

const open = async (wrapper: { find: (s: string) => { trigger: (e: string) => Promise<void> } }) => {
  await wrapper.find(".row-actions button").trigger("click");
  await flushPromises();
};
const items = () => [...document.querySelectorAll<HTMLAnchorElement>(".dropdown-item")];

describe("OutgoingVerificationRequestsPage", () => {
  beforeEach(() => {
    [GET, POST, success].forEach((f) => f.mockReset());
    document.body.innerHTML = "";
    sessionStorage.clear();
    bootMock.docsUrl = "https://docs.test";
  });

  it("lists the requests with the docs button and the create button", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(OutgoingVerificationRequestsPage, { organizationId: 3 }, URL);

    expect(GET).toHaveBeenCalledWith(LIST, { params: { path: { id: 3 }, query: { page: 1 } } });
    expect(wrapper.find(".breadcrumb").text()).toContain("Outgoing verification requests");
    expect(wrapper.find(".breadcrumb a.btn").attributes("href")).toBe(
      "https://docs.test/goto/organization-verify",
    );
    expect(wrapper.find("[data-test=verification-create]").text()).toContain(
      "Create Organization verification request",
    );
    expect(wrapper.find("table").text()).toContain("Andere Crew");
    expect(wrapper.find("table .badge").text()).toBe("Inbox");
    expect(document.body.textContent).not.toContain("Here you can find organizations");
  });

  it("has no docs button without a docs url and no create button without write permission", async () => {
    bootMock.docsUrl = null;
    GET.mockResolvedValue(page([row()], { can_write: false }));
    const { wrapper } = await mountPage(OutgoingVerificationRequestsPage, { organizationId: 3 }, URL);

    expect(wrapper.find(".breadcrumb a.btn").exists()).toBe(false);
    expect(wrapper.find("[data-test=verification-create]").exists()).toBe(false);
  });

  it("offers view and delete, delete only with write permission", async () => {
    GET.mockResolvedValue(page([row()]));
    const { wrapper } = await mountPage(OutgoingVerificationRequestsPage, { organizationId: 3 }, URL);
    await open(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual(["View", "Delete"]);
    expect(items()[0].getAttribute("href")).toBe(
      "/manage/admin_unit/3/outgoing_organization_verification_request/7",
    );
  });

  it("offers only view without write permission", async () => {
    GET.mockResolvedValue(page([row()], { can_write: false }));
    const { wrapper } = await mountPage(OutgoingVerificationRequestsPage, { organizationId: 3 }, URL);
    await open(wrapper);

    expect(items().map((i) => i.textContent?.trim())).toEqual(["View"]);
  });

  it("opens the request dialog for an unverified organization without requests", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve(path === VERIFIERS ? verifiers : page([], { suggest_create: true })),
    );
    await mountPage(OutgoingVerificationRequestsPage, { organizationId: 3 }, URL);

    expect(GET).toHaveBeenCalledWith(VERIFIERS, {
      params: { path: { id: 3 }, query: { page: 1 } },
    });
    expect(document.body.textContent).toContain("No organizations were found");
  });

  it("opens the request dialog on demand and reloads once a request was created", async () => {
    GET.mockImplementation((path: string) =>
      Promise.resolve(path === VERIFIERS ? verifiers : page([row()])),
    );
    const { wrapper } = await mountPage(OutgoingVerificationRequestsPage, { organizationId: 3 }, URL);
    expect(GET).not.toHaveBeenCalledWith(VERIFIERS, expect.anything());

    await wrapper.find("[data-test=verification-create]").trigger("click");
    await flushPromises();

    expect(GET).toHaveBeenCalledWith(VERIFIERS, expect.anything());
  });

  it("withdraws after a plain confirmation, toasts and reloads", async () => {
    GET.mockResolvedValue(page([row()]));
    POST.mockResolvedValue({
      data: { message: "Gone", redirect_url: "/x" },
      response: { ok: true },
    });
    const { wrapper } = await mountPage(OutgoingVerificationRequestsPage, { organizationId: 3 }, URL);
    await open(wrapper);
    items()[1].click();
    await flushPromises();

    expect(document.body.textContent).toContain(
      "Do you want to delete 'Organization verification request 7'?",
    );
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith(`${LIST}/{request_id}/withdraw`, {
      params: { path: { id: 3, request_id: 7 } },
      body: { inline: true },
    });
    expect(success).toHaveBeenCalledWith("Gone");
    expect(GET).toHaveBeenCalledTimes(2);
  });

  it("goes back a page when the last row of a later page was withdrawn", async () => {
    GET.mockResolvedValueOnce(page([row()], { page: 2, total: 51, pages: 2 }));
    GET.mockResolvedValue(page([], { page: 2, total: 50, pages: 1 }));
    POST.mockResolvedValue({ data: { message: "Gone" }, response: { ok: true } });
    const { wrapper, router } = await mountPage(
      OutgoingVerificationRequestsPage,
      { organizationId: 3 },
      `${URL}?page=2`,
    );
    await open(wrapper);
    items()[1].click();
    await flushPromises();
    document.querySelector<HTMLButtonElement>(".modal-footer .btn-danger")!.click();
    await flushPromises();

    expect(router.currentRoute.value.query.page).toBe("1");
  });

  it("shows no table for an empty list and the error of a failed load", async () => {
    GET.mockResolvedValue(page([]));
    const empty = await mountPage(OutgoingVerificationRequestsPage, { organizationId: 3 }, URL);
    expect(empty.wrapper.find("table").exists()).toBe(false);

    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    const failed = await mountPage(OutgoingVerificationRequestsPage, { organizationId: 3 }, URL);
    expect(failed.wrapper.find(".alert-danger").text()).toBe("Forbidden");
  });
});
