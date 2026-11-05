<script setup lang="ts">
import { BButton, BOverlay } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import ReadProps from "@/shared/ReadProps.vue";
import LabeledField from "@/shared/LabeledField.vue";
import PermissionCheckboxes from "../components/PermissionCheckboxes.vue";

type InstallableApp = components["schemas"]["InstallableAppRead"];

// The entry point an app links its users to: what the app is and which permissions it gets.
const props = defineProps<{ organizationId: number; appId: number }>();

const { t } = useI18n();

const app = ref<InstallableApp | null>(null);
const loading = ref(true);
const installing = ref(false);
const error = ref<string | null>(null);

onMounted(async () => {
  const { data, error: err } = await api.GET(
    "/bff/manage/organizations/{id}/installable-apps/{app_id}",
    { params: { path: { id: props.organizationId, app_id: props.appId } } },
  );
  loading.value = false;

  if (data) app.value = data;
  else error.value = errorMessage(err, t("Error"));
});

const title = computed(() =>
  t("Create %(model_display_name)s", { model_display_name: t("App installation") }),
);
// The permissions are only shown: every one the app asks for is granted.
const permissions = computed(() => app.value?.permissions ?? []);
const choices = computed(() => permissions.value.map((label) => ({ value: label, label })));

async function install() {
  if (installing.value || !app.value) return;
  installing.value = true;
  error.value = null;

  const { data, error: err } = await api.POST(
    "/bff/manage/organizations/{id}/app-installations",
    { params: { path: { id: props.organizationId } }, body: { app_id: props.appId } },
  );

  if (data) {
    // The server flashed the success message (with the setup link); the read page renders it.
    window.location.assign(data.redirect_url);
    return;
  }

  installing.value = false;
  error.value = errorMessage(err, t("Error"));
}
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
      <form v-if="app" data-test="install-form" @submit.prevent="install">
        <p>
          {{ t("Do you want to install '%(app_name)s'?", { app_name: app.client_name ?? "" }) }}
        </p>

        <ReadProps
          :rows="[
            { label: t('Homepage'), value: app.homepage_url, href: app.homepage_url ?? undefined },
            { label: t('Description'), value: app.description },
          ]"
        />

        <LabeledField :label="t('Permissions')">
          <PermissionCheckboxes
            :model-value="permissions"
            :choices="choices"
            id-prefix="permission"
            disabled
          />
        </LabeledField>

        <BButton id="submit" type="submit" variant="primary" :disabled="installing">
          {{ t("Install") }}
        </BButton>
      </form>
    </BOverlay>
  </div>
</template>
