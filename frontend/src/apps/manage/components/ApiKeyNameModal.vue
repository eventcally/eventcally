<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import ApiKeyFormFields from "@/shared/ApiKeyFormFields.vue";
import { errorMessage, mapFieldErrors } from "@/shared/apiError";
import { useNotify } from "@/shared/notify";

// The rename of an organization API key (the old update page) in a modal.
const props = defineProps<{ organizationId: number; apiKeyId: number | null; name: string }>();
const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ saved: [] }>();

const { t } = useI18n();
const notify = useNotify();

const value = ref("");
const busy = ref(false);
const error = ref<string | null>(null);
const errors = ref<Record<string, string>>({});

// Every opening starts with the current name.
watch(show, (open) => {
  if (open) {
    value.value = props.name;
    error.value = null;
    errors.value = {};
  }
});

async function save() {
  if (busy.value || props.apiKeyId === null) return;
  busy.value = true;
  error.value = null;
  errors.value = {};

  const { data, error: err } = await api.PUT(
    "/bff/manage/organizations/{id}/api-keys/{api_key_id}",
    {
      params: { path: { id: props.organizationId, api_key_id: props.apiKeyId } },
      body: { name: value.value },
    },
  );
  busy.value = false;

  if (!data) {
    const mapped = mapFieldErrors(err, ["name"]);
    if (mapped) {
      errors.value = mapped.byKey;
      if (mapped.unmatched.length) error.value = mapped.unmatched.join(" ");
    } else {
      error.value = errorMessage(err, t("Error"));
    }
    return;
  }

  notify.success(data.message);
  show.value = false;
  emit("saved");
}
</script>

<template>
  <BModal
    v-model="show"
    :title="t('Update %(model_display_name)s', { model_display_name: t('API key') })"
    :ok-title="t('Update')"
    :cancel-title="t('Cancel')"
    :ok-disabled="busy"
    @ok.prevent="save"
  >
    <div v-if="error" class="alert alert-danger" role="alert" data-test="api-key-name-error">
      {{ error }}
    </div>
    <form @submit.prevent="save">
      <ApiKeyFormFields v-model:name="value" :errors="errors" />
    </form>
  </BModal>
</template>
