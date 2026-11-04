<script setup lang="ts">
import { BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed, ref } from "vue";
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
import MemberRolesModal from "../components/MemberRolesModal.vue";

type Page = components["schemas"]["MemberInvitationListPage"];
type Item = Page["items"][number];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();

useFlashNotice();

const { page, loading, error, currentPage, load } = usePagedList<Page>(
  (current) =>
    api.GET("/bff/manage/organizations/{id}/member-invitations", {
      params: { path: { id: props.organizationId }, query: { page: current } },
    }),
  "organization-member-invitations",
  t("Error"),
);

const modelName = computed(() => t("Organization member invitation"));

const confirm = useConfirmAction<Item>({
  call: (item) =>
    api.POST("/bff/manage/organizations/{id}/member-invitations/{invitation_id}/delete", {
      params: { path: { id: props.organizationId, invitation_id: item.id } },
    }),
  onDone: async () => {
    await load();
    // The revoked invitation may have been the last one of the page.
    if (page.value?.items.length === 0 && currentPage.value > 1) {
      currentPage.value = currentPage.value - 1;
    }
  },
});

const editing = ref<Item | null>(null);
const showRoles = ref(false);

const fields = computed<TableFieldRaw[]>(() => [{ key: "email", label: t("Email") }]);

function actions(item: Item): RowAction[] {
  if (!page.value?.can_write) return [];

  return [
    {
      title: t("Edit"),
      onClick: () => {
        editing.value = item;
        showRoles.value = true;
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
      :items="[{ label: t('Organization member invitations') }]"
    />

    <div v-if="page?.can_write" class="my-4">
      <router-link
        :to="{ name: 'organization-member-invitation-create', params: { organizationId } }"
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
        <template #cell(email)="{ item }">
          <RowActions v-if="actions(item).length" :label="item.email" :actions="actions(item)" />
          <template v-else>{{ item.email }}</template>
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
      :confirm-title="t('Delete')"
      :instruction="
        t('Do you want to delete \'%(object_title)s\'?', {
          object_title: `${modelName} ${confirm.item.value?.id ?? ''}`,
        })
      "
      :busy="confirm.busy.value"
      :error="confirm.error.value"
      @submit="confirm.submit"
    />

    <MemberRolesModal
      v-model="showRoles"
      :organization-id="organizationId"
      kind="invitation"
      :item-id="editing?.id ?? null"
      :email="editing?.email ?? ''"
      :roles="editing?.roles ?? []"
      :choices="page?.role_choices ?? []"
      @saved="load"
    />
  </div>
</template>
