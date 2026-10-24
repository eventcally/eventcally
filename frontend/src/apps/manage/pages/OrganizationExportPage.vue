<script setup lang="ts">
import { BButton, BSpinner } from "bootstrap-vue-next";
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { boot } from "@/shared/boot";
import { formatDateTime, formatFileSize } from "@/shared/format";
import { useExportJob } from "../composables/useExportJob";

type OrganizationExport = components["schemas"]["OrganizationExport"];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();
const { job, start } = useExportJob(props.organizationId);

const info = ref<OrganizationExport | null>(null);
const loadError = ref<string | null>(null);

const running = computed(() => job.state === "running");

async function load() {
  loadError.value = null;
  const { data, error } = await api.GET("/bff/manage/organizations/{id}/export", {
    params: { path: { id: props.organizationId } },
  });
  if (data) {
    info.value = data;
  } else {
    loadError.value = error?.message ?? t("Error");
  }
}

// The new file replaces the listed one without a page reload.
watch(
  () => job.state,
  (state) => {
    if (state === "done") void load();
  },
);
onMounted(load);
</script>

<template>
  <div>
    <h1>{{ t("Export") }}</h1>

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <template v-if="info">
      <h2>{{ t("Download") }}</h2>
      <ul>
        <li v-if="info.file" data-test="file">
          <a :href="info.file.url">{{ t("All data") }}</a>
          <span class="badge rounded-pill text-bg-light ms-1">
            {{ formatDateTime(info.file.created_at, boot.locale) }}
          </span>
          <span class="badge rounded-pill text-bg-light ms-1">
            {{ formatFileSize(info.file.size) }}
          </span>
        </li>
        <li v-else data-test="no-file">{{ t("No files available") }}</li>
      </ul>
    </template>

    <p>
      <BButton id="submit_async" variant="primary" :disabled="running" @click="start">
        {{ t("Create export files") }}
      </BButton>
    </p>

    <BSpinner v-if="running" class="m-3" data-test="spinner" />
    <div v-if="job.state === 'failed'" class="alert alert-danger" role="alert">
      {{ job.error }}
    </div>
  </div>
</template>
