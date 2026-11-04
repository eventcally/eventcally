<script setup lang="ts">
import { BButton } from "bootstrap-vue-next";
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { api } from "@/shared/api";
import ApiKeyFormFields from "@/shared/ApiKeyFormFields.vue";
import { errorMessage, mapFieldErrors } from "@/shared/apiError";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();
const router = useRouter();

const name = ref("");
const saving = ref(false);
const error = ref<string | null>(null);
const errors = ref<Record<string, string>>({});

async function save() {
  if (saving.value) return;
  saving.value = true;
  error.value = null;
  errors.value = {};

  const { data, error: err } = await api.POST("/bff/manage/organizations/{id}/api-keys", {
    params: { path: { id: props.organizationId } },
    body: { name: name.value },
  });

  if (data) {
    // The key is only part of this answer: hand it to the read page, never to the URL.
    await router.push({
      name: "organization-api-key",
      params: { organizationId: props.organizationId, id: data.id },
      state: { key: data.key },
    });
    return;
  }

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
    <ManageBreadcrumb
      :organization-id="organizationId"
      :items="[
        { label: t('API keys'), to: { name: 'organization-api-keys', params: { organizationId } } },
        {
          label: t('Create %(model_display_name)s', { model_display_name: t('API key') }),
        },
      ]"
    />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <form data-test="api-key-form" @submit.prevent="save">
      <ApiKeyFormFields v-model:name="name" :errors="errors" />
      <BButton id="submit" type="submit" variant="primary" :disabled="saving">
        {{ t("Create") }}
      </BButton>
    </form>
  </div>
</template>
