import { onScopeDispose, reactive } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";

type MailJob = components["schemas"]["AdminMailJob"];

export type MailJobState = "idle" | "running" | "done" | "failed";

const POLL_INTERVAL_MS = 1000;

/** Follows a queued batch of mails: short-polls the job status until it is ready. */
export function useMailJob() {
  const { t } = useI18n();

  const job = reactive({
    state: "idle" as MailJobState,
    count: 0,
    completed: 0,
    error: null as string | null,
  });

  let timer: ReturnType<typeof setTimeout> | undefined;
  // Bumped by reset()/track() so a poll that is still in flight is dropped.
  let generation = 0;

  function stopTimer() {
    if (timer !== undefined) clearTimeout(timer);
    timer = undefined;
  }

  function reset() {
    generation++;
    stopTimer();
    job.state = "idle";
    job.count = 0;
    job.completed = 0;
    job.error = null;
  }

  async function poll(jobId: string, current: number) {
    const { data, error } = await api.GET("/bff/admin/mail-jobs/{job_id}", {
      params: { path: { job_id: jobId } },
    });
    if (current !== generation) return;

    if (!data) {
      job.state = "failed";
      job.error = error?.message ?? t("Error");
      return;
    }

    job.count = data.count;
    job.completed = data.completed;

    if (!data.ready) {
      timer = setTimeout(() => poll(jobId, current), POLL_INTERVAL_MS);
    } else if (data.successful) {
      job.state = "done";
    } else {
      job.state = "failed";
      job.error = t("Not all mails could be sent.");
    }
  }

  function track(mail: MailJob) {
    reset();
    job.count = mail.count;

    // Nothing to follow: the mails were already sent, or there are none.
    if (mail.job_id === null || mail.job_id === undefined) {
      job.completed = mail.count;
      job.state = "done";
      return;
    }

    job.state = "running";
    void poll(mail.job_id, generation);
  }

  onScopeDispose(reset);

  return { job, track, reset };
}
