<script setup lang="ts">
import { BButton } from "bootstrap-vue-next";
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";

const { t } = useI18n();

const newsletterEnabled = ref(false);
const loaded = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/user/profile");
  if (data) {
    newsletterEnabled.value = data.newsletter_enabled;
    loaded.value = true;
  } else {
    error.value = errorMessage(err, t("Error"));
  }
});

async function save() {
  if (saving.value) return;
  saving.value = true;
  error.value = null;
  const { data, error: err } = await api.PUT("/bff/user/settings/notifications", {
    body: { newsletter_enabled: newsletterEnabled.value },
  });
  if (data) {
    // The server flashed the message; like the general settings, this ends on the profile.
    window.location.assign(data.redirect_url);
    return;
  }
  saving.value = false;
  error.value = errorMessage(err, t("Error"));
}
</script>

<template>
  <div>
    <ProfileBreadcrumb :items="[{ label: t('Notifications') }]" />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <form v-if="loaded" data-test="notifications-form" @submit.prevent="save">
      <div class="mb-3">
        <div class="form-check form-switch">
          <input
            id="newsletter_enabled"
            v-model="newsletterEnabled"
            type="checkbox"
            class="form-check-input"
            role="switch"
          />
          <label class="form-check-label" for="newsletter_enabled">{{ t("Newsletter") }}</label>
        </div>
        <div class="form-text">
          {{ t("Information about new features and improvements.") }}
        </div>
      </div>
      <BButton id="submit" type="submit" variant="primary" :disabled="saving">
        {{ t("Save") }}
      </BButton>
    </form>
  </div>
</template>
