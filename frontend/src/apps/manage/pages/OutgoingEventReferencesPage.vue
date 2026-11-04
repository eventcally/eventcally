<script setup lang="ts">
import { BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppPager from "@/shared/AppPager.vue";
import { boot } from "@/shared/boot";
import { formatDate } from "@/shared/format";
import { LINK_CLOSE, LINK_OPEN } from "@/shared/instruction";
import InstructionText from "@/shared/InstructionText.vue";
import { publicPages } from "@/shared/legacy";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import RowActions, { type RowAction } from "@/shared/RowActions.vue";
import { usePagedList } from "@/shared/usePagedList";

type Page = components["schemas"]["OutgoingEventReferenceListPage"];
type Item = Page["items"][number];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();

const { page, loading, error, currentPage } = usePagedList<Page>(
  (current) =>
    api.GET("/bff/manage/organizations/{id}/outgoing-event-references", {
      params: { path: { id: props.organizationId }, query: { page: current } },
    }),
  "outgoing-event-references",
  t("Error"),
);

const instruction = computed(() =>
  t(
    "Here you can find your events that are recommended by other organizations. To ask another organization for a recommendation, select %(reference_open)s%(reference_title)s%(reference_close)s on one of your event pages that you can find through the %(search_open)ssearch%(search_close)s.",
    {
      reference_open: '"',
      reference_close: '"',
      reference_title: t("Request reference"),
      search_open: LINK_OPEN,
      search_close: LINK_CLOSE,
    },
  ),
);

const fields = computed<TableFieldRaw[]>(() => [
  { key: "event_name", label: t("Event") },
  { key: "organization_name", label: t("Organization") },
  { key: "created_at", label: t("Created at") },
]);

const actions = (item: Item): RowAction[] => [
  { title: t("View event"), href: publicPages.event(item.event_id) },
];
</script>

<template>
  <div>
    <ManageBreadcrumb
      :organization-id="organizationId"
      :items="[{ label: t('Outgoing references') }]"
    />

    <InstructionText
      :text="instruction"
      :to="{ name: 'manage-events', params: { organizationId } }"
    />

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
