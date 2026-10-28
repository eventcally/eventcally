<script setup lang="ts">
import { BButton, BOverlay, BSpinner } from "bootstrap-vue-next";
import { computed, nextTick, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import { toFieldErrors } from "@/shared/fieldErrors";
import { manage } from "@/shared/legacy";
import EventPlaceFormFields from "../components/EventPlaceFormFields.vue";
import {
  EVENT_PLACE_FORM_FIELDS,
  emptyLocation,
  eventPlaceFormValue,
  eventPlaceSaveBody,
  type EventPlaceFormValue,
} from "../eventPlaceForm";

type PlaceForm = components["schemas"]["EventPlaceForm"];

const props = defineProps<{ organizationId: number; id?: number }>();

const { t } = useI18n();


const loading = ref(true);
const loadError = ref<string | null>(null);
const saving = ref(false);
const saveError = ref<string | null>(null);
const placeForm = ref<PlaceForm | null>(null);

const form = ref<EventPlaceFormValue>({
  name: "",
  url: "",
  description: "",
  location: emptyLocation(),
  photo: null,
});
const photoPreview = ref<string | null>(null);
const errors = ref<Record<string, string>>({});
const originalName = ref("");

const isUpdate = computed(() => props.id !== undefined);
const title = computed(() =>
  t(isUpdate.value ? "Update %(model_display_name)s" : "Create %(model_display_name)s", {
    model_display_name: t("Place"),
  }),
);

async function load() {
  loading.value = true;
  const { data, error } = isUpdate.value
    ? await api.GET("/bff/manage/organizations/{id}/event-places/{place_id}", {
        params: { path: { id: props.organizationId, place_id: props.id! } },
      })
    : await api.GET("/bff/manage/organizations/{id}/event-places/create-form", {
        params: { path: { id: props.organizationId } },
      });
  loading.value = false;

  if (!data) {
    loadError.value = error?.message ?? t("Error");
    return;
  }

  placeForm.value = data;
  originalName.value = data.name;
  form.value = eventPlaceFormValue(data);
  photoPreview.value = data.photo?.image_base64 ?? null;
}

async function scrollToFirstInvalid() {
  await nextTick();
  document.querySelector(".is-invalid, [data-test=image-error]")?.scrollIntoView({
    block: "center",
  });
}

async function save() {
  if (saving.value || !placeForm.value) return;

  saving.value = true;
  saveError.value = null;
  errors.value = {};

  const body = eventPlaceSaveBody(form.value);
  const path = { id: props.organizationId };
  const { data, error } = isUpdate.value
    ? await api.PUT("/bff/manage/organizations/{id}/event-places/{place_id}", {
        params: { path: { ...path, place_id: props.id! } },
        body,
      })
    : await api.POST("/bff/manage/organizations/{id}/event-places", {
        params: { path },
        body,
      });

  if (data) {
    // The server flashed the success message; the list renders it. Keep the spinner.
    location.assign(data.redirect_url);
    return;
  }

  saving.value = false;

  if (error && "errors" in error) {
    const mapped = toFieldErrors(error.errors, EVENT_PLACE_FORM_FIELDS);
    errors.value = mapped.byKey;
    if (mapped.unmatched.length) saveError.value = mapped.unmatched.join(" ");
    await scrollToFirstInvalid();
  } else {
    saveError.value = error?.message ?? t("Error");
  }
}

onMounted(load);
</script>

<template>
  <div>
    <AppBreadcrumb
      :items="[{ label: t('Places'), href: manage.eventPlaces(organizationId) }, { label: title }]"
    />

    <div v-if="loadError" class="alert alert-danger" role="alert">{{ loadError }}</div>

    <BOverlay :show="loading">
      <form v-if="placeForm" data-test="place-form" @submit.prevent="save">
        <EventPlaceFormFields
          v-model="form"
          v-model:errors="errors"
          v-model:photo-preview="photoPreview"
          :organization-id="organizationId"
          :licenses="placeForm.licenses"
          :exclude-id="id"
          :original-name="originalName"
        />

        <div v-if="saveError" class="alert alert-danger" role="alert">{{ saveError }}</div>

        <BButton id="submit" type="submit" variant="primary" :disabled="saving">
          <BSpinner v-if="saving" small />
          {{ isUpdate ? t("Update place") : t("Create place") }}
        </BButton>
      </form>
    </BOverlay>
  </div>
</template>
