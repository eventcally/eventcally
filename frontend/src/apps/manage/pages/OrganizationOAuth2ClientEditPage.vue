<script setup lang="ts">
import { BButton } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import { errorMessage, mapFieldErrors } from "@/shared/apiError";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import OAuth2ClientFormFields from "@/shared/OAuth2ClientFormFields.vue";

// Create (no `id`) and update of an organization OAuth2 client.
const props = defineProps<{ organizationId: number; id?: number }>();

const FIELDS = ["client_name", "redirect_uris", "scopes"];

const { t } = useI18n();

const clientName = ref("");
const redirectUris = ref("");
const scopes = ref<string[]>([]);
const scopeChoices = ref<string[]>([]);
const loaded = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);
const errors = ref<Record<string, string>>({});

const modelName = computed(() => t("OAuth2 client"));
const title = computed(() =>
  t(props.id === undefined ? "Create %(model_display_name)s" : "Update %(model_display_name)s", {
    model_display_name: modelName.value,
  }),
);

onMounted(async () => {
  const form = await api.GET("/bff/manage/organizations/{id}/oauth2-clients/form", {
    params: { path: { id: props.organizationId } },
  });
  if (!form.data) {
    error.value = errorMessage(form.error, t("Error"));
    return;
  }
  scopeChoices.value = form.data.scopes;

  if (props.id !== undefined) {
    const { data, error: err } = await api.GET(
      "/bff/manage/organizations/{id}/oauth2-clients/{client_id}",
      { params: { path: { id: props.organizationId, client_id: props.id } } },
    );
    if (!data) {
      error.value = errorMessage(err, t("Error"));
      return;
    }
    clientName.value = data.client_name ?? "";
    redirectUris.value = data.redirect_uris.join("\n");
    scopes.value = data.scopes;
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
  };

  const answer =
    props.id === undefined
      ? await api.POST("/bff/manage/organizations/{id}/oauth2-clients", {
          params: { path: { id: props.organizationId } },
          body,
        })
      : await api.PUT("/bff/manage/organizations/{id}/oauth2-clients/{client_id}", {
          params: { path: { id: props.organizationId, client_id: props.id } },
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
        {
          label: t('OAuth2 clients'),
          to: { name: 'organization-oauth2-clients', params: { organizationId } },
        },
        { label: title },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <form v-if="loaded" data-test="oauth2-client-form" @submit.prevent="save">
      <OAuth2ClientFormFields
        v-model:client-name="clientName"
        v-model:redirect-uris="redirectUris"
        v-model:scopes="scopes"
        :scope-choices="scopeChoices"
        :errors="errors"
      />
      <BButton id="submit" type="submit" variant="primary" :disabled="saving">
        {{ t("Save") }}
      </BButton>
    </form>
  </div>
</template>
