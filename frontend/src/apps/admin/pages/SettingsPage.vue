<script setup lang="ts">
import { BOverlay } from "bootstrap-vue-next";
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import { publicPages } from "@/shared/legacy";
import ResetTosModal from "../components/ResetTosModal.vue";
import SettingCard from "../components/SettingCard.vue";

type Settings = components["schemas"]["AdminSettings"];
type SettingKey = keyof Settings;

const { t } = useI18n();

const settings = ref<Settings | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);
const showReset = ref(false);

const fields: { key: SettingKey; label: string; href?: string }[] = [
  { key: "start_page", label: t("Start page"), href: publicPages.home },
  { key: "tos", label: t("Terms of service"), href: publicPages.tos },
  {
    key: "legal_notice",
    label: t("Legal notice"),
    href: publicPages.legalNotice,
  },
  { key: "contact", label: t("Contact"), href: publicPages.contact },
  { key: "privacy", label: t("Privacy"), href: publicPages.privacy },
  { key: "announcement", label: t("Announcement") },
];

async function load() {
  loading.value = true;
  error.value = null;
  const { data, error: err } = await api.GET("/bff/admin/settings");
  if (data) settings.value = data;
  else error.value = err?.message ?? t("Error");
  loading.value = false;
}

async function saveSetting(key: SettingKey, value: string | null): Promise<string | null> {
  const { error: err } = await api.PUT("/bff/admin/settings/{key}", {
    params: { path: { key } },
    body: { value },
  });
  if (err) {
    const fieldMsg = "errors" in err ? err.errors[0]?.msg : undefined;
    throw new Error(fieldMsg ?? err.message ?? t("Error"));
  }
  return value;
}

onMounted(load);
</script>

<template>
  <div>
    <AppBreadcrumb
      :items="[{ label: t('Admin'), to: { name: 'home' } }, { label: t('Settings') }]"
    />

    <h1>{{ t("Settings") }}</h1>

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <div v-if="settings">
        <SettingCard
          v-for="f in fields"
          :key="f.key"
          class="mb-3"
          :label="f.label"
          :href="f.href"
          :input-id="`setting-${f.key}`"
          :value="settings[f.key] ?? null"
          :save="(v) => saveSetting(f.key, v)"
          @saved="(v) => (settings![f.key] = v)"
        />

        <div class="card border-danger mb-3">
          <div class="card-body">
            <h5 class="card-title">
              {{ t("Reset acceptance of terms of service and privacy") }}
            </h5>
            <p class="card-text">
              {{ t("All users have to accept the terms of service and privacy again.") }}
            </p>
            <button type="button" class="btn btn-outline-danger" @click="showReset = true">
              {{ t("Reset") }}
            </button>
          </div>
        </div>
      </div>
    </BOverlay>

    <ResetTosModal v-model="showReset" />
  </div>
</template>
