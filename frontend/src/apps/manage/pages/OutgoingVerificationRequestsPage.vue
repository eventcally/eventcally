<script setup lang="ts">
import { BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed, ref, watch } from "vue";
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
import ReviewStatusBadge from "../components/ReviewStatusBadge.vue";
import VerificationRequestCreateModal from "../components/VerificationRequestCreateModal.vue";

type Page = components["schemas"]["OutgoingVerificationRequestListPage"];
type Item = Page["items"][number];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();

useFlashNotice();

const { page, loading, error, currentPage, load } = usePagedList<Page>(
  (current) =>
    api.GET("/bff/manage/organizations/{id}/outgoing-verification-requests", {
      params: { path: { id: props.organizationId }, query: { page: current } },
    }),
  "outgoing-verification-requests",
  t("Error"),
);

const docsUrl = computed(() =>
  boot.docsUrl ? `${boot.docsUrl}/goto/organization-verify` : null,
);

const modelName = computed(() => t("Organization verification request"));
const objectTitle = (item: Item | null) => (item ? `${modelName.value} ${item.id}` : "");

// An unverified organization without a request is led straight to the request dialog (the
// old list redirected to the selection of verifiers).
const showCreate = ref(false);
let suggestionHandled = false;
watch(page, (value) => {
  if (value && !suggestionHandled) {
    suggestionHandled = true;
    if (value.suggest_create) showCreate.value = true;
  }
});

const confirm = useConfirmAction<Item>({
  call: (item) =>
    api.POST("/bff/manage/organizations/{id}/outgoing-verification-requests/{request_id}/withdraw", {
      params: { path: { id: props.organizationId, request_id: item.id } },
      body: { inline: true },
    }),
  onDone: async () => {
    await load();
    // The withdrawn request may have been the last one of the page.
    if (page.value?.items.length === 0 && currentPage.value > 1) {
      currentPage.value = currentPage.value - 1;
    }
  },
});

const fields = computed<TableFieldRaw[]>(() => [
  { key: "organization_name", label: t("Organization") },
  { key: "review_status", label: t("Review status") },
  { key: "created_at", label: t("Created at") },
]);

function actions(item: Item): RowAction[] {
  const result: RowAction[] = [
    {
      title: t("View"),
      to: {
        name: "outgoing-verification-request",
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
    <ManageBreadcrumb
      :organization-id="organizationId"
      :docs-url="docsUrl"
      :items="[{ label: t('Outgoing verification requests') }]"
    />

    <div v-if="page?.can_write" class="my-4">
      <button
        type="button"
        class="btn btn-outline-secondary"
        data-test="verification-create"
        @click="showCreate = true"
      >
        <i class="fa fa-plus"></i>
        {{ t("Create %(model_display_name)s", { model_display_name: modelName }) }}
      </button>
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

    <VerificationRequestCreateModal
      v-model="showCreate"
      :organization-id="organizationId"
      @created="load"
    />

    <ConfirmModal
      v-model="confirm.show.value"
      :title="t('Delete %(model_display_name)s', { model_display_name: modelName })"
      :confirm-title="t('Delete')"
      :instruction="
        t('Do you want to delete \'%(object_title)s\'?', {
          object_title: objectTitle(confirm.item.value),
        })
      "
      :busy="confirm.busy.value"
      :error="confirm.error.value"
      @submit="confirm.submit"
    />
  </div>
</template>
