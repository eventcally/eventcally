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
import { LINK_CLOSE, LINK_OPEN } from "@/shared/instruction";
import InstructionText from "@/shared/InstructionText.vue";
import { publicPages } from "@/shared/legacy";
import ListFilters from "@/shared/ListFilters.vue";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import RowActions, { type RowAction } from "@/shared/RowActions.vue";
import { usePagedList } from "@/shared/usePagedList";
import ReviewStatusBadge from "./ReviewStatusBadge.vue";

type Page = components["schemas"]["EventReferenceRequestListPage"];
type Item = Page["items"][number];

// The lists of the requests to (`incoming`) and from (outgoing) the organization; they differ
// in the endpoint, the texts and the row actions.
const props = defineProps<{ organizationId: number; incoming: boolean }>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const routeName = computed(() =>
  props.incoming ? "incoming-event-reference-requests" : "outgoing-event-reference-requests",
);
const url = computed(() =>
  props.incoming
    ? ("/bff/manage/organizations/{id}/incoming-event-reference-requests" as const)
    : ("/bff/manage/organizations/{id}/outgoing-event-reference-requests" as const),
);

// -1 is the "All" of the old filter.
const routeStatus = computed(() => {
  const value = Number(route.query.review_status);
  return Number.isInteger(value) && route.query.review_status !== undefined ? value : -1;
});
const status = ref(routeStatus.value);

const { page, loading, error, currentPage } = usePagedList<Page>(
  (current) =>
    api.GET(url.value, {
      params: {
        path: { id: props.organizationId },
        query: {
          page: current,
          review_status: routeStatus.value === -1 ? undefined : routeStatus.value,
        },
      },
    }),
  routeName.value,
  t("Error"),
);

const filtered = computed(() => routeStatus.value !== -1);

function applyFilters() {
  router.push({
    name: routeName.value,
    query: { review_status: status.value === -1 ? undefined : String(status.value) },
  });
}

function resetFilters() {
  status.value = -1;
  router.push({ name: routeName.value });
}

const title = computed(() =>
  props.incoming ? t("Incoming reference requests") : t("Outgoing reference requests"),
);

const instruction = computed(() =>
  props.incoming
    ? t(
        "Here you will find requests from other organizations asking you to recommend one of their events.",
      )
    : t(
        "Here you can find your recommendation requests to other organizations. To ask another organization for a recommendation, select %(request_open)s%(request_title)s%(request_close)s on one of your event pages that you can find through the %(search_open)ssearch%(search_close)s.",
        {
          request_open: '"',
          request_close: '"',
          request_title: t("Request reference"),
          search_open: LINK_OPEN,
          search_close: LINK_CLOSE,
        },
      ),
);

const fields = computed<TableFieldRaw[]>(() => [
  { key: "event_name", label: t("Event") },
  { key: "review_status", label: t("Review status") },
  { key: "organization_name", label: t("Organization") },
  { key: "created_at", label: t("Created at") },
]);

function actions(item: Item): RowAction[] {
  if (!props.incoming) {
    return [
      {
        title: t("View"),
        to: {
          name: "outgoing-event-reference-request",
          params: { organizationId: props.organizationId, id: item.id },
        },
      },
    ];
  }

  const result: RowAction[] = [];

  if (item.can_review) {
    result.push({
      title: t("Review request"),
      to: {
        name: "event-reference-request-review",
        params: { organizationId: props.organizationId, id: item.id },
      },
    });
  }

  result.push({ title: t("View event"), href: publicPages.event(item.event_id) });
  return result;
}
</script>

<template>
  <div>
    <ManageBreadcrumb :organization-id="organizationId" :items="[{ label: title }]" />

    <InstructionText
      :text="instruction"
      :to="{ name: 'manage-events', params: { organizationId } }"
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
        <template #cell(event_name)="{ item }">
          <RowActions :label="item.event_name" :actions="actions(item)" />
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
