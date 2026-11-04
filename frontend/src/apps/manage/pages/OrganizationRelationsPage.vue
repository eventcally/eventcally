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
import TriStateFilter from "@/shared/TriStateFilter.vue";
import { useConfirmAction } from "@/shared/useConfirmAction";
import { useFlashNotice } from "@/shared/useFlashNotice";
import { usePagedList } from "@/shared/usePagedList";

type Page = components["schemas"]["OrganizationRelationListPage"];
type Item = Page["items"][number];
type Tri = "" | "1" | "0";

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

useFlashNotice();

const SORTS = ["name", "-last_modified_at"] as const;
type Sort = (typeof SORTS)[number];

const tri = (value: unknown): Tri => (value === "1" || value === "0" ? value : "");
const toBool = (value: Tri) => (value === "" ? undefined : value === "1");

const routeSort = computed<Sort>(() => {
  const value = String(route.query.sort ?? "");
  return (SORTS as readonly string[]).includes(value) ? (value as Sort) : "name";
});
const routeKeyword = computed(() => String(route.query.keyword ?? ""));
const routeVerify = computed(() => tri(route.query.verify));
const routeAuto = computed(() => tri(route.query.auto_verify_event_reference_requests));

const keyword = ref(routeKeyword.value);
const sort = ref<Sort>(routeSort.value);
const verify = ref<Tri>(routeVerify.value);
const auto = ref<Tri>(routeAuto.value);

const { page, loading, error, currentPage, load } = usePagedList<Page>(
  (current) =>
    api.GET("/bff/manage/organizations/{id}/outgoing-organization-relations", {
      params: {
        path: { id: props.organizationId },
        query: {
          page: current,
          sort: routeSort.value,
          keyword: routeKeyword.value || undefined,
          verify: toBool(routeVerify.value),
          auto_verify_event_reference_requests: toBool(routeAuto.value),
        },
      },
    }),
  "outgoing-organization-relations",
  t("Error"),
);

// A set filter opens the collapse; the sort alone does not count (it is never empty).
const filtered = computed(
  () =>
    Boolean(routeKeyword.value) ||
    routeVerify.value !== "" ||
    routeAuto.value !== "" ||
    routeSort.value !== "name",
);

function applyFilters() {
  router.push({
    name: "outgoing-organization-relations",
    query: {
      keyword: keyword.value || undefined,
      verify: verify.value || undefined,
      auto_verify_event_reference_requests: auto.value || undefined,
      sort: sort.value,
    },
  });
}

function resetFilters() {
  keyword.value = "";
  sort.value = "name";
  verify.value = "";
  auto.value = "";
  router.push({ name: "outgoing-organization-relations" });
}

const modelName = computed(() => t("Outgoing organization relation"));

const confirm = useConfirmAction<Item>({
  call: (item) =>
    api.POST("/bff/manage/organizations/{id}/outgoing-organization-relations/{relation_id}/delete", {
      params: { path: { id: props.organizationId, relation_id: item.id } },
    }),
  onDone: async () => {
    await load();
    // The deleted relation may have been the last one of the page.
    if (page.value?.items.length === 0 && currentPage.value > 1) {
      currentPage.value = currentPage.value - 1;
    }
  },
});

const fields = computed<TableFieldRaw[]>(() => [
  { key: "organization_name", label: t("Organization") },
  ...(page.value?.can_verify_other ? [{ key: "verify", label: t("Verify other organization") }] : []),
  {
    key: "auto_verify_event_reference_requests",
    label: t("Verify reference requests automatically"),
  },
  { key: "last_modified_at", label: t("Last modified at") },
]);

function actions(item: Item): RowAction[] {
  if (!page.value?.can_write) return [];

  return [
    {
      title: t("Edit"),
      to: {
        name: "outgoing-organization-relation-update",
        params: { organizationId: props.organizationId, id: item.id },
      },
    },
    { title: t("Delete"), onClick: () => confirm.open(item) },
  ];
}
</script>

<template>
  <div>
    <ManageBreadcrumb
      :organization-id="organizationId"
      :items="[{ label: t('Outgoing organization relations') }]"
    />

    <div v-if="page?.can_write" class="my-4">
      <router-link
        :to="{ name: 'outgoing-organization-relation-create', params: { organizationId } }"
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
      <TriStateFilter
        v-if="page?.can_verify_other"
        id="verify"
        v-model="verify"
        :label="t('Verify other organization')"
      />
      <TriStateFilter
        id="auto-verify"
        v-model="auto"
        :label="t('Verify reference requests automatically')"
      />
      <div class="mb-3 col-md-4 px-0">
        <label class="form-label" for="sort">{{ t("Sort") }}</label>
        <select id="sort" v-model="sort" class="form-select">
          <option value="name">{{ t("Name") }}</option>
          <option value="-last_modified_at">{{ t("Last modified first") }}</option>
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
        <template #cell(organization_name)="{ item }">
          <RowActions v-if="actions(item).length" :label="item.organization_name" :actions="actions(item)" />
          <template v-else>{{ item.organization_name }}</template>
        </template>
        <template #cell(verify)="{ item }">
          <i v-if="item.verify" class="fa fa-check-circle" :title="t('Verify other organization')"></i>
        </template>
        <template #cell(auto_verify_event_reference_requests)="{ item }">
          <i
            v-if="item.auto_verify_event_reference_requests"
            class="fa fa-check-circle"
            :title="t('Verify reference requests automatically')"
          ></i>
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
      :confirm-title="t('Delete')"
      :instruction="
        t('Do you want to delete \'%(object_title)s\'?', {
          object_title: `${t('Organization relation')} ${confirm.item.value?.id ?? ''}`,
        })
      "
      :busy="confirm.busy.value"
      :error="confirm.error.value"
      @submit="confirm.submit"
    />
  </div>
</template>
