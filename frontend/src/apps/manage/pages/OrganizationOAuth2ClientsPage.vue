<script setup lang="ts">
import { BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppPager from "@/shared/AppPager.vue";
import ConfirmModal from "@/shared/ConfirmModal.vue";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import RowActions, { type RowAction } from "@/shared/RowActions.vue";
import { useConfirmAction } from "@/shared/useConfirmAction";
import { useFlashNotice } from "@/shared/useFlashNotice";
import { usePagedList } from "@/shared/usePagedList";

type Page = components["schemas"]["OAuth2ClientListPage"];
type Item = Page["items"][number];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();

useFlashNotice();

const { page, loading, error, currentPage, load } = usePagedList<Page>(
  (current) =>
    api.GET("/bff/manage/organizations/{id}/oauth2-clients", {
      params: { path: { id: props.organizationId }, query: { page: current } },
    }),
  "organization-oauth2-clients",
  t("Error"),
);

const modelName = computed(() => t("OAuth2 client"));
const clientTitle = (item: Item | null) =>
  item ? (item.client_name ?? `${modelName.value} ${item.id}`) : "";

const confirm = useConfirmAction<Item>({
  call: (item, name) =>
    api.POST("/bff/manage/organizations/{id}/oauth2-clients/{client_id}/delete", {
      params: { path: { id: props.organizationId, client_id: item.id } },
      body: { name: name ?? "", inline: true },
    }),
  onDone: async () => {
    await load();
    // The deleted client may have been the last one of the page.
    if (page.value?.items.length === 0 && currentPage.value > 1) {
      currentPage.value = currentPage.value - 1;
    }
  },
});

const fields = computed<TableFieldRaw[]>(() => [{ key: "client_name", label: t("Client Name") }]);

function actions(item: Item): RowAction[] {
  const params = { organizationId: props.organizationId, id: item.id };
  const result: RowAction[] = [
    { title: t("View"), to: { name: "organization-oauth2-client", params } },
  ];

  if (page.value?.can_write) {
    result.push(
      { title: t("Edit"), to: { name: "organization-oauth2-client-update", params } },
      { title: t("Delete"), onClick: () => confirm.open(item) },
    );
  }

  return result;
}
</script>

<template>
  <div>
    <ManageBreadcrumb :organization-id="organizationId" :items="[{ label: t('OAuth2 clients') }]" />

    <div v-if="page?.can_write" class="my-4">
      <router-link
        :to="{ name: 'organization-oauth2-client-create', params: { organizationId } }"
        class="btn btn-outline-secondary"
      >
        <i class="fa fa-plus"></i>
        {{ t("Create %(model_display_name)s", { model_display_name: modelName }) }}
      </router-link>
    </div>

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
        <template #cell(client_name)="{ item }">
          <RowActions :label="clientTitle(item)" :actions="actions(item)" />
        </template>
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
      :confirm-title="t('Delete OAuth2 client')"
      :instruction="
        t('Do you want to delete \'%(object_title)s\'?', {
          object_title: clientTitle(confirm.item.value),
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
