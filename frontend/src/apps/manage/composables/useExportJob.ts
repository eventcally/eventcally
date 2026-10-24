import { onScopeDispose, reactive } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";

export type ExportJobState = "idle" | "running" | "done" | "failed";

const POLL_INTERVAL_MS = 2000;

/** Starts the export of an organization and short-polls its job until it is ready. */
export function useExportJob(organizationId: number) {
  const { t } = useI18n();

  const job = reactive({
    state: "idle" as ExportJobState,
    error: null as string | null,
  });

  let timer: ReturnType<typeof setTimeout> | undefined;
  // Bumped by reset()/start() so a poll that is still in flight is dropped.
  let generation = 0;

  function reset() {
    generation++;
    if (timer !== undefined) clearTimeout(timer);
    timer = undefined;
    job.state = "idle";
    job.error = null;
  }

  function fail(message: string) {
    job.state = "failed";
    job.error = message;
  }

  async function poll(jobId: string, current: number) {
    const { data, error } = await api.GET("/bff/manage/organizations/{id}/export/jobs/{job_id}", {
      params: { path: { id: organizationId, job_id: jobId } },
    });
    if (current !== generation) return;

    if (!data) {
      fail(error?.message ?? t("Error"));
    } else if (!data.ready) {
      timer = setTimeout(() => poll(jobId, current), POLL_INTERVAL_MS);
    } else if (data.successful) {
      job.state = "done";
    } else {
      fail(t("The export files could not be created."));
    }
  }

  async function start() {
    reset();
    const current = generation;
    job.state = "running";

    const { data, error } = await api.POST("/bff/manage/organizations/{id}/export", {
      params: { path: { id: organizationId } },
    });
    if (current !== generation) return;

    if (!data) {
      fail(error?.message ?? t("Error"));
    } else if (data.job_id === null || data.job_id === undefined) {
      // Nothing to follow: the export already ran.
      job.state = "done";
    } else {
      void poll(data.job_id, current);
    }
  }

  onScopeDispose(reset);

  return { job, start, reset };
}
