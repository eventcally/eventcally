<script setup lang="ts">
import { BButton } from "bootstrap-vue-next";
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import TosAcceptLabel from "@/shared/TosAcceptLabel.vue";
import { errorMessage } from "@/shared/apiError";

// `next` is the page the user wanted before the ToS gate sent them here; the server
// validates it (an unsafe target falls back to the default one).
const props = defineProps<{ next?: string }>();

const { t } = useI18n();

const hasTos = ref(false);
const loaded = ref(false);
const accepted = ref(false);
const saving = ref(false);
const error = ref<string | null>(null);

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/user/accept-tos");
  if (data) {
    hasTos.value = data.has_tos;
    loaded.value = true;
  } else {
    error.value = errorMessage(err, t("Error"));
  }
});

async function submit() {
  if (saving.value) return;
  if (!accepted.value) return;

  saving.value = true;
  error.value = null;
  const { data, error: err } = await api.POST("/bff/user/accept-tos", {
    params: { query: { next: props.next } },
    body: { accept_tos: true },
  });
  if (data) {
    window.location.assign(data.redirect_url);
    return;
  }
  saving.value = false;
  error.value = errorMessage(err, t("Error"));
}
</script>

<template>
  <div>
    <AppBreadcrumb :items="[{ label: t('Confirmation required') }]" />

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <form v-if="loaded" data-test="accept-tos-form" @submit.prevent="submit">
      <div class="mb-3">
        <div class="form-check">
          <input
            id="accept_tos"
            v-model="accepted"
            type="checkbox"
            class="form-check-input"
            required
          />
          <label class="form-check-label" for="accept_tos">
            <TosAcceptLabel :has-tos="hasTos" />
          </label>
        </div>
      </div>
      <BButton id="submit" type="submit" variant="primary" :disabled="saving">
        {{ t("Confirm") }}
      </BButton>
    </form>
  </div>
</template>
