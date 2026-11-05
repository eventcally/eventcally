import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en" } }));

import AuditLine from "./AuditLine.vue";

const messages = {
  "Created at %(created_at)s.": "Created at {created_at}.",
  "Created at %(created_at)s by %(created_by)s.": "Created at {created_at} by {created_by}.",
  "Last updated at %(updated_at)s.": "Last updated at {updated_at}.",
  "Last updated at %(updated_at)s by %(updated_by)s.":
    "Last updated at {updated_at} by {updated_by}.",
};

function mountAudit(audit: object | null) {
  return mount(AuditLine, {
    props: { audit },
    global: {
      plugins: [createI18n({ legacy: false, locale: "en", messages: { en: messages } })],
    },
  });
}

describe("AuditLine", () => {
  it("renders nothing without audit data", () => {
    expect(mountAudit(null).find("[data-test=audit]").exists()).toBe(false);
  });

  it("names the creator", () => {
    const text = mountAudit({
      created_at: "2026-11-03T14:41:00Z",
      created_by_label: "test@test.de",
    }).text();

    expect(text).toContain("by test@test.de.");
  });

  it("shows the creation without a creator", () => {
    expect(mountAudit({ created_at: "2026-11-03T14:41:00Z" }).text()).toMatch(/^Created at .*\.$/);
  });

  it("adds the update only when it differs", () => {
    const same = mountAudit({
      created_at: "2026-11-03T14:41:00Z",
      updated_at: "2026-11-03T14:41:30Z",
    });
    expect(same.text()).not.toContain("Last updated");

    const later = mountAudit({
      created_at: "2026-11-03T14:41:00Z",
      updated_at: "2026-11-05T09:00:00Z",
      updated_by_label: "other@test.de",
    });
    expect(later.text()).toContain("Last updated at");
    expect(later.text()).toContain("by other@test.de.");

    const anonymous = mountAudit({
      created_at: "2026-11-03T14:41:00Z",
      updated_at: "2026-11-05T09:00:00Z",
    });
    expect(anonymous.text()).toMatch(/Last updated at [^b]*\.$/);
  });

  it("renders one plain line when inline", () => {
    const wrapper = mount(AuditLine, {
      props: { audit: { created_at: "2026-11-03T14:41:00Z" }, inline: true },
      global: {
        plugins: [createI18n({ legacy: false, locale: "en", messages: { en: messages } })],
      },
    });

    expect(wrapper.find("span[data-test=audit]").text()).toContain("Created at");
    expect(wrapper.find("div").exists()).toBe(false);
  });
});
