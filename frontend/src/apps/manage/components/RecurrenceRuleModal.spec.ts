import { flushPromises, mount } from "@vue/test-utils";
import { createBootstrap } from "bootstrap-vue-next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createI18n } from "vue-i18n";

const POST = vi.fn();
vi.mock("@/shared/api", () => ({ api: { POST: (...a: unknown[]) => POST(...a) } }));

import RecurrenceRuleModal from "./RecurrenceRuleModal.vue";

let mounted: { unmount: () => void } | null = null;

function mountModal(rule: string | null) {
  const wrapper = mount(RecurrenceRuleModal, {
    props: {
      organizationId: 5,
      start: "2030-12-30",
      idPrefix: "date_definitions-0-",
      modelValue: rule,
      show: false,
      "onUpdate:modelValue": (v: string | null) => wrapper.setProps({ modelValue: v }),
      "onUpdate:show": (v: boolean) => wrapper.setProps({ show: v }),
    },
    attachTo: document.body,
    global: {
      plugins: [createBootstrap(), createI18n({ legacy: false, locale: "en", messages: { en: {} } })],
      stubs: { transition: false },
    },
  });
  mounted = wrapper;
  return wrapper;
}

async function open(wrapper: ReturnType<typeof mountModal>) {
  await wrapper.setProps({ show: true });
  vi.advanceTimersByTime(300);
  await flushPromises();
}

const q = <T extends Element = HTMLElement>(selector: string) => document.body.querySelector<T>(selector)!;
const all = (selector: string) => Array.from(document.body.querySelectorAll<HTMLElement>(selector));

// Lets the watcher schedule the debounced preview, then runs it.
async function settle() {
  await flushPromises();
  vi.advanceTimersByTime(300);
  await flushPromises();
}

async function change(selector: string, value: string) {
  const element = q<HTMLInputElement | HTMLSelectElement>(selector);
  element.value = value;
  element.dispatchEvent(new Event(element.tagName === "SELECT" ? "change" : "input"));
  await settle();
}

async function click(selector: string) {
  q(selector).click();
  await settle();
}

function lastBody() {
  return POST.mock.calls.at(-1)![1].body;
}

describe("RecurrenceRuleModal", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    POST.mockReset().mockResolvedValue({
      data: {
        items: [
          { date: "20301230T000000", formatted_date: "30.12.2030", type: "start" },
          { date: "20301231T000000", formatted_date: "31.12.2030", type: "rrule" },
          { date: "20310101T000000", formatted_date: "01.01.2031", type: "exdate" },
          { date: "20310105T000000", formatted_date: "05.01.2031", type: "rdate" },
        ],
        has_more: true,
      },
    });
  });
  afterEach(() => {
    mounted?.unmount();
    vi.useRealTimers();
  });

  it("starts a new rule daily until the start and previews it", async () => {
    const wrapper = mountModal(null);
    await open(wrapper);

    expect(POST).toHaveBeenCalledWith("/bff/manage/organizations/{id}/events/occurrences", {
      params: { path: { id: 5 } },
      body: {
        start: "2030-12-30T00:00",
        rrule: "RRULE:FREQ=DAILY;UNTIL=20301230T000000",
        batch_start: 0,
      },
    });
    expect(all('[data-test="occurrence"]')).toHaveLength(4);
    expect(q('[data-test="remove-recurrence"]')).toBeNull();

    await click('[data-test="apply"]');

    expect(wrapper.props("modelValue")).toBe("RRULE:FREQ=DAILY;UNTIL=20301230T000000");
    expect(wrapper.props("show")).toBe(false);
  });

  it("edits a weekly rule with weekdays, interval and count", async () => {
    const wrapper = mountModal(null);
    await open(wrapper);

    await change("#date_definitions-0-recc-freq", "WEEKLY");
    await change("#date_definitions-0-recc-interval", "2");
    await click("#date_definitions-0-recc-weekday-FR");
    await click("#date_definitions-0-recc-weekday-MO");
    await click("#date_definitions-0-recc-end-count");
    await change("#date_definitions-0-recc-count", "4");

    expect(lastBody().rrule).toBe("RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=FR;COUNT=4");

    await click("#date_definitions-0-recc-end-never");
    await click('[data-test="apply"]');

    expect(wrapper.props("modelValue")).toBe("RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=FR");
  });

  it("edits monthly and yearly day options", async () => {
    const wrapper = mountModal("RRULE:FREQ=MONTHLY;BYMONTHDAY=15;COUNT=3");
    await open(wrapper);

    await click("#date_definitions-0-recc-weekdayofmonth");
    await change("#date_definitions-0-recc-weekdayindex", "-1");
    await change("#date_definitions-0-recc-weekday", "FR");
    expect(lastBody().rrule).toBe("RRULE:FREQ=MONTHLY;BYDAY=-1FR;COUNT=3");

    await change("#date_definitions-0-recc-freq", "YEARLY");
    await click("#date_definitions-0-recc-dayofmonth");
    await change("#date_definitions-0-recc-dayofmonth-month", "3");
    await change("#date_definitions-0-recc-monthday", "7");
    await click("#date_definitions-0-recc-end-until");
    await change("#date_definitions-0-recc-until", "");
    await change("#date_definitions-0-recc-until", "2035-12-31");
    await click('[data-test="apply"]');

    expect(wrapper.props("modelValue")).toBe(
      "RRULE:FREQ=YEARLY;BYMONTH=3;BYMONTHDAY=7;UNTIL=20351231T000000",
    );
  });

  it("excludes, includes and adds dates and pages the preview", async () => {
    const wrapper = mountModal("RRULE:FREQ=DAILY;COUNT=12\nEXDATE:20310101T000000\nRDATE:20310105T000000");
    await open(wrapper);

    const toggles = () => all('[data-test="toggle"]');
    expect(toggles().map((b) => b.textContent!.trim())).toEqual(["Exclude", "Include", "Remove"]);

    const toggle = async (index: number) => {
      toggles()[index].click();
      await settle();
    };
    await toggle(0);
    expect(lastBody().rrule).toContain("EXDATE:20301231T000000,20310101T000000");
    await toggle(1);
    await toggle(2);
    await change("#date_definitions-0-recc-add-date", "2031-02-01");
    await click('[data-test="add-date"]');

    expect(lastBody().rrule).toBe(
      "RRULE:FREQ=DAILY;COUNT=12\nEXDATE:20301231T000000\nRDATE:20310201T000000",
    );

    await click('[data-test="more"]');
    expect(lastBody().batch_start).toBe(10);
    expect(all('[data-test="occurrence"]')).toHaveLength(8);
  });

  it("shows a preview error", async () => {
    POST.mockResolvedValue({ error: { message: "Bad rule" } });
    const wrapper = mountModal(null);
    await open(wrapper);

    expect(document.body.textContent).toContain("Bad rule");
  });

  it("keeps a rule it cannot edit and can remove it", async () => {
    const wrapper = mountModal("RRULE:FREQ=DAILY;BYHOUR=3");
    await open(wrapper);

    expect(q('[data-test="raw-rule"]').textContent).toBe("RRULE:FREQ=DAILY;BYHOUR=3");
    expect(q('[data-test="apply"]')).toBeNull();
    expect(POST).not.toHaveBeenCalled();

    await click('[data-test="cancel"]');
    expect(wrapper.props("modelValue")).toBe("RRULE:FREQ=DAILY;BYHOUR=3");
    expect(wrapper.props("show")).toBe(false);
  });

  it("removes the recurrence", async () => {
    const wrapper = mountModal("RRULE:FREQ=DAILY;BYHOUR=3");
    await open(wrapper);

    await click('[data-test="remove-recurrence"]');

    expect(wrapper.props("modelValue")).toBeNull();
    expect(wrapper.props("show")).toBe(false);
  });
});
