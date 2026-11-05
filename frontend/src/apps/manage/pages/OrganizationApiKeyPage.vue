<script setup lang="ts">
import { BOverlay } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import AuditLine from "@/shared/AuditLine.vue";
import { boot } from "@/shared/boot";
import ConfirmModal from "@/shared/ConfirmModal.vue";
import { takeCreatedKey } from "@/shared/createdKey";
import { formatDate } from "@/shared/format";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import ReadActions from "@/shared/ReadActions.vue";
import ReadProps from "@/shared/ReadProps.vue";
import type { RowAction } from "@/shared/RowActions.vue";
import { useConfirmAction } from "@/shared/useConfirmAction";
import { useFlashNotice } from "@/shared/useFlashNotice";
import ApiKeyNameModal from "../components/ApiKeyNameModal.vue";

type ApiKey = components["schemas"]["ApiKeyRead"];

const props = defineProps<{ organizationId: number; id: number }>();

const { t } = useI18n();

useFlashNotice();

const apiKey = ref<ApiKey | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

// The key is only known right after the creation (the create page hands it over through
// the history state). It is taken out of the state, so a reload or any later visit never
// shows it.
const createdKey = takeCreatedKey();

async function load() {
  const { data, error: err } = await api.GET(
    "/bff/manage/organizations/{id}/api-keys/{api_key_id}",
    { params: { path: { id: props.organizationId, api_key_id: props.id } } },
  );
  loading.value = false;

  if (data) apiKey.value = data;
  else error.value = errorMessage(err, t("Error"));
}

onMounted(load);

const modelName = computed(() => t("API key"));
const objectTitle = computed(() => `${modelName.value} ${props.id}`);

const showName = ref(false);

// Deleting leaves the page: the server flashes the text for the list (a full page load, so
// the Flask frame shows the flash).
const confirm = useConfirmAction<ApiKey>({
  call: (item, name) =>
    api.POST("/bff/manage/organizations/{id}/api-keys/{api_key_id}/delete", {
      params: { path: { id: props.organizationId, api_key_id: item.id } },
      body: { name: name ?? "", inline: false },
    }),
  onDone: () =>
    window.location.assign(`/manage/admin_unit/${props.organizationId}/api_keys`),
});

const actions = computed<RowAction[]>(() => {
  if (!apiKey.value?.can_write) return [];

  return [
    { title: t("Edit"), onClick: () => (showName.value = true) },
    { title: t("Delete"), onClick: () => apiKey.value && confirm.open(apiKey.value) },
  ];
});
</script>

<template>
  <div>
    <div v-if="createdKey" class="alert alert-success" role="status">
      {{
        t("%(model_display_name)s successfully created", {
          model_display_name: modelName,
        })
      }}
    </div>
    <div v-if="createdKey" class="alert alert-warning" role="alert" data-test="created-key">
      {{
        t("Please note the key: %(key)s. It will only be displayed once.", {
          key: createdKey,
        })
      }}
    </div>

    <ManageBreadcrumb
      :organization-id="organizationId"
      :items="[
        { label: t('API keys'), to: { name: 'organization-api-keys', params: { organizationId } } },
        { label: objectTitle },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <template v-if="apiKey">
        <ReadActions :actions="actions" />

        <ReadProps
          :rows="[
            { label: t('Name'), value: apiKey.name },
            { label: t('Rate limit'), list: apiKey.rate_limits },
            { label: t('Created at'), value: formatDate(apiKey.created_at, boot.locale) },
          ]"
        />
        <AuditLine :audit="apiKey.audit" />

        <ApiKeyNameModal
          v-model="showName"
          :organization-id="organizationId"
          :api-key-id="apiKey.id"
          :name="apiKey.name"
          @saved="load"
        />
        <ConfirmModal
          v-model="confirm.show.value"
          :title="t('Delete %(model_display_name)s', { model_display_name: modelName })"
          :confirm-title="t('Delete')"
          :instruction="
            t('Do you want to delete \'%(object_title)s\'?', { object_title: objectTitle })
          "
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
