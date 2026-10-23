<script setup lang="ts">
import { BButton, BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppPager from "@/shared/AppPager.vue";
import { manage } from "@/shared/legacy";
import { useNotify } from "@/shared/notify";
import { takeFlash } from "../flash";
import CustomWidgetDeleteModal from "../components/CustomWidgetDeleteModal.vue";
import CustomWidgetInstallModal from "../components/CustomWidgetInstallModal.vue";

type CustomWidgetPage = components["schemas"]["CustomWidgetPage"];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const notify = useNotify();

const page = ref<CustomWidgetPage | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);
const installing = ref<number | null>(null);
const showInstall = ref(false);
const deleting = ref<{ id: number; name: string } | null>(null);
const showDelete = ref(false);

const currentPage = computed({
  get: () => Number(route.query.page ?? 1) || 1,
  set: (value: number) => {
    router.push({ name: "custom-widgets", query: { page: String(value) } });
  },
});

const fields = computed<TableFieldRaw[]>(() => [
  { key: "name", label: t("Name") },
  { key: "widget_type", label: t("Widget type") },
  { key: "actions", label: "" },
]);

const typeLabel = (type: string) => (type === "calendar" ? t("Calendar") : t("Search"));

async function load() {
  loading.value = true;
  error.value = null;
  const { data, error: err } = await api.GET("/bff/manage/organizations/{id}/custom-widgets", {
    params: {
      path: { id: props.organizationId },
      query: { page: currentPage.value },
    },
  });
  if (data) {
    page.value = data;
  } else {
    error.value = err?.message ?? t("Error");
  }
  loading.value = false;
}

function askInstall(id: number) {
  installing.value = id;
  showInstall.value = true;
}

function askDelete(item: { id: number; name: string }) {
  deleting.value = item;
  showDelete.value = true;
}

async function onDeleted() {
  await load();
  // The deleted widget may have been the last one of the page.
  if (page.value?.items.length === 0 && currentPage.value > 1) {
    currentPage.value = currentPage.value - 1;
  }
}

watch(() => route.query, load, { immediate: true });
onMounted(() => {
  const message = takeFlash();
  if (message) notify.success(message);
});
</script>

<template>
  <div>
    <h1>{{ t("Custom widgets") }}</h1>

    <div v-if="page?.can_write" class="my-4">
      <a :href="manage.customWidgetCreate(organizationId)" class="btn btn-outline-secondary">
        <i class="fa fa-plus"></i> {{ t("Add widget") }}
      </a>
    </div>

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <BTable
        :items="page?.items ?? []"
        :fields="fields"
        show-empty
        :empty-text="t('No widgets found')"
        responsive
        striped
        bordered
      >
        <template #cell(widget_type)="{ item }">{{ typeLabel(item.widget_type) }}</template>
        <template #cell(actions)="{ item }">
          <BButton variant="link" class="p-0 align-baseline me-2" @click="askInstall(item.id)">
            {{ t("Installation") }}
          </BButton>
          <a :href="manage.customWidgetUpdate(organizationId, item.id)" class="me-2">
            {{ t("Edit") }}
          </a>
          <BButton
            v-if="page?.can_write"
            variant="link"
            class="p-0 align-baseline"
            @click="askDelete(item)"
          >
            {{ t("Delete") }}
          </BButton>
        </template>
      </BTable>
    </BOverlay>

    <CustomWidgetInstallModal v-model="showInstall" :widget-id="installing" />
    <CustomWidgetDeleteModal v-model="showDelete" :widget="deleting" @deleted="onDeleted" />

    <AppPager
      v-if="page && page.total > 0"
      v-model:page="currentPage"
      :pages="page.pages"
      :total="page.total"
    />
  </div>
</template>
