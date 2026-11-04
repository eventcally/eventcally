<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import NameConfirmationForm from "@/shared/NameConfirmationForm.vue";
import { errorMessage, mapFieldErrors } from "../apiError";

const props = defineProps<{ mode: "request" | "cancel" }>();

const { t } = useI18n();

const busy = ref(false);
const error = ref<string | null>(null);
const emailError = ref<string | undefined>();

const title = computed(() =>
  props.mode === "request" ? t("Delete account") : t("Cancel deletion"),
);
const submitLabel = computed(() =>
  props.mode === "request" ? t("Request deletion") : t("Cancel deletion"),
);

async function submit(email: string) {
  if (busy.value) return;
  busy.value = true;
  error.value = null;
  emailError.value = undefined;

  const call = props.mode === "request" ? "/bff/user/deletion" : "/bff/user/deletion/cancel";
  const { data, error: err } = await api.POST(call, { body: { email } });

  if (data) {
    window.location.assign(data.redirect_url);
    return;
  }

  busy.value = false;
  const mapped = mapFieldErrors(err, ["email"]);
  if (mapped) {
    emailError.value = mapped.byKey.email;
    if (mapped.unmatched.length) error.value = mapped.unmatched.join(" ");
  } else {
    error.value = errorMessage(err, t("Error"));
  }
}
</script>

<template>
  <div>
    <AppBreadcrumb :items="[{ label: title }]" />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <NameConfirmationForm
      :label="t('Email')"
      input-id="email"
      input-type="email"
      :submit-label="submitLabel"
      submit-variant="primary"
      :error="emailError"
      :busy="busy"
      @submit="submit"
    >
      <p v-if="mode === 'request'">
        {{
          t(
            "The account is not deleted immediately. After a period of time, the account will be deleted. Until then, the deletion can be canceled.",
          )
        }}
      </p>
    </NameConfirmationForm>
  </div>
</template>
