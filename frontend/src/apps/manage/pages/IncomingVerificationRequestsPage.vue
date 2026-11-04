<script setup lang="ts">
import { BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppPager from "@/shared/AppPager.vue";
import { boot } from "@/shared/boot";
import { formatDate } from "@/shared/format";
import { publicPages } from "@/shared/legacy";
import ListFilters from "@/shared/ListFilters.vue";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import RowActions, { type RowAction } from "@/shared/RowActions.vue";
import { usePagedList } from "@/shared/usePagedList";
import ReviewStatusBadge from "../components/ReviewStatusBadge.vue";

type Page = components["schemas"]["IncomingVerificationRequestListPage"];
type Item = Page["items"][number];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

// -1 is the "All" of the old filter.
const routeStatus = computed(() => {
  const value = Number(route.query.review_status);
  return Number.isInteger(value) && route.query.review_status !== undefined ? value : -1;
});
const status = ref(routeStatus.value);

const { page, loading, error, currentPage } = usePagedList<Page>(
  (current) =>
    api.GET("/bff/manage/organizations/{id}/incoming-verification-requests", {
      params: {
        path: { id: props.organizationId },
        query: {
          page: current,
          review_status: routeStatus.value === -1 ? undefined : routeStatus.value,
        },
      },
    }),
  "incoming-verification-requests",
  t("Error"),
);

const filtered = computed(() => routeStatus.value !== -1);

function applyFilters() {
  router.push({
    name: "incoming-verification-requests",
    query: { review_status: status.value === -1 ? undefined : String(status.value) },
  });
}

function resetFilters() {
  status.value = -1;
  router.push({ name: "incoming-verification-requests" });
}

const fields = computed<TableFieldRaw[]>(() => [
  { key: "organization_name", label: t("Organization") },
  { key: "review_status", label: t("Review status") },
  { key: "created_at", label: t("Created at") },
]);

function actions(item: Item): RowAction[] {
  const result: RowAction[] = [];

  if (item.can_review) {
    result.push({
      title: t("Review request"),
      to: {
        name: "verification-request-review",
        params: { organizationId: props.organizationId, id: item.id },
      },
    });
  }

  result.push({ title: t("View organization"), href: publicPages.organization(item.organization_id) });
  return result;
}
</script>

<template>
  <div>
    <ManageBreadcrumb
      :organization-id="organizationId"
      :items="[{ label: t('Incoming verification requests') }]"
    />

    <ListFilters :active="filtered" @submit="applyFilters" @reset="resetFilters">
      <div class="mb-3 col-md-4 px-0">
        <label class="form-label" for="review_status">{{ t("Review status") }}</label>
        <select id="review_status" v-model="status" class="form-select">
          <option v-for="choice in page?.review_status_choices ?? []" :key="choice.value" :value="choice.value">
            {{ choice.label }}
          </option>
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
          <RowActions :label="item.organization_name" :actions="actions(item)" />
        </template>
        <template #cell(review_status)="{ item }">
          <ReviewStatusBadge :status="item.review_status" :label="item.review_status_label" />
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
  </div>
</template>
