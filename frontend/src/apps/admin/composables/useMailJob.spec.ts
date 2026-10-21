import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({ api: { GET: (...args: unknown[]) => GET(...args) } }));

import { useMailJob } from "./useMailJob";

function setup() {
  let result!: ReturnType<typeof useMailJob>;
  const wrapper = mount(
    defineComponent({
      setup() {
        result = useMailJob();
        return () => null;
      },
    }),
    { global: { plugins: [createI18n({ legacy: false, locale: "en", messages: { en: {} } })] } },
  );
  return { wrapper, ...result };
}

const status = (completed: number, ready: boolean, successful: boolean | null = null) => ({
  data: { job_id: "j1", count: 3, completed, ready, successful },
});

describe("useMailJob", () => {
  beforeEach(() => {
    GET.mockReset();
    vi.useFakeTimers();
  });
  afterEach(() => vi.useRealTimers());

  it("is done at once without a job id", () => {
    const { job, track } = setup();

    track({ job_id: null, count: 2 });

    expect(job).toMatchObject({ state: "done", count: 2, completed: 2 });
    expect(GET).not.toHaveBeenCalled();
  });

  it("polls until the job is ready", async () => {
    GET.mockResolvedValueOnce(status(1, false))
      .mockResolvedValueOnce(status(2, false))
      .mockResolvedValueOnce(status(3, true, true));
    const { job, track } = setup();

    track({ job_id: "j1", count: 3 });
    expect(job.state).toBe("running");
    await flushPromises();
    expect(job).toMatchObject({ state: "running", completed: 1 });

    await vi.advanceTimersByTimeAsync(1000);
    expect(job.completed).toBe(2);

    await vi.advanceTimersByTimeAsync(1000);
    expect(job).toMatchObject({ state: "done", completed: 3 });
    expect(GET).toHaveBeenCalledTimes(3);
    expect(GET.mock.calls[0][1]).toEqual({ params: { path: { job_id: "j1" } } });
  });

  it("fails when not all mails were sent", async () => {
    GET.mockResolvedValue(status(3, true, false));
    const { job, track } = setup();

    track({ job_id: "j1", count: 3 });
    await flushPromises();

    expect(job.state).toBe("failed");
    expect(job.error).toBe("Not all mails could be sent.");
  });

  it("fails with the server message, e.g. for an expired job", async () => {
    GET.mockResolvedValue({ error: { name: "Not Found", message: "Not found" } });
    const { job, track } = setup();

    track({ job_id: "j1", count: 3 });
    await flushPromises();

    expect(job).toMatchObject({ state: "failed", error: "Not found" });
    await vi.advanceTimersByTimeAsync(5000);
    expect(GET).toHaveBeenCalledTimes(1);
  });

  it("stops polling on reset", async () => {
    GET.mockResolvedValue(status(1, false));
    const { job, track, reset } = setup();

    track({ job_id: "j1", count: 3 });
    await flushPromises();
    reset();
    await vi.advanceTimersByTimeAsync(5000);

    expect(GET).toHaveBeenCalledTimes(1);
    expect(job.state).toBe("idle");
  });

  it("drops a poll that is in flight when reset", async () => {
    let resolve!: (v: unknown) => void;
    GET.mockReturnValue(new Promise((r) => (resolve = r)));
    const { job, track, reset } = setup();

    track({ job_id: "j1", count: 3 });
    reset();
    resolve(status(1, false));
    await flushPromises();
    await vi.advanceTimersByTimeAsync(5000);

    expect(job.state).toBe("idle");
    expect(GET).toHaveBeenCalledTimes(1);
  });

  it("stops polling when the component unmounts", async () => {
    GET.mockResolvedValue(status(1, false));
    const { wrapper, track } = setup();

    track({ job_id: "j1", count: 3 });
    await flushPromises();
    wrapper.unmount();
    await vi.advanceTimersByTimeAsync(5000);

    expect(GET).toHaveBeenCalledTimes(1);
  });
});
