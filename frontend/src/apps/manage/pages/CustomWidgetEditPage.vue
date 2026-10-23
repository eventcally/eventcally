<script setup lang="ts">
import {
  BButton,
  BFormInput,
  BFormRadioGroup,
  BFormSelect,
  BInputGroup,
  BInputGroupText,
  BOverlay,
  BSpinner,
} from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import {
  defaultSettings,
  mergeSettings,
  type SettingsByType,
  type WidgetType,
} from "@/shared/customWidget";
import { manage } from "@/shared/legacy";
import { setFlash } from "../flash";
import CustomWidgetPreview from "../components/CustomWidgetPreview.vue";
import CustomWidgetSettingsForm from "../components/CustomWidgetSettingsForm.vue";

const props = defineProps<{ organizationId: number; id?: number }>();

const { t } = useI18n();

const widgetType = ref<WidgetType>("search");
const name = ref("Widget");
// Settings are kept per type, so switching the type back and forth loses nothing.
const form = ref<SettingsByType>({
  search: defaultSettings("search", props.organizationId),
  calendar: defaultSettings("calendar", props.organizationId),
});
const loading = ref(false);
const ready = ref(props.id == null);
const saving = ref(false);
const nameError = ref<string | null>(null);
const error = ref<string | null>(null);

const previewSize = ref("100%");
const previewBackground = ref("#f8f9fa");

const settings = computed({
  get: () => form.value[widgetType.value],
  set: (value) => {
    (form.value as Record<WidgetType, unknown>)[widgetType.value] = value;
  },
});

const typeOptions = computed(() => [
  { value: "search", text: t("Search") },
  { value: "calendar", text: t("Calendar") },
]);
const sizeOptions = computed(() => [
  { value: "100%", text: t("Desktop") },
  { value: "768px", text: t("Tablet") },
  { value: "400px", text: t("Mobile") },
]);

const listUrl = computed(() => manage.customWidgets(props.organizationId));

async function load() {
  if (props.id == null) return;
  loading.value = true;
  const { data, error: err } = await api.GET("/bff/manage/custom-widgets/{id}", {
    params: { path: { id: props.id } },
  });
  loading.value = false;
  if (!data) {
    error.value = err?.message ?? t("Error");
    return;
  }
  const type = data.widget_type as WidgetType;
  widgetType.value = type;
  name.value = data.name;
  (form.value as Record<WidgetType, unknown>)[type] = mergeSettings(
    defaultSettings(type, props.organizationId),
    data.settings,
  );
  ready.value = true;
}

async function save() {
  saving.value = true;
  nameError.value = null;
  error.value = null;
  const body = {
    widget_type: widgetType.value,
    name: name.value,
    settings: settings.value as unknown as Record<string, never>,
  };
  const { error: err } =
    props.id == null
      ? await api.POST("/bff/manage/organizations/{id}/custom-widgets", {
          params: { path: { id: props.organizationId } },
          body,
        })
      : await api.PUT("/bff/manage/custom-widgets/{id}", {
          params: { path: { id: props.id } },
          body,
        });
  saving.value = false;

  if (err) {
    const fieldErrors = "errors" in err ? err.errors : [];
    const forName = fieldErrors.find((e) => e.loc.includes("name"));
    if (forName) nameError.value = forName.msg;
    else error.value = fieldErrors[0]?.msg ?? err.message ?? t("Error");
    return;
  }

  // The editor is a separate page load (no navbar), so the message travels via storage.
  setFlash(t("Widget successfully saved"));
  location.assign(listUrl.value);
}

onMounted(load);
</script>

<template>
  <div class="d-flex flex-column h-100">
    <div class="d-flex flex-wrap align-items-center gap-3 bg-light px-3 flex-shrink-0">
      <h1 class="my-3 fs-2">{{ t("Widget configurator") }}</h1>
      <BOverlay :show="loading">
        <form class="d-flex flex-wrap align-items-center gap-2" @submit.prevent="save">
          <BInputGroup class="w-auto">
            <BInputGroupText>{{ t("Widget type") }}</BInputGroupText>
            <BFormSelect
              v-model="widgetType"
              :options="typeOptions"
              :aria-label="t('Widget type')"
              data-test="widget-type"
            />
          </BInputGroup>
          <BInputGroup class="w-auto">
            <BInputGroupText>{{ t("Name") }}</BInputGroupText>
            <BFormInput
              v-model="name"
              :state="nameError ? false : null"
              :aria-label="t('Name')"
              data-test="widget-name"
            />
          </BInputGroup>
          <a :href="listUrl" class="btn btn-secondary" :class="{ disabled: saving }">
            {{ t("Cancel") }}
          </a>
          <BButton type="submit" variant="primary" :disabled="saving || !ready">
            <BSpinner v-if="saving" small />
            {{ t("Save") }}
          </BButton>
        </form>
      </BOverlay>
      <div v-if="nameError" class="text-danger small" role="alert">
        {{ nameError }}
      </div>
      <div v-if="error" class="alert alert-danger mb-0 py-1" role="alert">
        {{ error }}
      </div>
    </div>

    <div class="row g-0 flex-fill" style="min-height: 0">
      <div class="col-sm-3 mh-100 p-3 overflow-y-scroll">
        <BOverlay :show="loading">
          <div class="card">
            <CustomWidgetSettingsForm v-if="ready" v-model:settings="settings" :type="widgetType" />
          </div>
        </BOverlay>
      </div>
      <div class="col-sm-9 mh-100 p-3 d-flex flex-column">
        <div class="d-flex justify-content-end align-items-center gap-2 mb-2 flex-shrink-0">
          <BFormInput
            v-model="previewBackground"
            type="color"
            style="max-width: 60px"
            :aria-label="t('Background color')"
          />
          <BFormRadioGroup
            v-model="previewSize"
            :options="sizeOptions"
            size="sm"
            button-variant="outline-secondary"
            buttons
          />
        </div>
        <div class="flex-fill overflow-y-scroll" style="min-height: 0">
          <div
            class="h-100 border p-3 mx-auto overflow-y-scroll"
            :style="{ width: previewSize, backgroundColor: previewBackground }"
          >
            <div class="mb-2 fw-bold">{{ t("Preview") }}</div>
            <CustomWidgetPreview
              v-if="ready"
              :type="widgetType"
              :settings="settings"
              :size="previewSize"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
