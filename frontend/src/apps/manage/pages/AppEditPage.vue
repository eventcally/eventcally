<script setup lang="ts">
import { BButton } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import { errorMessage, mapFieldErrors } from "@/shared/apiError";
import LabeledField from "@/shared/LabeledField.vue";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import OAuth2ClientFormFields from "@/shared/OAuth2ClientFormFields.vue";
import PermissionCheckboxes, { type CheckboxChoice } from "../components/PermissionCheckboxes.vue";

// Create (no `id`) and update of an app of the organization.
const props = defineProps<{ organizationId: number; id?: number }>();

const FIELDS = [
  "client_name",
  "redirect_uris",
  "scopes",
  "app_permissions",
  "homepage_url",
  "setup_url",
  "description",
  "webhook.url",
  "webhook.secret",
  "webhook.disabled",
  "webhook.event_types",
];

const { t } = useI18n();

const clientName = ref("");
const redirectUris = ref("");
const scopes = ref<string[]>([]);
const permissions = ref<string[]>([]);
const homepageUrl = ref("");
const setupUrl = ref("");
const description = ref("");
const webhookUrl = ref("");
const webhookSecret = ref("");
const webhookDisabled = ref(false);
const eventTypes = ref<string[]>([]);

const scopeChoices = ref<string[]>([]);
const permissionChoices = ref<CheckboxChoice[]>([]);
const eventTypeChoices = ref<CheckboxChoice[]>([]);
const loaded = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);
const errors = ref<Record<string, string>>({});

const modelName = computed(() => t("App"));
const title = computed(() =>
  t(props.id === undefined ? "Create %(model_display_name)s" : "Update %(model_display_name)s", {
    model_display_name: modelName.value,
  }),
);

onMounted(async () => {
  const options = await api.GET("/bff/manage/organizations/{id}/apps/form", {
    params: { path: { id: props.organizationId } },
  });
  if (!options.data) {
    error.value = errorMessage(options.error, t("Error"));
    return;
  }
  scopeChoices.value = options.data.scopes;
  permissionChoices.value = options.data.app_permissions.map((p) => ({
    value: p.permission,
    label: p.label,
  }));
  eventTypeChoices.value = options.data.event_types.map((e) => ({ value: e, label: e }));

  if (props.id !== undefined) {
    const { data, error: err } = await api.GET(
      "/bff/manage/organizations/{id}/apps/{app_id}/form",
      { params: { path: { id: props.organizationId, app_id: props.id } } },
    );
    if (!data) {
      error.value = errorMessage(err, t("Error"));
      return;
    }
    clientName.value = data.client_name;
    redirectUris.value = (data.redirect_uris ?? []).join("\n");
    scopes.value = data.scopes ?? [];
    permissions.value = data.app_permissions;
    homepageUrl.value = data.homepage_url ?? "";
    setupUrl.value = data.setup_url ?? "";
    description.value = data.description ?? "";
    webhookUrl.value = data.webhook?.url ?? "";
    webhookSecret.value = data.webhook?.secret ?? "";
    webhookDisabled.value = data.webhook?.disabled ?? false;
    eventTypes.value = data.webhook?.event_types ?? [];
  }
  loaded.value = true;
});

async function save() {
  if (saving.value) return;
  saving.value = true;
  error.value = null;
  errors.value = {};

  const body = {
    client_name: clientName.value,
    redirect_uris: redirectUris.value.split(/\r?\n/),
    scopes: scopes.value,
    app_permissions: permissions.value,
    homepage_url: homepageUrl.value,
    setup_url: setupUrl.value,
    description: description.value,
    webhook: {
      url: webhookUrl.value,
      secret: webhookSecret.value,
      disabled: webhookDisabled.value,
      event_types: eventTypes.value,
    },
  };

  const answer =
    props.id === undefined
      ? await api.POST("/bff/manage/organizations/{id}/apps", {
          params: { path: { id: props.organizationId } },
          body,
        })
      : await api.PUT("/bff/manage/organizations/{id}/apps/{app_id}", {
          params: { path: { id: props.organizationId, app_id: props.id } },
          body,
        });

  if (answer.data) {
    // The server flashed the success message; the read page renders it. Keep the busy state.
    window.location.assign(answer.data.redirect_url);
    return;
  }

  saving.value = false;
  const mapped = mapFieldErrors(answer.error, FIELDS);
  if (mapped) {
    errors.value = mapped.byKey;
    if (mapped.unmatched.length) error.value = mapped.unmatched.join(" ");
  } else {
    error.value = errorMessage(answer.error, t("Error"));
  }
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

    <form v-if="loaded" data-test="app-form" @submit.prevent="save">
      <OAuth2ClientFormFields
        v-model:client-name="clientName"
        v-model:redirect-uris="redirectUris"
        v-model:scopes="scopes"
        :scope-choices="scopeChoices"
        :errors="errors"
      />

      <LabeledField :label="t('Permissions')" :error="errors.app_permissions" required>
        <PermissionCheckboxes v-model="permissions" :choices="permissionChoices" id-prefix="permission" />
      </LabeledField>

      <LabeledField :label="t('Homepage URL')" label-for="homepage_url" :error="errors.homepage_url">
        <input
          id="homepage_url"
          v-model="homepageUrl"
          type="text"
          class="form-control"
          :class="{ 'is-invalid': errors.homepage_url }"
        />
      </LabeledField>

      <LabeledField :label="t('Setup URL')" label-for="setup_url" :error="errors.setup_url">
        <input
          id="setup_url"
          v-model="setupUrl"
          type="text"
          class="form-control"
          :class="{ 'is-invalid': errors.setup_url }"
        />
      </LabeledField>

      <LabeledField :label="t('Description')" label-for="description" :error="errors.description">
        <textarea
          id="description"
          v-model="description"
          class="form-control"
          :class="{ 'is-invalid': errors.description }"
          rows="3"
        ></textarea>
      </LabeledField>

      <fieldset class="mb-3" data-test="webhook">
        <legend class="form-label fs-6">{{ t("Webhook") }}</legend>

        <LabeledField :label="t('URL')" label-for="webhook_url" :error="errors['webhook.url']">
          <input
            id="webhook_url"
            v-model="webhookUrl"
            type="text"
            class="form-control"
            :class="{ 'is-invalid': errors['webhook.url'] }"
          />
        </LabeledField>

        <LabeledField :label="t('Secret')" label-for="webhook_secret" :error="errors['webhook.secret']">
          <input
            id="webhook_secret"
            v-model="webhookSecret"
            type="text"
            class="form-control"
            :class="{ 'is-invalid': errors['webhook.secret'] }"
            autocomplete="off"
          />
        </LabeledField>

        <div class="form-check form-switch mb-3">
          <input
            id="webhook_disabled"
            v-model="webhookDisabled"
            type="checkbox"
            role="switch"
            class="form-check-input"
          />
          <label class="form-check-label" for="webhook_disabled">{{ t("Disabled") }}</label>
        </div>

        <LabeledField :label="t('Event types')" :error="errors['webhook.event_types']">
          <PermissionCheckboxes
            v-model="eventTypes"
            :choices="eventTypeChoices"
            id-prefix="event-type"
          />
        </LabeledField>
      </fieldset>

      <BButton id="submit" type="submit" variant="primary" :disabled="saving">
        {{ t("Save") }}
      </BButton>
    </form>
  </div>
</template>
