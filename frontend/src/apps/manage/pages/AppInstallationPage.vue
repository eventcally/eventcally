<script setup lang="ts">
import { BButton, BOverlay } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import AuditLine from "@/shared/AuditLine.vue";
import { boot } from "@/shared/boot";
import ConfirmModal from "@/shared/ConfirmModal.vue";
import { formatDate } from "@/shared/format";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import { useNotify } from "@/shared/notify";
import ReadActions from "@/shared/ReadActions.vue";
import ReadProps from "@/shared/ReadProps.vue";
import type { RowAction } from "@/shared/RowActions.vue";
import { useConfirmAction } from "@/shared/useConfirmAction";
import { useFlashNotice } from "@/shared/useFlashNotice";

type Installation = components["schemas"]["AppInstallationRead"];

const props = defineProps<{ organizationId: number; id: number }>();

const { t } = useI18n();
const notify = useNotify();

useFlashNotice();

const installation = ref<Installation | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

async function load() {
  const { data, error: err } = await api.GET(
    "/bff/manage/organizations/{id}/app-installations/{installation_id}",
    { params: { path: { id: props.organizationId, installation_id: props.id } } },
  );
  loading.value = false;

  if (data) installation.value = data;
  else error.value = errorMessage(err, t("Error"));
}

onMounted(load);

const modelName = computed(() => t("App installation"));
const title = computed(() => `${modelName.value} ${props.id}`);

// Uninstalling leaves the page: the server flashes the text for the list.
const confirm = useConfirmAction<Installation>({
  call: (item) =>
    api.POST("/bff/manage/organizations/{id}/app-installations/{installation_id}/delete", {
      params: { path: { id: props.organizationId, installation_id: item.id } },
      body: { inline: false },
    }),
  onDone: () =>
    window.location.assign(`/manage/admin_unit/${props.organizationId}/app_installations`),
});

const accepting = ref(false);

async function acceptPermissions() {
  if (accepting.value) return;
  accepting.value = true;

  const { data, error: err } = await api.PUT(
    "/bff/manage/organizations/{id}/app-installations/{installation_id}/permissions",
    { params: { path: { id: props.organizationId, installation_id: props.id } } },
  );
  accepting.value = false;

  if (!data) {
    notify.error(errorMessage(err, t("Error")));
    return;
  }

  notify.success(data.message);
  await load();
}

const actions = computed<RowAction[]>(() => {
  if (!installation.value?.can_write) return [];

  return [{ title: t("Delete"), onClick: () => installation.value && confirm.open(installation.value) }];
});
</script>

<template>
  <div>
    <ManageBreadcrumb
      :organization-id="organizationId"
      :items="[
        { label: t('App installations'), to: { name: 'app-installations', params: { organizationId } } },
        { label: title },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <template v-if="installation">
        <ReadActions :actions="actions" />

        <ReadProps
          :rows="[
            { label: t('App'), value: installation.app },
            { label: t('Permissions'), value: installation.permissions.join(', ') },
            { label: t('Created at'), value: formatDate(installation.created_at, boot.locale) },
          ]"
        />
        <AuditLine :audit="installation.audit" />

        <section
          v-if="installation.can_write && installation.needs_permission_update"
          class="alert alert-warning mt-4"
          data-test="accept-permissions"
        >
          <p class="fw-bold mb-2">{{ t("Accept permissions") }}</p>
          <p class="mb-2">{{ t("New permissions") }}</p>
          <ul>
            <li v-for="permission in installation.requested_permissions" :key="permission">
              {{ permission }}
            </li>
          </ul>
          <BButton variant="primary" :disabled="accepting" data-test="accept" @click="acceptPermissions">
            {{ t("Update") }}
          </BButton>
        </section>

        <ConfirmModal
          v-model="confirm.show.value"
          :title="t('Delete %(model_display_name)s', { model_display_name: modelName })"
          :confirm-title="t('Delete')"
          :instruction="t('Do you want to delete \'%(object_title)s\'?', { object_title: title })"
          :busy="confirm.busy.value"
          :error="confirm.error.value"
          @submit="confirm.submit"
        />
      </template>
    </BOverlay>
  </div>
</template>
