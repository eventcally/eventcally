<script setup lang="ts">
import { BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppPager from "@/shared/AppPager.vue";
import { boot } from "@/shared/boot";
import ConfirmModal from "@/shared/ConfirmModal.vue";
import { formatDate } from "@/shared/format";
import ListFilters from "@/shared/ListFilters.vue";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import RowActions, { type RowAction } from "@/shared/RowActions.vue";
import { useConfirmAction } from "@/shared/useConfirmAction";
import { useFlashNotice } from "@/shared/useFlashNotice";
import { usePagedList } from "@/shared/usePagedList";

type Page = components["schemas"]["ApiKeyListPage"];
type Item = Page["items"][number];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

useFlashNotice();

const SORTS = ["name", "-created_at"] as const;
type Sort = (typeof SORTS)[number];

const routeSort = computed<Sort>(() => {
  const value = String(route.query.sort ?? "");
  return (SORTS as readonly string[]).includes(value) ? (value as Sort) : "name";
});
const sort = ref<Sort>(routeSort.value);

const { page, loading, error, currentPage, load } = usePagedList<Page>(
  (current) =>
    api.GET("/bff/manage/organizations/{id}/api-keys", {
      params: {
        path: { id: props.organizationId },
        query: { page: current, sort: routeSort.value },
      },
    }),
  "organization-api-keys",
  t("Error"),
);

// A set filter opens the collapse; the sort alone does not count (it is never empty).
const filtered = computed(() => routeSort.value !== "name");

function applyFilters() {
  router.push({ name: "organization-api-keys", query: { sort: sort.value } });
}

function resetFilters() {
  sort.value = "name";
  router.push({ name: "organization-api-keys" });
}

const modelName = computed(() => t("API key"));

const confirm = useConfirmAction<Item>({
  call: (item, name) =>
    api.POST("/bff/manage/organizations/{id}/api-keys/{api_key_id}/delete", {
      params: { path: { id: props.organizationId, api_key_id: item.id } },
      body: { name: name ?? "", inline: true },
    }),
  onDone: async () => {
    await load();
    // The deleted key may have been the last one of the page.
    if (page.value?.items.length === 0 && currentPage.value > 1) {
      currentPage.value = currentPage.value - 1;
    }
  },
});

const fields = computed<TableFieldRaw[]>(() => [
  { key: "name", label: t("Name") },
  { key: "created_at", label: t("Created at") },
]);

function actions(item: Item): RowAction[] {
  const result: RowAction[] = [
    {
      title: t("View"),
      to: {
        name: "organization-api-key",
        params: { organizationId: props.organizationId, id: item.id },
      },
    },
  ];

  if (page.value?.can_write) {
    result.push({ title: t("Delete"), onClick: () => confirm.open(item) });
  }

  return result;
}
</script>

<template>
  <div>
    <ManageBreadcrumb :organization-id="organizationId" :items="[{ label: t('API keys') }]" />

    <div v-if="page?.can_write" class="my-4">
      <router-link
        :to="{ name: 'organization-api-key-create', params: { organizationId } }"
        class="btn btn-outline-secondary"
      >
        <i class="fa fa-plus"></i>
        {{ t("Create %(model_display_name)s", { model_display_name: modelName }) }}
      </router-link>
    </div>

    <ListFilters :active="filtered" @submit="applyFilters" @reset="resetFilters">
      <div class="mb-3 col-md-4 px-0">
        <label class="form-label" for="sort">{{ t("Sort") }}</label>
        <select id="sort" v-model="sort" class="form-select">
          <option value="name">{{ t("Name") }}</option>
          <option value="-created_at">{{ t("Last created first") }}</option>
        </select>
      </div>
    </ListFilters>

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <BTable
        v-if="page && page.items.length"
        :items="page.items"
        :fields="fields"
        thead-class="fw-bold"
        responsive
        small
        striped
        bordered
        hover
      >
        <template #cell(name)="{ item }">
          <RowActions :label="item.name" :actions="actions(item)" />
        </template>
        <template #cell(created_at)="{ item }">{{
          formatDate(item.created_at, boot.locale)
        }}</template>
      </BTable>
    </BOverlay>

    <AppPager
      v-if="page && page.total > 0"
      v-model:page="currentPage"
      :pages="page.pages"
      :total="page.total"
    />

    <ConfirmModal
      v-model="confirm.show.value"
      :title="t('Delete %(model_display_name)s', { model_display_name: modelName })"
      :confirm-title="t('Delete')"
      :instruction="
        t('Do you want to delete \'%(object_title)s\'?', {
          object_title: confirm.item.value?.name ?? '',
        })
      "
      :confirm-label="t('Name')"
      :busy="confirm.busy.value"
      :error="confirm.error.value"
      :name-error="confirm.nameError.value"
      @submit="confirm.submit"
    />
  </div>
</template>
