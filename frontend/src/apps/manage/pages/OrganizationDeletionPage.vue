<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import { errorMessage, mapFieldErrors } from "@/shared/apiError";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import NameConfirmationForm from "@/shared/NameConfirmationForm.vue";

// Request and cancel deletion are two URLs (e-mail and admin links) with one page.
const props = defineProps<{ organizationId: number; mode: "request" | "cancel" }>();

const { t } = useI18n();

const busy = ref(false);
const error = ref<string | null>(null);
const nameError = ref<string | undefined>();

const title = computed(() =>
  props.mode === "request"
    ? t("Delete %(model_display_name)s", { model_display_name: t("Organization") })
    : t("Cancel deletion"),
);
const submitLabel = computed(() =>
  props.mode === "request" ? t("Request deletion") : t("Cancel deletion"),
);

async function submit(name: string) {
  if (busy.value) return;
  busy.value = true;
  error.value = null;
  nameError.value = undefined;

  const params = { params: { path: { id: props.organizationId } }, body: { name } };
  const { data, error: err } =
    props.mode === "request"
      ? await api.POST("/bff/manage/organizations/{id}/deletion", params)
      : await api.POST("/bff/manage/organizations/{id}/deletion/cancel", params);

  if (data) {
    // Keep the busy state while the browser leaves.
    window.location.assign(data.redirect_url);
    return;
  }

  busy.value = false;
  const mapped = mapFieldErrors(err, ["name"]);

  if (mapped) {
    nameError.value = mapped.byKey.name;
    if (mapped.unmatched.length) error.value = mapped.unmatched.join(" ");
  } else {
    error.value = errorMessage(err, t("Error"));
  }
}
</script>

<template>
  <div>
    <ManageBreadcrumb :organization-id="organizationId" :items="[{ label: title }]" />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <NameConfirmationForm
      :label="t('Name of organization')"
      :submit-label="submitLabel"
      :error="nameError"
      :busy="busy"
      @submit="submit"
    >
      <p v-if="mode === 'request'" data-test="instruction">
        {{
          t(
            "The organization is not deleted immediately. After a period of time, the organization will be deleted. Until then, the deletion can be canceled.",
          )
        }}
      </p>
    </NameConfirmationForm>
  </div>
</template>
