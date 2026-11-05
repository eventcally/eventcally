<script setup lang="ts">
import { BButton, BOverlay, BTable, type TableFieldRaw } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import AuditLine from "@/shared/AuditLine.vue";
import ConfirmModal from "@/shared/ConfirmModal.vue";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import { useNotify } from "@/shared/notify";
import ReadActions from "@/shared/ReadActions.vue";
import ReadProps from "@/shared/ReadProps.vue";
import RowActions, { type RowAction } from "@/shared/RowActions.vue";
import { useConfirmAction } from "@/shared/useConfirmAction";
import { useFlashNotice } from "@/shared/useFlashNotice";

type App = components["schemas"]["AppRead"];
type Key = App["keys"][number];

const props = defineProps<{ organizationId: number; id: number }>();

const { t } = useI18n();
const notify = useNotify();

useFlashNotice();

const app = ref<App | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

async function load() {
  const { data, error: err } = await api.GET("/bff/manage/organizations/{id}/apps/{app_id}", {
    params: { path: { id: props.organizationId, app_id: props.id } },
  });
  loading.value = false;

  if (data) app.value = data;
  else error.value = errorMessage(err, t("Error"));
}

onMounted(load);

const modelName = computed(() => t("App"));
const title = computed(
  () => app.value?.client_name ?? `${t("OAuth2 client")} ${props.id}`,
);

// Deleting leaves the page: the server flashes the text for the list (a full page load, so
// the Flask frame shows the flash).
const confirm = useConfirmAction<App>({
  call: (item, name) =>
    api.POST("/bff/manage/organizations/{id}/apps/{app_id}/delete", {
      params: { path: { id: props.organizationId, app_id: item.id } },
      body: { name: name ?? "", inline: false },
    }),
  onDone: () => window.location.assign(`/manage/admin_unit/${props.organizationId}/apps`),
});

const keyConfirm = useConfirmAction<Key>({
  call: (item, name) =>
    api.POST("/bff/manage/organizations/{id}/apps/{app_id}/keys/{key_id}/delete", {
      params: { path: { id: props.organizationId, app_id: props.id, key_id: item.id } },
      body: { name: name ?? "", inline: true },
    }),
  onDone: load,
});

// The private key of a new key exists only in the answer of the create call: it is downloaded
// right away and kept here (never reloaded) until the page is left.
const privatePem = ref<string | null>(null);
const creating = ref(false);

function download(pem: string) {
  const url = URL.createObjectURL(new Blob([pem], { type: "application/x-pem-file" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "private_key.pem";
  link.click();
  URL.revokeObjectURL(url);
}

async function createKey() {
  if (creating.value) return;
  creating.value = true;

  const { data, error: err } = await api.POST(
    "/bff/manage/organizations/{id}/apps/{app_id}/keys",
    { params: { path: { id: props.organizationId, app_id: props.id } } },
  );
  creating.value = false;

  if (!data) {
    notify.error(errorMessage(err, t("Error")));
    return;
  }

  privatePem.value = data.private_pem;
  download(data.private_pem);
  notify.success(
    t("%(model_display_name)s successfully created", { model_display_name: t("App key") }),
  );
  await load();
}

const actions = computed<RowAction[]>(() => {
  if (!app.value?.can_write) return [];

  return [
    {
      title: t("Edit"),
      to: { name: "app-update", params: { organizationId: props.organizationId, id: props.id } },
    },
    { title: t("Delete"), onClick: () => app.value && confirm.open(app.value) },
  ];
});

const keyFields = computed<TableFieldRaw[]>(() => [
  { key: "kid", label: t("KID") },
  { key: "checksum", label: t("Checksum") },
]);

function keyActions(key: Key): RowAction[] {
  return [{ title: t("Delete"), onClick: () => keyConfirm.open(key) }];
}
</script>

<template>
  <div>
    <ManageBreadcrumb
      :organization-id="organizationId"
      :items="[
        { label: t('Apps'), to: { name: 'apps', params: { organizationId } } },
        { label: title },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <BOverlay :show="loading">
      <template v-if="app">
        <ReadActions :actions="actions" />

        <ReadProps
          :rows="[
            { label: t('Client ID'), value: app.client_id },
            { label: t('Client secret'), value: app.client_secret },
            { label: t('Grant types'), value: app.grant_types.join(', ') },
            { label: t('Redirect URIs'), value: app.redirect_uris.join(', ') },
            { label: t('Response types'), value: app.response_types.join(', ') },
            { label: t('Scope'), value: app.scope },
            {
              label: t('Token endpoint auth method'),
              value: app.token_endpoint_auth_method.join(', '),
            },
            { label: t('Permissions'), value: app.app_permissions.join(', ') },
            { label: t('Homepage'), value: app.homepage_url, href: app.homepage_url ?? undefined },
            { label: t('Setup URL'), value: app.setup_url, href: app.setup_url ?? undefined },
            { label: t('Webhook URL'), value: app.webhook_url, href: app.webhook_url ?? undefined },
            { label: t('Description'), value: app.description },
          ]"
        />

        <p v-if="app.can_read_deliveries">
          <router-link
            :to="{ name: 'webhook-deliveries', params: { organizationId, appId: id } }"
            data-test="deliveries-link"
          >
            {{ t("Webhook deliveries") }}
          </router-link>
        </p>

        <AuditLine :audit="app.audit" />

        <section v-if="app.can_read_keys" class="mt-4" data-test="keys">
          <h2 class="h5">{{ t("App keys") }}</h2>

          <div v-if="privatePem" class="alert alert-warning" role="alert" data-test="pem-warning">
            {{ t("Please download the private key. It will only be available once.") }}
            <BButton size="sm" variant="outline-secondary" class="ms-2" @click="download(privatePem)">
              {{ t("Download") }}
            </BButton>
          </div>

          <div v-if="app.can_write_keys" class="my-3">
            <BButton variant="outline-secondary" :disabled="creating" data-test="create-key" @click="createKey">
              <i class="fa fa-plus"></i>
              {{ t("Create %(model_display_name)s", { model_display_name: t("App key") }) }}
            </BButton>
          </div>

          <BTable
            v-if="app.keys.length"
            :items="app.keys"
            :fields="keyFields"
            thead-class="fw-bold"
            responsive
            small
            striped
            bordered
            hover
          >
            <template #cell(kid)="{ item }">
              <RowActions v-if="app.can_write_keys" :label="item.kid" :actions="keyActions(item)" />
              <template v-else>{{ item.kid }}</template>
            </template>
          </BTable>
        </section>

        <ConfirmModal
          v-model="confirm.show.value"
          :title="t('Delete %(model_display_name)s', { model_display_name: modelName })"
          :confirm-title="t('Delete')"
          :instruction="t('Do you want to delete \'%(object_title)s\'?', { object_title: title })"
          :confirm-label="t('Name')"
          :busy="confirm.busy.value"
          :error="confirm.error.value"
          :name-error="confirm.nameError.value"
          @submit="confirm.submit"
        />
        <ConfirmModal
          v-model="keyConfirm.show.value"
          :title="t('Delete %(model_display_name)s', { model_display_name: t('App key') })"
          :confirm-title="t('Delete')"
          :instruction="
            t('Do you want to delete \'%(object_title)s\'?', {
              object_title: `${t('App key')} ${keyConfirm.item.value?.id ?? ''}`,
            })
          "
          :confirm-label="t('KID')"
          :busy="keyConfirm.busy.value"
          :error="keyConfirm.error.value"
          :name-error="keyConfirm.nameError.value"
          @submit="keyConfirm.submit"
        />
      </template>
    </BOverlay>
  </div>
</template>
