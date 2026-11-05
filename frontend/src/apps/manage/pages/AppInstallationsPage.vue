<script setup lang="ts">
import { BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppPager from "@/shared/AppPager.vue";
import { boot } from "@/shared/boot";
import ConfirmModal from "@/shared/ConfirmModal.vue";
import { formatDate } from "@/shared/format";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import RowActions, { type RowAction } from "@/shared/RowActions.vue";
import { useConfirmAction } from "@/shared/useConfirmAction";
import { useFlashNotice } from "@/shared/useFlashNotice";
import { usePagedList } from "@/shared/usePagedList";

type Page = components["schemas"]["AppInstallationListPage"];
type Item = Page["items"][number];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();

useFlashNotice();

const { page, loading, error, currentPage, load } = usePagedList<Page>(
  (current) =>
    api.GET("/bff/manage/organizations/{id}/app-installations", {
      params: { path: { id: props.organizationId }, query: { page: current } },
    }),
  "app-installations",
  t("Error"),
);

const modelName = computed(() => t("App installation"));

// The old uninstall page had no name to type: a plain confirmation.
const confirm = useConfirmAction<Item>({
  call: (item) =>
    api.POST("/bff/manage/organizations/{id}/app-installations/{installation_id}/delete", {
      params: { path: { id: props.organizationId, installation_id: item.id } },
      body: { inline: true },
    }),
  onDone: async () => {
    await load();
    // The uninstalled app may have been the last one of the page.
    if (page.value?.items.length === 0 && currentPage.value > 1) {
      currentPage.value = currentPage.value - 1;
    }
  },
});

const fields = computed<TableFieldRaw[]>(() => [
  { key: "app", label: t("App") },
  { key: "created_at", label: t("Created at") },
]);

const appTitle = (item: Item) => item.app ?? `${modelName.value} ${item.id}`;

function actions(item: Item): RowAction[] {
  const result: RowAction[] = [
    {
      title: t("View"),
      to: { name: "app-installation", params: { organizationId: props.organizationId, id: item.id } },
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
    <ManageBreadcrumb
      :organization-id="organizationId"
      :items="[{ label: t('App installations') }]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading" class="mt-4">
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
        <template #cell(app)="{ item }">
          <RowActions :label="appTitle(item)" :actions="actions(item)" />
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
          object_title: confirm.item.value
            ? `${modelName} ${confirm.item.value.id}`
            : '',
        })
      "
      :busy="confirm.busy.value"
      :error="confirm.error.value"
      @submit="confirm.submit"
    />
  </div>
</template>
