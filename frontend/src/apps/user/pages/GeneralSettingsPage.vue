<script setup lang="ts">
import { BButton } from "bootstrap-vue-next";
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import LabeledField from "@/shared/LabeledField.vue";
import { errorMessage } from "@/shared/apiError";
import ProfileBreadcrumb from "../components/ProfileBreadcrumb.vue";

const { t } = useI18n();

// "" is the default: the language of the browser.
const locale = ref("");
const loaded = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/user/profile");
  if (data) {
    locale.value = data.locale ?? "";
    loaded.value = true;
  } else {
    error.value = errorMessage(err, t("Error"));
  }
});

async function save() {
  if (saving.value) return;
  saving.value = true;
  error.value = null;
  const { data, error: err } = await api.PUT("/bff/user/settings/general", {
    body: { locale: (locale.value || null) as "de" | "en" | null },
  });
  if (data) {
    // A full page load: the server flashed the message and the new language applies.
    window.location.assign(data.redirect_url);
    return;
  }
  saving.value = false;
  error.value = errorMessage(err, t("Error"));
}
</script>

<template>
  <div>
    <ProfileBreadcrumb :items="[{ label: t('General') }]" />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <form v-if="loaded" data-test="general-form" @submit.prevent="save">
      <LabeledField :label="t('Language')" label-for="locale">
        <select id="locale" v-model="locale" class="form-select">
          <option value="">{{ t("Default") }}</option>
          <option value="de">Deutsch</option>
          <option value="en">English</option>
        </select>
      </LabeledField>
      <BButton id="submit" type="submit" variant="primary" :disabled="saving">
        {{ t("Save") }}
      </BButton>
    </form>
  </div>
</template>
