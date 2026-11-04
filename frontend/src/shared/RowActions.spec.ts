import { mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { beforeEach, describe, expect, it, vi } from "vitest";
import RowActions from "./RowActions.vue";

describe("RowActions", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("opens the actions as links and callbacks", async () => {
    const onClick = vi.fn();
    const wrapper = mount(RowActions, {
      props: {
        label: "Mein Veranstalter",
        actions: [
          { title: "View", href: "/organizers/4" },
          { title: "Delete", onClick },
        ],
      },
      attachTo: document.body,
      global: { plugins: [createBootstrap()] },
    });

    expect(wrapper.text()).toContain("Mein Veranstalter");
    await wrapper.find("button").trigger("click");

    const items = [...document.querySelectorAll<HTMLElement>(".dropdown-item")];
    expect(items.map((i) => i.textContent?.trim())).toEqual(["View", "Delete"]);
    expect(items[0].getAttribute("href")).toBe("/organizers/4");
    items[1].click();
    expect(onClick).toHaveBeenCalledOnce();
  });
});
