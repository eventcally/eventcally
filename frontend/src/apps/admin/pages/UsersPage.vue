<script setup lang="ts">
import { BButton, BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { boot } from "@/shared/boot";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import AppPager from "@/shared/AppPager.vue";
import { formatDate } from "@/shared/format";
import UserDeleteModal from "../components/UserDeleteModal.vue";

type UserPage = components["schemas"]["AdminUserPage"];

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const page = ref<UserPage | null>(null);
const loading = ref(false);
const deleting = ref<{ id: number; email: string } | null>(null);
const showDelete = ref(false);
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

function askDelete(item: { id: number; email: string }) {
  deleting.value = item;
  showDelete.value = true;
}

async function onDeleted() {
  await load();
  // The deleted user may have been the last one of the page.
  if (page.value?.items.length === 0 && currentPage.value > 1) {
    currentPage.value = currentPage.value - 1;
  }
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
          <router-link :to="{ name: 'user-update', params: { id: item.id } }" class="me-2">
            {{ t("Edit") }}
          </router-link>
          <BButton variant="link" class="p-0 align-baseline" @click="askDelete(item)">
            {{ t("Delete") }}
          </BButton>
        </template>
      </BTable>
    </BOverlay>

    <UserDeleteModal v-model="showDelete" :user="deleting" @deleted="onDeleted" />

    <AppPager
      v-if="page && page.pages > 1"
      v-model:page="currentPage"
      :pages="page.pages"
      :total="page.total"
    />
  </div>
</template>
