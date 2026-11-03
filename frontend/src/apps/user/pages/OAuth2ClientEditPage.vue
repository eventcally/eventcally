<script setup lang="ts">
import { BButton } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { api } from "@/shared/api";
import { setFlash } from "@/shared/flash";
import OAuth2ClientFormFields from "@/shared/OAuth2ClientFormFields.vue";
import { errorMessage, mapFieldErrors } from "../apiError";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";

// Create (no `id`) and update of an OAuth2 client.
const props = defineProps<{ id?: number }>();

const FIELDS = ["client_name", "redirect_uris", "scopes"];

const { t } = useI18n();
const router = useRouter();

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
  const form = await api.GET("/bff/user/oauth2-clients/form");
  if (!form.data) {
    error.value = errorMessage(form.error, t("Error"));
    return;
  }
  scopeChoices.value = form.data.scopes;

  if (props.id !== undefined) {
    const { data, error: err } = await api.GET("/bff/user/oauth2-clients/{id}", {
      params: { path: { id: props.id } },
    });
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

  let failure: unknown;
  let id = props.id;
  let ok = false;

  if (id === undefined) {
    const { data, error: err } = await api.POST("/bff/user/oauth2-clients", {
      body,
    });
    if (data) {
      id = data.id;
      ok = true;
    } else failure = err;
  } else {
    const { error: err, response } = await api.PUT("/bff/user/oauth2-clients/{id}", {
      params: { path: { id } },
      body,
    });
    ok = response.ok;
    if (!ok) failure = err;
  }

  if (ok && id !== undefined) {
    setFlash(
      t(
        props.id === undefined
          ? "%(model_display_name)s successfully created"
          : "%(model_display_name)s successfully updated",
        { model_display_name: modelName.value },
      ),
    );
    await router.push({ name: "oauth2-client", params: { clientId: id } });
    return;
  }

  saving.value = false;
  const mapped = mapFieldErrors(failure, FIELDS);
  if (mapped) {
    errors.value = mapped.byKey;
    if (mapped.unmatched.length) error.value = mapped.unmatched.join(" ");
  } else {
    error.value = errorMessage(failure, t("Error"));
  }
}
</script>

<template>
  <div>
    <ProfileBreadcrumb
      :items="[{ label: t('OAuth2 clients'), to: { name: 'oauth2-clients' } }, { label: title }]"
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
