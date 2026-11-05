<script setup lang="ts">
import { BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppPager from "@/shared/AppPager.vue";
import { boot } from "@/shared/boot";
import { formatDateTime } from "@/shared/format";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import RowActions, { type RowAction } from "@/shared/RowActions.vue";
import { usePagedList } from "@/shared/usePagedList";

type Page = components["schemas"]["WebhookDeliveryListPage"];
type Item = Page["items"][number];

const props = defineProps<{ organizationId: number; appId: number }>();

const { t } = useI18n();

const { page, loading, error, currentPage } = usePagedList<Page>(
  (current) =>
    api.GET("/bff/manage/organizations/{id}/apps/{app_id}/webhook-deliveries", {
      params: {
        path: { id: props.organizationId, app_id: props.appId },
        query: { page: current },
      },
    }),
  "webhook-deliveries",
  t("Error"),
);

const fields = computed<TableFieldRaw[]>(() => [
  { key: "event_type", label: t("Event Type") },
  { key: "timestamp", label: t("Timestamp") },
  { key: "organization", label: t("Organization") },
]);

function actions(item: Item): RowAction[] {
  return [
    {
      title: t("View"),
      to: {
        name: "webhook-delivery",
        params: { organizationId: props.organizationId, appId: props.appId, id: item.id },
      },
    },
  ];
}
</script>

<template>
  <div>
    <ManageBreadcrumb
      :organization-id="organizationId"
      :items="[
        { label: t('Apps'), to: { name: 'apps', params: { organizationId } } },
        {
          label: page?.app_title ?? '…',
          to: { name: 'app', params: { organizationId, id: appId } },
        },
        { label: t('Webhook deliveries') },
      ]"
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
        <template #cell(event_type)="{ item }">
          <RowActions :label="item.event_type" :actions="actions(item)" />
        </template>
        <template #cell(timestamp)="{ item }">{{
          formatDateTime(item.timestamp, boot.locale)
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
