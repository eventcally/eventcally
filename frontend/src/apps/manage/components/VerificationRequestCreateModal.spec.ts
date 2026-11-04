import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, h, ref } from "vue";

vi.mock("@/shared/boot", () => ({ boot: { base: "/", locale: "en", csrfToken: "x" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a), POST: (...a: unknown[]) => POST(...a) },
}));
const success = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({ useNotify: () => ({ success, error: vi.fn() }) }));

import { mountPage } from "../testing";
import VerificationRequestCreateModal from "./VerificationRequestCreateModal.vue";

const VERIFIERS = "/bff/manage/organizations/{id}/verifier-organizations";
const CREATE = "/bff/manage/organizations/{id}/outgoing-verification-requests";
const verifier = (over = {}) => ({
  id: 4,
  name: "Andere Crew",
  is_verified: true,
  location: "38640 Goslar",
  logo_url: "/image/1?s=120",
  description: "We verify.",
  incoming_verification_requests_text: "Send us your site.",
  can_request: true,
  ...over,
});
const verifiers = (items: object[], over = {}) => ({
  data: {
    items,
    page: 1,
    per_page: 20,
    total: items.length,
    pages: items.length ? 1 : 0,
    can_write: true,
    organization_name: "Meine Crew",
    postal_code: "38640",
    ...over,
  },
});

const created = vi.fn();
const Host = defineComponent({
  setup() {
    const show = ref(false);
    (window as unknown as { open: () => void }).open = () => (show.value = true);
    return () =>
      h(VerificationRequestCreateModal, {
        modelValue: show.value,
        "onUpdate:modelValue": (value: boolean) => (show.value = value),
        organizationId: 3,
        onCreated: created,
      });
  },
});

async function openModal() {
  const mounted = await mountPage(Host, {}, "/manage/admin_unit/3/outgoing_organization_verification_requests");
  (window as unknown as { open: () => void }).open();
  await flushPromises();
  return mounted;
}
const body = () => document.body.textContent ?? "";
const click = async (selector: string) => {
  document.querySelector<HTMLButtonElement>(selector)!.click();
  await flushPromises();
};

describe("VerificationRequestCreateModal", () => {
  beforeEach(() => {
    [GET, POST, success, created].forEach((f) => f.mockReset());
    document.body.innerHTML = "";
  });

  it("lists the verifiers of the organization's postal code", async () => {
    GET.mockResolvedValue(verifiers([verifier()]));
    await openModal();

    expect(GET).toHaveBeenCalledWith(VERIFIERS, { params: { path: { id: 3 }, query: { page: 1 } } });
    expect(body()).toContain("Here you can find organizations that can verify other organizations.");
    expect(body()).toContain("Andere Crew");
    expect(body()).toContain("38640 Goslar");
    expect(body()).toContain("We verify.");
    expect(body()).toContain("Send us your site.");
    expect(document.querySelector("img")?.getAttribute("src")).toBe("/image/1?s=120");
    expect(document.querySelector("a[href='/organizations/4']")).not.toBeNull();
  });

  it("explains that no verifier was found", async () => {
    GET.mockResolvedValue(verifiers([]));
    await openModal();

    expect(body()).toContain(
      "No organizations were found that can verify your organization with postal code 38640.",
    );
  });

  it("disables the request for an organization that cannot be asked", async () => {
    GET.mockResolvedValue(verifiers([verifier({ can_request: false, is_verified: false })]));
    await openModal();

    expect(document.querySelector<HTMLButtonElement>("[data-test=verifier-select]")!.disabled).toBe(
      true,
    );
  });

  it("shows the error of a failed load", async () => {
    GET.mockResolvedValue({ error: { message: "Forbidden" } });
    await openModal();

    expect(document.querySelector("[data-test=verification-error]")?.textContent?.trim()).toBe(
      "Forbidden",
    );
  });

  it("pages through the verifiers", async () => {
    GET.mockResolvedValue(verifiers([verifier()], { total: 45, pages: 3 }));
    await openModal();
    await click('button[aria-label="Next page"]');

    expect(GET).toHaveBeenLastCalledWith(VERIFIERS, {
      params: { path: { id: 3 }, query: { page: 2 } },
    });
  });

  it("confirms the request for the selected verifier", async () => {
    GET.mockResolvedValue(verifiers([verifier()]));
    POST.mockResolvedValue({ data: { message: "Request successfully created." } });
    await openModal();
    await click("[data-test=verifier-select]");

    expect(body()).toContain('Request verification for organization "Meine Crew"');
    expect(body()).toContain('Ask "Andere Crew" to verify your organization.');

    await click("[data-test=verification-submit]");

    expect(POST).toHaveBeenCalledWith(CREATE, {
      params: { path: { id: 3 } },
      body: { target_id: 4 },
    });
    expect(success).toHaveBeenCalledWith("Request successfully created.");
    expect(created).toHaveBeenCalled();
  });

  it("shows the refusal inside the dialog and goes back to the list", async () => {
    GET.mockResolvedValue(verifiers([verifier({ is_verified: false })]));
    POST.mockResolvedValue({ error: { message: "Not allowed" } });
    await openModal();
    await click("[data-test=verifier-select]");
    await click("[data-test=verification-submit]");

    expect(document.querySelector("[data-test=verification-error]")?.textContent?.trim()).toBe(
      "Not allowed",
    );
    expect(created).not.toHaveBeenCalled();

    const cancel = [...document.querySelectorAll<HTMLButtonElement>(".modal-body button")].find(
      (b) => b.textContent?.trim() === "Cancel",
    )!;
    cancel.click();
    await flushPromises();

    expect(document.querySelector("[data-test=verifier-select]")).not.toBeNull();
  });
});
