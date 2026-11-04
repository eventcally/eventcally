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

type Page = components["schemas"]["EventPlaceListPage"];
type Item = Page["items"][number];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

useFlashNotice();

const SORTS = ["name", "-last_modified_at", "-number_of_events"] as const;
type Sort = (typeof SORTS)[number];

const routeSort = computed<Sort>(() => {
  const value = String(route.query.sort ?? "");
  return (SORTS as readonly string[]).includes(value) ? (value as Sort) : "name";
});
const routeKeyword = computed(() => String(route.query.keyword ?? ""));

const keyword = ref(routeKeyword.value);
const sort = ref<Sort>(routeSort.value);

const { page, loading, error, currentPage, load } = usePagedList<Page>(
  (current) =>
    api.GET("/bff/manage/organizations/{id}/event-places/list", {
      params: {
        path: { id: props.organizationId },
        query: {
          page: current,
          sort: routeSort.value,
          keyword: routeKeyword.value || undefined,
        },
      },
    }),
  "event-places",
  t("Error"),
);

// A set filter opens the collapse; the sort alone does not count (it is never empty).
const filtered = computed(() => Boolean(routeKeyword.value) || routeSort.value !== "name");

function applyFilters() {
  router.push({
    name: "event-places",
    query: { keyword: keyword.value || undefined, sort: sort.value },
  });
}

function resetFilters() {
  keyword.value = "";
  sort.value = "name";
  router.push({ name: "event-places" });
}

const modelName = computed(() => t("Place"));

const confirm = useConfirmAction<Item>({
  call: (item, name) =>
    api.POST("/bff/manage/organizations/{id}/event-places/{place_id}/delete", {
      params: { path: { id: props.organizationId, place_id: item.id } },
      body: { name: name ?? "" },
    }),
  onDone: async () => {
    await load();
    // The deleted place may have been the last one of the page.
    if (page.value?.items.length === 0 && currentPage.value > 1) {
      currentPage.value = currentPage.value - 1;
    }
  },
});

const fields = computed<TableFieldRaw[]>(() => [
  { key: "name", label: t("Name") },
  { key: "location", label: t("Location") },
  { key: "has_coordinates", label: t("Coordinates") },
  { key: "has_photo", label: t("Photo") },
  { key: "number_of_events", label: t("Number of events") },
  { key: "last_modified_at", label: t("Last modified at") },
]);

function actions(item: Item): RowAction[] {
  const result: RowAction[] = [];

  if (page.value?.can_write) {
    result.push(
      {
        title: t("Edit"),
        to: {
          name: "event-place-update",
          params: { organizationId: props.organizationId, id: item.id },
        },
      },
      { title: t("Delete"), onClick: () => confirm.open(item) },
    );
  }

  result.push({
    title: t("View events"),
    to: {
      name: "manage-events",
      params: { organizationId: props.organizationId },
      query: { event_place_id: String(item.id) },
    },
  });
  return result;
}
</script>

<template>
  <div>
    <ManageBreadcrumb :organization-id="organizationId" :items="[{ label: t('Places') }]" />

    <div v-if="page?.can_write" class="my-4">
      <router-link
        :to="{ name: 'event-place-create', params: { organizationId } }"
        class="btn btn-outline-secondary"
      >
        <i class="fa fa-plus"></i>
        {{ t("Create %(model_display_name)s", { model_display_name: modelName }) }}
      </router-link>
    </div>

    <ListFilters :active="filtered" @submit="applyFilters" @reset="resetFilters">
      <div class="mb-3 col-md-4 px-0">
        <label class="form-label" for="keyword">{{ t("Keyword") }}</label>
        <input id="keyword" v-model="keyword" type="text" class="form-control" />
      </div>
      <div class="mb-3 col-md-4 px-0">
        <label class="form-label" for="sort">{{ t("Sort") }}</label>
        <select id="sort" v-model="sort" class="form-select">
          <option value="name">{{ t("Name") }}</option>
          <option value="-last_modified_at">{{ t("Last modified first") }}</option>
          <option value="-number_of_events">{{ t("Number of events") }}</option>
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
        <template #cell(has_coordinates)="{ item }">
          <i v-if="item.has_coordinates" class="fa fa-check-circle" :title="t('Coordinates')"></i>
        </template>
        <template #cell(has_photo)="{ item }">
          <i v-if="item.has_photo" class="fa fa-check-circle" :title="t('Photo')"></i>
        </template>
        <template #cell(last_modified_at)="{ item }">{{
          formatDate(item.last_modified_at, boot.locale)
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
      :confirm-title="t('Delete place')"
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
