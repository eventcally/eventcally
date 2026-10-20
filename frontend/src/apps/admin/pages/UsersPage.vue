<script setup lang="ts">
import { BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { boot } from "@/shared/boot";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import AppPager from "@/shared/AppPager.vue";
import { formatDate } from "@/shared/format";
import { legacy } from "../legacy";

type UserPage = components["schemas"]["AdminUserPage"];

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const page = ref<UserPage | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

const currentPage = computed({
  get: () => Number(route.query.page ?? 1) || 1,
  set: (value: number) => {
    router.push({ name: "users", query: { page: String(value) } });
  },
});

const fields = computed<TableFieldRaw[]>(() => [
  { key: "email", label: t("Email") },
  { key: "created_at", label: t("Created at") },
  { key: "confirmed_at", label: t("Confirmed at") },
  { key: "tos_accepted_at", label: t("Terms of service accepted at") },
  { key: "deletion_requested_at", label: t("Deletion requested at") },
  { key: "actions", label: "" },
]);

const fmt = (iso: string | null | undefined) => formatDate(iso, boot.locale);

async function load() {
  loading.value = true;
  error.value = null;
  const { data, error: err } = await api.GET("/bff/admin/users", {
    params: { query: { page: currentPage.value } },
  });
  if (data) {
    page.value = data;
  } else {
    error.value = err?.message ?? t("Error");
  }
  loading.value = false;
}

watch(currentPage, load, { immediate: true });
</script>

<template>
  <div>
    <AppBreadcrumb :items="[{ label: t('Admin'), to: { name: 'home' } }, { label: t('Users') }]" />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <BTable :items="page?.items ?? []" :fields="fields" responsive striped bordered>
        <template #cell(created_at)="{ item }">{{ fmt(item.created_at) }}</template>
        <template #cell(confirmed_at)="{ item }">{{ fmt(item.confirmed_at) }}</template>
        <template #cell(tos_accepted_at)="{ item }">{{ fmt(item.tos_accepted_at) }}</template>
        <template #cell(deletion_requested_at)="{ item }">
          {{ fmt(item.deletion_requested_at) }}
        </template>
        <template #cell(actions)="{ item }">
          <a :href="legacy.userUpdate(item.id)" class="me-2">{{ t("Edit") }}</a>
          <a :href="legacy.userDelete(item.id)">{{ t("Delete") }}</a>
        </template>
      </BTable>
    </BOverlay>

    <AppPager
      v-if="page && page.pages > 1"
      v-model:page="currentPage"
      :pages="page.pages"
      :total="page.total"
    />
  </div>
</template>
