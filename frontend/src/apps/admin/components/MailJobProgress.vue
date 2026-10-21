<script setup lang="ts">
import { BProgress } from "bootstrap-vue-next";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { MailJobState } from "../composables/useMailJob";

const props = defineProps<{
  job: { state: MailJobState; count: number; completed: number; error: string | null };
}>();

const { t } = useI18n();

const percent = computed(() =>
  props.job.count > 0 ? Math.round((props.job.completed / props.job.count) * 100) : 0,
);
</script>

<template>
  <div v-if="job.state !== 'idle'" class="mail-job-progress mb-3">
    <div v-if="job.state === 'running'">
      <BProgress :value="percent" :max="100" animated show-progress />
      <small class="text-muted">{{ job.completed }} / {{ job.count }}</small>
    </div>
    <div v-else-if="job.state === 'done'" class="alert alert-success mb-0" role="alert">
      {{ t("Mails sent successfully") }} ({{ job.count }})
    </div>
    <div v-else class="alert alert-danger mb-0" role="alert">{{ job.error }}</div>
  </div>
</template>
