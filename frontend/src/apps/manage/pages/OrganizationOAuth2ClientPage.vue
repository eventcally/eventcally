<script setup lang="ts">
import { BOverlay } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import AuditLine from "@/shared/AuditLine.vue";
import ConfirmModal from "@/shared/ConfirmModal.vue";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import OAuth2ClientDetails from "@/shared/OAuth2ClientDetails.vue";
import ReadActions from "@/shared/ReadActions.vue";
import type { RowAction } from "@/shared/RowActions.vue";
import { useConfirmAction } from "@/shared/useConfirmAction";
import { useFlashNotice } from "@/shared/useFlashNotice";

type Client = components["schemas"]["OAuth2ClientRead"];

const props = defineProps<{ organizationId: number; id: number }>();

const { t } = useI18n();

useFlashNotice();

const client = ref<Client | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  const { data, error: err } = await api.GET(
    "/bff/manage/organizations/{id}/oauth2-clients/{client_id}",
    { params: { path: { id: props.organizationId, client_id: props.id } } },
  );
  loading.value = false;

  if (data) client.value = data;
  else error.value = errorMessage(err, t("Error"));
});

const modelName = computed(() => t("OAuth2 client"));
const title = computed(() => client.value?.client_name ?? `${modelName.value} ${props.id}`);

// Deleting leaves the page: the server flashes the text for the list (a full page load, so
// the Flask frame shows the flash).
const confirm = useConfirmAction<Client>({
  call: (item, name) =>
    api.POST("/bff/manage/organizations/{id}/oauth2-clients/{client_id}/delete", {
      params: { path: { id: props.organizationId, client_id: item.id } },
      body: { name: name ?? "", inline: false },
    }),
  onDone: () =>
    window.location.assign(`/manage/admin_unit/${props.organizationId}/oauth2_clients`),
});

const actions = computed<RowAction[]>(() => {
  if (!client.value?.can_write) return [];

  return [
    {
      title: t("Edit"),
      to: {
        name: "organization-oauth2-client-update",
        params: { organizationId: props.organizationId, id: props.id },
      },
    },
    { title: t("Delete"), onClick: () => client.value && confirm.open(client.value) },
  ];
});
</script>

<template>
  <div>
    <ManageBreadcrumb
      :organization-id="organizationId"
      :items="[
        {
          label: t('OAuth2 clients'),
          to: { name: 'organization-oauth2-clients', params: { organizationId } },
        },
        { label: title },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <template v-if="client">
        <ReadActions :actions="actions" />

        <OAuth2ClientDetails :client="client" />
        <AuditLine :audit="client.audit" />

        <ConfirmModal
          v-model="confirm.show.value"
          :title="t('Delete %(model_display_name)s', { model_display_name: modelName })"
          :confirm-title="t('Delete OAuth2 client')"
          :instruction="t('Do you want to delete \'%(object_title)s\'?', { object_title: title })"
          :confirm-label="t('Name')"
          :busy="confirm.busy.value"
          :error="confirm.error.value"
          :name-error="confirm.nameError.value"
          @submit="confirm.submit"
        />
      </template>
    </BOverlay>
  </div>
</template>
