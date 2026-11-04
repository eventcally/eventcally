<script setup lang="ts">
import { BButton } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { api } from "@/shared/api";
import ApiKeyFormFields from "@/shared/ApiKeyFormFields.vue";
import { setFlash } from "@/shared/flash";
import { errorMessage, mapFieldErrors } from "../apiError";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";

// Create (no `id`) and update of an API key.
const props = defineProps<{ id?: number }>();

const { t } = useI18n();
const router = useRouter();

const name = ref("");
const loaded = ref(props.id === undefined);
const saving = ref(false);
const error = ref<string | null>(null);
const errors = ref<Record<string, string>>({});

const title = computed(() =>
  t(props.id === undefined ? "Create %(model_display_name)s" : "Update %(model_display_name)s", {
    model_display_name: t("API key"),
  }),
);

onMounted(async () => {
  if (props.id === undefined) return;
  const { data, error: err } = await api.GET("/bff/user/api-keys/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) {
    name.value = data.name;
    loaded.value = true;
  } else {
    error.value = errorMessage(err, t("Error"));
  }
});

async function save() {
  if (saving.value) return;
  saving.value = true;
  error.value = null;
  errors.value = {};

  if (props.id === undefined) {
    const { data, error: err } = await api.POST("/bff/user/api-keys", {
      body: { name: name.value },
    });
    if (data) {
      // The key is only part of this answer: hand it to the read page, never to the URL.
      await router.push({
        name: "api-key",
        params: { apiKeyId: data.id },
        state: { key: data.key },
      });
      return;
    }
    return fail(err);
  }

  const { error: err, response } = await api.PUT("/bff/user/api-keys/{id}", {
    params: { path: { id: props.id } },
    body: { name: name.value },
  });
  if (response.ok) {
    setFlash(
      t("%(model_display_name)s successfully updated", {
        model_display_name: t("API key"),
      }),
    );
    await router.push({ name: "api-key", params: { apiKeyId: props.id } });
    return;
  }
  fail(err);
}

function fail(err: unknown) {
  saving.value = false;
  const mapped = mapFieldErrors(err, ["name"]);
  if (mapped) {
    errors.value = mapped.byKey;
    if (mapped.unmatched.length) error.value = mapped.unmatched.join(" ");
  } else {
    error.value = errorMessage(err, t("Error"));
  }
}
</script>

<template>
  <div>
    <ProfileBreadcrumb
      :items="[{ label: t('API keys'), to: { name: 'api-keys' } }, { label: title }]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <form v-if="loaded" data-test="api-key-form" @submit.prevent="save">
      <ApiKeyFormFields v-model:name="name" :errors="errors" />
      <BButton id="submit" type="submit" variant="primary" :disabled="saving">
        {{ id === undefined ? t("Create") : t("Save") }}
      </BButton>
    </form>
  </div>
</template>
