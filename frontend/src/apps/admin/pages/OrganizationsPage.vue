<script setup lang="ts">
import { useDebounceFn } from "@vueuse/core";
import {
  BButton,
  BFormInput,
  BOverlay,
  BTable,
  type TableFieldRaw,
} from "bootstrap-vue-next";
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { boot } from "@/shared/boot";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import AppPager from "@/shared/AppPager.vue";
import { formatDate } from "@/shared/format";
import { manage, publicPages } from "@/shared/legacy";
import OrganizationDeleteModal from "../components/OrganizationDeleteModal.vue";

type OrganizationPage = components["schemas"]["AdminOrganizationPage"];

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const page = ref<OrganizationPage | null>(null);
const loading = ref(false);
const deleting = ref<{ id: number; name: string } | null>(null);
const showDelete = ref(false);
const error = ref<string | null>(null);

const keyword = ref(typeof route.query.keyword === "string" ? route.query.keyword : "");
const currentKeyword = computed(() =>
  typeof route.query.keyword === "string" ? route.query.keyword : undefined,
);

const currentPage = computed({
  get: () => Number(route.query.page ?? 1) || 1,
  set: (value: number) => {
    router.push({
      name: "organizations",
      query: { keyword: currentKeyword.value, page: String(value) },
    });
  },
});

// A new search always starts on page 1; replace, so typing leaves no history entries.
const search = useDebounceFn((value: string) => {
  router.replace({ name: "organizations", query: { keyword: value.trim() || undefined } });
}, 300);

const fields = computed<TableFieldRaw[]>(() => [
  { key: "name", label: t("Name") },
  { key: "is_verified", label: t("Verified") },
  { key: "created_at", label: t("Created at") },
  { key: "deletion_requested_at", label: t("Deletion requested at") },
  { key: "actions", label: "" },
]);

const fmt = (iso: string | null | undefined) => formatDate(iso, boot.locale);

async function load() {
  loading.value = true;
  error.value = null;
  const { data, error: err } = await api.GET("/bff/admin/organizations", {
    params: { query: { page: currentPage.value, keyword: currentKeyword.value } },
  });
  if (data) {
    page.value = data;
  } else {
    error.value = err?.message ?? t("Error");
  }
  loading.value = false;
}

function askDelete(item: { id: number; name: string }) {
  deleting.value = item;
  showDelete.value = true;
}

async function onDeleted() {
  await load();
  // The deleted organization may have been the last one of the page.
  if (page.value?.items.length === 0 && currentPage.value > 1) {
    currentPage.value = currentPage.value - 1;
  }
}

watch(keyword, (value) => search(value));
watch(() => route.query, load, { immediate: true });
</script>

<template>
  <div>
    <AppBreadcrumb
      :items="[{ label: t('Admin'), to: { name: 'home' } }, { label: t('Organizations') }]"
    />

    <BFormInput
      v-model="keyword"
      type="search"
      class="mb-3"
      :placeholder="t('Keyword')"
      :aria-label="t('Keyword')"
      autocomplete="off"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <BTable
        :items="page?.items ?? []"
        :fields="fields"
        show-empty
        :empty-text="t('No organizations found')"
        responsive
        striped
        bordered
      >
        <template #cell(name)="{ item }">
          <router-link :to="{ name: 'organization-update', params: { id: item.id } }">
            {{ item.name }}
          </router-link>
        </template>
        <template #cell(is_verified)="{ item }">
          {{ item.is_verified ? t("Yes") : t("No") }}
        </template>
        <template #cell(created_at)="{ item }">{{ fmt(item.created_at) }}</template>
        <template #cell(deletion_requested_at)="{ item }">
          {{ fmt(item.deletion_requested_at) }}
        </template>
        <template #cell(actions)="{ item }">
          <a :href="manage.organization(item.id)" class="me-2">{{ t("Manage") }}</a>
          <a :href="publicPages.organization(item.id)" class="me-2">{{ t("View") }}</a>
          <router-link
            :to="{ name: 'organization-update', params: { id: item.id } }"
            class="me-2"
          >
            {{ t("Edit") }}
          </router-link>
          <BButton variant="link" class="p-0 align-baseline" @click="askDelete(item)">
            {{ t("Delete") }}
          </BButton>
        </template>
      </BTable>
    </BOverlay>

    <OrganizationDeleteModal v-model="showDelete" :organization="deleting" @deleted="onDeleted" />

    <AppPager
      v-if="page && page.pages > 1"
      v-model:page="currentPage"
      :pages="page.pages"
      :total="page.total"
    />
  </div>
</template>
