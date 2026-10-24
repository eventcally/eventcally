import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";
import { createI18n } from "vue-i18n";

vi.mock("@/shared/boot", () => ({ boot: { locale: "en", csrfToken: "x", loginUrl: "/login" } }));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...args: unknown[]) => GET(...args), POST: (...args: unknown[]) => POST(...args) },
}));

import { useExportJob } from "./useExportJob";

function setup() {
  let result!: ReturnType<typeof useExportJob>;
  const wrapper = mount(
    defineComponent({
      setup() {
        result = useExportJob(3);
        return () => null;
      },
    }),
    { global: { plugins: [createI18n({ legacy: false, locale: "en", messages: { en: {} } })] } },
  );
  return { wrapper, ...result };
}

const status = (ready: boolean, successful: boolean | null = null) => ({
  data: { ready, successful },
});

describe("useExportJob", () => {
  beforeEach(() => {
    GET.mockReset();
    POST.mockReset();
    vi.useFakeTimers();
  });
  afterEach(() => vi.useRealTimers());

  it("is done at once without a job id", async () => {
    POST.mockResolvedValue({ data: { job_id: null } });
    const { job, start } = setup();

    await start();

    expect(POST).toHaveBeenCalledWith("/bff/manage/organizations/{id}/export", {
      params: { path: { id: 3 } },
    });
    expect(job.state).toBe("done");
    expect(GET).not.toHaveBeenCalled();
  });

  it("polls every two seconds until the job is ready", async () => {
    POST.mockResolvedValue({ data: { job_id: "j1" } });
    GET.mockResolvedValueOnce(status(false)).mockResolvedValueOnce(status(true, true));
    const { job, start } = setup();

    await start();
    await flushPromises();
    expect(GET).toHaveBeenCalledWith("/bff/manage/organizations/{id}/export/jobs/{job_id}", {
      params: { path: { id: 3, job_id: "j1" } },
    });
    expect(job.state).toBe("running");

    await vi.advanceTimersByTimeAsync(1999);
    expect(GET).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1);
    expect(GET).toHaveBeenCalledTimes(2);
    expect(job.state).toBe("done");
  });

  it("fails when the job is not successful", async () => {
    POST.mockResolvedValue({ data: { job_id: "j1" } });
    GET.mockResolvedValue(status(true, false));
    const { job, start } = setup();

    await start();
    await flushPromises();

    expect(job).toMatchObject({
      state: "failed",
      error: "The export files could not be created.",
    });
  });

  it("fails when the start request fails", async () => {
    POST.mockResolvedValue({ error: { message: "Forbidden" } });
    const { job, start } = setup();

    await start();

    expect(job).toMatchObject({ state: "failed", error: "Forbidden" });
  });

  it("fails with a generic message when the status request fails", async () => {
    POST.mockResolvedValue({ data: { job_id: "j1" } });
    GET.mockResolvedValue({});
    const { job, start } = setup();

    await start();
    await flushPromises();

    expect(job).toMatchObject({ state: "failed", error: "Error" });
  });

  it("stops polling when the scope is disposed", async () => {
    POST.mockResolvedValue({ data: { job_id: "j1" } });
    GET.mockResolvedValue(status(false));
    const { wrapper, start } = setup();

    await start();
    await flushPromises();
    wrapper.unmount();
    await vi.advanceTimersByTimeAsync(10000);

    expect(GET).toHaveBeenCalledTimes(1);
  });

  it("drops a poll that is still in flight after a reset", async () => {
    POST.mockResolvedValue({ data: { job_id: "j1" } });
    let resolveGet!: (value: unknown) => void;
    GET.mockReturnValue(new Promise((resolve) => (resolveGet = resolve)));
    const { job, start, reset } = setup();

    await start();
    reset();
    resolveGet(status(true, true));
    await flushPromises();

    expect(job.state).toBe("idle");
  });

  it("drops a start that is superseded by a reset", async () => {
    let resolvePost!: (value: unknown) => void;
    POST.mockReturnValue(new Promise((resolve) => (resolvePost = resolve)));
    const { job, start, reset } = setup();

    const started = start();
    reset();
    resolvePost({ data: { job_id: "j1" } });
    await started;

    expect(job.state).toBe("idle");
    expect(GET).not.toHaveBeenCalled();
  });
});
