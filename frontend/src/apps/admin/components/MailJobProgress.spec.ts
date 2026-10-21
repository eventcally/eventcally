import { mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { describe, expect, it } from "vitest";
import { createI18n } from "vue-i18n";
import MailJobProgress from "./MailJobProgress.vue";

const mountProgress = (job: object) =>
  mount(MailJobProgress, {
    props: { job: job as never },
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
    },
  });

describe("MailJobProgress", () => {
  it("renders nothing while idle", () => {
    const wrapper = mountProgress({ state: "idle", count: 0, completed: 0, error: null });

    expect(wrapper.html()).toBe("<!--v-if-->");
  });

  it("shows the progress while running", () => {
    const wrapper = mountProgress({ state: "running", count: 4, completed: 1, error: null });

    expect(wrapper.find(".progress-bar").attributes("style")).toContain("width: 25%");
    expect(wrapper.text()).toContain("1 / 4");
  });

  it("shows the success message", () => {
    const wrapper = mountProgress({ state: "done", count: 4, completed: 4, error: null });

    expect(wrapper.find(".alert-success").text()).toBe("Mails sent successfully (4)");
  });

  it("shows the error", () => {
    const wrapper = mountProgress({ state: "failed", count: 4, completed: 2, error: "Boom" });

    expect(wrapper.find(".alert-danger").text()).toBe("Boom");
  });
});
