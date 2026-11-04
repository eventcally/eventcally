<script setup lang="ts">
import { BButton, BOverlay, BSpinner } from "bootstrap-vue-next";
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { errorMessage, mapFieldErrors } from "@/shared/apiError";
import ManageBreadcrumb from "@/shared/ManageBreadcrumb.vue";
import { useNotify } from "@/shared/notify";
import WidgetEmbedModal from "../components/WidgetEmbedModal.vue";

type Settings = components["schemas"]["WidgetSettingsForm"];

const props = defineProps<{ organizationId: number }>();

const { t } = useI18n();
const notify = useNotify();

const FIELDS = ["font", "background_color", "primary_color", "link_color"];

const settings = ref<Settings | null>(null);
const loading = ref(true);
const loadError = ref<string | null>(null);
const saving = ref(false);
const saveError = ref<string | null>(null);
const errors = ref<Record<string, string>>({});
const showEmbed = ref(false);

const font = ref("");
const backgroundColor = ref("");
const primaryColor = ref("");
const linkColor = ref("");

onMounted(async () => {
  const { data, error } = await api.GET("/bff/manage/organizations/{id}/widget-settings", {
    params: { path: { id: props.organizationId } },
  });
  loading.value = false;

  if (!data) {
    loadError.value = errorMessage(error, t("Error"));
    return;
  }

  settings.value = data;
  font.value = data.font ?? "";
  backgroundColor.value = data.background_color;
  primaryColor.value = data.primary_color;
  linkColor.value = data.link_color;
});

async function save() {
  if (saving.value) return;

  saving.value = true;
  saveError.value = null;
  errors.value = {};

  const { data, error } = await api.PUT("/bff/manage/organizations/{id}/widget-settings", {
    params: { path: { id: props.organizationId } },
    body: {
      font: font.value,
      background_color: backgroundColor.value,
      primary_color: primaryColor.value,
      link_color: linkColor.value,
    },
  });
  saving.value = false;

  if (data) {
    notify.success(data.message);
    return;
  }

  const mapped = mapFieldErrors(error, FIELDS);

  if (mapped) {
    errors.value = mapped.byKey;
    if (mapped.unmatched.length) saveError.value = mapped.unmatched.join(" ");
  } else {
    saveError.value = errorMessage(error, t("Error"));
  }
}
</script>

<template>
  <div>
    <ManageBreadcrumb :organization-id="organizationId" :items="[{ label: t('Widgets') }]" />

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <template v-if="settings">
        <form data-test="widget-form" @submit.prevent="save">
          <div class="mb-3">
            <label class="form-label" for="widget_font">{{ t("Font") }}</label>
            <input
              id="widget_font"
              v-model="font"
              type="text"
              class="form-control"
              :class="{ 'is-invalid': errors.font }"
              maxlength="255"
            />
            <div v-if="errors.font" class="invalid-feedback">{{ errors.font }}</div>
          </div>
          <div class="mb-3">
            <label class="form-label" for="widget_background_color">{{ t("Background Color") }}</label>
            <input
              id="widget_background_color"
              v-model="backgroundColor"
              type="color"
              class="form-control form-control-color"
              :class="{ 'is-invalid': errors.background_color }"
            />
            <div v-if="errors.background_color" class="invalid-feedback">
              {{ errors.background_color }}
            </div>
          </div>
          <div class="mb-3">
            <label class="form-label" for="widget_primary_color">{{ t("Primary Color") }}</label>
            <input
              id="widget_primary_color"
              v-model="primaryColor"
              type="color"
              class="form-control form-control-color"
              :class="{ 'is-invalid': errors.primary_color }"
            />
            <div v-if="errors.primary_color" class="invalid-feedback">
              {{ errors.primary_color }}
            </div>
          </div>
          <div class="mb-3">
            <label class="form-label" for="widget_link_color">{{ t("Link Color") }}</label>
            <input
              id="widget_link_color"
              v-model="linkColor"
              type="color"
              class="form-control form-control-color"
              :class="{ 'is-invalid': errors.link_color }"
            />
            <div v-if="errors.link_color" class="invalid-feedback">{{ errors.link_color }}</div>
          </div>

          <div v-if="saveError" class="alert alert-danger" role="alert">{{ saveError }}</div>

          <BButton id="submit" type="submit" variant="primary" :disabled="saving">
            <BSpinner v-if="saving" small />
            {{ t("Update") }}
          </BButton>
        </form>

        <h2 class="mt-4">{{ t("Embed events as a widget") }}</h2>
        <p>
          {{
            t(
              "You can easily embed the events of your organization on your website as a widget.",
            )
          }}
        </p>

        <div class="btn-group mb-3">
          <button
            type="button"
            class="btn btn-outline-info"
            data-test="embed"
            @click="showEmbed = true"
          >
            <i class="fa fa-wrench"></i> {{ t("Installation") }}
          </button>
          <a
            class="btn btn-outline-info"
            :href="settings.preview_url"
            target="_blank"
            rel="noopener noreferrer"
          >
            <i class="fa fa-external-link-alt"></i> {{ t("Preview") }}
          </a>
        </div>

        <WidgetEmbedModal
          v-model="showEmbed"
          :organization-id="organizationId"
          :loader-url="settings.loader_url"
          :iframe-url="settings.iframe_url"
        />
      </template>
    </BOverlay>
  </div>
</template>
