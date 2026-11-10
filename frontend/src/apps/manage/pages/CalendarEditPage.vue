<script setup lang="ts">
import { BButton, BFormCheckbox, BFormInput, BFormTextarea, BOverlay, BSpinner } from "bootstrap-vue-next";
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import { mapFieldErrors } from "@/shared/apiError";
import LabeledField from "@/shared/LabeledField.vue";

const props = defineProps<{ organizationId: number; id?: number }>();

const { t } = useI18n();

const FIELDS = ["name", "description", "private"];
const CHECK_DELAY_MS = 300;

const loading = ref(true);
const loadError = ref<string | null>(null);
const saving = ref(false);
const saveError = ref<string | null>(null);
const ready = ref(false);

const name = ref("");
const description = ref("");
const isPrivate = ref(false);
const errors = ref<Record<string, string>>({});
const originalName = ref("");
// Live availability of the name: the message when taken, "" when free, `null` unchecked.
const nameTaken = ref<string | null>(null);
let checkTimer: ReturnType<typeof setTimeout> | undefined;

const isUpdate = computed(() => props.id !== undefined);
const modelName = computed(() => t("Calendar"));
const title = computed(() =>
  t(isUpdate.value ? "Update %(model_display_name)s" : "Create %(model_display_name)s", {
    model_display_name: modelName.value,
  }),
);
const nameError = computed(() => errors.value.name ?? nameTaken.value ?? undefined);

async function load() {
  loading.value = true;
  const { data, error } = isUpdate.value
    ? await api.GET("/bff/manage/organizations/{id}/calendars/{calendar_id}", {
        params: { path: { id: props.organizationId, calendar_id: props.id! } },
      })
    : await api.GET("/bff/manage/organizations/{id}/calendars/create-form", {
        params: { path: { id: props.organizationId } },
      });
  loading.value = false;

  if (!data) {
    loadError.value = error?.message ?? t("Error");
    return;
  }

  name.value = data.name;
  originalName.value = data.name;
  description.value = data.description ?? "";
  isPrivate.value = data.private ?? false;
  ready.value = true;
}

function checkName(value: string) {
  clearTimeout(checkTimer);
  const trimmed = value.trim();
  const rest = { ...errors.value };
  delete rest.name;
  errors.value = rest;
  nameTaken.value = null;

  if (!trimmed || trimmed === originalName.value) return;

  checkTimer = setTimeout(async () => {
    const { data } = await api.GET("/bff/manage/organizations/{id}/calendars/name-availability", {
      params: { path: { id: props.organizationId }, query: { name: trimmed, exclude_id: props.id } },
    });
    // The field changed while the request was in flight.
    if (!data || name.value.trim() !== trimmed) return;
    nameTaken.value = data.name_taken ? t("A calendar already exists with this name.") : "";
  }, CHECK_DELAY_MS);
}

function onName(value: string) {
  name.value = value;
  checkName(value);
}

async function save() {
  if (saving.value || !ready.value) return;

  saving.value = true;
  saveError.value = null;
  errors.value = {};

  const body = { name: name.value, description: description.value, private: isPrivate.value, inline: false };
  const path = { id: props.organizationId };
  const { data, error } = isUpdate.value
    ? await api.PUT("/bff/manage/organizations/{id}/calendars/{calendar_id}", {
        params: { path: { ...path, calendar_id: props.id! } },
        body,
      })
    : await api.POST("/bff/manage/organizations/{id}/calendars", { params: { path }, body });

  if (data) {
    // The server flashed the success message; the list renders it. Keep the spinner.
    location.assign(data.redirect_url);
    return;
  }

  saving.value = false;
  const mapped = mapFieldErrors(error, FIELDS);

  if (mapped) {
    errors.value = mapped.byKey;
    if (mapped.unmatched.length) saveError.value = mapped.unmatched.join(" ");
  } else {
    saveError.value = error?.message ?? t("Error");
  }
}

onMounted(load);
onBeforeUnmount(() => clearTimeout(checkTimer));
</script>

<template>
  <div>
    <AppBreadcrumb
      :items="[
        { label: t('Calendars'), to: { name: 'calendars', params: { organizationId } } },
        { label: title },
      ]"
    />

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <form v-if="ready" data-test="calendar-form" @submit.prevent="save">
        <LabeledField :label="t('Name')" label-for="name" :error="nameError" required>
          <BFormInput
            id="name"
            :model-value="name"
            required
            maxlength="255"
            autocomplete="off"
            :state="nameError ? false : null"
            @update:model-value="onName($event as string)"
          />
        </LabeledField>

        <LabeledField :label="t('Description')" label-for="description" :error="errors.description">
          <BFormTextarea id="description" v-model="description" rows="4" />
        </LabeledField>

        <LabeledField
          :label="t('Private')"
          label-for="private"
          :description="
            t(
              'Private calendars have no public page and cannot be used as search filter by others.',
            )
          "
          :error="errors.private"
        >
          <BFormCheckbox id="private" v-model="isPrivate" switch>{{ t("Private") }}</BFormCheckbox>
        </LabeledField>

        <div v-if="saveError" class="alert alert-danger" role="alert">{{ saveError }}</div>

        <BButton id="submit" type="submit" variant="primary" :disabled="saving">
          <BSpinner v-if="saving" small />
          {{ isUpdate ? t("Update calendar") : t("Create calendar") }}
        </BButton>
      </form>
    </BOverlay>
  </div>
</template>
