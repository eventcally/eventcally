<script setup lang="ts">
import { BOverlay } from "bootstrap-vue-next";
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import SettingCard from "../components/SettingCard.vue";

const { t } = useI18n();

const value = ref<string | null>(null);
const loaded = ref(false);
const loading = ref(false);
const error = ref<string | null>(null);

const example = `[
  {
    "title": "My calendar",
    "url": "https://example.com/calendar.ics",
    "active": true
  }
]`;

async function load() {
  loading.value = true;
  error.value = null;
  const { data, error: err } = await api.GET("/bff/admin/planning");
  if (data) {
    value.value = data.planning_external_calendars ?? null;
    loaded.value = true;
  } else {
    error.value = err?.message ?? t("Error");
  }
  loading.value = false;
}

async function save(v: string | null): Promise<string | null> {
  const { data, error: err } = await api.PUT("/bff/admin/planning", {
    body: { planning_external_calendars: v },
  });
  if (!data) {
    const fieldMsg = err && "errors" in err ? err.errors[0]?.msg : undefined;
    throw new Error(fieldMsg ?? err?.message ?? t("Error"));
  }
  return data.planning_external_calendars ?? null;
}

onMounted(load);
</script>

<template>
  <div>
    <AppBreadcrumb
      :items="[{ label: t('Admin'), to: { name: 'home' } }, { label: t('Planning') }]"
    />

    <h1>{{ t("Planning") }}</h1>

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <SettingCard
        v-if="loaded"
        :label="t('External calendars')"
        input-id="planning-external-calendars"
        monospace
        :rows="16"
        :value="value"
        :save="save"
        @saved="(v) => (value = v)"
      >
        <template #help>
          <p class="mb-1">{{ t("Example") }}</p>
          <pre class="small">{{ example }}</pre>
        </template>
      </SettingCard>
    </BOverlay>
  </div>
</template>
